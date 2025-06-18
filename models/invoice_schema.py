from typing import List, Optional
from datetime import date
from pydantic import BaseModel

class LineItem(BaseModel):
    """Model for invoice line items"""
    description: str
    quantity: float
    unit_price: float
    total: float

class Invoice(BaseModel):
    """Model for invoice data"""
    invoice_number: str
    date: str
    vendor_name: str
    vendor_address: Optional[str] = None
    customer_name: str
    customer_address: Optional[str] = None
    items: List[LineItem]
    subtotal: float
    tax: float
    total: float
    payment_terms: Optional[str] = None
    due_date: Optional[str] = None
    source_file: str

class InvoiceAnalysis(BaseModel):
    """Model for invoice analysis results"""
    total_invoices: int
    total_amount: float
    average_amount: float
    total_tax: float
    vendors: dict
    date_range: dict
    insights: Optional[str] = None# Smart Invoice Extractor System