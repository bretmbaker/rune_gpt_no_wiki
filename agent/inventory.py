# inventory.py - Tracks items and equipment

import os
import pandas as pd
from typing import Dict, List, Optional

class Inventory:
    """
    Tracks the agent's inventory and equipment.
    """
    def __init__(self):
        # Initialize empty inventory (28 slots)
        self.items = [None] * 28
        
        # Initialize equipment slots
        self.equipment = {
            "head": None,
            "cape": None,
            "neck": None,
            "ammo": None,
            "weapon": None,
            "shield": None,
            "body": None,
            "legs": None,
            "hands": None,
            "feet": None,
            "ring": None
        }
    
    def add_item(self, item: str) -> bool:
        """
        Add an item to the inventory.
        
        Args:
            item: The item to add
            
        Returns:
            True if item was added, False if inventory is full
        """
        # Find first empty slot
        for i in range(len(self.items)):
            if self.items[i] is None:
                self.items[i] = item
                print(f"[Inventory]: Added {item} to slot {i+1}")
                return True
        
        print("[Inventory]: Inventory is full!")
        return False
    
    def remove_item(self, item: str) -> bool:
        """
        Remove an item from the inventory.
        
        Args:
            item: The item to remove
            
        Returns:
            True if item was removed, False if not found
        """
        for i in range(len(self.items)):
            if self.items[i] == item:
                self.items[i] = None
                print(f"[Inventory]: Removed {item} from slot {i+1}")
                return True
        
        print(f"[Inventory]: Could not find {item} in inventory!")
        return False
    
    def has_item(self, item: str) -> bool:
        """Check if an item is in the inventory."""
        return item in self.items
    
    def equip_item(self, item: str) -> bool:
        """
        Equip an item from the inventory.
        
        Args:
            item: The item to equip
            
        Returns:
            True if item was equipped, False if not found
        """
        # Find the item in inventory
        if not self.has_item(item):
            print(f"[Inventory]: Cannot equip {item} - not in inventory!")
            return False
        
        # Determine equipment slot based on item type
        slot = self._get_equipment_slot(item)
        if not slot:
            print(f"[Inventory]: Cannot equip {item} - not equipment!")
            return False
        
        # Unequip current item in slot if any
        if self.equipment[slot]:
            self.unequip_item(slot)
        
        # Equip new item
        self.equipment[slot] = item
        self.remove_item(item)
        print(f"[Inventory]: Equipped {item} in {slot} slot")
        return True
    
    def unequip_item(self, slot: str) -> bool:
        """
        Unequip an item from a slot.
        
        Args:
            slot: The equipment slot to unequip
            
        Returns:
            True if item was unequipped, False if slot was empty
        """
        if not self.equipment[slot]:
            print(f"[Inventory]: Nothing equipped in {slot} slot!")
            return False
        
        # Try to add to inventory
        if self.add_item(self.equipment[slot]):
            self.equipment[slot] = None
            print(f"[Inventory]: Unequipped item from {slot} slot")
            return True
        
        print("[Inventory]: Cannot unequip - inventory is full!")
        return False
    
    def _get_equipment_slot(self, item: str) -> str:
        """
        Determine which equipment slot an item goes in.
        
        Args:
            item: The item to check
            
        Returns:
            The equipment slot name, or None if not equipment
        """
        # Fallback to basic pattern matching
        item = item.lower()
        
        if "helmet" in item or "hat" in item or "hood" in item:
            return "head"
        elif "cape" in item:
            return "cape"
        elif "amulet" in item or "necklace" in item:
            return "neck"
        elif "arrow" in item or "bolt" in item:
            return "ammo"
        elif "sword" in item or "axe" in item or "scimitar" in item:
            return "weapon"
        elif "shield" in item or "defender" in item:
            return "shield"
        elif "body" in item or "platebody" in item or "chainbody" in item:
            return "body"
        elif "legs" in item or "chaps" in item:
            return "legs"
        elif "gloves" in item or "gauntlets" in item:
            return "hands"
        elif "boots" in item or "shoes" in item:
            return "feet"
        elif "ring" in item:
            return "ring"
        
        return None
    
    def print_status(self):
        """Print the current inventory and equipment status."""
        print("\n[RuneGPT Inventory]")
        print("Inventory:")
        for i, item in enumerate(self.items, 1):
            print(f"  {i}. {item if item else 'Empty'}")
        
        print("\nEquipment:")
        for slot, item in self.equipment.items():
            print(f"  {slot.capitalize()}: {item if item else 'Empty'}")
        print("-" * 50)

    def get_state(self) -> dict:
        """
        Get a serializable state representation of the inventory and equipment.
        
        Returns:
            Dictionary containing inventory items and equipped items
        """
        return {
            "items": self.items.copy(),
            "equipment": self.equipment.copy()
        }

# Create a global inventory instance
inventory = Inventory() 