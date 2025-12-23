"""
Requests-HTML scraper for JavaScript-rendered pages (alternative to Selenium)
"""
import logging
import time
from typing import Dict, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

try:
    from requests_html import HTMLSession, AsyncHTMLSession
    import asyncio
    REQUESTS_HTML_AVAILABLE = True
except ImportError as e:
    REQUESTS_HTML_AVAILABLE = False
    logger.warning(f"requests-html not available: {e}, install with: pip install requests-html")


class RequestsHtmlScraper(BaseScraper):
    """Scraper using requests-html for JavaScript-rendered pages"""
    
    def __init__(self, url: str, wait_time: int = 10):
        super().__init__(url)
        self.wait_time = wait_time
        self.session = None
    
    def setup_session(self):
        """Setup HTML session"""
        if not REQUESTS_HTML_AVAILABLE:
            logger.error("requests-html is not available")
            return None
        
        if not self.session:
            self.session = HTMLSession()
        
        return self.session
    
    def fetch_page_html(self, url: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Fetch page using requests-html and render JavaScript"""
        target_url = url or self.url
        
        try:
            # Try async session first (better for JS rendering)
            try:
                async_session = AsyncHTMLSession()
                logger.info(f"Loading page with requests-html (async): {target_url}")
                
                # Create event loop if needed
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run async fetch
                async def fetch():
                    response = await async_session.get(target_url, timeout=30)
                    await response.html.arender(wait=self.wait_time, timeout=30)
                    return response.html.html
                
                html_content = loop.run_until_complete(fetch())
                async_session.close()
                
            except Exception as async_error:
                logger.warning(f"Async failed, trying sync: {async_error}")
                # Fallback to sync session
                session = self.setup_session()
                if not session:
                    return None
                
                logger.info(f"Loading page with requests-html (sync): {target_url}")
                response = session.get(target_url, timeout=30)
                
                # Render JavaScript (executes JS on the page)
                response.html.render(wait=self.wait_time, timeout=30)
                
                # Get rendered HTML
                html_content = response.html.html
            
            return BeautifulSoup(html_content, 'html.parser')
            
        except Exception as e:
            logger.error(f"Error fetching page with requests-html: {str(e)}")
            return None
    
    def scrape(self) -> Dict:
        """Scrape using requests-html"""
        soup = self.fetch_page_html()
        if not soup:
            return {
                'company': self.get_company_name(),
                'url': self.url,
                'status': 'error',
                'error': 'Could not fetch page with requests-html',
                'prices': []
            }
        
        # Use parent class methods to extract prices
        prices = []
        
        # Method 1: Look for pricing tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = ' '.join([cell.get_text() for cell in cells])
                
                if any(kw in row_text.lower() for kw in ['fiyat', 'tarife', 'ücret', 'ucret', 'price', 'kwh', 'kw']):
                    price = self.extract_price_from_text(row_text)
                    if price:
                        charging_type = self.extract_charging_type(row_text)
                        power = self.extract_power(row_text)
                        prices.append(self.format_price_data(price, row_text, charging_type, power))
        
        # Method 2: Look for price sections
        price_sections = soup.find_all(
            ['div', 'section', 'article'],
            class_=lambda x: x and any(
                keyword in ' '.join(x).lower() 
                for keyword in ['price', 'fiyat', 'tarife', 'pricing', 'plan', 'paket']
            )
        )
        
        for section in price_sections:
            text = section.get_text()
            price = self.extract_price_from_text(text)
            if price:
                charging_type = self.extract_charging_type(text)
                power = self.extract_power(text)
                prices.append(self.format_price_data(price, text, charging_type, power))
        
        # Method 3: Look for price keywords
        keyword_prices = self.find_price_keywords(soup)
        prices.extend(keyword_prices)
        
        # Method 4: Look for list items
        lists = soup.find_all(['ul', 'ol', 'dl'])
        for list_elem in lists:
            items = list_elem.find_all('li', recursive=False)
            for item in items:
                text = item.get_text()
                if any(kw in text.lower() for kw in ['fiyat', 'tarife', 'ücret', 'kwh', 'kw']):
                    price = self.extract_price_from_text(text)
                    if price:
                        charging_type = self.extract_charging_type(text)
                        power = self.extract_power(text)
                        prices.append(self.format_price_data(price, text, charging_type, power))
        
        # Remove duplicates
        seen = set()
        unique_prices = []
        
        for price_info in prices:
            price_val = price_info.get('price', 0)
            desc = price_info.get('description', '') or ''
            desc_key = desc[:50] if desc else ''
            
            price_key = round(price_val, 2)
            unique_key = (price_key, desc_key)
            
            if unique_key not in seen and price_info.get('description'):
                seen.add(unique_key)
                unique_prices.append(price_info)
        
        unique_prices.sort(key=lambda x: x.get('price', 0))
        unique_prices = unique_prices[:10]
        
        return {
            'company': self.get_company_name(),
            'url': self.url,
            'status': 'success' if unique_prices else 'no_prices_found',
            'prices': unique_prices
        }

