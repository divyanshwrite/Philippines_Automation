import requests
import logging
import time
import json
from bs4 import BeautifulSoup
from config import FDA_API_URL, PH_GUIDANCE_URL

logging.basicConfig(level=logging.INFO)

RETRY_COUNT = 3
RETRY_DELAY = 2

class Fetcher:
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

    def fetch_fda_pdfs(self):
        """Fetch FDA regulatory documents from Latest Issuances as user requested"""
        all_posts = []
        seen_urls = set()
        
        # User's list of FDA regulatory documents from Latest Issuances
        known_fda_docs = [
            {
                'title': 'FDA Circular No.2025-004 || Adoption of Codex Standard for Follow-Up Formula for Older Infants and Product/Drink for Young Children (CXS 156-1987) as Technical Regulation',
                'url': 'https://www.fda.gov.ph/fda-circular-no-2025-004-adoption-of-codex-standard-for-follow-up-formula-for-older-infants-and-product-drink-for-young-children-cxs-156-1987-as-technical-regulation/'
            },
            {
                'title': 'FDA Circular No.2025-003 || Adoption of Codex Guidelines for Ready-To-Use Therapeutic Foods (RUTF) (CXG 95-2022) as Technical Regulation',
                'url': 'https://www.fda.gov.ph/fda-circular-no-2025-003-adoption-of-codex-guidelines-for-ready-to-use-therapeutic-foods-rutf-cxg-95-2022-as-technical-regulation/'
            },
            {
                'title': 'FDA Order No.2023-0790-B || Lifting the Temporary Ban on the Importation of Processed Pork Products from the Republic of Korea',
                'url': 'https://www.fda.gov.ph/fda-order-no-2023-0790-b-lifting-the-temporary-ban-on-the-importation-of-processed-pork-products-from-the-republic-of-korea/'
            },
            {
                'title': 'DEPARTMENT CIRCULAR NO.2025-0240 || Temporary Suspension for Sixty (60) Working Days of the Implementation of Administrative Order No. 2024-0016',
                'url': 'https://www.fda.gov.ph/department-circular-no-2025-0240-all-undersecretaries-and-assistant-secretaries-directors-of-bureaus-services-and-centers-for-health-development-minister-of-health-bangsamoro-autonomous-region/'
            },
            {
                'title': 'FDA Circular No.2025-002 || Updates and Amendments to the ASEAN Cosmetic Directive (ACD)',
                'url': 'https://www.fda.gov.ph/fda-circular-no-2025-002-updates-and-amendments-to-the-asean-cosmetic-directive-acd-as-adopted-during-the-39th-asean-cosmetic-committee-acc-meeting-and-its-related-meetings/'
            },
            {
                'title': 'FDA Circular No.2025-0001 || Guidelines on the Classification of Vitamins and Minerals for Food/Dietary Supplements',
                'url': 'https://www.fda.gov.ph/fda-circular-no-2025-0001-guidelines-on-the-classification-of-vitamins-and-minerals-for-food-dietary-supplements-for-adults-under-processed-food-product-repealing-the-level-set-for-food-in-the-off/'
            },
            {
                'title': 'Administrative Order No. 2024-0016 || Implementing Guidelines on the New Schedule of Fees and Charges',
                'url': 'https://www.fda.gov.ph/administrative-order-implementing-guidelines-on-the-new-schedule-of-fees-and-charges-of-the-food-and-drug-administration/'
            },
            {
                'title': 'Administrative Order No.2024-0015 || Prescribing the Rules, Requirements and Procedures in the Application for License to Operate',
                'url': 'https://www.fda.gov.ph/administrative-order-no-2024-0015-prescribing-the-rules-requirements-and-procedures-in-the-application-for-license-to-operate-of-covered-health-product-establishments-with-the-food-and-drug-adm/'
            },
            {
                'title': 'Administrative Order No.2024-0013 || General Rules and Regulations on the Registration of Pharmaceutical Products',
                'url': 'https://www.fda.gov.ph/administrative-order-no-2024-0013-general-rules-and-regulations-pharmaceutical-products-and-ingredients-intended-for-human-use-on-the-registration-of-active-pharmaceutical/'
            },
            {
                'title': 'Administrative Order No. 2024-0012 || Prescribing the Rules and Regulations on the Registration of Pharmaceutical Products Intended Solely for Export',
                'url': 'https://www.fda.gov.ph/administrative-order-no-2024-0012-prescribing-the-rules-and-regulations-on-the-registration-of-pharmaceutical-products-and-active-pharmaceutical-ingredients-intended-solely-for-export/'
            }
        ]
        
        logging.info(f"� Fetching {len(known_fda_docs)} FDA regulatory documents from Latest Issuances")
        
        # Process each known FDA regulatory document
        for i, doc in enumerate(known_fda_docs, 1):
            logging.info(f"[{i}/{len(known_fda_docs)}] Processing: {doc['title'][:60]}...")
            self._process_single_post(doc['url'], doc['title'], all_posts, seen_urls)
            time.sleep(0.5)
        
        logging.info(f"🎉 Total FDA regulatory documents: {len(all_posts)}")
        return all_posts

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
