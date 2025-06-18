import os
import shutil
import base64
from typing import Optional
import streamlit as st
from config.settings import settings

def cleanup_temp_files():
    """Clean up and recreate the temporary directory."""
    if os.path.exists(settings.TEMP_DIR):
        shutil.rmtree(settings.TEMP_DIR)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)


def validate_file_size(file_path: str) -> bool:
    """Return True if the file at file_path is ≤ MAX_FILE_SIZE_MB (in megabytes)."""
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return file_size_mb <= settings.MAX_FILE_SIZE_MB


def format_currency(amount: Optional[float]) -> str:
    """
    Format a number as currency (e.g. 1234.5 → "$1,234.50").
    If amount is None or not a valid number, treat it as 0.0.
    """
    try:
        value = float(amount or 0.0)
    except (ValueError, TypeError):
        value = 0.0
    return f"${value:,.2f}"


def get_file_icon(file_extension: str) -> str:
    """
    Return an emoji icon based on file extension.
    Defaults to a paperclip if the extension isn’t recognized.
    """
    icons = {
        '.pdf': '📄',
        '.png': '🖼️',
        '.jpg': '🖼️',
        '.jpeg': '🖼️',
        '.csv': '📑',
        '.xlsx': '📊'
    }
    return icons.get(file_extension.lower(), '📎')


@st.cache_data
def load_sample_data() -> list[dict]:
    """Load sample invoice data for testing purposes."""
    return [
        {
            "invoice_number": "INV-001",
            "date": "2024-01-15",
            "vendor_name": "ABC Corp",
            "total": 1500.00,
            "tax": 150.00
        },
        {
            "invoice_number": "INV-002",
            "date": "2024-01-20",
            "vendor_name": "XYZ Ltd",
            "total": 2300.00,
            "tax": 230.00
        }
    ]


def create_download_link(file_path: str, link_text: str) -> str:
    """
    Create an HTML download link for a given file.
    Embeds the file content as base64 so Streamlit can render it.
    """
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    filename = os.path.basename(file_path)
    return f'<a href="data:file/octet-stream;base64,{b64}" download="{filename}">{link_text}</a>'
