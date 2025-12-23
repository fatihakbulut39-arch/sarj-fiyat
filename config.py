"""
Configuration file for the charging price scraper
"""
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data directory
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# JSON file path
PRICES_JSON = os.path.join(DATA_DIR, "charging_prices.json")

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# Scraping settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 1  # seconds

# List of charging station websites - ONLY SUCCESSFUL SCRAPERS
# Force mode kaldırıldı, sadece başarılı 66 site kalıyor (100% otomatik)
CHARGING_STATION_URLS = [
    # Force mode'da olan 32 site (guaranteed accurate)
    "https://www.bolgem.com.tr/fiyat-tarifesi/",
    "https://carbonage.net",
    "https://d-rectcharge.com/en/fiyatlar/",
    "https://www.ecoboxsarj.com/tarifeler",
    "https://www.electrise.com.tr",
    "https://www.epsis.net/elektrikli-arac-sarj-tarifeleri/",
    "https://www.estasyon.com.tr/sarj-istasyonu-fiyatlari",
    "https://www.ev-bee.com/sabit-sarj-istasyonlari-fiyat-listesi",
    "https://evroad.com.tr/#",
    "https://fast-go.com.tr/fiyatlandirma/",
    "https://gioev.com/fiyatlandirma",
    "https://greensarjistasyonlari.com/cozumler/",
    "https://www.greenwatt.com.tr/tarifelerimiz.html",
    "https://www.isarj.com/tarifeler/",
    "https://incharge.com.tr/tr/index.html",
    "https://magiclinesarj.com",
    "https://meischarge.com/fiyatlar/",
    "https://mercurysarj.com.tr/fiyatlandirma/",
    "https://minusenergy.net/sarj-noktalari/#fiyat_ref3",
    "https://porty.tech/tr/porty-nedir/elektrikli-arac-sarj-istasyonu",
    "https://solarsarj.org/fiyatlar/",
    "https://tuncmatikcharge.com/fiyatlar/",
    "https://usarj.com.tr/fiyat-tarifesi",
    "https://volti.com/elektrikli-arac-sarj-fiyatlari/",
    "https://www.voltrun.com/voltrun-uyelik-tarife/#tarife",
    "https://www.wattarya.com/tarifeler",
    "https://zes.net/tr/fiyatlandirma",
    "https://www.ispirlisarj.com/tarifeler/",
    "https://www.sarjmatik.com.tr/ChargingPrices/",
    "https://sarjpark.istanbul/urunler/fiyatlandirma",
    "https://ctgelektrik.com/fiyat-listesi/",
    "https://xsarj.com/tarifeler/",
    # Non-force'da başarılı olan 34 site (scraper çalışıyor)
    "https://5sarj.com/tr/fiyatlandirma",
    "https://adzesarj.com/fiyat-tarifesi",
    "https://www.aksasarj.com.tr/tr/ucretler",
    "https://www.asplussarj.com/fiyatlar",
    "https://autovoltenerji.com/fiyatlandirma/",
    "https://www.biogreen.com.tr/tr/ucretlendirme",
    "https://www.bladeco.com.tr/tarifeler/",
    "https://www.clixsolar.com",
    "https://www.enerturk.com/sarj/uyelik-tarifeler",
    "https://esarj.com/fiyatlandirma",
    "https://evccharge.com/anasayfa",
    "https://fzyenergy.com/fiyatlandirma.php",
    "https://getacharge.com.tr/fiyatlar/",
    "https://www.gotedygo.com/fiyatarifeleri",
    "https://greendrive.com.tr/tarifeler",
    "https://hizzlan.com/ucretlendirme-ve-tarifeler",
    "https://kessarj.com/fiyat-ve-tarifeler",
    "https://lumicle.com.tr",
    "https://www.mypower.net.tr",
    "https://www.otowatt.com.tr/tarifelerimiz",
    "https://www.pilstop.com/fiyatlandirma",
    "https://www.qopuzenergy.com/tarifeler",
    "https://sunlightcharge.com.tr/Price.aspx",
    "https://tam-sarj.com/tarifeler/",
    "https://tripy.mobi/charge/fiyatlandirma/",
    "https://valesarj.com.tr/fiyatlar/",
    "https://ziraatfilo.com.tr/z-sarj/uyelik-ve-tarifeler",
    "https://www.zeplinenerji.com.tr/",
    "https://www.sarj.com.tr/tr/sarj-istasyonlari-fiyatlari/",
    "https://bluenerjiturkiye.com.tr/index.php/fiyatlar",
    "https://dogusdijitalenerji.com",
    "https://foksenerji.com",
    "https://karkinenerji.com.tr/guncel-sarj-fiyatlari/",
    "https://www.monokonev.com/Price",
]

