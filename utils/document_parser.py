from typing import Dict, Any, Optional
import os
import logging
import PyPDF2
from datetime import datetime
import pytesseract
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class DocumentParser:
    """Utility for parsing different document formats."""
    
    def __init__(self, ocr_enabled: bool = True):
        self.ocr_enabled = ocr_enabled
        
    def parse(self, file_path: str) -> str:
        """Parse a document and return the text content."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self._parse_pdf(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']:
            return self._parse_image(file_path)
        elif file_ext in ['.txt', '.md', '.csv']:
            return self._parse_text_file(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_ext}")
            return ""
    
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from the document."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {}
            
        file_ext = os.path.splitext(file_path)[1].lower()
        file_stat = os.stat(file_path)
        
        # Common metadata for all file types
        metadata = {
            "filename": os.path.basename(file_path),
            "file_size": file_stat.st_size,
            "last_modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "file_type": file_ext[1:] if file_ext.startswith('.') else file_ext
        }
        
        # Add format-specific metadata
        if file_ext == '.pdf':
            pdf_metadata = self._get_pdf_metadata(file_path)
            metadata.update(pdf_metadata)
            
        return metadata
    
    def _parse_pdf(self, file_path: str) -> str:
        """Parse a PDF file and extract text."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Check if PDF has text
                first_page = reader.pages[0]
                text = first_page.extract_text()
                
                # If no text is found and OCR is enabled, use OCR
                if not text.strip() and self.ocr_enabled:
                    logger.info(f"No text found in PDF, attempting OCR: {file_path}")
                    return self._ocr_pdf(file_path)
                
                # Extract text from all pages
                full_text = []
                for page in reader.pages:
                    full_text.append(page.extract_text())
                    
                return "\n".join(full_text)
                
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            return ""
    
    def _ocr_pdf(self, file_path: str) -> str:
        """Perform OCR on a PDF file."""
        # This would require converting PDF to images first
        # This is a simplified implementation
        return "OCR result would be here"
    
    def _parse_image(self, file_path: str) -> str:
        """Parse an image file using OCR."""
        if not self.ocr_enabled:
            logger.warning("OCR is not enabled, cannot extract text from image")
            return ""
            
        try:
            # Read the image
            image = cv2.imread(file_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding to improve OCR
            _, threshold = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Perform OCR
            text = pytesseract.image_to_string(threshold)
            
            return text
            
        except Exception as e:
            logger.error(f"Error parsing image {file_path}: {str(e)}")
            return ""
    
    def _parse_text_file(self, file_path: str) -> str:
        """Parse a plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with a different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Error parsing text file {file_path}: {str(e)}")
                return ""
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {str(e)}")
            return ""
    
    def _get_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from a PDF file."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata = {
                    "num_pages": len(reader.pages)
                }
                
                # Extract document info
                if reader.metadata:
                    for key, value in reader.metadata.items():
                        if key.startswith('/'):
                            key = key[1:]  # Remove the leading slash
                        metadata[key.lower()] = value
                        
                return metadata
                
        except Exception as e:
            logger.error(f"Error extracting PDF metadata {file_path}: {str(e)}")
            return {}