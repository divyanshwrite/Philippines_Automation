import requests
import logging
import time
from bs4 import BeautifulSoup
from config import FDA_API_URL, PH_GUIDANCE_URL

logging.basicConfig(level=logging.INFO)

RETRY_COUNT = 3
RETRY_DELAY = 2

class Fetcher:
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

    def fetch_fda_pdfs(self):
        """Fetch all posts from FDA latest issuances pages and category pages"""
        all_posts = []
        base_url = "https://www.fda.gov.ph/latest-issuances/"
        seen_urls = set()  # Track processed URLs to avoid duplicates
        
        logging.info(f"🔍 Starting to fetch from: {base_url}")
        
        try:
            # First, get the latest posts from the main pages
            for page_num in range(1, 9):  # 8 pages total
                if page_num == 1:
                    page_url = base_url
                else:
                    page_url = f"{base_url}?_page={page_num}"
                
                logging.info(f"🔍 Processing page {page_num}: {page_url}")
                
                try:
                    page_resp = requests.get(page_url, timeout=15, headers=self.HEADERS)
                    if page_resp.status_code != 200:
                        logging.warning(f"Failed to fetch page {page_num}: {page_resp.status_code}")
                        continue
                    
                    page_soup = BeautifulSoup(page_resp.text, 'html.parser')
                    
                    # Look for actual post links - they have "||" and longer descriptive titles
                    for link in page_soup.find_all('a', href=True):
                        href = link['href']
                        title = link.get_text(strip=True)
                        
                        # Make sure it's a full URL
                        if not href.startswith('http') and href.startswith('/'):
                            href = 'https://www.fda.gov.ph' + href
                        
                        # Filter for actual FDA post links
                        if (title and len(title) > 20  # Long descriptive titles
                            and 'fda.gov.ph' in href
                            and href not in seen_urls  # Avoid duplicates
                            and ('||' in title  # Posts typically have || separator
                                 or any(word in title.lower() for word in ['advisory', 'circular', 'memorandum', 'order', 'announcement'])
                                 and 'no.' in title.lower())  # Or contain FDA document keywords with numbers
                            and not any(skip in href.lower() for skip in [
                                '/category/', '/tag/', '/author/', '/page/',
                                '/citizens-charter', '/fda-academy', '/downloadables',
                                '/transparency', '/lifting-advisories', '/old-fda-advisories',
                                '/administrative-order', '/memorandum-circular', '/pharmacovigilance',
                                '/philippine-national-standards', '/bids-and-awards'
                            ])):
                            
                            self._process_single_post(href, title, all_posts, seen_urls)
                    
                    time.sleep(2)  # Be polite between pages
                    
                except Exception as e:
                    logging.warning(f"Failed to process page {page_num}: {e}")
            
            # Now, also check category/archive pages for more content
        # Check category pages for additional content (skip Old FDA Advisories to avoid huge processing)
        category_urls = [
            "https://www.fda.gov.ph/fda-circular/",
            "https://www.fda.gov.ph/fda-memorandum/", 
            "https://www.fda.gov.ph/administrative-order/",
            "https://www.fda.gov.ph/memorandum-circular/",
            "https://www.fda.gov.ph/executive-order/",
            "https://www.fda.gov.ph/republic-act/",
            "https://www.fda.gov.ph/archives/"
            # Skipping old-fda-advisories as it has 1000+ PDFs
        ]
        
        for category_url in category_urls:
                logging.info(f"🔍 Checking category: {category_url}")
                
                try:
                    cat_resp = requests.get(category_url, timeout=15, headers=self.HEADERS)
                    if cat_resp.status_code != 200:
                        logging.warning(f"Failed to fetch category {category_url}: {cat_resp.status_code}")
                        continue
                    
                    cat_soup = BeautifulSoup(cat_resp.text, 'html.parser')
                    
                    # Look for posts in the category page
                    category_posts = 0
                    for link in cat_soup.find_all('a', href=True):
                        href = link['href']
                        title = link.get_text(strip=True)
                        
                        # Make sure it's a full URL
                        if not href.startswith('http') and href.startswith('/'):
                            href = 'https://www.fda.gov.ph' + href
                        
                        # Look for individual document posts
                        if (title and len(title) > 15
                            and 'fda.gov.ph' in href
                            and href not in seen_urls
                            and not any(skip in href for skip in ['/page/', '/category/', '/tag/', '/wp-content/'])
                            and (any(word in title.lower() for word in ['fda', 'circular', 'advisory', 'order', 'memorandum', 'no.'])
                                 or 'no.' in title.lower())):
                            
                            if self._process_single_post(href, title, all_posts, seen_urls):
                                category_posts += 1
                                
                                # Limit posts per category to avoid overload
                                if category_posts >= 10:
                                    break
                    
                    logging.info(f"✓ Found {category_posts} posts in category")
                    time.sleep(3)  # Be polite
                    
                except Exception as e:
                    logging.warning(f"Failed to process category {category_url}: {e}")
            
        logging.info(f"🎉 Total items collected: {len(all_posts)}")
        return all_posts
    
    def _process_single_post(self, post_url, post_title, all_posts, seen_urls):
        """Process a single post and add it to the results"""
        if post_url in seen_urls:
            return False
            
        seen_urls.add(post_url)
        logging.info(f"   📄 Processing: {post_title[:60]}...")
        
        try:
            post_resp = requests.get(post_url, timeout=15, headers=self.HEADERS)
            if post_resp.status_code != 200:
                logging.warning(f"   ❌ Failed to fetch post: {post_resp.status_code}")
                return False
            
            post_soup = BeautifulSoup(post_resp.text, 'html.parser')
            
            # Extract content from main tag
            main_content = ""
            main_tag = post_soup.find('main')
            
            if main_tag:
                # Remove unwanted elements
                for element in main_tag(['script', 'style', 'nav', 'footer', 'header', '.sidebar', '.menu']):
                    element.decompose()
                
                main_content = main_tag.get_text(separator='\n', strip=True)
            else:
                # Fallback: try article or content div
                content_tag = post_soup.find('article') or post_soup.find('div', class_='content')
                if content_tag:
                    for element in content_tag(['script', 'style', 'nav', 'footer', 'header']):
                        element.decompose()
                    main_content = content_tag.get_text(separator='\n', strip=True)
            
            # Clean up the content
            if main_content:
                lines = [line.strip() for line in main_content.split('\n') if line.strip()]
                cleaned_lines = []
                prev_line = ""
                for line in lines:
                    if line != prev_line and len(line) > 3:
                        cleaned_lines.append(line)
                        prev_line = line
                main_content = '\n'.join(cleaned_lines)
            
            # Find PDF attachments
            pdf_links = []
            for a in post_soup.find_all('a', href=True):
                href = a['href']
                if href.lower().endswith('.pdf'):
                    if not href.startswith('http'):
                        href = 'https://www.fda.gov.ph' + href
                    pdf_links.append(href)
            
            # Add text content
            all_posts.append({
                'source': 'FDA',
                'url': post_url,
                'page_url': post_url,
                'title': post_title,
                'text_content': main_content,
                'is_text_only': True
            })
            
            # Add PDF attachments
            for pdf_url in pdf_links:
                all_posts.append({
                    'source': 'FDA',
                    'url': pdf_url,
                    'page_url': post_url,
                    'title': f"{post_title} - PDF Attachment",
                    'text_content': main_content,
                    'is_text_only': False
                })
            
            logging.info(f"   ✅ Extracted content ({len(main_content)} chars) + {len(pdf_links)} PDFs")
            time.sleep(1)  # Be polite
            return True
            
        except Exception as e:
            logging.warning(f"   ❌ Failed to process post {post_url}: {e}")
            return False

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
        for pdf in self.fetch_fda_pdfs():
            yield pdf
        for pdf in self.fetch_ph_guidance_pdfs():
            yield pdf
