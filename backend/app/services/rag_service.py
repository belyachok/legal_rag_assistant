"""
RAG (Retrieval-Augmented Generation) service module.
Coordinates all services to implement the RAG pipeline.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import uuid
from pathlib import Path

from .ocr_service import ocr_service
from .embedding_service import embedding_service
from .vector_db_service import vector_db_service
from .llm_service import llm_service
from ..models.chat import Source
from ..core.database import get_db, Document, DocumentStatus
from ..core.utils import generate_document_id, get_file_size
from ..config import settings
from datetime import datetime

logger = logging.getLogger(__name__)


class RAGService:
    """
    Main RAG (Retrieval-Augmented Generation) service.
    Orchestrates the entire pipeline from document ingestion to question answering.
    """
    
    def __init__(self):
        """Initialize RAG service."""
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.top_k = settings.top_k_results
        logger.info("RAG Service initialized")
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += (self.chunk_size - self.chunk_overlap)
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    async def process_document(self, file_path: Path, document_name: str) -> Tuple[str, bool, str]:
        """
        Process a document through the full pipeline:
        1. OCR extraction
        2. Text chunking
        3. Embedding generation
        4. Vector DB storage
        """
        # Генерируем ID документа
        document_id = generate_document_id()
        
        try:
            # Получаем сессию базы данных
            db = next(get_db())
            
            # Сохраняем документ в БД
            doc = Document(
                id=document_id,
                name=document_name,
                file_path=str(file_path),
                file_size=get_file_size(file_path),
                status=DocumentStatus.OCR_PROCESSING
            )
            db.add(doc)
            db.commit()
            
            logger.info(f"Processing document {document_id}: {document_name}")
            
            # Шаг 1: Извлечение текста (OCR)
            logger.info(f"Starting OCR for {document_id}")
            full_text, total_pages, page_texts = await ocr_service.extract_text_from_pdf(file_path)
            full_text = ocr_service.cleanup_text(full_text)
            
            # Обновляем документ результатами OCR
            doc.ocr_text = full_text
            doc.pages = total_pages
            doc.status = DocumentStatus.INDEXING_PROCESSING
            db.commit()
            
            if not full_text.strip():
                doc.status = DocumentStatus.OCR_FAILED
                doc.error_message = "No text extracted from document"
                db.commit()
                return document_id, False, "No text extracted"
            
            logger.info(f"OCR completed for {document_id}, extracted {len(full_text)} chars")
            
            # Шаг 2: Разбиваем текст на чанки
            chunks = self.chunk_text(full_text)
            logger.info(f"Created {len(chunks)} chunks for {document_id}")
            
            # Шаг 3: Генерируем эмбеддинги
            embeddings = await embedding_service.encode(chunks)
            logger.info(f"Generated embeddings for {document_id}")
            
            # Шаг 4: Сохраняем в векторную базу данных
            metadata_list = [
                {
                    "page": idx // 10,
                    "chunk_index": idx,
                    "source": document_name
                }
                for idx in range(len(chunks))
            ]
            
            await vector_db_service.add_document_chunks(
                document_id=document_id,
                document_name=document_name,
                chunks=chunks,
                embeddings=embeddings,
                metadata_list=metadata_list
            )
            
            # Обновляем статус документа
            from datetime import datetime
            doc.status = DocumentStatus.INDEXED
            doc.processed_at = datetime.now()
            db.commit()
            
            logger.info(f"Successfully processed document {document_id}")
            return document_id, True, ""
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            try:
                db = next(get_db())
                doc = db.query(Document).filter(Document.id == document_id).first()
                if doc:
                    doc.status = DocumentStatus.OCR_FAILED
                    doc.error_message = str(e)
                    db.commit()
            except:
                pass
            return document_id, False, str(e)
    
    async def answer_question(
        self,
        question: str,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> Tuple[str, List[Source], float]:
        start_time = time.time()
        
        try:
            query_embedding = await embedding_service.encode_query(question)
            k = top_k or self.top_k
            search_results = await vector_db_service.search(
                query_embedding=query_embedding,
                top_k=k,
                document_id=document_id
            )
            
            if not search_results:
                return "Я не нашел ответа в предоставленных документах.", [], (time.time() - start_time) * 1000
            
            sources = []
            for i, result in enumerate(search_results):
                chunk_text = result["text"]
                metadata = result["metadata"]
                similarity = result.get("similarity", 0)
                
                sources.append(Source(
                    document_id=metadata.get("document_id", ""),
                    document_name=metadata.get("document_name", "Unknown"),
                    chunk_text=chunk_text[:500],
                    page=metadata.get("page"),
                    relevance_score=similarity
                ))
            
            # Формируем ответ из первого найденного фрагмента
            answer = f"Найдена информация:\n\n{sources[0].chunk_text}"
            
            processing_time = (time.time() - start_time) * 1000
            return answer, sources, processing_time
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"Ошибка: {str(e)}", [], (time.time() - start_time) * 1000


rag_service = RAGService()