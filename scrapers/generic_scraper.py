"""
Generic scraper for websites without specific scrapers
"""
import logging
import re
from typing import Dict, List, Set
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GenericScraper(BaseScraper):
    """Generic scraper that tries to find prices on any website"""
    
    def scrape(self) -> Dict:
        """Generic scraping method"""
        soup = self.fetch_page()
        if not soup:
            return {
                'company': self.get_company_name(),
                'url': self.url,
                'status': 'error',
                'error': 'Could not fetch page',
                'prices': []
            }
        
        prices = []
        
        # Method 1: Look for pricing tables (most reliable)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = ' '.join([cell.get_text() for cell in cells])
                
                # Check if row contains pricing keywords
                if any(kw in row_text.lower() for kw in ['fiyat', 'tarife', 'ücret', 'ucret', 'price', 'kwh', 'kw']):
                    price = self.extract_price_from_text(row_text)
                    if price:
                        charging_type = self.extract_charging_type(row_text)
                        power = self.extract_power(row_text)
                        prices.append(self.format_price_data(price, row_text, charging_type, power))
        
        # Method 2: Look for pricing cards/sections (including "hizmet", "fiyatlandırma")
        price_sections = soup.find_all(
            ['div', 'section', 'article'],
            class_=lambda x: x and any(
                keyword in ' '.join(x).lower() 
                for keyword in ['price', 'fiyat', 'tarife', 'pricing', 'plan', 'paket', 'hizmet', 'fiyatlandırma', 'fiyatlandirma']
            )
        )
        
        for section in price_sections:
            text = section.get_text()
            price = self.extract_price_from_text(text)
            if price:
                charging_type = self.extract_charging_type(text)
                power = self.extract_power(text)
                prices.append(self.format_price_data(price, text, charging_type, power))
        
        # Method 3: Look for price keywords in text
        keyword_prices = self.find_price_keywords(soup)
        prices.extend(keyword_prices)
        
        # Method 4: Look for list items with prices
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
        
        # Method 5: Look for divs/spans with price-like classes or data attributes
        price_elements = soup.find_all(
            ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4'],
            class_=lambda x: x and any(
                keyword in ' '.join(x).lower() 
                for keyword in ['price', 'fiyat', 'tarife', 'ucret', 'cost', 'amount']
            )
        )
        
        for elem in price_elements:
            text = elem.get_text()
            price = self.extract_price_from_text(text)
            if price:
                charging_type = self.extract_charging_type(text)
                power = self.extract_power(text)
                prices.append(self.format_price_data(price, text, charging_type, power))
        
        # Method 6: Look for divs/spans with AC/DC and prices together
        # This helps find prices like "AC 22 kWh 8.2 TL/kWh" or "AC 6 TL/kWh"
        all_divs = soup.find_all(['div', 'span', 'p', 'h2', 'h3', 'h4'])
        for elem in all_divs:
            text = elem.get_text()
            # Check if contains both AC/DC and a price
            if (('ac' in text.lower() or 'dc' in text.lower()) and 
                any(kw in text.lower() for kw in ['kwh', 'kw', 'tl', '₺', 'fiyat'])):
                # Use extract_price_from_text which now handles whole numbers too
                price = self.extract_price_from_text(text)
                if price:
                    charging_type = self.extract_charging_type(text)
                    power = self.extract_power(text)
                    prices.append(self.format_price_data(price, text, charging_type, power))
                
                # Also try to extract all prices (including whole numbers) from this element
                # Pattern for both decimal and whole numbers
                price_matches = re.findall(r'(\d+(?:[.,]\d{1,2})?)', text)
                for price_str in price_matches:
                    try:
                        # Handle Turkish number format: comma as decimal separator
                        if ',' in price_str and '.' not in price_str:
                            price_val = float(price_str.replace(',', '.'))
                        elif ',' in price_str and '.' in price_str:
                            # Both comma and dot: assume comma is decimal (Turkish format)
                            if price_str.rindex(',') > price_str.rindex('.'):
                                price_val = float(price_str.replace('.', '').replace(',', '.'))
                            else:
                                price_val = float(price_str.replace(',', ''))
                        else:
                            # Whole number
                            price_val = float(price_str)
                        
                        if 0.5 <= price_val <= 50:
                            charging_type = self.extract_charging_type(text)
                            power = self.extract_power(text)
                            prices.append(self.format_price_data(price_val, text, charging_type, power))
                    except ValueError:
                        continue
        
        # Remove duplicates and invalid entries
        seen: Set[tuple] = set()
        unique_prices = []
        
        for price_info in prices:
            # Create unique key based on price (rounded to 2 decimals) and description
            price_val = price_info.get('price', 0)
            desc = price_info.get('description', '') or ''
            desc_key = desc[:50] if desc else ''
            
            # Round price for comparison
            price_key = round(price_val, 2)
            unique_key = (price_key, desc_key)
            
            if unique_key not in seen and price_info.get('description'):  # Only add if has description
                seen.add(unique_key)
                unique_prices.append(price_info)
        
        # Sort by price
        unique_prices.sort(key=lambda x: x.get('price', 0))
        
        # Limit to reasonable number of prices (max 10)
        unique_prices = unique_prices[:10]
        
        return {
            'company': self.get_company_name(),
            'url': self.url,
            'status': 'success' if unique_prices else 'no_prices_found',
            'prices': unique_prices
        }

