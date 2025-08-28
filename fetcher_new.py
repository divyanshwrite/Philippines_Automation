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
        """Fetch all posts from FDA latest issuances pages"""
        all_posts = []
        base_url = "https://www.fda.gov.ph/latest-issuances/"
        seen_urls = set()
        
        logging.info(f"🔍 Starting to fetch from: {base_url}")
        
        # Process the main page (since pagination shows same content)
        logging.info(f"🔍 Processing main page: {base_url}")
        
        try:
            resp = requests.get(base_url, timeout=15, headers=self.HEADERS)
            if resp.status_code != 200:
                logging.warning(f"Failed to fetch main page: {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Look for actual post links with || separator
            main_posts = 0
            for link in soup.find_all('a', href=True):
                href = link['href']
                title = link.get_text(strip=True)
                
                # Make sure it's a full URL
                if not href.startswith('http') and href.startswith('/'):
                    href = 'https://www.fda.gov.ph' + href
                
                # Filter for actual FDA post links with || separator
                if (title and len(title) > 20
                    and 'fda.gov.ph' in href
                    and href not in seen_urls
                    and '||' in title
                    and not any(skip in href.lower() for skip in [
                        '/category/', '/tag/', '/author/', '/page/',
                        '/wp-content/themes/', '/wp-admin/'
                    ])):
                    
                    self._process_single_post(href, title, all_posts, seen_urls)
                    main_posts += 1
            
            logging.info(f"   📄 Found {main_posts} main posts")
            
        except Exception as e:
            logging.warning(f"Failed to process main page: {e}")
        
        # Check archives for historical content (limited to avoid overload)
        logging.info("🔍 Checking archives for additional content...")
        
        try:
            archive_url = "https://www.fda.gov.ph/archives/"
            resp = requests.get(archive_url, timeout=15, headers=self.HEADERS)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                archive_posts = 0
                pdf_count = 0
                
                # Look for both post links and direct PDF links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    title = link.get_text(strip=True)
                    
                    if not href.startswith('http') and href.startswith('/'):
                        href = 'https://www.fda.gov.ph' + href
                    
                    # Check for direct PDF links or post pages
                    if (href not in seen_urls and 
                        ('fda.gov.ph' in href) and
                        (href.lower().endswith('.pdf') or 
                         (title and len(title) > 15 and not any(skip in href.lower() for skip in [
                             '/wp-content/themes/', '/wp-admin/', '/category/', '/tag/',
                             '/citizens-charter', '/fda-academy', '/downloadables',
                             '/transparency', '/bids-and-awards', '/about-fda'
                         ])))):
                        
                        if href.lower().endswith('.pdf'):
                            # Direct PDF link
                            pdf_count += 1
                            all_posts.append({
                                'source': 'FDA',
                                'url': href,
                                'page_url': archive_url,
                                'title': title or f'PDF Document {pdf_count}',
                                'text_content': '',
                                'is_text_only': False
                            })
                            seen_urls.add(href)
                            
                            # Limit PDFs to avoid overwhelming processing
                            if pdf_count >= 50:  # Limit to first 50 PDFs
                                break
                        else:
                            # Regular post page
                            self._process_single_post(href, title, all_posts, seen_urls)
                            archive_posts += 1
                
                logging.info(f"   📄 Found {archive_posts} archive posts + {pdf_count} PDFs")
                
        except Exception as e:
            logging.warning(f"Failed to process archives: {e}")
        
        logging.info(f"🎉 Total items collected: {len(all_posts)}")
        return all_posts

    def _process_single_post(self, post_url, post_title, all_posts, seen_urls):
        """Process a single post and add it to the results"""
        if post_url in seen_urls:
            return
        
        seen_urls.add(post_url)
        
        try:
            logging.info(f"   📄 Processing: {post_title[:60]}...")
            
            resp = requests.get(post_url, timeout=15, headers=self.HEADERS)
            if resp.status_code != 200:
                logging.warning(f"Failed to fetch post {post_url}: {resp.status_code}")
                return
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extract main content from the <main> tag
            main_content = ""
            main_tag = soup.find('main')
            if main_tag:
                # Remove navigation, scripts, styles
                for element in main_tag(['script', 'style', 'nav', 'aside', 'footer', 'header']):
                    element.decompose()
                
                main_content = main_tag.get_text(separator='\n', strip=True)
                
                # Clean up the content
                lines = [line.strip() for line in main_content.split('\n') if line.strip()]
                cleaned_lines = []
                prev_line = ""
                for line in lines:
                    if line != prev_line and len(line) > 5:
                        cleaned_lines.append(line)
                        prev_line = line
                main_content = '\n'.join(cleaned_lines)
            
            # Find PDF attachments
            pdf_count = 0
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.lower().endswith('.pdf'):
                    if not href.startswith('http'):
                        href = 'https://www.fda.gov.ph' + href if href.startswith('/') else post_url + '/' + href
                    
                    all_posts.append({
                        'source': 'FDA',
                        'url': href,
                        'page_url': post_url,
                        'title': f"{post_title} - PDF Attachment{f'_{pdf_count}' if pdf_count > 0 else ''}",
                        'text_content': main_content
                    })
                    pdf_count += 1
            
            # Add the text content of the page itself
            all_posts.append({
                'source': 'FDA',
                'url': post_url,
                'page_url': post_url,
                'title': post_title,
                'text_content': main_content,
                'is_text_only': True
            })
            
            logging.info(f"   ✅ Extracted content ({len(main_content)} chars) + {pdf_count} PDFs")
            
        except Exception as e:
            logging.warning(f"Failed to process post {post_url}: {e}")

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
