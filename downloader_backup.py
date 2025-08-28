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
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:80]  # Limit length
        
        if not safe_title:
            safe_title = "document"
            
        # Add PDF suffix if it's from PDF extraction
        if is_pdf:
            filename = f"{safe_title}_PDF.txt"
        else:
            filename = f"{safe_title}_HTML.txt"
        
        filepath = os.path.join(self.html_dir, filename)
        
        # Handle duplicate filenames
        counter = 1
        original_filepath = filepath
        while os.path.exists(filepath):
            name, ext = os.path.splitext(original_filepath)
            filepath = f"{name}_{counter}{ext}"
            counter += 1
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Source: {source}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Title: {title}\n")
                f.write(f"Type: {'PDF' if is_pdf else 'HTML'}\n")
                f.write("="*80 + "\n\n")
                f.write(text_content)
                
            logging.info(f"✅ Saved {'PDF' if is_pdf else 'HTML'} text content to: {filepath}")
            return filepath
            
        except Exception as e:
            logging.warning(f"Failed to save text content: {e}")
            return None

    def download_pdf(self, url, source, text_content="", title=""):
        """Download PDF and extract text from both HTML and PDF"""
        
        # Always save HTML text content if available
        html_text_filepath = None
        if text_content and len(text_content.strip()) > 50:
            html_text_filepath = self.save_text_content(url, source, text_content, title, is_pdf=False)
        
        # If it's a text-only page (no PDF), return the HTML text file path
        if not url.lower().endswith('.pdf'):
            return html_text_filepath
        
        # Handle PDF downloads
        filename = os.path.basename(url.split('?')[0])
        if not filename.endswith('.pdf'):
            filename += '.pdf'
            
        filepath = os.path.join(self.pdf_dir, filename)
        
        HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        
        # Download PDF
        for attempt in range(RETRY_COUNT):
            try:
                resp = requests.get(url, timeout=20, headers=HEADERS)
                if resp.status_code == 200 and resp.headers.get('content-type','').startswith('application/pdf'):
                    with open(filepath, 'wb') as f:
                        f.write(resp.content)
                    logging.info(f"📄 Downloaded PDF: {url} -> {filepath}")
                    
                    # Extract text from the downloaded PDF
                    pdf_text = self.extract_pdf_text(filepath)
                    if pdf_text and len(pdf_text.strip()) > 50:
                        pdf_text_filepath = self.save_text_content(url, source, pdf_text, title, is_pdf=True)
                        logging.info(f"📝 Extracted PDF text: {len(pdf_text)} characters")
                        return pdf_text_filepath
                    else:
                        logging.warning(f"PDF text extraction failed or empty for {filename}")
                        return filepath
                        
                else:
                    raise Exception(f"Bad response: {resp.status_code}")
                    
            except Exception as e:
                logging.warning(f"Download failed for {url}: {e}")
                if attempt < RETRY_COUNT-1:
                    time.sleep(RETRY_DELAY)
        
        # If PDF download failed but we have HTML text content, return HTML text file path
        return html_text_filepath
