#!/usr/bin/env python3
"""
Test script to fetch and store real content from FDA URLs
"""
import requests
from bs4 import BeautifulSoup
from db import Database
import logging

logging.basicConfig(level=logging.INFO)

def test_real_content():
    """Fetch real content from one FDA URL and store it"""
    
    print('🌐 TESTING REAL CONTENT EXTRACTION')
    print('=' * 50)
    
    # Use one of the real FDA URLs
    test_url = "https://www.fda.gov.ph/fda-advisory-no-2025-0924-public-health-warning-against-the-purchase-and-consumption-of-the-unregistered-food-supplement-neygold-plus-dietary-supplement/"
    
    print(f'📡 Fetching content from: {test_url[:80]}...')
    
    try:
        # Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(test_url, timeout=30, headers=headers)
        response.raise_for_status()
        
        print(f'✅ Successfully fetched page ({len(response.text)} characters)')
        
        # Extract content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text_content = soup.get_text()
        
        # Clean up the text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = ' '.join(chunk for chunk in chunks if chunk)
        
        print(f'📝 Extracted text length: {len(clean_text)} characters')
        print(f'📋 Text preview: {clean_text[:300]}...')
        
        # Get title from the page
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else 'FDA Advisory Document'
        
        print(f'📄 Page title: {title}')
        
        # Store in database
        db = Database()
        try:
            db.upsert_guideline(
                title=title,
                summary=clean_text[:500] + '...' if len(clean_text) > 500 else clean_text,
                issue_date=None,
                products=None,
                link_guidance=test_url,
                link_file=None,
                country='Philippines',
                agency='FDA Philippines',
                all_text=clean_text,  # Store the full extracted text
                json_data={
                    'source_url': test_url,
                    'content_length': len(clean_text),
                    'extraction_test': True
                }
            )
            
            print('✅ Successfully stored document with full content!')
            
            # Verify what was stored
            with db.conn.cursor() as cursor:
                cursor.execute('SELECT title, all_text FROM source.medical_guidelines WHERE link_guidance = %s', (test_url,))
                result = cursor.fetchone()
                if result:
                    stored_title, stored_text = result
                    print(f'\\n🔍 VERIFICATION:')
                    print(f'   Stored title: {stored_title[:60]}...')
                    print(f'   Stored text length: {len(stored_text) if stored_text else 0} characters')
                    if stored_text:
                        print(f'   Stored text preview: {stored_text[:200]}...')
                        
        except Exception as e:
            print(f'❌ Database error: {e}')
        finally:
            db.close()
            
    except Exception as e:
        print(f'❌ Error fetching content: {e}')

if __name__ == '__main__':
    test_real_content()
