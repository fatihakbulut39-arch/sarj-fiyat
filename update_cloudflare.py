#!/usr/bin/env python3
"""
Cloudflare Worker'a veri güncellemesi yapan script
GitHub Actions'ta 3 günde bir çalışacak
"""
import json
import subprocess
from datetime import datetime, timezone, timedelta
import requests
import logging
import sys
import os

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('update_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Config
WORKER_URL = os.getenv('WORKER_URL', 'https://your-api.workers.dev')
API_KEY = os.getenv('CF_API_KEY', 'your-secret-key')
DATA_FILE = 'data/charging_prices_standard.json'

def run_scraper():
    """Scraper'ı çalıştır ve veri topla"""
    logger.info("📊 Scraper başlatılıyor...")
    
    result = subprocess.run(
        ['python3', 'scraper_runner.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Scraper hatası: {result.stderr}")
        return False
    
    logger.info("✅ Scraper tamamlandı")
    return True

def load_prices():
    """JSON'dan fiyatları yükle"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            prices = json.load(f)
        
        if not isinstance(prices, list):
            logger.error("❌ Veri formatı hatalı: Liste değil")
            return None
            
        if len(prices) < 10:
            logger.warning(f"⚠️ Çok az veri var ({len(prices)} firma). Gönderim iptal edilebilir.")
            # İsterseniz burada return None yapıp göndermeyi engelleyebilirsiniz
            
        logger.info(f"📁 {len(prices)} firma yüklendi")
        return prices
    except Exception as e:
        logger.error(f"Dosya okuma hatası: {e}")
        return None

def send_to_cloudflare(prices):
    """Cloudflare Worker'a veri gönder"""
    if not prices:
        logger.error("Gönderilecek veri yok!")
        return False
    
    try:
        logger.info(f"🚀 Cloudflare'e gönderiliyor ({len(prices)} firma)...")
        
        response = requests.post(
            f"{WORKER_URL}/api/update",
            json=prices,
            headers={
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Başarılı! {result.get('message', 'Veri kaydedildi')}")
            return True
        else:
            logger.error(f"❌ Hata {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Gönderme hatası: {e}")
        return False

def health_check():
    """API health check"""
    try:
        response = requests.get(
            f"{WORKER_URL}/api/health",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API sağlıklı - {data.get('dataCount', 0)} firma")
            return True
        else:
            logger.error(f"API hatası: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Health check hatası: {e}")
        return False

def main():
    """Ana işlem"""
    logger.info("=" * 60)
    logger.info("🔄 Şarj Fiyatları Güncelleme Başladı")
    logger.info("=" * 60)
    
    # 1. Scraper çalıştır
    if not run_scraper():
        logger.error("Scraper başarısız oldu!")
        sys.exit(1)
    
    # 2. Veriyi yükle
    prices = load_prices()
    if not prices:
        logger.error("Veri yüklenemedi!")
        sys.exit(1)
    
    # 3. Cloudflare'e gönder
    if not send_to_cloudflare(prices):
        logger.error("Cloudflare'e gönderim başarısız!")
        sys.exit(1)
    
    # 4. Health check
    if health_check():
        logger.info("✅ Sistem tamamen çalışıyor!")
        logger.info("=" * 60)
    else:
        logger.warning("⚠️ Health check başarısız oldu")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
