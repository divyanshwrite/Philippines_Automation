#!/usr/bin/env python3
"""
Test script to validate database integration for FDA Philippines documents
"""

import logging
import psycopg2
from config import DB_CONFIG, TABLE_NAME
from fetcher import Fetcher
from db import Database

logging.basicConfig(level=logging.INFO)

def test_database_integration():
    """Test the complete database integration workflow"""
    
    # Step 1: Clear existing FDA Philippines records for testing
    print("🧹 Clearing existing FDA Philippines records for testing...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {TABLE_NAME} WHERE agency = %s", ('FDA Philippines',))
    deleted_count = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Cleared {deleted_count} existing FDA Philippines records")
    
    # Step 2: Use the working main workflow but limit documents
    print("\n🚀 Testing FDA document processing with database integration...")
    
    # Initialize components
    fetcher = Fetcher()
    db = Database()
    
    # Set small test parameters to avoid processing too many documents
    import tempfile
    import os
    
    # Create a temporary processed URLs file with most URLs to limit new processing
    temp_dir = tempfile.mkdtemp()
    temp_processed_file = os.path.join(temp_dir, "test_processed_urls.txt")
    
    # Copy current processed URLs and modify
    with open("processed_urls.txt", "r") as f:
        processed_urls = f.readlines()
    
    # Write only first 900 URLs to allow some new processing
    with open(temp_processed_file, "w") as f:
        f.writelines(processed_urls[:900])
    
    # Temporarily replace the processed URLs file
    original_file = "processed_urls.txt"
    backup_file = "processed_urls_test_backup.txt"
    
    os.rename(original_file, backup_file)
    os.rename(temp_processed_file, original_file)
    
    try:
        # Step 3: Run the fetching process (limited)
        print("📄 Fetching and processing documents...")
        all_posts = fetcher.fetch_fda_pdfs()
        print(f"📋 Found {len(all_posts)} documents to process")
        
        # Step 4: Process documents with database integration
        processed_count = 0
        for i, doc_data in enumerate(fetcher.yield_all_pdfs(), 1):
            if i > 5:  # Limit to first 5 documents for testing
                break
                
            print(f"\n[{i}] Processing: {doc_data['title'][:70]}...")
            
            # Insert into database
            db.upsert_guideline(
                title=doc_data['title'],
                summary=doc_data['summary'],
                issue_date=doc_data['issue_date'],
                products=doc_data['products'],
                link_guidance=doc_data['link_guidance'],
                link_file=doc_data['link_file'],
                country=doc_data['country'],
                agency=doc_data['agency'],
                all_text=doc_data['all_text'],
                json_data=doc_data['json_data']
            )
            processed_count += 1
            
    finally:
        # Restore original processed URLs file
        os.rename(original_file, temp_processed_file)
        os.rename(backup_file, original_file)
        os.remove(temp_processed_file)
        os.rmdir(temp_dir)
    
    # Step 5: Verify database storage
    print(f"\n🔍 Verifying database storage...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Count FDA Philippines documents
    cur.execute(f'SELECT COUNT(*) FROM {TABLE_NAME} WHERE agency = %s', ('FDA Philippines',))
    fda_count = cur.fetchone()[0]
    
    # Get the stored documents
    cur.execute(f'SELECT title, agency, country FROM {TABLE_NAME} WHERE agency = %s', ('FDA Philippines',))
    stored_docs = cur.fetchall()
    
    print(f"📊 Database verification results:")
    print(f"   Documents processed: {processed_count}")
    print(f"   Documents in database: {fda_count}")
    print(f"   ✅ Database integration: {'SUCCESS' if fda_count >= processed_count else 'FAILED'}")
    
    if stored_docs:
        print(f"\n📋 Stored documents:")
        for i, (title, agency, country) in enumerate(stored_docs, 1):
            print(f"   {i}. {title[:70]}...")
            print(f"      Agency: {agency} | Country: {country}")
    
    cur.close()
    conn.close()
    db.close()
    
    print(f"\n🎉 Test completed!")
    return fda_count >= processed_count

if __name__ == "__main__":
    success = test_database_integration()
    if success:
        print("🎊 DATABASE INTEGRATION TEST: PASSED!")
    else:
        print("❌ DATABASE INTEGRATION TEST: FAILED!")
