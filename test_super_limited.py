#!/usr/bin/env python3
"""
Super limited test - only fetch first 10 documents from API
"""
import logging
import time
from fetcher import Fetcher
from db import Database

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def main():
    # Initialize components
    db = Database()
    
    processed_count = 0
    max_documents = 10  # Limit to 10 documents for testing
    
    try:
        logging.info(f"🧪 SUPER LIMITED TEST - fetching only {max_documents} documents from API...")
        
        # Create fetcher but manually control the process
        fetcher = Fetcher()
        
        # We'll manually iterate and stop early
        for pdf_info in fetcher.yield_all_pdfs():
            if processed_count >= max_documents:
                logging.info(f"🛑 Reached limit of {max_documents} documents - stopping test")
                break
                
            try:
                processed_count += 1
                title = pdf_info['title']
                
                logging.info(f"\n✅ [{processed_count}/{max_documents}] Processing: {title[:60]}...")
                logging.info(f"   URL: {pdf_info['link_guidance']}")
                
                # Insert/update document in database
                db.upsert_guideline(
                    title=pdf_info['title'],
                    summary=pdf_info['summary'],
                    issue_date=pdf_info['issue_date'],
                    products=pdf_info['products'],
                    link_guidance=pdf_info['link_guidance'],
                    link_file=pdf_info['link_file'],
                    country=pdf_info['country'],
                    agency=pdf_info['agency'],
                    all_text=pdf_info['all_text'],
                    json_data=pdf_info['json_data']
                )
                    
            except Exception as e:
                logging.error(f"   ❌ Error processing document {processed_count}: {e}")
                continue
        
    except Exception as e:
        logging.error(f"❌ Error in main execution: {e}")
    finally:
        logging.info(f"🧪 TEST COMPLETE!")
        logging.info(f"   📊 Documents processed: {processed_count}")
        logging.info(f"   🗄️ Documents stored in PostgreSQL database")
        db.close()

if __name__ == '__main__':
    main()
