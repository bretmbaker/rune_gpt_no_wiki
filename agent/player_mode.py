from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import json
from pathlib import Path
from datetime import datetime, timedelta

class PlayerMode(Enum):
    REGULAR = "regular"
    IRONMAN = "ironman"
    HARDCORE_IRONMAN = "hardcore_ironman"
    ULTIMATE_IRONMAN = "ultimate_ironman"

@dataclass
class PlayerStatus:
    """Represents the player's mode and membership status."""
    mode: PlayerMode
    is_member: bool
    membership_expiry: Optional[str]  # ISO 8601 datetime
    quest_points: int
    total_level: int
    combat_level: int
    wealth: Dict[str, int]  # gp, items value, etc.
    achievements: List[str]
    restrictions: List[str]  # Mode-specific restrictions
    bond_purchase_log: List[Dict]  # History of bond purchases and redemptions
    quests_completed: List[str]  # List of completed quests
    diaries_completed: List[str]  # List of completed achievement diaries
    combat_achievements: List[str]  # List of completed combat achievements
    item_history: List[Dict]  # History of item acquisitions and losses
    ge_transactions: List[Dict]  # History of Grand Exchange transactions

class PlayerModeManager:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.status_file = state_dir / "player_status.json"
        self.status = self._load_status()
    
    def _load_status(self) -> PlayerStatus:
        """Load player status from file or create default."""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                data = json.load(f)
                return PlayerStatus(
                    mode=PlayerMode(data['mode']),
                    is_member=data.get('is_member', False),
                    membership_expiry=data.get('membership_expiry', None),
                    quest_points=data.get('quest_points', 0),
                    total_level=data.get('total_level', 32),
                    combat_level=data.get('combat_level', 3),
                    wealth=data.get('wealth', {'gp': 0, 'items_value': 0}),
                    achievements=data.get('achievements', []),
                    restrictions=data.get('restrictions', []),
                    bond_purchase_log=data.get('bond_purchase_log', []),
                    quests_completed=data.get('quests_completed', []),
                    diaries_completed=data.get('diaries_completed', []),
                    combat_achievements=data.get('combat_achievements', []),
                    item_history=data.get('item_history', []),
                    ge_transactions=data.get('ge_transactions', [])
                )
        return self._create_default_status()
    
    def _create_default_status(self) -> PlayerStatus:
        """Create default player status."""
        return PlayerStatus(
            mode=PlayerMode.REGULAR,
            is_member=False,
            membership_expiry=None,
            quest_points=0,
            total_level=32,  # Starting total level
            combat_level=3,  # Starting combat level
            wealth={'gp': 0, 'items_value': 0},
            achievements=[],
            restrictions=[],
            bond_purchase_log=[],
            quests_completed=[],
            diaries_completed=[],
            combat_achievements=[],
            item_history=[],
            ge_transactions=[]
        )
    
    def save_status(self):
        """Save current player status to file."""
        data = {
            'mode': self.status.mode.value,
            'is_member': self.status.is_member,
            'membership_expiry': self.status.membership_expiry,
            'quest_points': self.status.quest_points,
            'total_level': self.status.total_level,
            'combat_level': self.status.combat_level,
            'wealth': self.status.wealth,
            'achievements': self.status.achievements,
            'restrictions': self.status.restrictions,
            'bond_purchase_log': self.status.bond_purchase_log,
            'quests_completed': self.status.quests_completed,
            'diaries_completed': self.status.diaries_completed,
            'combat_achievements': self.status.combat_achievements,
            'item_history': self.status.item_history,
            'ge_transactions': self.status.ge_transactions
        }
        with open(self.status_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def set_mode(self, mode: PlayerMode):
        """Set player mode and update restrictions."""
        self.status.mode = mode
        self.status.restrictions = self._get_mode_restrictions(mode)
        self.save_status()
    
    def set_membership(self, is_member: bool, expiry_days: int = 14):
        """Update membership status and set expiry date."""
        self.status.is_member = is_member
        
        if is_member:
            # Set membership expiry to 14 days from now
            expiry_date = datetime.now() + timedelta(days=expiry_days)
            self.status.membership_expiry = expiry_date.isoformat()
        else:
            # Clear membership expiry
            self.status.membership_expiry = None
        
        self.save_status()
    
    def check_membership_expiry(self) -> bool:
        """
        Check if membership has expired and update status if needed.
        
        Returns:
            True if membership status changed, False otherwise
        """
        if not self.status.is_member or not self.status.membership_expiry:
            return False
        
        # Parse expiry date
        expiry_date = datetime.fromisoformat(self.status.membership_expiry)
        
        # Check if membership has expired
        if datetime.now() > expiry_date:
            # Membership has expired
            self.status.is_member = False
            self.status.membership_expiry = None
            self.save_status()
            return True
        
        return False
    
    def get_membership_days_remaining(self) -> Optional[int]:
        """
        Get the number of days remaining in membership.
        
        Returns:
            Number of days remaining, or None if not a member
        """
        if not self.status.is_member or not self.status.membership_expiry:
            return None
        
        # Parse expiry date
        expiry_date = datetime.fromisoformat(self.status.membership_expiry)
        
        # Calculate days remaining
        days_remaining = (expiry_date - datetime.now()).days
        return max(0, days_remaining)
    
    def log_bond_purchase(self, bond_price: int, quantity: int = 1):
        """
        Log a bond purchase.
        
        Args:
            bond_price: Price of the bond in GP
            quantity: Number of bonds purchased
        """
        self.status.bond_purchase_log.append({
            'action': 'purchase',
            'timestamp': datetime.now().isoformat(),
            'price': bond_price,
            'quantity': quantity,
            'total_cost': bond_price * quantity
        })
        self.save_status()
    
    def log_bond_redemption(self, quantity: int = 1):
        """
        Log a bond redemption.
        
        Args:
            quantity: Number of bonds redeemed
        """
        self.status.bond_purchase_log.append({
            'action': 'redemption',
            'timestamp': datetime.now().isoformat(),
            'quantity': quantity
        })
        self.save_status()
    
    def log_item_acquisition(self, item_name: str, quantity: int, source: str, value: int = 0):
        """
        Log an item acquisition.
        
        Args:
            item_name: Name of the item
            quantity: Quantity acquired
            source: Source of the item (e.g., "GE", "Drop", "Quest")
            value: Value of the item in GP
        """
        self.status.item_history.append({
            'action': 'acquisition',
            'timestamp': datetime.now().isoformat(),
            'item': item_name,
            'quantity': quantity,
            'source': source,
            'value': value
        })
        self.save_status()
    
    def log_item_loss(self, item_name: str, quantity: int, reason: str, value: int = 0):
        """
        Log an item loss.
        
        Args:
            item_name: Name of the item
            quantity: Quantity lost
            reason: Reason for loss (e.g., "Death", "GE", "Quest")
            value: Value of the item in GP
        """
        self.status.item_history.append({
            'action': 'loss',
            'timestamp': datetime.now().isoformat(),
            'item': item_name,
            'quantity': quantity,
            'reason': reason,
            'value': value
        })
        self.save_status()
    
    def log_ge_transaction(self, item_name: str, quantity: int, price: int, is_buy: bool):
        """
        Log a Grand Exchange transaction.
        
        Args:
            item_name: Name of the item
            quantity: Quantity traded
            price: Price per item in GP
            is_buy: True if buying, False if selling
        """
        self.status.ge_transactions.append({
            'action': 'buy' if is_buy else 'sell',
            'timestamp': datetime.now().isoformat(),
            'item': item_name,
            'quantity': quantity,
            'price': price,
            'total': price * quantity
        })
        self.save_status()
    
    def update_wealth(self, gp_change: int = 0, items_value_change: int = 0):
        """Update player's wealth tracking."""
        self.status.wealth['gp'] += gp_change
        self.status.wealth['items_value'] += items_value_change
        self.save_status()
    
    def can_use_ge(self, item_name: str = None) -> bool:
        """
        Check if the player can use the Grand Exchange.
        
        Args:
            item_name: Optional item name to check for specific restrictions
            
        Returns:
            True if the player can use the GE, False otherwise
        """
        # Ironman accounts can only use the GE for bonds
        if self.status.mode != PlayerMode.REGULAR:
            if item_name and item_name.lower() == "old school bond":
                return True
            return False
        
        return True
    
    def _get_mode_restrictions(self, mode: PlayerMode) -> List[str]:
        """Get restrictions based on player mode."""
        restrictions = []
        if mode == PlayerMode.IRONMAN:
            restrictions.extend([
                "Cannot trade with other players",
                "Cannot use the Grand Exchange",
                "Cannot receive items from other players",
                "Cannot pick up items dropped by other players"
            ])
        elif mode == PlayerMode.HARDCORE_IRONMAN:
            restrictions.extend([
                "Cannot trade with other players",
                "Cannot use the Grand Exchange",
                "Cannot receive items from other players",
                "Cannot pick up items dropped by other players",
                "Loses Hardcore status upon death"
            ])
        elif mode == PlayerMode.ULTIMATE_IRONMAN:
            restrictions.extend([
                "Cannot trade with other players",
                "Cannot use the Grand Exchange",
                "Cannot receive items from other players",
                "Cannot pick up items dropped by other players",
                "Cannot use banks",
                "Cannot use death storage",
                "Loses Ultimate status upon death"
            ])
        return restrictions 