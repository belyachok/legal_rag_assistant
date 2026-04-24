"""
Chat API endpoints.
Handles question answering via RAG.
"""

import logging
from typing import Optional
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.chat import ChatRequest, ChatResponse, Source
from ..services.rag_service import rag_service
from ..core.database import get_db, Document

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question about the uploaded documents.
    """
    # Validate document ID if provided
    if request.document_id:
        doc = db.query(Document).filter(Document.id == request.document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        if doc.status != "indexed":
            raise HTTPException(
                status_code=400,
                detail=f"Document is not ready yet. Status: {doc.status}"
            )
    
    # Get answer from RAG service
    answer, sources, processing_time = await rag_service.answer_question(
        question=request.question,
        document_id=request.document_id,
        top_k=request.top_k
    )
    
    return ChatResponse(
        answer=answer,
        sources=sources,
        question=request.question,
        processing_time_ms=processing_time
    )


@router.post("/ask/stream")
async def ask_question_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question with streaming response.
    """
    # TODO: Implement streaming response with Server-Sent Events
    # For now, return regular response
    return await ask_question(request, db)