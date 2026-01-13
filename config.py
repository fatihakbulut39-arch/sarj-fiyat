"""
Configuration file for the charging price scraper
"""
import json
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data directory
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# JSON file path
PRICES_JSON = os.path.join(DATA_DIR, "charging_prices.json")

# URL list file path
URLS_JSON = os.path.join(DATA_DIR, "charging_station_urls.json")

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# Scraping settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 1  # seconds

# Default list of charging station websites - legacy 66 URLs
def _load_urls_from_file():
    """Load URL list from JSON file or fall back to empty list."""
    if os.path.exists(URLS_JSON):
        try:
            with open(URLS_JSON, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                cleaned = sorted({url.strip() for url in data if isinstance(url, str) and url.strip()})
                if cleaned:
                    return cleaned
        except Exception:
            pass

    return []


CHARGING_STATION_URLS = _load_urls_from_file()

