#!/usr/bin/env python3
"""
Test script to show URLs being fetched and stored
"""
import logging
from db import Database

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_url_display():
    """Check what URLs are actually in the database"""
    
    print('🔍 CHECKING URLS IN DATABASE')
    print('=' * 50)
    
    db = Database()
    
    try:
        with db.conn.cursor() as cursor:
            # Get all FDA Philippines documents with their URLs
            cursor.execute("""
                SELECT title, link_guidance, json_data, created_at 
                FROM source.medical_guidelines 
                WHERE agency = %s 
                ORDER BY created_at DESC 
                LIMIT 10
            """, ('FDA Philippines',))
            
            docs = cursor.fetchall()
            
            print(f'📊 Found {len(docs)} FDA Philippines documents:')
            print()
            
            for i, (title, link_guidance, json_data, created_at) in enumerate(docs, 1):
                print(f'📄 Document {i}:')
                print(f'   Title: {title}')
                print(f'   Link Guidance: {link_guidance}')
                print(f'   Created: {created_at}')
                
                # Parse JSON data to see if URL is stored there
                if json_data:
                    import json
                    try:
                        json_parsed = json.loads(json_data) if isinstance(json_data, str) else json_data
                        print(f'   Source URL from JSON: {json_parsed.get("source_url", "Not found")}')
                        print(f'   PDF URL from JSON: {json_parsed.get("pdf_url", "Not found")}')
                    except:
                        print(f'   JSON Data: {json_data}')
                
                print()
                
        # Also check the processed_urls.txt file to see what URLs were processed
        print('📁 CHECKING PROCESSED URLS FILE:')
        print('=' * 30)
        
        try:
            with open('processed_urls.txt', 'r') as f:
                urls = f.readlines()
                print(f'📊 Total URLs in processed_urls.txt: {len(urls)}')
                print('📋 Last 5 URLs processed:')
                for url in urls[-5:]:
                    print(f'   - {url.strip()}')
        except FileNotFoundError:
            print('❌ processed_urls.txt not found')
            
    except Exception as e:
        print(f'❌ Error: {e}')
    finally:
        db.close()

if __name__ == '__main__':
    test_url_display()
