
import json
import os
import requests
import logging

# Config
WORKER_URL = os.getenv('WORKER_URL', 'https://sarj-api.fatihakbulut39.workers.dev')
# Note: Using the default key from update_cloudflare.py since environment variable might not be set in this shell
API_KEY = os.getenv('CF_API_KEY', 'sarj-fiyat-api-key-2025')
DATA_FILE = 'data/charging_prices_standard.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def manual_upload():
    print(f"Target URL: {WORKER_URL}")
    print(f"Data File: {DATA_FILE}")
    
    if not os.path.exists(DATA_FILE):
        print("❌ Data file not found")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        prices = json.load(f)
        
    print(f"Read {len(prices)} items from file.")
    
    try:
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
            print("✅ Upload SUCCESS!")
            print(response.json())
        else:
            print(f"❌ Upload FAILED: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception during upload: {e}")

if __name__ == "__main__":
    manual_upload()
