"""
Base scraper class for all charging station scrapers
"""
import re
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all charging station scrapers"""
    
    def __init__(self, url: str):
        self.url = url
        self.domain = urlparse(url).netloc
        self.session = requests.Session()
        self.ua = UserAgent()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        })
    
    def fetch_page(self, url: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page"""
        target_url = url or self.url
        try:
            response = self.session.get(target_url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {target_url}: {str(e)}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean text from CSS, JS, and other noise"""
        if not text:
            return ""
        
        # Remove script and style content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove common CSS/JS patterns
        text = re.sub(r'\{[^}]*\}', '', text)  # Remove CSS blocks
        text = re.sub(r'\.\w+\s*\{[^}]*\}', '', text)  # Remove CSS classes
        text = re.sub(r'var\s+\w+\s*=.*?;', '', text)  # Remove JS vars
        text = re.sub(r'function\s+\w+.*?\{.*?\}', '', text, flags=re.DOTALL)  # Remove JS functions
        text = re.sub(r'__\w+__', '', text)  # Remove internal markers
        
        # Remove CSS selector strings (e.g., ".title,.nav .nav-item.active > a")
        text = re.sub(r'[.#][a-z0-9\-_:]*(\s*[>,+~]\s*[.#]?[a-z0-9\-_:]*)*', '', text, flags=re.IGNORECASE)
        
        # Remove long HTML class/id attributes that are not useful
        text = re.sub(r'(class|id)=["\'][^"\']{80,}["\']', '', text, flags=re.IGNORECASE)
        
        # Remove HTML attributes
        text = re.sub(r'\s+(data-|aria-|on)[a-z-]*=["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
        
        # Clean whitespace
        text = ' '.join(text.split())
        
        # Remove very long words (likely encoded data or CSS selector strings)
        words = text.split()
        words = [w for w in words if len(w) < 50]
        text = ' '.join(words)
        
        return text.strip()
    
    def extract_price_from_text(self, text: str, min_price: float = 0.5, max_price: float = 50.0) -> Optional[float]:
        """Extract price value from text with validation.
        Filters out dates (e.g., "01.07.2025" -> 1.07) and power ratings (e.g., "3 kW" -> 3.0).
        """
        if not text:
            return None
        
        # Clean text first
        text = self.clean_text(text)
        
        # Date patterns to filter out (e.g., "01.07.2025" -> 1.07, "05.11.2025" -> 5.11)
        # Match dates like "01.07.2025", "05.11.2025", "1.07.2025", etc.
        date_pattern = r'\b0?[0-3]?[0-9]\.(0[1-9]|1[0-2])\.(20\d{2})\b'  # Matches "01.07.2025", "05.11.2025", etc.
        
        # Filter out power ratings - if text contains "X kW" or "X kW - Y kW", don't extract X as price
        # This prevents "3 kW" from being extracted as price 3.0
        power_pattern = r'\b(\d+)\s*kW\b'
        power_matches = re.findall(power_pattern, text, re.IGNORECASE)
        power_values = set([int(m) for m in power_matches])
        
        # Try to find price patterns (e.g., 5.50, 5,50, 5.50 TL, 6 TL, etc.)
        # More specific patterns first - handle both comma and dot as decimal separator
        # Also handle whole numbers (e.g., 6 TL/kWh, 10 TL/kWh)
        # IMPORTANT: Prioritize patterns with currency (TL/₺) to avoid extracting power ratings
        patterns = [
            r'(\d+[.,]\d{1,2})\s*(?:TL|₺|TRY)\s*/?\s*(?:kWh|kW|kw)',
            r'(?:₺|TL|TRY)\s*(\d+[.,]\d{1,2})\s*/?\s*(?:kWh|kW|kw)',
            r'(\d+)\s*(?:TL|₺|TRY)\s*/?\s*(?:kWh|kW|kw)',  # Whole numbers: 6 TL/kWh
            r'(?:₺|TL|TRY)\s*(\d+)\s*/?\s*(?:kWh|kW|kw)',  # Whole numbers: ₺10/kWh
            r'(\d+[.,]\d{1,2})\s*(?:TL|₺|TRY)',
            r'(?:₺|TL|TRY)\s*(\d+[.,]\d{1,2})',
            r'(\d+)\s*(?:TL|₺|TRY)',  # Whole numbers: 6 TL
            r'(?:₺|TL|TRY)\s*(\d+)',  # Whole numbers: ₺10
            r'(\d+[.,]\d{1,2})\s*/?\s*(?:kWh|kW|kw)',
            r'(\d+)\s*/?\s*(?:kWh|kW|kw)',  # Whole numbers: 6/kWh
            r'(\d+[.,]\d{1,2})',
            r'(\d+)',  # Whole numbers as fallback
        ]
        
        # First, try to find prices with currency (TL/₺) - these are more reliable
        # Handle formats like "TL / kWh 8.9" or "8.9 TL/kWh" or "AC1 8.99 TL/kWh"
        currency_patterns = [
            r'(?:AC|DC)\d+\s*(\d+[.,]\d{1,2})\s*(?:TL|₺|TRY)',  # "AC1 8.99 TL" or "DC1 9.99 TL"
            r'(?:TL|₺|TRY)\s*/?\s*(?:kWh|kW|kw)?\s*(\d+[.,]\d{1,2})',  # "TL / kWh 8.9"
            r'(\d+[.,]\d{1,2})\s*(?:TL|₺|TRY)\s*/?\s*(?:kWh|kW|kw)?',  # "8.9 TL/kWh"
            r'(?:₺|TL|TRY)\s*(\d+[.,]\d{1,2})\s*/?\s*(?:kWh|kW|kw)?',  # "₺8.9/kWh"
            r'(\d+)\s*(?:TL|₺|TRY)\s*/?\s*(?:kWh|kW|kw)?',  # "8 TL/kWh"
            r'(?:₺|TL|TRY)\s*(\d+)\s*/?\s*(?:kWh|kW|kw)?',  # "₺8/kWh"
        ]
        
        currency_prices = []
        for pattern in currency_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price_str = match.group(1)
                    match_start = match.start()
                    match_end = match.end()
                    
                    # Check if this is part of a date pattern (e.g., "01.07.2025 tarihi itibariyle")
                    # Look at context around the match (50 chars before and after)
                    context_start = max(0, match_start - 50)
                    context_end = min(len(text), match_end + 50)
                    context = text[context_start:context_end]
                    
                    # Check if this number is part of a date
                    if re.search(date_pattern, context):
                        # This is likely a date, not a price - skip it
                        continue
                    
                    # Handle Turkish number format
                    if ',' in price_str and '.' not in price_str:
                        price_str = price_str.replace(',', '.')
                    elif ',' in price_str and '.' in price_str:
                        if price_str.rindex(',') > price_str.rindex('.'):
                            price_str = price_str.replace('.', '').replace(',', '.')
                        else:
                            price_str = price_str.replace(',', '')
                    
                    price = float(price_str)
                    
                    # Filter out very low prices that are likely dates (e.g., 1.07, 1.08, 1.09)
                    # These are usually dates like "01.07.2025" parsed as "1.07"
                    if price < 2.0 and price >= 1.0:
                        # Check if context contains date-related words
                        context_lower = context.lower()
                        date_keywords = ['tarih', 'tarihi', 'itibariyle', 'geçerli', 'geçerlidir', 
                                       'geçerli olmak', 'yürürlük', 'yürürlüğ', 'başlayan', 
                                       'yapılmıştır', 'yapılması', 'tarihinden', 'tarihine',
                                       'efektif', 'effective', 'since', 'from', 'başlama']
                        if any(word in context_lower for word in date_keywords):
                            continue  # Skip dates
                        # Also check for month abbreviations or number sequences that look like dates
                        if re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|ocak|şub|mar|nisan|mayıs|haz|tem|ağu|eyl|eki|kas|ara)\b', 
                                    context_lower):
                            continue  # Skip if near month names
                    
                    # Filter out power ratings - if this number appears as a power rating, skip it
                    # Power ratings are typically: 3, 3.6, 7.2, 11, 22, 30, 50, 60, 100, 120, 180, 200, 250, 300 kW
                    # If price matches a power value AND is not followed by currency/kWh, it's likely a power rating
                    if price in power_values:
                        context_after = text[match_end:match_end+30].lower()
                        # Check if it's followed by currency or kWh - if not, it's likely a power rating
                        if not any(currency in context_after for currency in ['tl', '₺', 'try', 'kwh', '/kwh', '/kw']):
                            continue
                        # Also check if it's immediately followed by "kw" or "kwh" without currency - that's a power rating
                        immediate_after = text[match_end:match_end+5].lower().strip()
                        if immediate_after.startswith('kw') or immediate_after.startswith('kwh'):
                            # Check if there's currency before this number
                            context_before = text[max(0, match_start-30):match_start].lower()
                            if not any(currency in context_before for currency in ['tl', '₺', 'try']):
                                continue  # This is a power rating, not a price
                    
                    if min_price <= price <= max_price:
                        currency_prices.append(price)
                except (ValueError, IndexError):
                    continue
        
        # If we found prices with currency, return the first one (most reliable)
        if currency_prices:
            return currency_prices[0]
        
        # Collect all potential prices
        all_prices = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price_str = match.group(1)
                    match_start = match.start()
                    match_end = match.end()
                    
                    # Check if this is part of a date pattern
                    context_start = max(0, match_start - 50)
                    context_end = min(len(text), match_end + 50)
                    context = text[context_start:context_end]
                    
                    # Check if this number is part of a date
                    if re.search(date_pattern, context):
                        # This is likely a date, not a price - skip it
                        continue
                    
                    # Handle Turkish number format: comma as decimal separator
                    # If comma is used, replace with dot
                    if ',' in price_str and '.' not in price_str:
                        price_str = price_str.replace(',', '.')
                    elif ',' in price_str and '.' in price_str:
                        # Both comma and dot: assume comma is decimal (Turkish format)
                        # e.g., "12,94" -> 12.94
                        if price_str.rindex(',') > price_str.rindex('.'):
                            price_str = price_str.replace('.', '').replace(',', '.')
                        else:
                            price_str = price_str.replace(',', '')
                    
                    price = float(price_str)
                    
                    # Filter out very low prices that are likely dates (e.g., 1.07, 1.08, 1.09)
                    if price < 2.0 and price >= 1.0:
                        context_lower = context.lower()
                        date_keywords = ['tarih', 'tarihi', 'itibariyle', 'geçerli', 'geçerlidir', 
                                       'geçerli olmak', 'yürürlük', 'yürürlüğ', 'başlayan', 
                                       'yapılmıştır', 'yapılması', 'tarihinden', 'tarihine',
                                       'efektif', 'effective', 'since', 'from', 'başlama']
                        if any(word in context_lower for word in date_keywords):
                            continue  # Skip dates
                        # Also check for month abbreviations or number sequences that look like dates
                        if re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|ocak|şub|mar|nisan|mayıs|haz|tem|ağu|eyl|eki|kas|ara)\b', 
                                    context_lower):
                            continue  # Skip if near month names
                    
                    # Filter out power ratings - if this number appears as a power rating, skip it
                    # Power ratings are typically: 3, 3.6, 7.2, 11, 22, 30, 50, 60, 100, 120, 180, 200, 250, 300 kW
                    if price in power_values:
                        context_after = text[match_end:match_end+30].lower()
                        # Check if it's followed by currency or kWh - if not, it's likely a power rating
                        if not any(currency in context_after for currency in ['tl', '₺', 'try', 'kwh', '/kwh', '/kw']):
                            continue
                        # Also check if it's immediately followed by "kw" or "kwh" without currency - that's a power rating
                        immediate_after = text[match_end:match_end+5].lower().strip()
                        if immediate_after.startswith('kw') or immediate_after.startswith('kwh'):
                            # Check if there's currency before this number
                            context_before = text[max(0, match_start-30):match_start].lower()
                            if not any(currency in context_before for currency in ['tl', '₺', 'try']):
                                continue  # This is a power rating, not a price
                    
                    # Validate price range (reasonable for Turkish charging stations)
                    if min_price <= price <= max_price:
                        all_prices.append(price)
                except (ValueError, IndexError):
                    continue
        
        # Return the first valid price found
        if all_prices:
            return all_prices[0]
        
        return None
    
    def extract_charging_type(self, text: str, price_position: int = None) -> Optional[str]:
        """Extract charging type (AC/DC) from text, optionally near a specific price position"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # If price position is provided, prioritize text BEFORE the price (200 chars before)
        # This helps when both AC and DC appear in the same text
        if price_position is not None:
            # Check text before price first (most relevant) - use 200 chars to catch "11 - 22 kW AC" patterns
            before_context = text_lower[max(0, price_position - 200):price_position]
            # Also check small context after
            after_context = text_lower[price_position:min(len(text), price_position + 20)]
            # Combine but prioritize before
            context = before_context + ' ' + after_context
        else:
            context = text_lower
        
        # If price position is provided, check for specific power range patterns first
        # These are more reliable (e.g., "11 - 22 kW AC" or "60 - 180 kW DC")
        if price_position is not None:
            # Check for power range patterns first (most specific)
            power_range_ac = re.search(r'\d+\s*-\s*\d+\s*kW\s*AC', context, re.IGNORECASE)
            power_range_dc = re.search(r'\d+\s*-\s*\d+\s*kW\s*DC', context, re.IGNORECASE)
            
            if power_range_ac and power_range_dc:
                # Both found - use the one closer to the price
                ac_pos = power_range_ac.end()
                dc_pos = power_range_dc.end()
                # price_position is relative to context start, so we need to adjust
                context_start = max(0, price_position - 200) if price_position > 200 else 0
                price_pos_in_context = price_position - context_start
                
                ac_dist = abs(ac_pos - price_pos_in_context)
                dc_dist = abs(dc_pos - price_pos_in_context)
                
                if ac_dist < dc_dist:
                    return 'AC'
                else:
                    return 'DC'
            elif power_range_ac:
                return 'AC'
            elif power_range_dc:
                return 'DC'
        
        # Check for AC patterns FIRST (before DC) - AC is more common
        # AC patterns: "AC soket", "AC tip", "AC şarj", "AC type", "AC Söketler", "11 - 22 kW AC"
        ac_patterns = [
            r'\d+\s*-\s*\d+\s*kW\s*AC',  # "11 - 22 kW AC" pattern
            r'ac\s*soket|ac\s*söket|ac\s*tip|ac\s*type|ac\s*şarj',
            r'\bac\s*[<>=]',
            r'ac\s*istasyon|ac\s*cihaz',
            r'\bac\b',
            r'alternating\s*current|alternatif\s*akım'
        ]
        for pattern in ac_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return 'AC'
        
        # Check for DC patterns (more specific first)
        # DC patterns: "DC soket", "DC şarj", "DC hızlı", "DC combo", "DC chademo", "DC Söketler", "60 - 180 kW DC", "DC1", "DC2", "DC 60 kW"
        dc_patterns = [
            r'DC\s+\d+\s*kW',  # "DC 60 kW", "DC 120 kW" pattern (must be uppercase)
            r'\d+\s*-\s*\d+\s*kW\s*DC',  # "60 - 180 kW DC" pattern
            r'dc[12]\s*soket|dc[12]\s*tarifesi',  # "DC1 Soket", "DC2 Soket Tarifesi" pattern
            r'dc\s*soket|dc\s*söket|dc\s*şarj|dc\s*hızlı|dc\s*combo|dc\s*chademo',
            r'\bdc\s*[<>=]',
            r'dc\s*istasyon|dc\s*cihaz',
            r'\bdc\b',
            r'direct\s*current|doğru\s*akım'
        ]
        for pattern in dc_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return 'DC'
        
        return None
    
    def extract_power(self, text: str) -> Optional[str]:
        """Extract power rating from text (e.g., 22kW, 50kW)"""
        if not text:
            return None
        
        # Look for kW patterns
        pattern = r'(\d+(?:[.,]\d+)?)\s*kW'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}kW"
        
        return None
    
    def format_price_data(self, price: float, description: str, charging_type: Optional[str] = None, power: Optional[str] = None) -> Dict:
        """Format price data in standard format"""
        # Clean description
        clean_desc = self.clean_text(description)
        # Limit description length and remove noise
        if len(clean_desc) > 150:
            clean_desc = clean_desc[:150] + "..."
        
        # Remove very short or meaningless descriptions
        if len(clean_desc) < 10:
            clean_desc = None
        
        return {
            'price': round(price, 2),
            'unit': 'kWh',
            'charging_type': charging_type,
            'power': power,
            'description': clean_desc,
            'source': self.domain
        }
    
    def find_price_keywords(self, soup: BeautifulSoup) -> List[Dict]:
        """Generic method to find prices using common keywords"""
        prices = []
        
        # Common Turkish keywords for pricing
        keywords = [
            'fiyat', 'tarife', 'ücret', 'ucret', 'price', 'pricing',
            'kwh', 'kw/h', 'kWh', 'kilowatt', 'kilovat'
        ]
        
        # Look for elements containing these keywords
        for keyword in keywords:
            elements = soup.find_all(
                text=re.compile(keyword, re.IGNORECASE)
            )
            
            for element in elements:
                parent = element.parent
                if parent:
                    text = parent.get_text()
                    price = self.extract_price_from_text(text)
                    if price:
                        charging_type = self.extract_charging_type(text)
                        power = self.extract_power(text)
                        prices.append(self.format_price_data(price, text, charging_type, power))
        
        return prices
    
    @abstractmethod
    def scrape(self) -> Dict:
        """
        Scrape pricing information from the website
        Returns a dictionary with company info and prices
        """
        pass
    
    def get_company_name(self) -> str:
        """Extract company name from domain"""
        domain = self.domain.replace('www.', '')
        return domain.split('.')[0].title()


