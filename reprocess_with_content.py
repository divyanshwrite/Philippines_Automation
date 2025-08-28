#!/usr/bin/env python3
"""
Script to re-process existing URLs and extract full content
"""
import logging
from fetcher import Fetcher
from db import Database
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def reprocess_with_content():
    """Re-process some URLs to extract full content"""
    
    print('🔄 RE-PROCESSING URLS WITH FULL CONTENT EXTRACTION')
    print('=' * 60)
    
    # Get first 5 URLs from processed file
    with open('processed_urls.txt', 'r') as f:
        urls = [line.strip() for line in f.readlines()[:5]]
    
    print(f'📋 Will re-process {len(urls)} URLs to extract full content:')
    for i, url in enumerate(urls, 1):
        print(f'   {i}. {url[:80]}...')
    
    print()
    
    # Initialize fetcher and database
    fetcher = Fetcher()
    db = Database()
    
    try:
        processed_count = 0
        
        for i, url in enumerate(urls, 1):
            print(f'\\n[{i}/{len(urls)}] Processing: {url[:80]}...')
            
            try:
                # Use the fetcher's content extraction method
                processed_urls_temp = set()
                all_posts = []
                
                # Extract the title from URL (approximate)
                title_part = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
                title = title_part.replace('-', ' ').title()
                
                # Process this single URL
                fetcher._process_single_post(url, title, all_posts, processed_urls_temp)
                
                if all_posts:
                    # Get the processed document
                    doc = all_posts[0]
                    
                    print(f'   📄 Title: {doc["title"][:60]}...')
                    print(f'   📝 Content length: {len(doc["content"])} characters')
                    print(f'   📋 Content preview: {doc["content"][:150]}...')
                    
                    # Store in database with full content
                    db.upsert_guideline(
                        title=doc['title'],
                        summary=doc['content'][:500] + '...' if len(doc['content']) > 500 else doc['content'],
                        issue_date=None,
                        products=None,
                        link_guidance=doc['url'],
                        link_file=None,
                        country='Philippines',
                        agency='FDA Philippines',
                        all_text=doc['content'],  # Full extracted content
                        json_data={
                            'source_url': doc['url'],
                            'content_length': len(doc['content']),
                            'reprocessed': True
                        }
                    )
                    
                    processed_count += 1
                    print(f'   ✅ Stored with full content!')
                    
                else:
                    print(f'   ❌ Failed to extract content')
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                print(f'   ❌ Error processing {url}: {e}')
                continue
        
        print(f'\\n🎉 SUMMARY:')
        print(f'   📊 URLs processed: {processed_count}/{len(urls)}')
        print(f'   💾 Documents stored with full content')
        
        # Verify what's now in the database
        print(f'\\n🔍 VERIFICATION:')
        with db.conn.cursor() as cursor:
            cursor.execute('SELECT title, link_guidance, LENGTH(all_text) as content_length FROM source.medical_guidelines WHERE agency = %s ORDER BY created_at DESC LIMIT 5', ('FDA Philippines',))
            docs = cursor.fetchall()
            
            for i, (title, url, content_length) in enumerate(docs, 1):
                print(f'   {i}. {title[:60]}...')
                print(f'      URL: {url[:70]}...')
                print(f'      Content: {content_length} characters')
                print()
        
    except Exception as e:
        print(f'❌ Error: {e}')
    finally:
        db.close()

if __name__ == '__main__':
    reprocess_with_content()
