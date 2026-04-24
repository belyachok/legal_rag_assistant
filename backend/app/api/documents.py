"""
Document management API endpoints.
Handles upload, list, delete operations.
"""

import shutil
import uuid
from pathlib import Path
from typing import List
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..core.database import get_db, Document, DocumentStatus
from ..models.document import (
    DocumentUploadResponse,
    DocumentInfo,
    DocumentListResponse,
    DocumentDeleteResponse
)
from ..services.rag_service import rag_service
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


async def process_document_background(document_id: str, file_path: Path, document_name: str):
    """
    Background task to process document after upload.
    """
    await rag_service.process_document(file_path, document_name)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Проверка на дубликат по имени файла
    existing = db.query(Document).filter(
        Document.name == file.filename,
        Document.status != DocumentStatus.DELETED
    ).first()
    
    if existing:
        return DocumentUploadResponse(
            id=existing.id,
            name=file.filename,
            status=existing.status.value,
            message="Document already exists"
        )
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_id = str(uuid.uuid4())
    file_path = settings.upload_dir / f"{file_id}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    doc = Document(
        id=file_id,
        name=file.filename,
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        status=DocumentStatus.UPLOADED
    )
    db.add(doc)
    db.commit()
    
    background_tasks.add_task(process_document_background, file_id, file_path, file.filename)
    
    return DocumentUploadResponse(
        id=file_id,
        name=file.filename,
        status="uploaded",
        message="Document uploaded successfully"
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get list of all documents.
    """
    documents = db.query(Document).filter(
        Document.status != DocumentStatus.DELETED
    ).offset(skip).limit(limit).all()
    
    total = db.query(Document).filter(
        Document.status != DocumentStatus.DELETED
    ).count()
    
    return DocumentListResponse(
        documents=[DocumentInfo(**doc.to_dict()) for doc in documents],
        total=total
    )


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get document by ID.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentInfo(**doc.to_dict())


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document and all its associated data.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete from vector database
        from ..services.vector_db_service import vector_db_service
        await vector_db_service.delete_document(document_id)
        
        # Delete file from filesystem
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Update or delete database record
        doc.status = DocumentStatus.DELETED
        db.commit()
        
        return DocumentDeleteResponse(
            id=document_id,
            success=True,
            message="Document deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")