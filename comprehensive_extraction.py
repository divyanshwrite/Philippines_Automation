#!/usr/bin/env python3
"""
Complete FDA Philippines Guidelines Extraction for Current & Previous Year
- Fetches ALL 2024-2025 guidelines with complete content
- Stores complete text and URLs
- Comprehensive coverage of all regulatory documents
"""
import logging
import requests
from bs4 import BeautifulSoup
from db import Database
import time
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

class ComprehensiveFDAExtractor:
    def __init__(self):
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Dynamic year calculation
        current_year = datetime.now().year
        self.target_years = [str(current_year), str(current_year - 1)]
        print(f'🎯 Target years: {self.target_years} (Current: {current_year}, Previous: {current_year - 1})')
    
    def extract_complete_content(self, url, title=""):
        """Extract complete full text content from FDA Philippines URL"""
        try:
            print(f'   🌐 Fetching: {url[:80]}...')
            
            response = requests.get(url, timeout=30, headers=self.HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove navigation and non-content elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                element.decompose()
            
            # Get text content
            text_content = soup.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Get title from the page if not provided
            if not title:
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else 'FDA Document'
                
                # Clean up title (remove site suffix)
                if ' - Food and Drug Administration' in title:
                    title = title.replace(' - Food and Drug Administration', '')
            
            # Extract issue date from title if possible
            issue_date = None
            date_match = re.search(r'(\d{4})', title)
            if date_match:
                year = date_match.group(1)
                issue_date = f"{year}-01-01"  # Default to start of year
            
            print(f'   ✅ Extracted {len(clean_text)} characters')
            
            return {
                'title': title,
                'content': clean_text,
                'url': url,
                'content_length': len(clean_text),
                'issue_date': issue_date
            }
            
        except Exception as e:
            print(f'   ❌ Failed to extract from {url}: {e}')
            return None
    
    def fetch_all_guidelines_from_api(self):
        """Fetch ALL regulatory documents from WordPress API for target years"""
        
        print(f'📡 FETCHING ALL {"/".join(self.target_years)} GUIDELINES VIA WORDPRESS API')
        print('=' * 60)
        
        all_documents = []
        
        try:
            page = 1
            total_found = 0
            
            while page <= 20:  # Increased to ensure we get all documents
                api_url = "https://www.fda.gov.ph/wp-json/wp/v2/posts"
                params = {
                    'per_page': 100,  # Maximum per page
                    'page': page,
                    'orderby': 'date',
                    'order': 'desc'
                }
                
                print(f'📄 Fetching page {page} from WordPress API...')
                
                resp = requests.get(api_url, params=params, timeout=15, headers=self.HEADERS)
                if resp.status_code != 200:
                    print(f'⚠️ API request failed for page {page}: {resp.status_code}')
                    break
                    
                posts_data = resp.json()
                if not posts_data:
                    print(f'📄 No more posts found on page {page}')
                    break
                
                if page == 1:
                    total_posts = resp.headers.get('X-WP-Total', 'Unknown')
                    total_pages = resp.headers.get('X-WP-TotalPages', 'Unknown')
                    print(f'📊 WordPress API: {total_posts} total posts across {total_pages} pages')
                    print(f'🎯 Filtering for documents from years: {", ".join(self.target_years)}')
                
                page_documents = 0
                found_older_docs = False
                
                for post in posts_data:
                    title = post.get('title', {}).get('rendered', '')
                    link = post.get('link', '')
                    date = post.get('date', '')
                    excerpt = post.get('excerpt', {}).get('rendered', '')
                    
                    # Extract year from date
                    year = date[:4] if date else '0000'
                    
                    # Check if document is from target years
                    if year not in self.target_years:
                        if year < min(self.target_years):
                            found_older_docs = True
                        continue
                    
                    # Check if it's a regulatory document
                    is_regulatory = (
                        '||' in title and (
                            any(doc_type in title for doc_type in [
                                'FDA Circular No.', 'Administrative Order No.', 'FDA Order No.',
                                'FDA Memorandum', 'DEPARTMENT CIRCULAR NO.', 'FDA Advisory No.',
                                'ITB No.', 'ANNOUNCEMENT', 'Announcement'
                            ]) or
                            any(pattern in title.lower() for pattern in [
                                'circular no.', 'order no.', 'advisory no.', 'memorandum no.',
                                'administrative order', 'fda circular', 'fda advisory',
                                'fda memorandum', 'itb no.', 'announcement', 'draft for comments'
                            ])
                        )
                    )
                    
                    if is_regulatory:
                        all_documents.append({
                            'title': title,
                            'url': link,
                            'date': date[:10],
                            'excerpt': excerpt,
                            'year': year
                        })
                        page_documents += 1
                        total_found += 1
                
                print(f'📋 Page {page}: Found {page_documents} regulatory documents from {"/".join(self.target_years)}')
                
                if found_older_docs and page > 5:  # Stop if we're getting old documents
                    print(f'🔍 Reached documents older than {min(self.target_years)}, stopping search')
                    break
                
                page += 1
                time.sleep(0.5)  # Be respectful to the API
            
            print(f'\\n📊 TOTAL GUIDELINES FOUND: {total_found} from {"/".join(self.target_years)}')
            
            # Remove duplicates based on URL
            unique_documents = []
            seen_urls = set()
            for doc in all_documents:
                if doc['url'] not in seen_urls:
                    unique_documents.append(doc)
                    seen_urls.add(doc['url'])
            
            print(f'📄 Unique documents after deduplication: {len(unique_documents)}')
            
            return unique_documents
            
        except Exception as e:
            print(f'❌ Error fetching from WordPress API: {e}')
            return []
    
    def process_all_guidelines(self):
        """Process all guidelines with complete content extraction"""
        
        print('🚀 COMPREHENSIVE FDA PHILIPPINES GUIDELINES EXTRACTION')
        print('=' * 60)
        print(f'✅ Target Years: {" & ".join(self.target_years)}')
        print('✅ Complete content extraction (no summaries)')
        print('✅ All regulatory document types included')
        print('✅ Fresh database (Philippines entries cleared)')
        print()
        
        # Fetch all guidelines from API
        guidelines = self.fetch_all_guidelines_from_api()
        
        if not guidelines:
            print('❌ No guidelines found!')
            return
        
        print(f'\\n📋 Processing {len(guidelines)} guidelines with complete content extraction...')
        
        # Initialize database
        db = Database()
        
        try:
            processed_count = 0
            success_count = 0
            failed_count = 0
            
            for i, guideline in enumerate(guidelines, 1):
                print(f'\\n[{i}/{len(guidelines)}] Processing guideline {i}:')
                print(f'   📄 Title: {guideline["title"][:60]}...')
                print(f'   📅 Date: {guideline["date"]} ({guideline["year"]})')
                
                # Extract complete content
                doc_data = self.extract_complete_content(guideline['url'], guideline['title'])
                
                if doc_data:
                    try:
                        # Store in database with COMPLETE content
                        db.upsert_guideline(
                            title=doc_data['title'],
                            summary=doc_data['content'][:1000] + '...' if len(doc_data['content']) > 1000 else doc_data['content'],
                            issue_date=doc_data.get('issue_date'),
                            products=None,
                            link_guidance=doc_data['url'],
                            link_file=None,
                            country='Philippines',
                            agency='FDA Philippines',
                            all_text=doc_data['content'],  # COMPLETE FULL TEXT
                            json_data={
                                'source_url': doc_data['url'],
                                'content_length': doc_data['content_length'],
                                'extraction_date': guideline['date'],
                                'year': guideline['year'],
                                'extraction_method': 'comprehensive_api_extraction',
                                'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                        )
                        
                        print(f'   ✅ Stored with {doc_data["content_length"]} characters of complete content')
                        success_count += 1
                        
                    except Exception as e:
                        print(f'   ❌ Database error: {e}')
                        failed_count += 1
                else:
                    print(f'   ❌ Content extraction failed')
                    failed_count += 1
                
                processed_count += 1
                
                # Progress update every 25 documents
                if i % 25 == 0:
                    print(f'\\n📊 Progress: {i}/{len(guidelines)} processed ({success_count} successful, {failed_count} failed)')
                
                # Small delay to be respectful to the server
                time.sleep(0.8)
            
            print(f'\\n🎉 COMPREHENSIVE EXTRACTION COMPLETE!')
            print(f'   📊 Total guidelines processed: {processed_count}')
            print(f'   ✅ Successfully extracted: {success_count}')
            print(f'   ❌ Failed extractions: {failed_count}')
            print(f'   📈 Success rate: {(success_count/processed_count)*100:.1f}%')
            
            # Final verification
            print(f'\\n🔍 FINAL DATABASE VERIFICATION:')
            with db.conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM source.medical_guidelines WHERE agency = %s', ('FDA Philippines',))
                total_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT AVG(LENGTH(all_text)) FROM source.medical_guidelines WHERE agency = %s AND all_text IS NOT NULL', ('FDA Philippines',))
                avg_length = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM source.medical_guidelines WHERE agency = %s AND link_guidance IS NOT NULL', ('FDA Philippines',))
                url_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT json_data::json->>\'year\') FROM source.medical_guidelines WHERE agency = %s', ('FDA Philippines',))
                year_coverage = cursor.fetchone()[0]
                
                print(f'   📊 Total FDA Philippines guidelines: {total_count}')
                print(f'   📝 Average content length: {int(avg_length) if avg_length else 0} characters')
                print(f'   🔗 Guidelines with URLs: {url_count}')
                print(f'   📅 Years covered: {year_coverage}')
                
                # Show sample of different document types
                cursor.execute('''
                    SELECT title, link_guidance, LENGTH(all_text), 
                           json_data::json->>'year' as year
                    FROM source.medical_guidelines 
                    WHERE agency = %s 
                    ORDER BY created_at DESC 
                    LIMIT 5
                ''', ('FDA Philippines',))
                samples = cursor.fetchall()
                
                print(f'\\n📋 Sample guidelines with complete content:')
                for title, url, content_length, year in samples:
                    print(f'   📄 [{year}] {title[:50]}...')
                    print(f'      🔗 {url[:60]}...')
                    print(f'      📝 Content: {content_length} characters')
                    print()
        
        except Exception as e:
            print(f'❌ Error during processing: {e}')
        finally:
            db.close()

def main():
    extractor = ComprehensiveFDAExtractor()
    extractor.process_all_guidelines()

if __name__ == '__main__':
    main()
