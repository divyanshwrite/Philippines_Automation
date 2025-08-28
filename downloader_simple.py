import os
import logging
from config import DOWNLOAD_DIR

logging.basicConfig(level=logging.INFO)

class Downloader:
    def __init__(self):
        # Create ONLY HTML_EXTRACT folder - NO PDF processing
        self.base_dir = DOWNLOAD_DIR
        self.html_dir = os.path.join(self.base_dir, "HTML_EXTRACT")
        
        os.makedirs(self.html_dir, exist_ok=True)
        logging.info(f"📁 Created HTML_EXTRACT folder only: {self.html_dir}")

    def save_text_content(self, url, source, text_content, title):
        """Save ONLY HTML text content to HTML_EXTRACT folder"""
        if not text_content or len(text_content.strip()) < 50:
            return None
            
        # Create safe filename from title
        safe_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', ' ')[:70]  # Limit length
        filename = f"{safe_title}_HTML.txt"
        
        # Handle duplicates
        filepath = os.path.join(self.html_dir, filename)
        counter = 1
        original_filepath = filepath
        while os.path.exists(filepath):
            base_name = original_filepath.replace('_HTML.txt', '')
            filepath = f"{base_name}_HTML_{counter}.txt"
            counter += 1
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Source: {source}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Title: {title}\n")
                f.write(f"Type: HTML Content\n")
                f.write("="*80 + "\n\n")
                f.write(text_content)
            
            logging.info(f"✅ Saved HTML text content to: {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"Failed to save text content: {e}")
            return None

    def download_pdf(self, url, source, text_content, title):
        """
        SIMPLIFIED: Only save HTML text content - NO PDF processing
        This method only handles text content now
        """
        return self.save_text_content(url, source, text_content, title)
