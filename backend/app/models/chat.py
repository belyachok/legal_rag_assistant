"""
Pydantic models for chat operations.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Source(BaseModel):
    """Source reference for answer."""
    document_id: str
    document_name: str
    chunk_text: str
    page: Optional[int] = None
    relevance_score: Optional[float] = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., description="User's question", min_length=1)
    document_id: Optional[str] = Field(
        default=None,
        description="Optional document ID to limit search"
    )
    top_k: Optional[int] = Field(
        default=5,
        description="Number of relevant chunks to retrieve",
        ge=1,
        le=10
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    sources: List[Source]
    question: str
    processing_time_ms: float


class ChatHistoryItem(BaseModel):
    """Single chat history item."""
    question: str
    answer: str
    timestamp: str
    sources: List[Source]