import json
import pandas as pd
from typing import List, Dict, Optional, Union
import os
from datetime import datetime
from config.settings import settings

class DataExtractor:
    def __init__(self):
        self.extracted_data = []
    
    def save_to_json(self, data: Union[Dict, List[Dict]], filename: str = None) -> str:
        """Save extracted data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"invoice_data_{timestamp}.json"
        
        filepath = os.path.join(settings.EXPORT_DIR, filename)
        os.makedirs(settings.EXPORT_DIR, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def save_to_csv(self, data: List[Dict], filename: str = None) -> str:
        """Save extracted data to CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"invoice_data_{timestamp}.csv"
        
        filepath = os.path.join(settings.EXPORT_DIR, filename)
        os.makedirs(settings.EXPORT_DIR, exist_ok=True)
        
        # Flatten nested data for CSV
        flattened_data = []
        for invoice in data:
            flat_invoice = self.flatten_dict(invoice)
            flattened_data.append(flat_invoice)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    def flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # For lists, we'll take the first item or create a summary
                if v and isinstance(v[0], dict):
                    # Handle list of items
                    items.append((f"{new_key}_count", len(v)))
                    items.append((f"{new_key}_total", sum(item.get('total', 0) for item in v if isinstance(item, dict))))
                else:
                    items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def aggregate_data(self, structured_data: List[Dict]) -> Dict:
        """Aggregate data from multiple invoices"""
        if not structured_data:
            return {}
        
        total_amount = 0
        total_tax = 0
        vendors = {}
        date_range = {"min": None, "max": None}
        
        for invoice in structured_data:
            if "error" not in invoice:
                # Sum totals
                total_amount += invoice.get("total", 0) or 0
                total_tax += invoice.get("tax", 0) or 0
                
                # Count vendors
                vendor = invoice.get("vendor_name", "Unknown")
                vendors[vendor] = vendors.get(vendor, 0) + 1
                
                # Track date range
                invoice_date = invoice.get("date")
                if invoice_date:
                    if date_range["min"] is None or invoice_date < date_range["min"]:
                        date_range["min"] = invoice_date
                    if date_range["max"] is None or invoice_date > date_range["max"]:
                        date_range["max"] = invoice_date
        
        return {
            "total_invoices": len(structured_data),
            "total_amount": total_amount,
            "total_tax": total_tax,
            "average_amount": total_amount / len(structured_data) if structured_data else 0,
            "vendors": vendors,
            "date_range": date_range
        }
