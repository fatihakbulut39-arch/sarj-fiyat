"""
Data converter for converting between different price formats
"""
import logging

logger = logging.getLogger(__name__)


class DataConverter:
    """Converts charging price data between formats"""
    
    def __init__(self):
        pass
    
    def convert_to_standard(self, raw_data):
        """Convert raw scraped data to standard format"""
        standard_data = []
        
        if isinstance(raw_data, dict):
            for url, prices in raw_data.items():
                entry = self._create_standard_entry(url, prices)
                if entry:
                    standard_data.append(entry)
        elif isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict):
                    url = item.get('url')
                    prices = item.get('prices', {})
                    entry = self._create_standard_entry(url, prices)
                    if entry:
                        standard_data.append(entry)
        
        return standard_data
    
    def _create_standard_entry(self, url, prices):
        """Create a standard entry from URL and prices"""
        if not url:
            return None
        
        ac_prices = prices.get('ac', []) if isinstance(prices, dict) else []
        dc_prices = prices.get('dc', []) if isinstance(prices, dict) else []
        
        company_name = url.split('/')[2].replace('www.', '').title()
        
        # Logo URL logic placeholder
        logo_url = None

        entry = {
            "firma": company_name,
            "ulke": "TR",
            "webSitesi": url,
            "acCurrency": "TRY",
            "dcCurrency": "TRY",
            "logoUrl": logo_url,
            "acFiyat": min(ac_prices) if ac_prices else None,
            "dcFiyat": max(dc_prices) if dc_prices else None
        }
        
        return entry
    
    def deduplicate_by_domain(self, data):
        """Remove duplicates based on domain"""
        from urllib.parse import urlparse
        
        seen_domains = {}
        deduped = []
        
        for entry in data:
            url = entry.get('webSitesi', '')
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '').lower()
            
            if domain not in seen_domains:
                seen_domains[domain] = entry
                deduped.append(entry)
        
        logger.info(f"Deduplicated {len(data)} entries to {len(deduped)}")
        return deduped
