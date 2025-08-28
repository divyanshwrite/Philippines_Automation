import logging
import time
from fetcher import Fetcher
from db import Database

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def main():
    # Initialize components
    fetcher = Fetcher()
    db = Database()
    
    processed_count = 0
    
    try:
        logging.info("🚀 Starting FDA Philippines document extraction with database integration...")
        
        for pdf_info in fetcher.yield_all_pdfs():
            try:
                processed_count += 1
                title = pdf_info['title']
                
                logging.info(f"\n[{processed_count}] Processing: {title[:60]}...")
                
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
                
                if processed_count % 25 == 0:
                    logging.info(f"   📊 Milestone: {processed_count} documents processed")
                    
                time.sleep(0.5)  # Polite delay
                    
            except Exception as e:
                logging.error(f"   ❌ Error processing document {processed_count}: {e}")
                continue
        
    except Exception as e:
        logging.error(f"❌ Error in main execution: {e}")
    finally:
        db.close()
        logging.info(f"\n🎉 Processing Complete!")
        logging.info(f"   📊 Total FDA Philippines documents processed: {processed_count}")
        logging.info(f"   🗄️ All documents stored in PostgreSQL database")
        logging.info(f"   🔌 Database connection closed")

if __name__ == '__main__':
    main()
