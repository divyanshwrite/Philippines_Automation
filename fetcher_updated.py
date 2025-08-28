import requests
import logging
import time
import json
import os
from bs4 import BeautifulSoup
from config import FDA_API_URL, PH_GUIDANCE_URL

logging.basicConfig(level=logging.INFO)

RETRY_COUNT = 3
RETRY_DELAY = 2

class Fetcher:
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

    def fetch_fda_pdfs(self):
        """Dynamically fetch FDA regulatory documents from Latest Issuances page"""
        all_posts = []
        seen_urls = set()
        
        logging.info(f"🔍 Dynamically fetching from Latest Issuances page: {PH_GUIDANCE_URL}")
        
        try:
            # Load already processed URLs to skip duplicates
            processed_urls = self._load_processed_urls()
            
            # Fetch from Latest Issuances page dynamically
            resp = requests.get(PH_GUIDANCE_URL, timeout=15, headers=self.HEADERS)
            if resp.status_code != 200:
                logging.warning(f"Failed to fetch Latest Issuances page: {resp.status_code}")
                return all_posts
                
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Find all links with FDA regulatory document patterns
            all_links = soup.find_all('a', href=True)
            fda_docs = []
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Skip if already processed
                if href in processed_urls:
                    continue
                
                # Look for FDA regulatory documents by URL pattern and title
                if ('fda.gov.ph' in href and
                    href not in seen_urls and
                    any(doc_pattern in href.lower() for doc_pattern in [
                        'fda-circular-no', 'administrative-order-no', 'fda-order-no',
                        'fda-memorandum', 'department-circular-no'
                    ]) and
                    ('||' in text or any(keyword in text.lower() for keyword in [
                        'circular', 'order', 'memorandum', 'administrative'
                    ]))):
                    
                    # Make URL absolute if needed
                    if href.startswith('/'):
                        href = 'https://www.fda.gov.ph' + href
                    
                    fda_docs.append({
                        'title': text if text and len(text) > 10 else href.split('/')[-1].replace('-', ' ').title(),
                        'url': href
                    })
                    seen_urls.add(href)
            
            # If no documents found from page scraping, try WordPress API as fallback
            if not fda_docs:
                logging.info("📄 No documents found from page scraping, trying WordPress API...")
                fda_docs = self._fetch_from_wordpress_api(processed_urls)
            
            logging.info(f"📄 Found {len(fda_docs)} new FDA regulatory documents")
            
            # Process each document and save URLs to avoid reprocessing
            new_processed_urls = []
            for i, doc in enumerate(fda_docs, 1):
                if doc['url'] not in processed_urls:
                    logging.info(f"[{i}/{len(fda_docs)}] Processing: {doc['title'][:60]}...")
                    self._process_single_post(doc['url'], doc['title'], all_posts, seen_urls)
                    new_processed_urls.append(doc['url'])
                    time.sleep(0.5)
                else:
                    logging.info(f"[{i}/{len(fda_docs)}] Skipping (already processed): {doc['title'][:60]}...")
            
            # Save newly processed URLs
            if new_processed_urls:
                self._save_processed_urls(new_processed_urls)
            
        except Exception as e:
            logging.warning(f"Failed to process Latest Issuances page: {e}")
        
        logging.info(f"🎉 Total new FDA regulatory documents: {len(all_posts)}")
        return all_posts
    
    def _fetch_from_wordpress_api(self, processed_urls):
        """Fallback: Fetch from WordPress API if page scraping fails"""
        fda_docs = []
        try:
            api_url = "https://www.fda.gov.ph/wp-json/wp/v2/posts"
            params = {
                'per_page': 100,
                'orderby': 'date',
                'order': 'desc'
            }
            
            resp = requests.get(api_url, params=params, timeout=15, headers=self.HEADERS)
            if resp.status_code == 200:
                posts_data = resp.json()
                
                for post in posts_data:
                    title = post.get('title', {}).get('rendered', '')
                    link = post.get('link', '')
                    
                    # Look for regulatory documents
                    if (link not in processed_urls and
                        '||' in title and 
                        any(doc_type in title for doc_type in [
                            'FDA Circular No.', 'Administrative Order No.', 'FDA Order No.',
                            'FDA Memorandum', 'DEPARTMENT CIRCULAR NO.'
                        ])):
                        
                        fda_docs.append({
                            'title': title,
                            'url': link
                        })
        except Exception as e:
            logging.warning(f"WordPress API fallback failed: {e}")
        
        return fda_docs
    
    def _load_processed_urls(self):
        """Load previously processed URLs to avoid duplicates"""
        processed_file = os.path.join(os.path.dirname(__file__), 'processed_urls.txt')
        processed_urls = set()
        
        if os.path.exists(processed_file):
            try:
                with open(processed_file, 'r', encoding='utf-8') as f:
                    processed_urls = set(line.strip() for line in f if line.strip())
                logging.info(f"📋 Loaded {len(processed_urls)} previously processed URLs")
            except Exception as e:
                logging.warning(f"Failed to load processed URLs: {e}")
        
        return processed_urls
    
    def _save_processed_urls(self, new_urls):
        """Save newly processed URLs to avoid reprocessing"""
        processed_file = os.path.join(os.path.dirname(__file__), 'processed_urls.txt')
        
        try:
            with open(processed_file, 'a', encoding='utf-8') as f:
                for url in new_urls:
                    f.write(f"{url}\n")
            logging.info(f"💾 Saved {len(new_urls)} new URLs to processed list")
        except Exception as e:
            logging.warning(f"Failed to save processed URLs: {e}")

    def _process_single_post(self, url, title, all_posts, seen_urls):
        """Process a single FDA post and extract ONLY main page content"""
        if url in seen_urls:
            return
        seen_urls.add(url)
        
        try:
            resp = requests.get(url, timeout=15, headers=self.HEADERS)
            if resp.status_code != 200:
                logging.warning(f"Failed to fetch {url}: {resp.status_code}")
                return
                
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Extract main text content ONLY
            content_div = soup.find('div', class_='entry-content') or soup.find('div', class_='content') or soup.find('main')
            if content_div:
                # Remove navigation and sidebar elements
                for element in content_div.find_all(['nav', 'aside', 'footer', 'header']):
                    element.decompose()
                text_content = content_div.get_text(strip=True, separator=' ')
            else:
                text_content = soup.get_text(strip=True, separator=' ')
            
            logging.info(f"   📄 Processing: {title[:60]}...")
            logging.info(f"   ✅ Extracted HTML content ({len(text_content)} chars)")
            
            # Add ONLY main page content - NO PDFs
            all_posts.append({
                'url': url,
                'source': 'FDA_Latest_Issuances',
                'title': title,
                'text_content': text_content,
                'is_text_only': True
            })
            
        except Exception as e:
            logging.warning(f"Failed to process {url}: {e}")

    def fetch_ph_guidance_pdfs(self):
        pdfs = []
        next_url = PH_GUIDANCE_URL
        while next_url:
            for attempt in range(RETRY_COUNT):
                try:
                    resp = requests.get(next_url, timeout=10, headers=self.HEADERS)
                    if resp.status_code != 200:
                        raise Exception(f"Status {resp.status_code}")
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    main = soup.find('main')
                    if main:
                        for a in main.find_all('a', href=True):
                            href = a['href']
                            if href.lower().endswith('.pdf'):
                                pdfs.append({'source': 'PH', 'url': href, 'page_url': next_url})
                    # Find next page
                    next_link = soup.find('a', {'class': 'next'})
                    next_url = next_link['href'] if next_link else None
                    break
                except Exception as e:
                    logging.warning(f"PH page fetch failed: {e}")
                    time.sleep(RETRY_DELAY)
            else:
                break
        return pdfs

    def yield_all_pdfs(self):
        # Only fetch FDA latest issuances (no PH guidance, no archives)
        for pdf in self.fetch_fda_pdfs():
            yield pdf
