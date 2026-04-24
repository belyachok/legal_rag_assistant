"""
Embedding service module.
Handles text vectorization using sentence-transformers.
"""

import logging
import numpy as np
from typing import List, Union, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from sentence_transformers import SentenceTransformer
import torch

from ..config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings.
    Uses sentence-transformers for vectorization.
    """
    
    def __init__(self):
        """Initialize embedding service."""
        self.model_name = settings.embedding_model_name
        self.batch_size = settings.embedding_batch_size
        self._model = None
        self._device = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        logger.info(f"Embedding Service created with model: {self.model_name}")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            self._load_model()
        return self._model
    
    @property
    def device(self) -> str:
        """Get device (CPU/GPU) for inference."""
        if self._device is None:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        return self._device
    
    def _load_model(self) -> None:
        """Load the embedding model."""
        logger.info(f"Loading embedding model: {self.model_name}")
        logger.info(f"Using device: {self.device}")
        
        try:
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _encode_sync(self, texts: List[str]) -> np.ndarray:
        """Synchronous encoding of texts."""
        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
    
    async def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Asynchronously encode texts to embeddings."""
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(self.executor, self._encode_sync, texts)
        return embeddings
    
    async def encode_query(self, query: str) -> np.ndarray:
        """Encode a single query text."""
        embeddings = await self.encode(query)
        return embeddings[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model."""
        return self.model.get_sentence_embedding_dimension()


embedding_service = EmbeddingService()