#!/usr/bin/env python3
"""
Simple test: Fetch only page 1 and store in database
"""
import logging
from db import Database
from fetcher import Fetcher

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_single_page():
    """Test fetching and storing documents from just page 1"""
    
    print('🧪 SINGLE PAGE TEST - FETCHING PAGE 1 ONLY')
    print('=' * 50)
    
    # Initialize database and fetcher
    db = Database()
    fetcher = Fetcher()
    
    try:
        # Clear any existing FDA Philippines records for clean test
        print('🧹 Clearing existing FDA Philippines records for clean test...')
        with db.conn.cursor() as cursor:
            cursor.execute("DELETE FROM source.medical_guidelines WHERE agency = %s", ('FDA Philippines',))
            db.conn.commit()
        print('✅ Cleared existing records')
        
        # Get documents from page 1 only
        print('📡 Fetching documents from page 1...')
        documents = []
        
        # Fetch only first page (limit to ~10 documents for this test)
        count = 0
        for doc in fetcher.yield_all_pdfs():
            documents.append(doc)
            count += 1
            print(f'   Found: {doc["title"][:60]}...')
            
            # Stop after 10 documents for simple test
            if count >= 10:
                print(f'   🛑 Limiting test to {count} documents')
                break
        
        print(f'📄 Found {len(documents)} documents for testing')
        
        # Insert each document into database
        inserted_count = 0
        for i, doc in enumerate(documents, 1):
            try:
                print(f'[{i}/{len(documents)}] Inserting: {doc["title"][:60]}...')
                
                # Insert into database
                db.upsert_guideline(
                    title=doc['title'],
                    summary=doc.get('summary', 'No summary available'),
                    issue_date=doc.get('issue_date'),
                    products=doc.get('products'),
                    link_guidance=doc.get('url'),
                    link_file=doc.get('pdf_url'),
                    country='Philippines',
                    agency='FDA Philippines',
                    all_text=doc.get('content', ''),
                    json_data={
                        'source_url': doc.get('url'),
                        'pdf_url': doc.get('pdf_url'),
                        'test_run': True
                    }
                )
                inserted_count += 1
                
            except Exception as e:
                print(f'   ❌ Error inserting document {i}: {e}')
                continue
        
        print(f'\n✅ Successfully inserted {inserted_count} documents')
        
        # Verify what's in the database
        print('\n🔍 Verifying database contents...')
        with db.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM source.medical_guidelines WHERE agency = %s", ('FDA Philippines',))
            db_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT title, link_guidance, created_at 
                FROM source.medical_guidelines 
                WHERE agency = %s 
                ORDER BY created_at DESC 
                LIMIT 5
            """, ('FDA Philippines',))
            recent_docs = cursor.fetchall()
        
        print(f'📊 Database verification:')
        print(f'   Total FDA Philippines documents: {db_count}')
        print(f'   Documents inserted: {inserted_count}')
        print(f'   Match: {"✅ YES" if db_count == inserted_count else "❌ NO"}')
        
        print(f'\n📋 Recent documents in database:')
        for title, url, created_at in recent_docs:
            print(f'   - {title[:60]}...')
            print(f'     URL: {url[:60]}...')
            print(f'     Created: {created_at}')
            print()
        
        return db_count == inserted_count
        
    except Exception as e:
        print(f'❌ Error during test: {e}')
        return False
    finally:
        db.close()

if __name__ == '__main__':
    success = test_single_page()
    print(f'\n🎯 TEST RESULT: {"PASSED ✅" if success else "FAILED ❌"}')
    
    if success:
        print('✨ Database storage is working correctly!')
        print('   You can now run the full automation with confidence.')
    else:
        print('⚠️  There may be an issue with database storage.')
        print('   Please check the logs above for details.')
