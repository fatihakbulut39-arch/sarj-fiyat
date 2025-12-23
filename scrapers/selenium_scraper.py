"""
Selenium-based scraper for JavaScript-rendered pages
"""
import logging
import time
from typing import Dict, Optional
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class SeleniumScraper(BaseScraper):
    """Scraper using Selenium for JavaScript-rendered pages"""
    
    def __init__(self, url: str, wait_time: int = 10):
        super().__init__(url)
        self.wait_time = wait_time
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome driver with options"""
        if self.driver:
            return self.driver
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--ignore-certificate-errors')  # SSL sertifika hatalarını ignore et
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--ignore-certificate-errors-spki-list')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # Use Selenium's built-in driver manager (Selenium 4.6+)
            # This automatically downloads and manages ChromeDriver
            logger.info("Setting up Chrome driver with Selenium Manager...")
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver setup successful")
            return self.driver
        except Exception as e:
            logger.error(f"Error setting up Chrome driver: {e}")
            # Try with explicit service
            try:
                logger.info("Trying with ChromeDriverManager...")
                driver_path = ChromeDriverManager().install()
                import os
                # Fix path if it points to a directory
                if os.path.isdir(driver_path):
                    possible_paths = [
                        os.path.join(driver_path, 'chromedriver'),
                        os.path.join(driver_path, 'chromedriver-mac-arm64', 'chromedriver'),
                        os.path.join(driver_path, 'chromedriver-mac-x64', 'chromedriver'),
                    ]
                    for path in possible_paths:
                        if os.path.isfile(path) and os.access(path, os.X_OK):
                            driver_path = path
                            break
                
                if driver_path and os.path.isfile(driver_path):
                    service = Service(driver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("Chrome driver setup successful with ChromeDriverManager")
                    return self.driver
            except Exception as e2:
                logger.error(f"ChromeDriverManager also failed: {e2}")
            
            logger.error("Selenium scraper requires Chrome browser")
            logger.error("Please ensure Chrome is installed and up to date")
            return None
    
    def fetch_page_selenium(self, url: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Fetch page using Selenium and wait for content to load"""
        target_url = url or self.url
        
        try:
            driver = self.setup_driver()
            if not driver:
                return None
            
            logger.info(f"Loading page with Selenium: {target_url}")
            driver.get(target_url)
            
            # Wait for page to load
            time.sleep(self.wait_time)
            
            # Try to wait for common price-related elements
            try:
                # Wait for body to be present
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Additional wait for dynamic content
                time.sleep(5)  # Increased wait time
                
                # Scroll to load lazy content (multiple scrolls for card-based layouts)
                for i in range(3):  # Scroll multiple times
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(2)
                    # Scroll to middle
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                    time.sleep(2)
                
                # Wait for price-related elements (cards, divs with prices)
                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(), '₺') or contains(text(), 'TL') or contains(text(), 'kWh')]")) > 0
                    )
                except:
                    pass  # Continue even if not found
                
                time.sleep(3)  # Final wait
                
                # Try to find price-related elements
                price_keywords = ['fiyat', 'tarife', 'price', 'ücret', 'ucret', 'kwh', 'kw', '₺']
                found = False
                for keyword in price_keywords:
                    try:
                        elements = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                        if elements:
                            found = True
                            break
                    except:
                        continue
                
                if found:
                    # Wait a bit more for prices to render
                    time.sleep(3)
                
            except Exception as e:
                logger.warning(f"Timeout waiting for elements: {e}")
            
            # Get page source
            page_source = driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            logger.error(f"Error fetching page with Selenium: {str(e)}")
            return None
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
    
    def scrape(self) -> Dict:
        """Scrape using Selenium"""
        soup = self.fetch_page_selenium()
        if not soup:
            return {
                'company': self.get_company_name(),
                'url': self.url,
                'status': 'error',
                'error': 'Could not fetch page with Selenium',
                'prices': []
            }
        
        # Use parent class methods to extract prices
        prices = []
        
        # Method 1: Look for pricing tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            table_text = table.get_text()
            
            # Check if this is a pricing table with column structure (AC/DC columns)
            is_column_table = any(kw in table_text.lower() for kw in ['şarj fiyatı', 'soket tipi', 'ac tip', 'dc ccs'])
            
            if is_column_table:
                # Find header row with AC/DC information
                header_row_idx = None
                header_cells = []
                for i, row in enumerate(rows):
                    cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                    row_text_lower = ' '.join(cells).lower()
                    # Check if this row contains AC/DC or socket type info
                    if any(kw in row_text_lower for kw in ['ac tip', 'dc ccs', 'soket tipi']):
                        header_row_idx = i
                        header_cells = cells
                        break
                
                if header_row_idx is not None and len(header_cells) > 1:
                    # Determine which column is AC and which is DC
                    ac_cols = []
                    dc_cols = []
                    for j, cell_text in enumerate(header_cells):
                        cell_lower = cell_text.lower()
                        if 'ac' in cell_lower and ('tip' in cell_lower or 'tip-2' in cell_lower):
                            ac_cols.append(j)
                        elif 'dc' in cell_lower or 'ccs' in cell_lower:
                            dc_cols.append(j)
                    
                    # Now parse data rows (rows after header)
                    for data_row in rows[header_row_idx + 1:]:
                        data_cells = [cell.get_text().strip() for cell in data_row.find_all(['td', 'th'])]
                        # Extract prices from each column
                        for col_idx, cell_text in enumerate(data_cells):
                            price = self.extract_price_from_text(cell_text)
                            if price and 0.5 <= price <= 50:
                                # Determine type based on column
                                charging_type = None
                                if col_idx in ac_cols:
                                    charging_type = 'AC'
                                elif col_idx in dc_cols:
                                    charging_type = 'DC'
                                
                                # If type not found from column, try to extract from cell text
                                if not charging_type:
                                    charging_type = self.extract_charging_type(cell_text)
                                
                                power = self.extract_power(cell_text)
                                prices.append(self.format_price_data(price, cell_text, charging_type, power))
            
            # Fallback: original method for tables without clear header structure
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # Table format: description in first cell, price in second cell
                    desc_cell = cells[0].get_text()
                    price_cell = cells[1].get_text()
                    
                    # Extract price from price cell
                    price = self.extract_price_from_text(price_cell)
                    if price:
                        # Extract type and power from description cell
                        charging_type = self.extract_charging_type(desc_cell)
                        power = self.extract_power(desc_cell)
                        prices.append(self.format_price_data(price, desc_cell + ' ' + price_cell, charging_type, power))
                
                # Also try full row text (for tables with different formats)
                row_text = ' '.join([cell.get_text() for cell in cells])
                if any(kw in row_text.lower() for kw in ['fiyat', 'tarife', 'ücret', 'ucret', 'price', 'kwh', 'kw']):
                    price = self.extract_price_from_text(row_text)
                    if price:
                        charging_type = self.extract_charging_type(row_text)
                        power = self.extract_power(row_text)
                        prices.append(self.format_price_data(price, row_text, charging_type, power))
        
        # Method 2: Look for price sections (including "hizmet", "fiyatlandırma")
        # First try by class
        price_sections = soup.find_all(
            ['div', 'section', 'article'],
            class_=lambda x: x and any(
                keyword in ' '.join(x).lower() 
                for keyword in ['price', 'fiyat', 'tarife', 'pricing', 'plan', 'paket', 'hizmet', 'fiyatlandırma', 'fiyatlandirma']
            )
        )
        
        # Also check divs/sections that contain "fiyat" or "tarife" in their text
        all_sections = soup.find_all(['div', 'section', 'article'])
        for section in all_sections:
            text = section.get_text()
            if any(kw in text.lower() for kw in ['fiyat tarifeleri', 'fiyat tarife', 'tarife', 'fiyatlandırma']):
                if section not in price_sections:
                    price_sections.append(section)
        
        for section in price_sections:
            text = section.get_text()
            # Extract all prices from this section (not just the first one)
            # Find all prices with TL/₺ - use finditer to get positions
            price_pattern = r'(\d+[.,]\d{1,2})\s*(?:TL|₺|TRY)\s*/?\s*(?:kWh|kW|kw|dk|min)?'
            whole_pattern = r'(\d+)\s*(?:TL|₺|TRY)\s*/?\s*(?:kWh|kW|kw|dk|min)?'
            
            for match in re.finditer(price_pattern, text, re.IGNORECASE):
                price_str = match.group(1)
                match_start = match.start()
                match_end = match.end()
                
                try:
                    # Skip if it's per minute (dk/min) - we only want per kWh
                    context_after = text[match_end:match_end+30].lower()
                    if 'dk' in context_after or 'min' in context_after:
                        continue  # Skip per-minute prices
                    
                    # Get context around the price (200 chars before to catch "11 - 22 kW AC" patterns, 50 after)
                    context = text[max(0, match_start-200):match_end+50]
                    
                    # Handle Turkish number format
                    if ',' in price_str and '.' not in price_str:
                        price_val = float(price_str.replace(',', '.'))
                    elif ',' in price_str and '.' in price_str:
                        if price_str.rindex(',') > price_str.rindex('.'):
                            price_val = float(price_str.replace('.', '').replace(',', '.'))
                        else:
                            price_val = float(price_str.replace(',', ''))
                    else:
                        price_val = float(price_str)
                    
                    if 0.5 <= price_val <= 50:
                        # Extract charging type and power from context (not entire section)
                        # Pass price position in original text for better context
                        charging_type = self.extract_charging_type(context, match_start - max(0, match_start-200))
                        power = self.extract_power(context)
                        prices.append(self.format_price_data(price_val, context, charging_type, power))
                except ValueError:
                    continue
            
            # Also check whole numbers
            for match in re.finditer(whole_pattern, text, re.IGNORECASE):
                price_str = match.group(1)
                match_start = match.start()
                match_end = match.end()
                
                try:
                    # Skip if it's per minute
                    context_after = text[match_end:match_end+30].lower()
                    if 'dk' in context_after or 'min' in context_after:
                        continue
                    
                    # Get context around the price (200 chars before to catch "11 - 22 kW AC" patterns)
                    context = text[max(0, match_start-200):match_end+50]
                    
                    price_val = float(price_str)
                    
                    if 0.5 <= price_val <= 50:
                        charging_type = self.extract_charging_type(context)
                        power = self.extract_power(context)
                        prices.append(self.format_price_data(price_val, context, charging_type, power))
                except ValueError:
                    continue
        
        # Method 3: Look for price keywords
        keyword_prices = self.find_price_keywords(soup)
        prices.extend(keyword_prices)
        
        # Method 4: Look for list items
        lists = soup.find_all(['ul', 'ol', 'dl'])
        for list_elem in lists:
            items = list_elem.find_all('li', recursive=False)
            for item in items:
                text = item.get_text()
                if any(kw in text.lower() for kw in ['fiyat', 'tarife', 'ücret', 'kwh', 'kw', 'ac', 'dc']):
                    price = self.extract_price_from_text(text)
                    if price:
                        charging_type = self.extract_charging_type(text)
                        power = self.extract_power(text)
                        prices.append(self.format_price_data(price, text, charging_type, power))
        
        # Method 5: Look for divs/spans with AC/DC and prices together
        # This helps find prices like "AC 22 kWh 8.2 TL/kWh" or "AC 6 TL/kWh"
        # IMPORTANT: Only extract prices that are followed by TL/₺ to avoid extracting power ratings
        all_divs = soup.find_all(['div', 'span', 'p', 'h2', 'h3', 'h4'])
        for elem in all_divs:
            text = elem.get_text()
            # Check if contains both AC/DC and a price
            if (('ac' in text.lower() or 'dc' in text.lower()) and 
                any(kw in text.lower() for kw in ['kwh', 'kw', 'tl', '₺', 'fiyat', 'socket'])):
                # Use extract_price_from_text which now handles whole numbers too
                price = self.extract_price_from_text(text)
                if price:
                    # Extract charging type from text - prioritize AC/DC keywords before price
                    # For patterns like "AC Socket 9,49 ₺" or "DC Socket 10,00 ₺"
                    charging_type = self.extract_charging_type(text)
                    power = self.extract_power(text)
                    
                    # For Elaris pattern: "AC Socket 9,49 ₺ AC-22 Tarifesi Halka açık"
                    # Expand context to include parent and siblings for better description
                    expanded_text = text
                    parent = elem.parent
                    if parent:
                        parent_text = parent.get_text()
                        # If parent contains "halka açık" or "AC-22", add it to description
                        if ('halka açık' in parent_text.lower() or 'ac-22' in parent_text.lower() or 'dc tarifesi' in parent_text.lower()) and len(parent_text) < 500:
                            expanded_text = text + ' ' + parent_text[:300]  # Add parent context
                    
                    prices.append(self.format_price_data(price, expanded_text, charging_type, power))
                
                # Also try to extract prices that are explicitly followed by TL/₺
                # This prevents extracting "3 kW" as price 3.0
                # Pattern: number followed by TL/₺ (with optional /kWh)
                # Use finditer to get position for better context extraction
                price_with_currency = re.finditer(r'(\d+[.,]\d{1,2})\s*(?:TL|₺|TRY)\s*/?\s*(?:kWh|kW|kw|KWh)?', text, re.IGNORECASE)
                # Also whole numbers with currency
                whole_with_currency = re.finditer(r'(\d+)\s*(?:TL|₺|TRY)\s*/?\s*(?:kWh|kW|kw|KWh)?', text, re.IGNORECASE)
                
                for match in list(price_with_currency) + list(whole_with_currency):
                    try:
                        price_str = match.group(1)
                        match_start = match.start()
                        match_end = match.end()
                        
                        # Get context before the price (50 chars) to find AC/DC type
                        context_before = text[max(0, match_start-50):match_start].lower()
                        
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
                            # Extract charging type from context before price (more accurate)
                            # For patterns like "AC Soketli ... 7.90 ₺/kWh"
                            charging_type = self.extract_charging_type(context_before)
                            if not charging_type:
                                # Fallback to full text
                                charging_type = self.extract_charging_type(text)
                            power = self.extract_power(text)
                            prices.append(self.format_price_data(price_val, text, charging_type, power))
                    except ValueError:
                        continue
        
        # Remove duplicates and filter invalid prices
        seen = set()
        unique_prices = []
        
        for price_info in prices:
            price_val = price_info.get('price', 0)
            desc = price_info.get('description', '') or ''
            
            # Skip per-minute prices (dk/min)
            if 'dk' in desc.lower() or 'min' in desc.lower():
                continue
            
            # Skip very low prices that are likely not charging prices
            # But allow prices >= 3.0 (was < 3.0)
            if price_val < 3.0:
                continue
            
            desc_key = desc[:100] if desc else ''  # Longer key for better uniqueness
            charging_type = price_info.get('charging_type')
            power = price_info.get('power')
            
            # Create unique key: price + charging_type + power (to distinguish same price for different power levels)
            price_key = round(price_val, 2)
            unique_key = (price_key, charging_type, power)
            
            if unique_key not in seen and price_info.get('description'):
                seen.add(unique_key)
                unique_prices.append(price_info)
        
        unique_prices.sort(key=lambda x: x.get('price', 0))
        unique_prices = unique_prices[:20]  # Increased limit
        
        return {
            'company': self.get_company_name(),
            'url': self.url,
            'status': 'success' if unique_prices else 'no_prices_found',
            'prices': unique_prices
        }

