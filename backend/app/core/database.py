"""
Database module for managing document metadata.
Uses SQLite for storing document information.
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any

from ..config import settings


# Database setup
engine = create_engine(
    f"sqlite:///{settings.metadata_db_path}",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DocumentStatus(str, PyEnum):
    """Document processing status."""
    UPLOADED = "uploaded"
    OCR_PENDING = "ocr_pending"
    OCR_PROCESSING = "ocr_processing"
    OCR_COMPLETED = "ocr_completed"
    OCR_FAILED = "ocr_failed"
    INDEXING_PENDING = "indexing_pending"
    INDEXING_PROCESSING = "indexing_processing"
    INDEXED = "indexed"
    INDEXING_FAILED = "indexing_failed"
    DELETED = "deleted"


class Document(Base):
    """Document metadata model."""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    pages = Column(Integer, default=0)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED)
    ocr_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "file_size": self.file_size,
            "pages": self.pages,
            "status": self.status.value,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)