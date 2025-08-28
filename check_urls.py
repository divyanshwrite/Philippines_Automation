#!/usr/bin/env python3
"""
Quick URL check - stop early to see what URLs fetcher provides
"""
from fetcher import Fetcher

def check_fetcher_urls():
    fetcher = Fetcher()
    count = 0
    
    print('🔍 CHECKING URLs FROM FETCHER (FIRST 5 ONLY):')
    print('=' * 60)
    
    try:
        for pdf_info in fetcher.yield_all_pdfs():
            count += 1
            print(f'{count}. Title: {pdf_info["title"][:50]}...')
            print(f'   URL: "{pdf_info["link_guidance"]}"')
            print(f'   Source URL: "{pdf_info.get("json_data", {}).get("source_url", "")}"')
            print()
            
            if count >= 5:  # Stop after 5
                print(f'🛑 Stopping after {count} documents to avoid full processing')
                break
                
    except KeyboardInterrupt:
        print(f'\n⏹️  Stopped by user after {count} documents')
    except Exception as e:
        print(f'\n❌ Error: {e}')
    
    print(f'\n✅ Checked {count} documents')

if __name__ == '__main__':
    check_fetcher_urls()
