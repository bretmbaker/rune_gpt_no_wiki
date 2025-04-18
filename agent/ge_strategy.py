#!/usr/bin/env python3
"""
GE Strategy Module for RuneGPT
Tracks profitable item flips and suggests what to sell
"""

import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

from tools.price_fetcher import PriceFetcher

logger = logging.getLogger(__name__)

class GEStrategy:
    """
    Tracks profitable item flips and suggests what to sell.
    Prioritizes saving for a Bond.
    """
    
    def __init__(self, price_fetcher: PriceFetcher, state_dir: Path):
        """
        Initialize the GE strategy.
        
        Args:
            price_fetcher: PriceFetcher instance for getting item prices
            state_dir: Directory for saving state
        """
        self.price_fetcher = price_fetcher
        self.state_dir = state_dir
        self.state_file = state_dir / "ge_strategy.json"
        self.state = self._load_state()
        self.bond_price = self.price_fetcher.get_bond_price() or 7000000  # Default to 7M if not available
        self.last_update = time.time()
        self.update_interval = 3600  # Update prices every hour
    
    def _load_state(self) -> Dict:
        """Load GE strategy state from file or create default."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading GE strategy state: {str(e)}")
                return self._create_default_state()
        return self._create_default_state()
    
    def _create_default_state(self) -> Dict:
        """Create default GE strategy state."""
        return {
            "bond_status": {
                "has_bond": False,
                "time_remaining_days": None,
                "gp_saved": 0,
                "gp_needed": 7000000,
                "last_bond_purchase": None,
                "last_bond_redemption": None
            },
            "flip_history": [],
            "active_flips": [],
            "suggested_sells": [],
            "last_price_update": 0
        }
    
    def save_state(self):
        """Save current GE strategy state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving GE strategy state: {str(e)}")
    
    def update_bond_price(self):
        """Update the bond price from the price fetcher."""
        current_time = time.time()
        if current_time - self.last_update > self.update_interval:
            self.bond_price = self.price_fetcher.get_bond_price() or self.bond_price
            self.state["bond_status"]["gp_needed"] = self.bond_price
            self.last_update = current_time
            self.save_state()
    
    def set_bond_status(self, has_bond: bool, time_remaining_days: Optional[int] = None):
        """
        Update the bond status.
        
        Args:
            has_bond: Whether the player has a bond
            time_remaining_days: Days remaining in membership
        """
        self.state["bond_status"]["has_bond"] = has_bond
        
        if time_remaining_days is not None:
            self.state["bond_status"]["time_remaining_days"] = time_remaining_days
            if time_remaining_days > 0:
                self.state["bond_status"]["last_bond_redemption"] = datetime.now().isoformat()
        
        self.save_state()
    
    def update_gp_saved(self, gp: int):
        """
        Update the GP saved toward a bond.
        
        Args:
            gp: Amount of GP saved
        """
        self.state["bond_status"]["gp_saved"] = gp
        self.save_state()
    
    def log_bond_purchase(self, bond_price: int):
        """
        Log a bond purchase.
        
        Args:
            bond_price: Price of the bond in GP
        """
        self.state["bond_status"]["last_bond_purchase"] = datetime.now().isoformat()
        self.state["bond_status"]["gp_saved"] = 0
        self.save_state()
    
    def get_bond_status(self) -> Dict:
        """
        Get the current bond status.
        
        Returns:
            Dictionary containing bond status
        """
        return self.state["bond_status"]
    
    def get_bond_progress(self) -> Tuple[int, int, float]:
        """
        Get the progress toward a bond.
        
        Returns:
            Tuple of (GP saved, GP needed, percentage complete)
        """
        gp_saved = self.state["bond_status"]["gp_saved"]
        gp_needed = self.state["bond_status"]["gp_needed"]
        percentage = (gp_saved / gp_needed) * 100 if gp_needed > 0 else 0
        return gp_saved, gp_needed, percentage
    
    def find_profitable_flips(self, min_profit: int = 100, max_items: int = 10) -> List[Dict]:
        """
        Find profitable items to flip on the Grand Exchange.
        
        Args:
            min_profit: Minimum profit per item in GP
            max_items: Maximum number of items to return
            
        Returns:
            List of profitable items to flip
        """
        # This is a simplified implementation
        # In a real implementation, this would analyze price history and trends
        
        # Example profitable items (in a real implementation, this would be dynamic)
        profitable_items = [
            {"name": "coal", "buy_price": 200, "sell_price": 250, "profit": 50},
            {"name": "iron ore", "buy_price": 150, "sell_price": 200, "profit": 50},
            {"name": "willow logs", "buy_price": 50, "sell_price": 70, "profit": 20},
            {"name": "oak logs", "buy_price": 100, "sell_price": 130, "profit": 30},
            {"name": "cowhide", "buy_price": 100, "sell_price": 150, "profit": 50},
            {"name": "raw lobsters", "buy_price": 200, "sell_price": 250, "profit": 50},
            {"name": "raw sharks", "buy_price": 1000, "sell_price": 1200, "profit": 200},
            {"name": "yew logs", "buy_price": 300, "sell_price": 350, "profit": 50},
            {"name": "magic logs", "buy_price": 1000, "sell_price": 1100, "profit": 100},
            {"name": "runite ore", "buy_price": 10000, "sell_price": 11000, "profit": 1000}
        ]
        
        # Filter by minimum profit
        profitable_items = [item for item in profitable_items if item["profit"] >= min_profit]
        
        # Sort by profit (highest first)
        profitable_items.sort(key=lambda x: x["profit"], reverse=True)
        
        # Limit to max_items
        return profitable_items[:max_items]
    
    def suggest_items_to_sell(self, inventory: Dict[str, int]) -> List[Dict]:
        """
        Suggest items to sell based on current prices.
        
        Args:
            inventory: Dictionary of items and quantities
            
        Returns:
            List of suggested items to sell
        """
        suggestions = []
        
        for item_name, quantity in inventory.items():
            # Skip if quantity is 0
            if quantity <= 0:
                continue
            
            # Get current price
            price = self.price_fetcher.get_item_price(item_name)
            if not price:
                continue
            
            # Check if it's a raw material that can be processed
            processed_item = self._get_processed_version(item_name)
            if processed_item:
                processed_price = self.price_fetcher.get_item_price(processed_item)
                if processed_price and processed_price > price:
                    # Calculate potential profit
                    profit = (processed_price - price) * quantity
                    suggestions.append({
                        "item": item_name,
                        "quantity": quantity,
                        "current_price": price,
                        "processed_item": processed_item,
                        "processed_price": processed_price,
                        "potential_profit": profit,
                        "action": "process"
                    })
                else:
                    # Suggest selling if price is good
                    suggestions.append({
                        "item": item_name,
                        "quantity": quantity,
                        "current_price": price,
                        "potential_value": price * quantity,
                        "action": "sell"
                    })
            else:
                # Suggest selling if price is good
                suggestions.append({
                    "item": item_name,
                    "quantity": quantity,
                    "current_price": price,
                    "potential_value": price * quantity,
                    "action": "sell"
                })
        
        # Sort by potential value (highest first)
        suggestions.sort(key=lambda x: x.get("potential_profit", x.get("potential_value", 0)), reverse=True)
        
        return suggestions
    
    def _get_processed_version(self, item_name: str) -> Optional[str]:
        """
        Get the processed version of a raw material.
        
        Args:
            item_name: Name of the raw material
            
        Returns:
            Name of the processed item, or None if not applicable
        """
        processed_items = {
            "logs": "planks",
            "oak logs": "oak planks",
            "willow logs": "willow planks",
            "maple logs": "maple planks",
            "yew logs": "yew planks",
            "magic logs": "magic planks",
            "raw shrimp": "shrimp",
            "raw anchovies": "anchovies",
            "raw sardine": "sardine",
            "raw herring": "herring",
            "raw mackerel": "mackerel",
            "raw trout": "trout",
            "raw salmon": "salmon",
            "raw tuna": "tuna",
            "raw lobster": "lobster",
            "raw swordfish": "swordfish",
            "raw monkfish": "monkfish",
            "raw shark": "shark",
            "copper ore": "copper bar",
            "tin ore": "tin bar",
            "iron ore": "iron bar",
            "silver ore": "silver bar",
            "coal": "coal",
            "gold ore": "gold bar",
            "mithril ore": "mithril bar",
            "adamantite ore": "adamantite bar",
            "runite ore": "runite bar"
        }
        
        return processed_items.get(item_name.lower())
    
    def log_flip(self, item_name: str, buy_price: int, sell_price: int, quantity: int, profit: int):
        """
        Log a successful flip.
        
        Args:
            item_name: Name of the item
            buy_price: Price bought at
            sell_price: Price sold at
            quantity: Quantity flipped
            profit: Profit made
        """
        flip = {
            "item": item_name,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "quantity": quantity,
            "profit": profit,
            "timestamp": datetime.now().isoformat()
        }
        
        self.state["flip_history"].append(flip)
        
        # Keep only the last 100 flips
        if len(self.state["flip_history"]) > 100:
            self.state["flip_history"] = self.state["flip_history"][-100:]
        
        self.save_state()
    
    def get_flip_history(self) -> List[Dict]:
        """
        Get the flip history.
        
        Returns:
            List of flip history entries
        """
        return self.state["flip_history"]
    
    def get_total_profit(self) -> int:
        """
        Get the total profit from flipping.
        
        Returns:
            Total profit in GP
        """
        return sum(flip["profit"] for flip in self.state["flip_history"])
    
    def prioritize_bond_saving(self, current_gp: int) -> Dict:
        """
        Prioritize saving for a bond.
        
        Args:
            current_gp: Current GP
            
        Returns:
            Dictionary containing bond saving strategy
        """
        gp_saved, gp_needed, percentage = self.get_bond_progress()
        
        # If already have a bond, don't prioritize saving
        if self.state["bond_status"]["has_bond"]:
            return {
                "prioritize_bond": False,
                "gp_saved": gp_saved,
                "gp_needed": gp_needed,
                "percentage": percentage,
                "message": "Already have a bond, no need to prioritize saving."
            }
        
        # If close to having enough for a bond, prioritize saving
        if gp_saved >= gp_needed * 0.8:
            return {
                "prioritize_bond": True,
                "gp_saved": gp_saved,
                "gp_needed": gp_needed,
                "percentage": percentage,
                "message": f"Very close to having enough for a bond! Only need {gp_needed - gp_saved:,} more GP."
            }
        
        # If have a significant amount saved, continue prioritizing
        if gp_saved >= gp_needed * 0.5:
            return {
                "prioritize_bond": True,
                "gp_saved": gp_saved,
                "gp_needed": gp_needed,
                "percentage": percentage,
                "message": f"Over halfway to a bond! Keep saving {gp_needed - gp_saved:,} more GP needed."
            }
        
        # If have some saved but not much, suggest focusing on money-making
        if gp_saved > 0:
            return {
                "prioritize_bond": True,
                "gp_saved": gp_saved,
                "gp_needed": gp_needed,
                "percentage": percentage,
                "message": f"Have started saving for a bond. Focus on money-making methods to earn {gp_needed - gp_saved:,} more GP."
            }
        
        # If haven't started saving, suggest starting
        return {
            "prioritize_bond": True,
            "gp_saved": gp_saved,
            "gp_needed": gp_needed,
            "percentage": percentage,
            "message": f"Start saving for a bond! Need {gp_needed:,} GP."
        } 