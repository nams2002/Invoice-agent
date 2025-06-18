import os
from typing import List, Dict, Union
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import json
from config.settings import settings

class InvoiceProcessor:
    def __init__(self):
        self.processed_invoices = []
        
    def process_file(self, file_path: str) -> Dict:
        """Process a single invoice file"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            text = self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        return {
            "file_name": os.path.basename(file_path),
            "raw_text": text,
            "file_path": file_path
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyPDF2 and OCR fallback"""
        text = ""
        
        try:
            # Try PyPDF2 first
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            # If no text extracted, use OCR
            if not text.strip():
                text = self.ocr_pdf(pdf_path)
                
        except Exception as e:
            # Fallback to OCR
            text = self.ocr_pdf(pdf_path)
        
        return text
    
    def ocr_pdf(self, pdf_path: str) -> str:
        """OCR PDF using pdf2image and pytesseract"""
        try:
            images = convert_from_path(pdf_path)
            text = ""
            
            for i, image in enumerate(images):
                text += f"--- Page {i+1} ---\n"
                text += pytesseract.image_to_string(image)
                text += "\n"
            
            return text
        except Exception as e:
            raise Exception(f"OCR failed: {str(e)}")
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise Exception(f"Image OCR failed: {str(e)}")
    
    def process_multiple_files(self, file_paths: List[str]) -> List[Dict]:
        """Process multiple invoice files"""
        results = []
        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                results.append({
                    "file_name": os.path.basename(file_path),
                    "error": str(e),
                    "file_path": file_path
                })
        
        self.processed_invoices = results
        return results
