# ⚡ Şarj İstasyonu Fiyat Takip Sistemi

Türkiye'deki 149+ elektrikli araç şarj istasyonu firmasının fiyatlarını otomatik olarak toplayan sistem.

## 🚀 Nasıl Çalışır?

- **GitHub Actions** her 3 günde bir otomatik olarak çalışır
- Fiyatlar `data/charging_prices_standard.json` dosyasına kaydedilir  
- **GitHub Pages** üzerinden canlı web sitesi yayınlanır
- 66 site scraping yapılıyor, 32 site force mode ile garantili doğru

## 🛠️ Kurulum

### Bağımlılıkları yükle

```bash
pip install -r requirements.txt
```

### Manuel Scraping

```bash
python scraper_runner.py
```

## 📁 Temel Dosyalar

- `quick_scrape.py` - Web scraper (regex tabanlı)
- `scraper_runner.py` - Scraper koordinatörü
- `config.py` - Yapılandırma (66 site URL'si)
- `index.html` - Frontend (canlı görüntüleme)
- `data/` - JSON dosyaları

## 📊 Veri Formatı

```json
{
  "firma": "Şarj İstasyonu Adı",
  "webSitesi": "https://...",
  "acFiyat": 8.99,
  "dcFiyat": 12.99,
  "acCurrency": "TRY",
  "dcCurrency": "TRY"
}
```

## 🔧 Sistem Yapısı

- **Force Mode**: 32 site (garantili doğru fiyat - fallback)
- **Scraping**: 34 site (web'ten otomatik çekme)
- **Toplam**: 66 site, 149 firma

## 🤖 Otomatik Güncelleme

- **Sıklık**: Her 3 günde bir
- **Zaman**: Sabah 03:00 UTC (06:00 Türkiye)
- **Sonuç**: Otomatik commit ve GitHub Pages'e deploy

## 📈 Özellikler

✅ 164+ şarj istasyonu firması  
✅ Otomatik veri toplama  
✅ Gerçek zamanlı arama ve filtreleme  
✅ Responsive tasarım  
✅ Fiyat karşılaştırması  
✅ Ücretsiz hosting (GitHub Pages)

## 🔧 Geliştirme

```bash
# Virtual environment oluştur
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt

# Test et
python scraper_runner.py
```

## 📝 Lisans

MIT License - Özgürce kullanabilirsiniz!

---

**Son Güncelleme:** Her 3 günde bir otomatik 🤖
