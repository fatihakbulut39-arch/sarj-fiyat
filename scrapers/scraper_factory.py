"""
Factory for creating appropriate scrapers for different websites
"""
import logging
from urllib.parse import urlparse
from scrapers.generic_scraper import GenericScraper
from scrapers.selenium_scraper import SeleniumScraper
from scrapers.requests_html_scraper import RequestsHtmlScraper

logger = logging.getLogger(__name__)


class ScraperFactory:
    """Factory to create appropriate scraper for each website"""
    
    # Domains that require Selenium (JavaScript-rendered pages)
    SELENIUM_DOMAINS = [
        'fast-go.com.tr',
        'greensarjistasyonlari.com',
        'ksarj.com',
        'meischarge.com',
        'mercurysarj.com.tr',
        'magiclinesarj.com',
        'onizsarj.com',
        'pgdenergy.com',
        'volti.com',
        'voltrun.com',
        'wattarya.com',
        'sarj.360enerji.com.tr',
        '360enerji.com.tr',
        'sarjmatik.com.tr',
        'd-rectcharge.com',
        'drectcharge.com',
        'tuvturk.com.tr',  # TÜVTürk - JavaScript rendered
        'ekosarj.com',  # Ekoşarj - JavaScript rendered
        'basergrup.com.tr',  # Basergrup - JavaScript rendered
        'sparkev.com.tr',  # Sparkev - JavaScript rendered
        'adzesarj.com',  # Adzeşarj - JavaScript rendered
        'aksasarj.com.tr',  # Aksaşarj - JavaScript rendered
        'astorsarj.com.tr',  # Astorşarj - JavaScript rendered
        'efish.com.tr',  # Efish - JavaScript rendered
        'elaris.com.tr',  # Elaris - JavaScript rendered
        'esarj.com',  # Eşarj - JavaScript rendered
        'greensarjistasyonlari.com',  # Green Şarj İstasyonları - JavaScript rendered
        'hizzlan.com',  # HIZZLAN - JavaScript rendered
        'krnenerji.com',  # KRN Enerji - JavaScript rendered
        'ksarj.com',  # K-Şarj - JavaScript rendered
        'lumicle.com.tr',  # Lumicle - JavaScript rendered
        'bolgem.com.tr',  # Bölgem - JavaScript rendered
        'd-rectcharge.com',  # D-Rect Charge - JavaScript rendered
        'incharge.com.tr',  # Incharge - JavaScript rendered
        'arconasarj.com',  # Arcona Şarj - JavaScript rendered
        'acropolsarj.com',  # Acropolşarj - JavaScript rendered
        'aktifsarj.com',  # Aktifşarj - JavaScript rendered
        'aostechnology.com.tr',  # Aostechnology - JavaScript rendered
        'arsimaenerji.com',  # Arsimaenerji - JavaScript rendered
        'autovoltenerji.com',  # Autovoltenerji - JavaScript rendered
        'b-charge.net',  # B-charge - JavaScript rendered
        'basergrup.com.tr',  # Basergrup - JavaScript rendered
        'beefull.com',  # Beefull - JavaScript rendered
        'bestsarj.com',  # Bestşarj - JavaScript rendered
        'bluenerjiturkiye.com.tr',  # Bluenerjiturkiye - JavaScript rendered
        'carbonage.net',  # Carbonage - JavaScript rendered
        'ctgelektrik.com',  # CTG Elektrik - JavaScript rendered
        'cv-charging.com',  # CV-Charging - JavaScript rendered
        'dcharge.com.tr',  # Dcharge - JavaScript rendered
        'e4sarj.com.tr',  # E4Şarj - JavaScript rendered
        'ecoboxsarj.com',  # Ecoboxşarj - JavaScript rendered
        'econ.net.tr',  # Econ - JavaScript rendered
        'ekosarj.com',  # Ekoşarj - JavaScript rendered (already added before)
        'electrise.com.tr',  # Electrise - JavaScript rendered
        'enerturk.com',  # Enerturk - JavaScript rendered
        'epsis.net',  # Epsis - JavaScript rendered
        'estasyon.com.tr',  # Estasyon - JavaScript rendered
        'evroad.com.tr',  # Evroad - JavaScript rendered
        'esarj.com',  # Eşarj - JavaScript rendered (already added before)
        'fast-go.com.tr',  # Fast-Go - JavaScript rendered
        # Problematic sites that fail to load prices - added for improved scraping
        'checkpointsarj.com.tr',  # Checkpoint - JavaScript rendered content
        'sharz.net',  # Sharz - Dinamik fiyat yükleme
        'e4sarj.com',  # E4Sarj - Dinamik (not e4sarj.com.tr)
        'evroad.com',  # Evroad - Dinamik (not evroad.com.tr)
        'antkemsarj.com',  # Antkem - Dinamik fiyat
        'ziraatiygg.com.tr',  # Ziraat Elektronik - Dinamik
        'g-charge.com.tr',  # G-Charge - Dinamik fiyat yükleme
        'sarjstart.com',  # Şarj Start - Dinamik fiyat layout
    ]
    
    # Map of domain patterns to specific scraper classes
    SCRAPER_MAP = {
        # Add specific scrapers here when needed
        # 'example.com': ExampleScraper,
    }
    
    @staticmethod
    def create_scraper(url: str):
        """Create appropriate scraper for the given URL"""
        domain = urlparse(url).netloc.replace('www.', '')
        
        # Check if domain requires JavaScript rendering
        for js_domain in ScraperFactory.SELENIUM_DOMAINS:
            if js_domain in domain:
                # Use Selenium (more reliable for JS rendering)
                logger.info(f"Using Selenium scraper for {domain} (JavaScript-rendered)")
                return SeleniumScraper(url, wait_time=20)  # Wait 20 seconds for content to load
        
        # Check if we have a specific scraper for this domain
        for pattern, scraper_class in ScraperFactory.SCRAPER_MAP.items():
            if pattern in domain:
                logger.info(f"Using specific scraper for {domain}")
                return scraper_class(url)
        
        # Default to generic scraper
        logger.info(f"Using generic scraper for {domain}")
        return GenericScraper(url)

