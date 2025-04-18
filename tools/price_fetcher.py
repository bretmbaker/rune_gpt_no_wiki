#!/usr/bin/env python3
"""
Price Fetcher for RuneGPT
Fetches item prices from the OSRS Grand Exchange API
"""

import json
import logging
import time
from typing import Dict, Optional, List
from pathlib import Path
import requests
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class PriceFetcher:
    """Fetches and caches item prices from the OSRS Grand Exchange API."""
    
    def __init__(self, cache_file: Path = Path("state/price_cache.json")):
        """
        Initialize the price fetcher.
        
        Args:
            cache_file: Path to the price cache file
        """
        self.cache_file = cache_file
        self.cache_dir = cache_file.parent
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()
        self.last_update = self.cache.get("last_update", 0)
        self.prices = self.cache.get("prices", {})
        self.update_interval = 3600  # Update prices every hour
    
    def _load_cache(self) -> Dict:
        """Load the price cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading price cache: {str(e)}")
                return {"last_update": 0, "prices": {}}
        return {"last_update": 0, "prices": {}}
    
    def _save_cache(self):
        """Save the price cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump({
                    "last_update": self.last_update,
                    "prices": self.prices
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving price cache: {str(e)}")
    
    def _should_update(self) -> bool:
        """Check if the price cache should be updated."""
        current_time = time.time()
        return current_time - self.last_update > self.update_interval
    
    def _fetch_prices(self):
        """Fetch prices from the OSRS GE API."""
        try:
            logger.info("Fetching prices from OSRS GE API")
            response = requests.get("https://prices.runescape.wiki/api/v1/osrs/latest")
            response.raise_for_status()
            data = response.json()
            
            # Update prices
            self.prices = data.get("data", {})
            self.last_update = time.time()
            self._save_cache()
            
            logger.info(f"Updated {len(self.prices)} item prices")
        except Exception as e:
            logger.error(f"Error fetching prices: {str(e)}")
    
    def get_item_price(self, item_name: str) -> Optional[int]:
        """
        Get the price of an item.
        
        Args:
            item_name: Name of the item
            
        Returns:
            Price of the item in GP, or None if not found
        """
        # Always update the price for Old School Bond
        if item_name.lower() == "old school bond":
            self._fetch_prices()
        
        # Update prices if needed
        elif self._should_update():
            self._fetch_prices()
        
        # Try to find the item by name
        for item_id, item_data in self.prices.items():
            if item_data.get("name", "").lower() == item_name.lower():
                return item_data.get("high", 0)
        
        # If not found in GE, try to find in wiki data
        try:
            wiki_data_dir = Path("wiki_data")
            for category_dir in wiki_data_dir.iterdir():
                if not category_dir.is_dir():
                    continue
                    
                metadata_file = category_dir / "metadata.json"
                if not metadata_file.exists():
                    continue
                    
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                for name, data in metadata.items():
                    if name.lower() == item_name.lower():
                        txt_file = category_dir / "txt" / data["txt"].split("/")[-1]
                        if txt_file.exists():
                            with open(txt_file, 'r') as f:
                                content = f.read()
                                # Extract price from content
                                price_match = re.search(r"Grand Exchange Value: ([\d,]+) coins", content)
                                if price_match:
                                    return int(price_match.group(1).replace(",", ""))
        except Exception as e:
            logger.error(f"Error getting price from wiki data: {str(e)}")
        
        return None
    
    def get_item_id(self, item_name: str) -> Optional[int]:
        """
        Get the ID of an item.
        
        Args:
            item_name: Name of the item
            
        Returns:
            ID of the item, or None if not found
        """
        # Try to find the item by name
        for item_id, item_data in self.prices.items():
            if item_data.get("name", "").lower() == item_name.lower():
                return int(item_id)
        
        # If not found, try to find by partial name
        for item_id, item_data in self.prices.items():
            if item_name.lower() in item_data.get("name", "").lower():
                return int(item_id)
        
        logger.warning(f"Item ID not found: {item_name}")
        return None
    
    def get_bond_price(self) -> Optional[int]:
        """
        Get the current price of an Old School Bond.
        
        Returns:
            Price of the bond in GP, or None if not found
        """
        return self.get_item_price("Old School Bond")
    
    def get_item_history(self, item_name: str, days: int = 30) -> List[Dict]:
        """
        Get the price history of an item.
        
        Args:
            item_name: Name of the item
            days: Number of days of history to fetch
            
        Returns:
            List of price history entries
        """
        item_id = self.get_item_id(item_name)
        if not item_id:
            return []
        
        try:
            logger.info(f"Fetching price history for {item_name}")
            response = requests.get(f"https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=1d&id={item_id}")
            response.raise_for_status()
            data = response.json()
            
            # Filter to the requested number of days
            history = data.get("data", {}).get(str(item_id), [])
            cutoff_date = datetime.now() - timedelta(days=days)
            
            filtered_history = []
            for entry in history:
                entry_date = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                if entry_date >= cutoff_date:
                    filtered_history.append({
                        "date": entry_date.isoformat(),
                        "high": entry.get("high", 0),
                        "low": entry.get("low", 0),
                        "avg": (entry.get("high", 0) + entry.get("low", 0)) // 2
                    })
            
            return filtered_history
        except Exception as e:
            logger.error(f"Error fetching price history: {str(e)}")
            return [] 