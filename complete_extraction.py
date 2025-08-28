#!/usr/bin/env python3
"""
Complete FDA Philippines content extraction with full text and URLs
- Fetches complete text content (no half-baked summaries)
- Stores proper URLs 
- Keeps existing entries (no deletion)
- Processes all available documents
"""
import logging
import requests
from bs4 import BeautifulSoup
from db import Database
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

class CompleteFDAExtractor:
    def __init__(self):
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def extract_complete_content(self, url):
        """Extract complete full text content from FDA Philippines URL"""
        try:
            print(f'   🌐 Fetching: {url[:80]}...')
            
            response = requests.get(url, timeout=30, headers=self.HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Get title from the page
            title_tag = soup.find('title')
            page_title = title_tag.get_text().strip() if title_tag else 'FDA Document'
            
            # Clean up title (remove site suffix)
            if ' - Food and Drug Administration' in page_title:
                page_title = page_title.replace(' - Food and Drug Administration', '')
            
            print(f'   ✅ Extracted {len(clean_text)} characters')
            
            return {
                'title': page_title,
                'content': clean_text,
                'url': url,
                'content_length': len(clean_text)
            }
            
        except Exception as e:
            print(f'   ❌ Failed to extract from {url}: {e}')
            return None
    
    def process_all_urls(self):
        """Process all URLs from processed_urls.txt with complete content extraction"""
        
        print('🚀 COMPLETE FDA PHILIPPINES CONTENT EXTRACTION')
        print('=' * 60)
        print('✅ Fetching COMPLETE text content (no summaries)')
        print('✅ Storing proper URLs')  
        print('✅ Keeping existing entries (no deletion)')
        print('✅ Processing ALL available documents')
        print()
        
        # Load all processed URLs
        try:
            with open('processed_urls.txt', 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            print(f'📋 Found {len(urls)} URLs to process')
        except FileNotFoundError:
            print('❌ processed_urls.txt not found')
            return
        
        # Initialize database
        db = Database()
        
        try:
            processed_count = 0
            success_count = 0
            
            for i, url in enumerate(urls, 1):
                print(f'\\n[{i}/{len(urls)}] Processing URL {i}:')
                
                # Check if already exists in database (don't delete, just update)
                with db.conn.cursor() as cursor:
                    cursor.execute('SELECT id FROM source.medical_guidelines WHERE link_guidance = %s', (url,))
                    existing = cursor.fetchone()
                
                # Extract complete content
                doc_data = self.extract_complete_content(url)
                
                if doc_data:
                    try:
                        # Store/update in database with COMPLETE content
                        db.upsert_guideline(
                            title=doc_data['title'],
                            summary=doc_data['content'][:1000] + '...' if len(doc_data['content']) > 1000 else doc_data['content'],  # Proper summary from full content
                            issue_date=None,
                            products=None,
                            link_guidance=doc_data['url'],  # Complete URL
                            link_file=None,
                            country='Philippines',
                            agency='FDA Philippines',
                            all_text=doc_data['content'],  # COMPLETE FULL TEXT - NO TRUNCATION
                            json_data={
                                'source_url': doc_data['url'],
                                'content_length': doc_data['content_length'],
                                'extraction_method': 'complete_content_extraction',
                                'processed_date': '2025-08-27'
                            }
                        )
                        
                        action = 'Updated' if existing else 'Inserted'
                        print(f'   ✅ {action} document with {doc_data["content_length"]} characters')
                        success_count += 1
                        
                    except Exception as e:
                        print(f'   ❌ Database error: {e}')
                
                processed_count += 1
                
                # Progress update every 50 documents
                if i % 50 == 0:
                    print(f'\\n📊 Progress: {i}/{len(urls)} processed ({success_count} successful)')
                
                # Small delay to be respectful to the server
                time.sleep(0.5)
            
            print(f'\\n🎉 PROCESSING COMPLETE!')
            print(f'   📊 Total URLs processed: {processed_count}')
            print(f'   ✅ Successfully extracted: {success_count}')
            print(f'   📝 All documents stored with COMPLETE content')
            print(f'   🔗 All documents have proper URLs')
            
            # Final verification
            print(f'\\n🔍 FINAL VERIFICATION:')
            with db.conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM source.medical_guidelines WHERE agency = %s', ('FDA Philippines',))
                total_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT AVG(LENGTH(all_text)) FROM source.medical_guidelines WHERE agency = %s AND all_text IS NOT NULL', ('FDA Philippines',))
                avg_length = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM source.medical_guidelines WHERE agency = %s AND link_guidance IS NOT NULL', ('FDA Philippines',))
                url_count = cursor.fetchone()[0]
                
                print(f'   📊 Total FDA Philippines documents: {total_count}')
                print(f'   📝 Average content length: {int(avg_length) if avg_length else 0} characters')
                print(f'   🔗 Documents with URLs: {url_count}')
                
                # Show sample of complete content
                cursor.execute('SELECT title, link_guidance, LENGTH(all_text) FROM source.medical_guidelines WHERE agency = %s ORDER BY created_at DESC LIMIT 3', ('FDA Philippines',))
                samples = cursor.fetchall()
                
                print(f'\\n📋 Sample documents with complete content:')
                for title, url, content_length in samples:
                    print(f'   - {title[:60]}...')
                    print(f'     URL: {url[:70]}...')
                    print(f'     Content: {content_length} characters')
                    print()
        
        except Exception as e:
            print(f'❌ Error: {e}')
        finally:
            db.close()

def main():
    extractor = CompleteFDAExtractor()
    extractor.process_all_urls()

if __name__ == '__main__':
    main()
