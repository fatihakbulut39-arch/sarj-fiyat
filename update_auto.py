import json
import requests
import subprocess
from datetime import datetime

WORKER_URL = "https://broken-water-2c5f.fatihakbulut39.workers.dev"
API_KEY = "sarj-fiyat-api-key-2025"

print(f"[{datetime.now()}] Güncelleme başlıyor...")

# Verileri scrape et
result = subprocess.run(['python3', 'scraper_runner.py'], capture_output=True)
if result.returncode != 0:
    print("Scrape hatası")
    exit(1)

# JSON'ı oku
with open('data/charging_prices_standard.json', 'r', encoding='utf-8') as f:
    prices = json.load(f)

# KV'ye gönder
response = requests.post(
    f"{WORKER_URL}/update",
    json=prices,
    headers={'X-API-Key': API_KEY}
)

if response.status_code == 200:
    print(f"Başarılı: {len(prices)} firma")
else:
    print(f"Hata: {response.status_code}")
