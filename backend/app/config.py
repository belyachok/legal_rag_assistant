"""
Configuration management module for the application.
Handles loading environment variables and providing configuration objects.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="Legal RAG Assistant", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(default="dev-secret-key", alias="SECRET_KEY")
    
    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    upload_dir: Path = Field(
        default=Path(__file__).resolve().parent / "storage" / "uploads",
        alias="UPLOAD_DIR"
    )
    chroma_db_dir: Path = Field(
        default=Path(__file__).resolve().parent / "storage" / "chroma_db",
        alias="CHROMA_DB_DIR"
    )
    metadata_db_path: Path = Field(
        default=Path(__file__).resolve().parent / "storage" / "metadata.db",
        alias="METADATA_DB_PATH"
    )
    
    # OCR Settings
    tesseract_cmd: str = Field(default="tesseract", alias="TESSERACT_CMD")
    ocr_language: str = Field(default="rus", alias="OCR_LANGUAGE")
    
    # Embedding Model
    embedding_model_name: str = Field(
        default="intfloat/multilingual-e5-large",
        alias="EMBEDDING_MODEL_NAME"
    )
    embedding_batch_size: int = Field(default=32, alias="EMBEDDING_BATCH_SIZE")
    
    # RAG Settings
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    top_k_results: int = Field(default=5, alias="TOP_K_RESULTS")
    
    # LLM Settings
    llm_model_name: str = Field(
        default="meta-llama/Llama-2-7b-chat-hf",
        alias="LLM_MODEL_NAME"
    )
    llm_model_type: str = Field(default="llama", alias="LLM_MODEL_TYPE")
    max_new_tokens: int = Field(default=512, alias="MAX_NEW_TOKENS")
    temperature: float = Field(default=0.3, alias="TEMPERATURE")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def setup_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_db_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_db_path.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()