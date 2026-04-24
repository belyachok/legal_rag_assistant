"""
Pydantic models for document operations.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    id: str
    name: str
    status: str
    message: str = Field(default="Document uploaded successfully")


class DocumentInfo(BaseModel):
    """Document information response."""
    id: str
    name: str
    file_size: int
    pages: int
    status: str
    error_message: Optional[str] = None
    created_at: str
    processed_at: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response for list of documents."""
    documents: List[DocumentInfo]
    total: int


class DocumentDeleteResponse(BaseModel):
    """Response for document deletion."""
    id: str
    success: bool
    message: str