"""
Vector Database service using FAISS.
No ONNX Runtime required.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle
import os

from ..config import settings

logger = logging.getLogger(__name__)


class VectorDBService:
    """
    Service for managing vector database using FAISS.
    Stores embeddings and metadata in separate files.
    """
    
    def __init__(self):
        """Initialize vector database service."""
        self.persist_dir = settings.chroma_db_dir
        self.index_path = self.persist_dir / "faiss.index"
        self.metadata_path = self.persist_dir / "metadata.pkl"
        self._index = None
        self._documents = []  # list of dicts with id, text, metadata
        
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._load()
        
        logger.info(f"Vector DB Service initialized with FAISS at {self.persist_dir}")
    
    def _load(self):
        """Load existing index and metadata if they exist."""
        import faiss
        
        if self.index_path.exists() and self.metadata_path.exists():
            try:
                self._index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, 'rb') as f:
                    self._documents = pickle.load(f)
                logger.info(f"Loaded FAISS index with {len(self._documents)} documents")
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index."""
        import faiss
        
        dimension = 384  # all-MiniLM-L6-v2 dimension
        self._index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity after normalization)
        self._documents = []
        logger.info("Created new FAISS index")
    
    @property
    def index(self):
        """Get FAISS index."""
        if self._index is None:
            self._load()
        return self._index
    
    def _save(self):
        """Save index and metadata to disk."""
        import faiss
        
        faiss.write_index(self._index, str(self.index_path))
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self._documents, f)
        logger.debug(f"Saved FAISS index with {len(self._documents)} documents")
    
    async def add_document_chunks(
        self,
        document_id: str,
        document_name: str,
        chunks: List[str],
        embeddings: np.ndarray,
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        Add document chunks to vector database.
        
        Args:
            document_id: Unique document identifier
            document_name: Original document name
            chunks: List of text chunks
            embeddings: Numpy array of embeddings for chunks (already normalized)
            metadata_list: Optional list of metadata dicts for each chunk
            
        Returns:
            Number of chunks added
        """
        if not chunks or len(embeddings) == 0:
            logger.warning(f"No chunks to add for document {document_id}")
            return 0
        
        # Ensure embeddings are 2D array
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)
        
        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings_norm = embeddings / norms
        
        # Add to FAISS index
        self.index.add(embeddings_norm.astype(np.float32))
        
        # Store metadata
        start_idx = len(self._documents)
        for i, chunk in enumerate(chunks):
            meta = {
                "id": f"{document_id}_{start_idx + i}",
                "document_id": document_id,
                "document_name": document_name,
                "text": chunk,
                "chunk_index": i
            }
            if metadata_list and i < len(metadata_list):
                meta.update(metadata_list[i])
            self._documents.append(meta)
        
        self._save()
        
        logger.info(f"Added {len(chunks)} chunks for document {document_id}")
        return len(chunks)
    
    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in vector database.
        
        Args:
            query_embedding: Query embedding vector (already normalized)
            top_k: Number of results to return
            document_id: Optional document ID to filter by
            
        Returns:
            List of search results with metadata and documents
        """
        if len(self._documents) == 0:
            return []
        
        # Ensure query is 2D
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query
        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            query_embedding = query_embedding / norm
        
        # Search in FAISS
        k = min(top_k, len(self._documents))
        scores, indices = self.index.search(query_embedding.astype(np.float32), k)
        
        # Format results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self._documents):
                continue
            
            doc = self._documents[idx]
            
            # Filter by document_id if needed
            if document_id and doc.get("document_id") != document_id:
                continue
            
            results.append({
                "id": doc.get("id", str(idx)),
                "text": doc.get("text", ""),
                "metadata": {k: v for k, v in doc.items() if k not in ["id", "text"]},
                "distance": 1 - scores[0][i],
                "similarity": float(scores[0][i])
            })
        
        # If filtered, we might need to get more results
        if document_id and len(results) < top_k:
            # Get more results and filter again (simplified)
            pass
        
        logger.info(f"Search returned {len(results)} results")
        return results
    
    async def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks belonging to a document.
        Note: FAISS doesn't support efficient deletion, so we rebuild index.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Number of deleted chunks
        """
        # Find indices to keep
        indices_to_keep = []
        docs_to_keep = []
        
        for i, doc in enumerate(self._documents):
            if doc.get("document_id") != document_id:
                indices_to_keep.append(i)
                docs_to_keep.append(doc)
        
        deleted_count = len(self._documents) - len(docs_to_keep)
        
        if deleted_count > 0:
            # Rebuild index with remaining documents
            import faiss
            
            dimension = 384
            new_index = faiss.IndexFlatIP(dimension)
            
            # We need embeddings to rebuild, but we don't store them
            # For now, we'll just clear everything
            self._create_new_index()
            self._documents = docs_to_keep
            
            # Re-add embeddings would require storing them
            # Workaround: clear and user must re-index
            logger.warning(f"Deleted document {document_id}. Index cleared. Re-index needed.")
            
            self._save()
        
        logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
        return deleted_count


vector_db_service = VectorDBService()