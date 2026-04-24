"""
OCR service module.
Handles image preprocessing and text extraction from scanned documents.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import tempfile

import cv2
import numpy as np
import pytesseract
from PIL import Image
import pdf2image

from ..config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """
    Service for Optical Character Recognition (OCR).
    Uses Tesseract with OpenCV preprocessing.
    """
    
    def __init__(self):
        """Initialize OCR service."""
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        
        self.language = settings.ocr_language
        self.executor = ThreadPoolExecutor(max_workers=2)
        logger.info(f"OCR Service initialized with language: {self.language}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply threshold (binarization) using Otsu's method
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.medianBlur(thresh, 3)
        
        # Deskew (correct rotation)
        coords = np.column_stack(np.where(denoised > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = 90 + angle
            if abs(angle) > 0.5:
                (h, w) = denoised.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                denoised = cv2.warpAffine(denoised, M, (w, h), 
                                          flags=cv2.INTER_CUBIC, 
                                          borderMode=cv2.BORDER_REPLICATE)
        
        return denoised
    
    def extract_text_from_image(self, image: np.ndarray) -> str:
        """
        Extract text from a single image.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Extracted text
        """
        processed = self.preprocess_image(image)
        pil_image = Image.fromarray(processed)
        custom_config = f'--oem 3 --psm 6 -l {self.language}'
        text = pytesseract.image_to_string(pil_image, config=custom_config)
        return text.strip()
    
    def extract_text_from_pdf_page(self, pdf_path: Path, page_num: int) -> Tuple[int, str]:
        """
        Extract text from a specific page of a PDF.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            Tuple of (page_number, extracted_text)
        """
        try:
            images = pdf2image.convert_from_path(
                str(pdf_path),
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=300
            )
            
            if not images:
                return page_num, ""
            
            image = np.array(images[0])
            text = self.extract_text_from_image(image)
            return page_num, text
            
        except Exception as e:
            logger.error(f"Error processing page {page_num}: {e}")
            return page_num, ""
    
    async def extract_text_from_pdf(self, pdf_path: Path) -> Tuple[str, int, List[Tuple[int, str]]]:
        """Extract text from PDF using PyPDF2 (no Poppler needed)."""
        try:
            import PyPDF2
            
            text_parts = []
            total_pages = 0
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        page_text = f"[PAGE {page_num + 1}]\n{text}"
                        text_parts.append(page_text)
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(full_text)} characters from {total_pages} pages")
            return full_text, total_pages, []
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def cleanup_text(self, text: str) -> str:
        """
        Clean up extracted text by removing OCR artifacts.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        import re
        
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\b[a-zA-Z0-9]\b', '', text)
        text = text.replace('|', 'I').replace('0', 'О').replace('3', 'З')
        text = re.sub(r' +', ' ', text)
        text = text.strip()
        
        return text


ocr_service = OCRService()