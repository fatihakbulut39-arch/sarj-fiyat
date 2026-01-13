# ⚡️ Elektrikli Araç Şarj Fiyatları API

Bu proje, Türkiye'deki elektrikli araç şarj istasyonu fiyatlarını otomatik olarak toplar ve Cloudflare Workers üzerinden JSON API olarak sunar.

## 📂 Proje Yapısı

*   `quick_scrape.py`: Ana scraping motoru (Requests + BeautifulSoup ve Selenium fallback).
*   `scraper_runner.py`: Scraper'ı çalıştırır, logoları ekler ve veriyi standart formata dönüştürür.
*   `update_cloudflare.py`: GitHub Actions tarafından çalıştırılır. Fiyatları toplar ve Cloudflare KV'ye günceller.
*   `data/`:
    *   `charging_station_urls.json`: Taranacak sitelerin listesi.
    *   `logo_map.json`: Firmaların logo URL'lerinin tanımlandığı dosya.
    *   `charging_prices_standard.json`: Son taranan ve kaydedilen veri.
*   `.github/workflows/update-prices.yml`: 3 günde bir çalışan otomasyon.

## 🚀 Kurulum ve Kullanım

### Gereksinimler
```bash
pip install -r requirements.txt
```

### Manuel Çalıştırma
Fiyatları güncelleyip Cloudflare'e göndermek için:
```bash
export WORKER_URL="https://sarj-api.fatihakbulut39.workers.dev"
export CF_API_KEY="senin-gizli-anahtarin"
python3 update_cloudflare.py
```

### Logo Ayarları
Logolar `data/logo_map.json` dosyasından çekilir. Yeni bir site eklerseniz logosunu bu dosyaya eklemeyi unutmayın.

## ⚙️ Otomasyon
GitHub Actions (`.github/workflows/update-prices.yml`) her 3 günde bir (Cron: `0 2 */3 * *`) çalışarak sistemi günceller.
GitHub Secrets içinde `WORKER_URL` ve `CF_API_KEY` tanımlı olmalıdır.
