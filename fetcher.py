import requests
import logging
import time
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from config import FDA_API_URL, PH_GUIDANCE_URL

logging.basicConfig(level=logging.INFO)

RETRY_COUNT = 3
RETRY_DELAY = 2

class Fetcher:
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

    def fetch_fda_pdfs(self):
        """Fetch FDA regulatory documents ONLY from Latest Issuances page (Current Year & Previous Year)"""
        all_posts = []
        processed_urls_during_session = set()
        
        # Get current year and previous year dynamically
        current_year = datetime.now().year
        previous_year = current_year - 1
        target_years = [str(current_year), str(previous_year)]
        
        logging.info(f"🔍 Fetching ONLY from Latest Issuances page: {PH_GUIDANCE_URL}")
        logging.info(f"📅 Targeting documents from {previous_year} and {current_year} only")
        
        try:
            processed_urls = self._load_processed_urls()
            fda_docs = self._fetch_from_latest_issuances_page(processed_urls, target_years)
            
            logging.info(f"📄 Found {len(fda_docs)} FDA regulatory documents from {previous_year}-{current_year}")
            
            new_processed_urls = []
            for i, doc in enumerate(fda_docs, 1):
                if doc['url'] not in processed_urls:
                    logging.info(f"[{i}/{len(fda_docs)}] Processing: {doc['title'][:60]}...")
                    self._process_single_post(doc['url'], doc['title'], all_posts, processed_urls_during_session)
                    new_processed_urls.append(doc['url'])
                    time.sleep(0.5)
                else:
                    logging.info(f"[{i}/{len(fda_docs)}] Skipping (already processed): {doc['title'][:60]}...")
            
            if new_processed_urls:
                self._save_processed_urls(new_processed_urls)
            
        except Exception as e:
            logging.warning(f"Failed to process Latest Issuances page: {e}")
        
        logging.info(f"🎉 Total new FDA regulatory documents from Latest Issuances ({previous_year}-{current_year}): {len(all_posts)}")
        return all_posts

    def _fetch_from_latest_issuances_page(self, processed_urls, target_years):
        """Fetch documents from Latest Issuances using WordPress REST API (Current Year & Previous Year Only)"""
        fda_docs = []
        
        try:
            page = 1
            total_docs = 0
            
            while page <= 10:
                api_url = "https://www.fda.gov.ph/wp-json/wp/v2/posts"
                params = {
                    'per_page': 100,
                    'page': page,
                    'orderby': 'date',
                    'order': 'desc'
                }
                
                logging.info(f"📄 Fetching Latest Issuances page {page} via WordPress API...")
                
                resp = requests.get(api_url, params=params, timeout=15, headers=self.HEADERS)
                if resp.status_code != 200:
                    logging.warning(f"API request failed for page {page}: {resp.status_code}")
                    break
                    
                posts_data = resp.json()
                if not posts_data:
                    break
                
                if page == 1:
                    total_posts = resp.headers.get('X-WP-Total', 'Unknown')
                    total_pages = resp.headers.get('X-WP-TotalPages', 'Unknown')
                    logging.info(f"📋 WordPress API: {total_posts} total posts across {total_pages} pages")
                    logging.info(f"🎯 Filtering for documents from years: {', '.join(target_years)}")
                
                page_regulatory_docs = 0
                found_older_docs = False
                
                for post in posts_data:
                    title = post.get('title', {}).get('rendered', '')
                    link = post.get('link', '')
                    date = post.get('date', '')
                    
                    year = date[:4] if date else '0000'
                    
                    if year not in target_years:
                        if year < min(target_years):
                            found_older_docs = True
                        continue
                    
                    if link in processed_urls:
                        continue
                    
                    is_regulatory = (
                        '||' in title and (
                            any(doc_type in title for doc_type in [
                                'FDA Circular No.', 'Administrative Order No.', 'FDA Order No.',
                                'FDA Memorandum', 'DEPARTMENT CIRCULAR NO.', 'FDA Advisory No.',
                                'ITB No.', 'ANNOUNCEMENT'
                            ]) or
                            any(pattern in title.lower() for pattern in [
                                'circular no.', 'order no.', 'advisory no.', 'memorandum no.',
                                'administrative order', 'fda circular', 'fda advisory',
                                'fda memorandum', 'itb no.', 'announcement'
                            ])
                        )
                    )
                    
                    if is_regulatory:
                        fda_docs.append({
                            'title': title,
                            'url': link,
                            'date': date[:10]
                        })
                        page_regulatory_docs += 1
                        total_docs += 1
                
                logging.info(f"📋 Page {page}: Found {page_regulatory_docs} regulatory documents from {'/'.join(target_years)}")
                
                if found_older_docs:
                    logging.info(f"🔍 Reached documents older than {min(target_years)}, stopping search")
                    break
                
                page += 1
                time.sleep(0.5)
            
            logging.info(f"📄 Total regulatory documents found from {'/'.join(target_years)}: {total_docs}")
            
        except Exception as e:
            logging.error(f"Error fetching from WordPress API: {e}")
        
        unique_docs = []
        seen_urls = set()
        for doc in fda_docs:
            if doc['url'] not in seen_urls:
                unique_docs.append(doc)
                seen_urls.add(doc['url'])
        
        return unique_docs

    def _process_single_post(self, url, title, all_posts, processed_urls_during_session):
        if url in processed_urls_during_session:
            logging.info(f"   ⏭️ Skipping (already processed in this session): {title[:60]}...")
            return
        
        processed_urls_during_session.add(url)
        
        try:
            logging.info(f"   🌐 Fetching URL: {url}")
            
            for attempt in range(RETRY_COUNT):
                try:
                    resp = requests.get(url, timeout=15, headers=self.HEADERS)
                    if resp.status_code == 200:
                        break
                except Exception as e:
                    logging.warning(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                    if attempt < RETRY_COUNT - 1:
                        time.sleep(RETRY_DELAY)
                    else:
                        logging.error(f"   ❌ Failed to fetch after {RETRY_COUNT} attempts")
                        return
            
            if resp.status_code != 200:
                logging.warning(f"   ⚠️ Failed to fetch: HTTP {resp.status_code}")
                return
            
            content = resp.text
            logging.info(f"   📏 Content length: {len(content)} chars")
            
            logging.info(f"   📄 Processing: {title[:60]}...")
            
            soup = BeautifulSoup(content, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            if clean_text:
                all_posts.append({
                    'title': title,
                    'url': url,
                    'content': clean_text
                })
                logging.info(f"   ✅ Extracted HTML content ({len(clean_text)} chars)")
                logging.info(f"   💾 Added to all_posts. Total posts now: {len(all_posts)}")
            else:
                logging.warning(f"   ⚠️ No content extracted from {url}")
                
        except Exception as e:
            logging.error(f"   ❌ Error processing {url}: {e}")
    
    def _load_processed_urls(self):
        processed_file = 'processed_urls.txt'
        if os.path.exists(processed_file):
            with open(processed_file, 'r') as f:
                urls = set(line.strip() for line in f if line.strip())
            logging.info(f"📂 Loaded {len(urls)} previously processed URLs")
            return urls
        return set()
    
    def _save_processed_urls(self, new_urls):
        processed_file = 'processed_urls.txt'
        with open(processed_file, 'a') as f:
            for url in new_urls:
                f.write(f"{url}\n")
        logging.info(f"💾 Saved {len(new_urls)} new URLs to {processed_file}")

    def fetch_ph_guidance(self):
        logging.info("⚠️ This method is deprecated. All documents are now fetched from Latest Issuances page only.")
        return []

    def yield_all_pdfs(self):
        """
        Generator function that yields documents one by one for database storage
        """
        all_posts = self.fetch_fda_pdfs()
        
        for post in all_posts:
            # Extract filename from URL
            filename = post.get('url', '').split('/')[-1] if post.get('url') else 'unknown'
            if not filename or filename == '':
                filename = f"fda_advisory_{post.get('title', 'unknown')[:20].replace(' ', '_')}"
            
            # Parse issue date from title if possible (look for date patterns)
            issue_date = None
            title = post.get('title', '')
            # Try to extract date from title like "FDA Advisory No.2025-0317"
            import re
            date_match = re.search(r'(\d{4})', title)
            if date_match:
                year = date_match.group(1)
                issue_date = f"{year}-01-01"  # Default to start of year if no specific date
            
            # Prepare data for database insertion matching the schema
            yield {
                'title': post.get('title', 'Unknown Title'),
                'summary': post.get('content', '')[:500] + '...' if len(post.get('content', '')) > 500 else post.get('content', ''),
                'issue_date': issue_date,
                'products': None,  # Could be extracted from content in future
                'link_guidance': post.get('url', ''),  # Fixed: use 'url' instead of 'page_url'
                'link_file': None,  # No PDF files, only HTML content
                'country': 'Philippines',
                'agency': 'FDA Philippines',
                'all_text': post.get('content', ''),  # Fixed: use 'content' instead of 'text_content'
                'json_data': {
                    'source_url': post.get('url'),  # Fixed: use 'url' instead of 'page_url'
                    'extraction_date': post.get('extraction_date'),
                    'content_length': len(post.get('content', '')),  # Fixed: use 'content'
                    'is_text_only': True
                }
            }
