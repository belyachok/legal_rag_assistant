"""
LLM service module.
Handles loading and inference of local large language models.
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from transformers import BitsAndBytesConfig

from ..config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for loading and running local LLM inference.
    Supports models like Llama, Mistral, etc.
    """
    
    def __init__(self):
        """Initialize LLM service."""
        self.model_name = settings.llm_model_name
        self.model_type = settings.llm_model_type
        self.max_new_tokens = settings.max_new_tokens
        self.temperature = settings.temperature
        self._model = None
        self._tokenizer = None
        self._pipe = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        logger.info(f"LLM Service initialized with model: {self.model_name}")
    
    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            self._load_model()
        return self._model
    
    @property
    def tokenizer(self):
        """Lazy load the tokenizer."""
        if self._tokenizer is None:
            self._load_model()
        return self._tokenizer
    
    @property
    def pipe(self):
        """Lazy load the pipeline."""
        if self._pipe is None:
            self._load_model()
        return self._pipe
    
    def _load_model(self) -> None:
        """Load the model and tokenizer."""
        logger.info(f"Loading LLM: {self.model_name}")
        
        # Configure quantization for memory efficiency
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )
        
        try:
            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Load model with 4-bit quantization
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )
            
            # Create pipeline
            self._pipe = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self._tokenizer.eos_token_id
            )
            
            logger.info("LLM loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            raise
    
    def _generate_sync(self, prompt: str) -> str:
        """Synchronous generation."""
        try:
            response = self.pipe(prompt)[0]["generated_text"]
            # Remove the prompt from the response
            if response.startswith(prompt):
                response = response[len(prompt):]
            return response.strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"Error generating response: {str(e)}"
    
    async def generate(self, prompt: str) -> str:
        """Asynchronously generate text."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(self.executor, self._generate_sync, prompt)
        return response
    
    def format_prompt(self, context: str, question: str) -> str:
        """
        Format prompt for the LLM with system instruction and context.
        
        Args:
            context: Retrieved document chunks
            question: User's question
            
        Returns:
            Formatted prompt
        """
        system_prompt = """Ты - интеллектуальный помощник юриста. Отвечай на вопрос, используя только предоставленные фрагменты документов.

Инструкции:
1. Если ответ содержится в контексте - дай точный ответ, указав источник
2. Если ответ не содержится в контексте - скажи: "Я не нашел ответа в предоставленных документах"
3. Не используй свои знания вне предоставленного контекста
4. Отвечай на русском языке, кратко и по существу
5. Если в контексте есть несколько источников, укажи их"""

        return f"""{system_prompt}

Контекст:
{context}

Вопрос: {question}

Ответ:"""


llm_service = LLMService()