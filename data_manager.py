"""
Data manager for handling charging prices data
"""
import json
import os
import logging
import config

logger = logging.getLogger(__name__)


class DataManager:
    """Manages loading and saving charging price data"""
    
    def __init__(self):
        self.data_dir = config.DATA_DIR
        self.prices_json = config.PRICES_JSON
        self.standard_json = os.path.join(self.data_dir, 'charging_prices_standard.json')
        
    def load_prices(self):
        """Load existing prices from JSON file"""
        try:
            if os.path.exists(self.prices_json):
                with open(self.prices_json, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load prices: {e}")
        return []
    
    def save_prices(self, data):
        """Save prices to JSON file"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.prices_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(data)} prices to {self.prices_json}")
            return True
        except Exception as e:
            logger.error(f"Failed to save prices: {e}")
            return False
    
    def load_standard_prices(self):
        """Load standard format prices"""
        try:
            if os.path.exists(self.standard_json):
                with open(self.standard_json, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load standard prices: {e}")
        return []
    
    def save_standard_prices(self, data):
        """Save standard format prices"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.standard_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(data)} standard prices to {self.standard_json}")
            return True
        except Exception as e:
            logger.error(f"Failed to save standard prices: {e}")
            return False
