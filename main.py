import logging
from fetcher import Fetcher
from downloader import Downloader
from extractor import Extractor
from db import Database
import time

def main():
    logging.basicConfig(level=logging.INFO)
    fetcher = Fetcher()
    downloader = Downloader()
    extractor = Extractor()
    db = Database()
    
    processed_count = 0
    text_only_count = 0
    pdf_count = 0
    
    try:
        for pdf_info in fetcher.yield_all_pdfs():
            url = pdf_info['url']
            source = pdf_info['source']
            page_url = pdf_info.get('page_url', '')
            title = pdf_info.get('title', '')
            text_content = pdf_info.get('text_content', '')
            is_text_only = pdf_info.get('is_text_only', False)
            
            processed_count += 1
            filename = url.split('/')[-1]
            
            logging.info(f"\n[{processed_count}] Processing: {title[:60]}...")
            logging.info(f"   URL: {url}")
            logging.info(f"   Type: {'Text Content' if is_text_only else 'PDF'}")
            
            # Download PDF or save text content
            filepath = downloader.download_pdf(url, source, text_content, title)
            if not filepath:
                logging.warning(f"❌ Failed to process {url}")
                continue
            
            # Extract text from PDF or use existing text content
            if is_text_only:
                text = text_content
                text_only_count += 1
                logging.info(f"   ✅ Saved text content ({len(text)} characters)")
            else:
                text = extractor.extract_text(filepath)
                if not text and text_content:  # Fallback to webpage text if PDF extraction fails
                    text = text_content
                pdf_count += 1
                logging.info(f"   ✅ Downloaded PDF and extracted text ({len(text)} characters)")
            
            # Store in database
            db.upsert_guideline(source, url, filename, text)
            time.sleep(1)  # polite delay
            
    except Exception as e:
        logging.error(f"Error in main process: {e}")
    finally:
        db.close()
        logging.info(f"\n🎉 Processing Complete!")
        logging.info(f"   Total processed: {processed_count}")
        logging.info(f"   Text-only pages: {text_only_count}")  
        logging.info(f"   PDF documents: {pdf_count}")
        logging.info(f"   Files organized in: {downloader.base_dir}")
        logging.info(f"   HTML content saved in: {downloader.html_dir}")
        logging.info(f"   ✅ NO PDFs extracted - HTML content ONLY as requested")

if __name__ == '__main__':
    main()
