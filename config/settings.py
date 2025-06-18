import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # OpenAI Settings
    OPENAI_MODEL = "gpt-4-turbo-preview"
    TEMPERATURE = 0.1
    MAX_TOKENS = 4000
    
    # File Processing
    SUPPORTED_FORMATS = ['.pdf', '.png', '.jpg', '.jpeg']
    MAX_FILE_SIZE_MB = 10
    TEMP_DIR = "data/temp"
    EXPORT_DIR = "data/exports"
    
    # Invoice Extraction Schema
    INVOICE_SCHEMA = {
        "invoice_number": "string",
        "date": "string (YYYY-MM-DD)",
        "vendor_name": "string",
        "vendor_address": "string",
        "customer_name": "string",
        "customer_address": "string",
        "items": [
            {
                "description": "string",
                "quantity": "number",
                "unit_price": "number",
                "total": "number"
            }
        ],
        "subtotal": "number",
        "tax": "number",
        "total": "number",
        "payment_terms": "string",
        "due_date": "string (YYYY-MM-DD)"
    }
    
    # Streamlit Settings
    PAGE_TITLE = "Smart Invoice Extractor"
    PAGE_ICON = "📄"
    LAYOUT = "wide"

settings = Settings()