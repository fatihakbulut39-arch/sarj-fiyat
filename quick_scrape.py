"""
Quick scraper using requests and BeautifulSoup for fast scraping
Selenium fallback for JavaScript-heavy sites
"""
import json
import logging
from pathlib import Path
import re
import time
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Try to import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class QuickScraper:
    """Fast scraper for charging station prices"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        self.timeout = 15  # Increased slightly
        
        # JavaScript-heavy sites that need Selenium
        self.js_sites = {
            "https://www.ecoboxsarj.com/tarifeler": "ecobox",
            "https://evroad.com.tr/#": "evroad",
            "https://magiclinesarj.com": "magicline",
            "https://minusenergy.net/sarj-noktalari/#fiyat_ref3": "minus",
            "https://5sarj.com/tr/fiyatlandirma": "5sarj",
            "https://greendrive.com.tr/tarifeler": "greendrive",
            "https://tripy.mobi/charge/fiyatlandirma/": "tripy",
            "https://karkinenerji.com.tr/guncel-sarj-fiyatlari/": "karkin"
        }
        
        # Force prices - hardcoded for sites that are hard to scrape
        self.force_prices = {
            # "https://carbonage.net": {"ac": [4.50], "dc": [6.50]}, # Removed stale
        }
        
        # Fallback prices - used when scraping fails
        self.fallback_prices = {
            "https://www.bolgem.com.tr/fiyat-tarifesi/": {"ac": [5.99], "dc": [7.99]},
            "https://carbonage.net": {"ac": [4.50], "dc": [6.50]},
            "https://www.electrise.com.tr": {"ac": [5.50], "dc": [8.00]},
            "https://www.ecoboxsarj.com/tarifeler": {"ac": [8.99], "dc": [11.99]},
            "https://evroad.com.tr/#": {"ac": [8.49], "dc": [10.99]},
            "https://magiclinesarj.com": {"ac": [8.50], "dc": [11.00]},
            "https://minusenergy.net/sarj-noktalari/#fiyat_ref3": {"ac": [9.00], "dc": [12.00]},
            "https://greendrive.com.tr/tarifeler": {"ac": [7.99], "dc": [10.99]},
            "https://tripy.mobi/charge/fiyatlandirma/": {"ac": [8.29], "dc": [10.29]},
            "https://karkinenerji.com.tr/guncel-sarj-fiyatlari/": {"ac": [8.49], "dc": [10.99]},
        }

        self._hydrate_fallbacks_from_latest_data()
        
        self.driver = None

    def _hydrate_fallbacks_from_latest_data(self) -> None:
        """Populate fallback prices from the most recent standard dataset."""
        standard_path = Path("data/charging_prices_standard.json")

        if not standard_path.exists():
            return

        try:
            with standard_path.open("r", encoding="utf-8") as file:
                entries = json.load(file)
        except Exception as exc:
            logger.debug("Fallback hydration skipped: %s", exc)
            return

        if not isinstance(entries, list):
            return

        for entry in entries:
            url = entry.get("webSitesi")
            if not isinstance(url, str) or not url.strip() or url in self.fallback_prices:
                continue

            ac_price = entry.get("acFiyat")
            dc_price = entry.get("dcFiyat")

            hydrated = {"ac": [], "dc": []}
            if ac_price is not None:
                try:
                    p = float(ac_price)
                    if 4.0 <= p <= 35.0:
                        hydrated["ac"] = [p]
                except:
                    pass
            
            if dc_price is not None:
                try:
                    p = float(dc_price)
                    if 4.0 <= p <= 35.0:
                        hydrated["dc"] = [p]
                except:
                    pass

            if hydrated["ac"] or hydrated["dc"]:
                self.fallback_prices[url] = hydrated
    
    def scrape_all(self) -> Dict:
        """Scrape all URLs from config"""
        import config
        
        results = {}
        
        for idx, url in enumerate(config.CHARGING_STATION_URLS, 1):
            logger.info(f"[{idx}/{len(config.CHARGING_STATION_URLS)}] Scraping: {url}")
            
            result = self.scrape_url(url)
            results[url] = result
            
            # Rate limiting
            time.sleep(0.5)
        
        return results
    
    def scrape_url(self, url: str) -> Dict:
        """Scrape a single URL for prices"""
        try:
            # Check if URL has hardcoded force prices
            if url in self.force_prices:
                logger.info(f"Using force prices for {url}")
                return self.force_prices[url].copy()
            
            # Check if this is a JavaScript-heavy site
            if url in self.js_sites:
                logger.info(f"Using Selenium for JS-heavy site: {url}")
                return self.scrape_with_selenium(url)
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract AC and DC prices
            ac_prices = self._extract_prices(soup, 'ac')
            dc_prices = self._extract_prices(soup, 'dc')
            
            if ac_prices or dc_prices:
                logger.info(f"Found AC: {ac_prices}, DC: {dc_prices}")
                return {
                    'ac': ac_prices,
                    'dc': dc_prices,
                    'status': 'success'
                }
            else:
                # Use fallback if available
                if url in self.fallback_prices:
                    logger.warning(f"No prices found, using fallback for {url}")
                    return self.fallback_prices[url].copy()
                
                logger.warning(f"No prices found for {url}")
                return {'ac': [], 'dc': [], 'status': 'no_prices'}
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            
            # Use fallback if available
            if url in self.fallback_prices:
                logger.info(f"Using fallback prices for {url} due to error")
                return self.fallback_prices[url].copy()
            
            return {'ac': [], 'dc': [], 'status': 'error', 'error': str(e)}
    
    def scrape_with_selenium(self, url: str) -> Dict:
        """Scrape JavaScript-rendered pages using Selenium"""
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available, using fallback")
            if url in self.fallback_prices:
                return self.fallback_prices[url].copy()
            return {'ac': [], 'dc': [], 'status': 'no_selenium'}
        
        driver = None
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
            
            # Create driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Load page and wait for content
            driver.get(url)
            time.sleep(4)  # Increased wait time
            
            # Try multiple wait strategies
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "body"))
                )
            except:
                pass
            
            # Get rendered HTML
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract prices
            ac_prices = self._extract_prices(soup, 'ac')
            dc_prices = self._extract_prices(soup, 'dc')
            
            if ac_prices or dc_prices:
                logger.info(f"✅ Selenium: Found AC: {ac_prices}, DC: {dc_prices}")
                return {
                    'ac': ac_prices,
                    'dc': dc_prices,
                    'status': 'selenium_success'
                }
            else:
                logger.warning(f"No prices found with Selenium, using fallback for {url}")
                if url in self.fallback_prices:
                    return self.fallback_prices[url].copy()
                return {'ac': [], 'dc': [], 'status': 'selenium_no_prices'}
        
        except Exception as e:
            logger.error(f"Selenium error for {url}: {e}, using fallback")
            if url in self.fallback_prices:
                return self.fallback_prices[url].copy()
            return {'ac': [], 'dc': [], 'status': 'selenium_error', 'error': str(e)}
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _extract_prices(self, soup: BeautifulSoup, price_type: str) -> List[float]:
        """Extract prices from HTML using common patterns"""
        prices = []
        
        # Look for price patterns in the page
        # Prioritize visible text
        text = soup.get_text(" ", strip=True)
        
        # More robust regex: looking for currency symbols or keywords nearby
        # Matches: "5.50", "5,50", "₺5.50", "5.50 TL", etc.
        # But we filter by reasonable EV charging price range
        price_pattern = r'(?:₺|TL)?\s*(\d+[.,]\d{1,2})\s*(?:₺|TL)?'
        matches = re.finditer(price_pattern, text, re.IGNORECASE)
        
        for match in matches:
            price_str = match.group(1).replace(',', '.')
            
            # Check for date context (e.g. 18.10.2025 matches 18.10)
            start, end = match.span(1)
            # Look ahead for more digits/dots
            next_chars = text[end:end+5]
            if re.match(r'[\./-]\d{2,4}', next_chars):
                continue
                
            try:
                price = float(price_str)
                # Reasonable price range for EV charging in Turkey
                # Filter out small numbers like 1.0, 2.0 (likely fees/steps)
                # Keep legitimate prices (lowest known ~4.5, highest ~30)
                if 4.0 <= price <= 35.0:
                    prices.append(price)
            except ValueError:
                continue
        
        # Specialized logic can be added here for specific challenging sites if needed
        # e.g. finding elements by specific class names if general regex fails
        
        # Remove duplicates and sort
        prices = sorted(list(set(prices)))
        
        return prices
    
    def scrape_with_selenium_advanced(self, url: str) -> Dict:
        """Advanced Selenium scraping with multiple wait strategies"""
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available")
            return {'ac': [], 'dc': [], 'status': 'no_selenium'}
        
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.get(url)
            
            # Wait longer and try multiple selectors
            wait_time = 5
            selectors_to_try = [
                (By.CSS_SELECTOR, "[class*='price']"),
                (By.CSS_SELECTOR, "[class*='tarif']"),
                (By.CSS_SELECTOR, "[class*='fiyat']"),
                (By.XPATH, "//*[contains(text(), '₺')]"),
                (By.XPATH, "//*[contains(text(), 'TRY')]"),
            ]
            
            for selector_type, selector in selectors_to_try:
                try:
                    WebDriverWait(driver, wait_time).until(
                        EC.presence_of_all_elements_located((selector_type, selector))
                    )
                    logger.info(f"Found elements with selector: {selector}")
                    break
                except:
                    continue
            
            time.sleep(2)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            ac_prices = self._extract_prices(soup, 'ac')
            dc_prices = self._extract_prices(soup, 'dc')
            
            if ac_prices or dc_prices:
                logger.info(f"✅ Advanced Selenium: Found AC: {ac_prices}, DC: {dc_prices}")
                return {
                    'ac': ac_prices,
                    'dc': dc_prices,
                    'status': 'advanced_selenium'
                }
            else:
                logger.warning(f"No prices found with advanced Selenium for {url}")
                return {'ac': [], 'dc': [], 'status': 'no_prices_advanced'}
        
        except Exception as e:
            logger.error(f"Advanced Selenium error for {url}: {e}")
            return {'ac': [], 'dc': [], 'status': 'advanced_error'}
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
