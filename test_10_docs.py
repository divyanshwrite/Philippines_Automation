#!/usr/bin/env python3
"""
Test with exactly 10 documents - clear processed URLs and limit processing
"""
import logging
import time
import os
from fetcher import Fetcher
from db import Database

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_10_documents():
    # Clear processed URLs to force fresh processing
    if os.path.exists('processed_urls.txt'):
        os.rename('processed_urls.txt', 'processed_urls_backup_test.txt')
        print("📁 Backed up processed URLs")
    
    # Initialize components
    fetcher = Fetcher()
    db = Database()
    
    processed_count = 0
    max_documents = 10  # Only process 10 documents
    
    try:
        print(f"🧪 Testing with {max_documents} documents only...")
        print("🔄 Cleared processed URLs to force fresh processing")
        print()
        
        for pdf_info in fetcher.yield_all_pdfs():
            if processed_count >= max_documents:
                print(f"🛑 Reached limit of {max_documents} documents")
                break
                
            processed_count += 1
            title = pdf_info['title']
            url = pdf_info['link_guidance']
            
            print(f"[{processed_count}] Processing: {title[:50]}...")
            print(f"    URL: {url}")
            
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
            
            time.sleep(0.1)  # Small delay
        
        print(f"\n✅ Processed {processed_count} documents")
        
        # Check database
        import psycopg2
        from config import DB_CONFIG, TABLE_NAME
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(f'SELECT COUNT(*) FROM {TABLE_NAME} WHERE agency = %s', ('FDA Philippines',))
        fda_count = cur.fetchone()[0]
        
        cur.execute(f'SELECT title, link_guidance FROM {TABLE_NAME} WHERE agency = %s ORDER BY updated_at DESC LIMIT 5', ('FDA Philippines',))
        recent_docs = cur.fetchall()
        
        print(f"\n📊 Database Results:")
        print(f"   FDA Philippines documents: {fda_count}")
        print(f"   Recent documents:")
        for title, url in recent_docs:
            print(f"     - {title[:50]}...")
            print(f"       URL: {url}")
        
        cur.close()
        conn.close()
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.close()
    finally:
        # Restore processed URLs
        if os.path.exists('processed_urls_backup_test.txt'):
            os.rename('processed_urls_backup_test.txt', 'processed_urls.txt')
            print("\n📁 Restored processed URLs backup")

if __name__ == '__main__':
    test_10_documents()
