import os
import re
from typing import List, Dict, Optional, Tuple
import requests
from urllib.parse import urlparse, parse_qs
import zipfile
from config.settings import settings

class DriveHandler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_file_id(self, url: str) -> Tuple[Optional[str], str]:
        """Extract file or folder ID from Google Drive URL and determine type"""
        # Check if it's a folder
        folder_patterns = [
            r'/folders/([a-zA-Z0-9-_]+)',
            r'folders/([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in folder_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), 'folder'
        
        # Check if it's a file
        file_patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'/d/([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), 'file'
        
        return None, 'unknown'
    
    def download_file(self, file_id: str, file_name: str = None) -> str:
        """Download a single file from Google Drive"""
        try:
            # Try direct download first
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            response = self.session.get(download_url, stream=True)
            
            # Check if we need to confirm download (for large files)
            if 'download_warning' in response.text:
                # Extract confirmation token
                for line in response.text.split('\n'):
                    if 'confirm=' in line:
                        confirm_token = re.search(r'confirm=([0-9A-Za-z_]+)', line)
                        if confirm_token:
                            download_url = f"https://drive.google.com/uc?export=download&confirm={confirm_token.group(1)}&id={file_id}"
                            response = self.session.get(download_url, stream=True)
                            break
            
            # Determine filename
            if not file_name:
                # Try to get filename from headers
                content_disposition = response.headers.get('content-disposition')
                if content_disposition:
                    filename_match = re.search(r'filename="(.+)"', content_disposition)
                    if filename_match:
                        file_name = filename_match.group(1)
                    else:
                        file_name = f"invoice_{file_id}.pdf"
                else:
                    file_name = f"invoice_{file_id}.pdf"
            
            # Save file
            file_path = os.path.join(settings.TEMP_DIR, file_name)
            os.makedirs(settings.TEMP_DIR, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return file_path
        except Exception as e:
            raise Exception(f"Error downloading file: {str(e)}")
    
    def download_folder_as_zip(self, folder_id: str) -> List[str]:
        """Download all files from a public Google Drive folder"""
        try:
            # For folders, we'll use a different approach
            # First, try to download as zip
            download_url = f"https://drive.google.com/drive/folders/{folder_id}"
            
            # Note: Downloading entire folders requires different handling
            # For now, return a message indicating manual download needed
            raise NotImplementedError(
                "Folder download requires manual selection of files. "
                "Please share individual files or use Google Drive API with authentication."
            )
            
        except Exception as e:
            raise Exception(f"Error downloading folder: {str(e)}")
    
    def get_direct_download_link(self, file_id: str) -> str:
        """Generate direct download link for a file"""
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    def validate_link(self, url: str) -> bool:
        """Validate if the provided link is a valid Google Drive link"""
        valid_domains = ['drive.google.com', 'docs.google.com']
        try:
            parsed = urlparse(url)
            return parsed.netloc in valid_domains
        except:
            return False