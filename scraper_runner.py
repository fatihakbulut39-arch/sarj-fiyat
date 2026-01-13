"""
Main scraper runner that processes all websites
Basitleştirilmiş quick_scrape tabanlı sistem
"""
import time
import logging
import json
from typing import List, Dict
import config
from data_converter import DataConverter
from data_manager import DataManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# quick_scrape.py'den import (eğer aynı dizinde varsa)
try:
    from quick_scrape import QuickScraper
except ImportError:
    QuickScraper = None



class ScraperRunner:
    """Çalışan scraper - quick_scrape ile basitleştirildi"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.converter = DataConverter()
        self.urls = config.CHARGING_STATION_URLS
        self.scraper = QuickScraper() if QuickScraper else None
    
    def scrape_all(self, delay: float = None) -> Dict:
        """quick_scrape ile tüm siteleri scrape et"""
        results = {
            'total': len(self.urls),
            'success': 0,
            'failed': 0,
            'no_prices': 0,
            'companies': []
        }
        
        if not self.scraper:
            logger.error("QuickScraper yüklenemedi!")
            return results
        
        logger.info(f"Başlanıyor: {len(self.urls)} website")
        
        # Tümünü scrape et
        scrape_results = self.scraper.scrape_all()
        
        # Sonuçları işle
        for url, result in scrape_results.items():
            ac_prices = result.get('ac', [])
            dc_prices = result.get('dc', [])
            
            if ac_prices or dc_prices:
                results['success'] += 1
                company_name = url.split('/')[2].replace('www.', '').title()
                results['companies'].append({
                    'company': company_name,
                    'url': url,
                    'status': 'success',
                    'prices': {
                        'ac': ac_prices,
                        'dc': dc_prices
                    }
                })
            else:
                results['no_prices'] += 1
        
        # scrape_results.json'ı kaydet
        with open('scrape_results.json', 'w') as f:
            json.dump(scrape_results, f, indent=2)
        
        # Yeni JSON'u oluştur
        self._process_and_save_results(scrape_results)
        
        logger.info(f"Tamamlandı: {results['success']} başarılı, "
                   f"{results['no_prices']} fiyat yok")
        
        return results
    
    def _process_and_save_results(self, scrape_results: Dict):
        """scrape_results'u standard JSON'a dönüştür ve duplikatleri sil"""
        from urllib.parse import urlparse
        
        try:
            with open('data/charging_prices_standard.json', 'r') as f:
                existing = json.load(f)
                existing_map = {c['webSitesi']: c for c in existing}
        except:
            existing_map = {}
        
        new_data = []
        
        for url, result in scrape_results.items():
            ac_prices = result.get('ac', [])
            dc_prices = result.get('dc', [])
            
            if not ac_prices and not dc_prices:
                if url in existing_map:
                    new_data.append(existing_map[url])
                continue
            
            company_name = url.split('/')[2].replace('www.', '').title()
            
            # Eğer force mode'da ama fiyat boşsa, fallback'ten al
            from quick_scrape import QuickScraper
            scraper = QuickScraper()
            if url in scraper.force_prices and url in scraper.fallback_prices:
                fallback = scraper.fallback_prices[url]
                if not ac_prices:
                    ac_prices = fallback.get('ac', [])
                if not dc_prices:
                    dc_prices = fallback.get('dc', [])
            
            # Load logo URL from map
            logo_url = None
            try:
                 with open('data/logo_map.json', 'r') as f:
                     logo_map = json.load(f)
                 logo_url = logo_map.get(url)
            except:
                 pass

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
            
            new_data.append(entry)
        
        # Scrape edilmeyenleri ekle
        for url, company in existing_map.items():
            if url not in scrape_results:
                new_data.append(company)
        
        # Domain'e göre deduplicate (aynı site'in farklı URL'leri)
        def normalize_domain(url):
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '').lower()
        
        seen_domains = {}
        final_data = []
        
        for entry in new_data:
            domain = normalize_domain(entry['webSitesi'])
            
            if domain not in seen_domains:
                seen_domains[domain] = entry
                final_data.append(entry)
            else:
                # Domain zaten var - daha iyi verisi varsa değiştir
                existing_entry = seen_domains[domain]
                if entry.get('acFiyat') or entry.get('dcFiyat'):
                    if not (existing_entry.get('acFiyat') or existing_entry.get('dcFiyat')):
                        seen_domains[domain] = entry
                        final_data[final_data.index(existing_entry)] = entry
        
        # Kaydet
        with open('data/charging_prices_standard.json', 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ {len(final_data)} firma kaydedildi (duplicates temizlendi)")


if __name__ == "__main__":
    runner = ScraperRunner()
    results = runner.scrape_all()
    print(f"\n📊 Sonuçlar:")
    print(f"Toplam: {results['total']}")
    print(f"Başarılı: {results['success']}")
    print(f"Fiyat Yok: {results['no_prices']}")
