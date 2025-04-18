#!/usr/bin/env python3
"""
XP Rate Model for RuneGPT
Calculates XP gains for different skills and methods
"""

import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import random

logger = logging.getLogger(__name__)

class XPRateModel:
    """
    Calculates XP rates for different skills and methods.
    Tracks best methods for each skill level.
    """
    
    def __init__(self, state_dir: Path):
        """
        Initialize the XP rate model.
        
        Args:
            state_dir: Directory for saving state
        """
        self.state_dir = state_dir
        self.state_file = state_dir / "xp_rates.json"
        self.state = self._load_state()
        
        # Load XP rate data
        self.xp_rates = self._load_xp_rates()
        self.methods = self._load_methods()
        self.session_start_time = time.time()
        self.session_xp_gained = {}
        self.session_time_spent = {}
        self.session_items_gained = {}
        
        # Initialize session tracking for all skills
        for skill in self.xp_rates.keys():
            self.session_xp_gained[skill] = 0
            self.session_time_spent[skill] = 0
            self.session_items_gained[skill] = {}
    
    def _load_state(self) -> Dict:
        """Load XP rate model state from file or create default."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading XP rate model state: {str(e)}")
                return self._create_default_state()
        return self._create_default_state()
    
    def _create_default_state(self) -> Dict:
        """Create default XP rate model state."""
        return {
            "best_methods": {},
            "method_history": {},
            "xp_rate_history": {}
        }
    
    def _load_xp_rates(self) -> Dict:
        """Load XP rates for different skills and methods."""
        return {
            "attack": {
                "cows": {"base_xp": 18, "xp_per_hour": 40000},
                "rock_crabs": {"base_xp": 25, "xp_per_hour": 60000},
                "ammonite_crabs": {"base_xp": 30, "xp_per_hour": 75000},
                "nightmare_zone": {"base_xp": 35, "xp_per_hour": 90000}
            },
            "strength": {
                "cows": {"base_xp": 18, "xp_per_hour": 40000},
                "rock_crabs": {"base_xp": 25, "xp_per_hour": 60000},
                "ammonite_crabs": {"base_xp": 30, "xp_per_hour": 75000},
                "nightmare_zone": {"base_xp": 35, "xp_per_hour": 90000}
            },
            "defence": {
                "cows": {"base_xp": 18, "xp_per_hour": 40000},
                "rock_crabs": {"base_xp": 25, "xp_per_hour": 60000},
                "ammonite_crabs": {"base_xp": 30, "xp_per_hour": 75000},
                "nightmare_zone": {"base_xp": 35, "xp_per_hour": 90000}
            },
            "ranged": {
                "cows": {"base_xp": 20, "xp_per_hour": 45000},
                "rock_crabs": {"base_xp": 28, "xp_per_hour": 65000},
                "ammonite_crabs": {"base_xp": 32, "xp_per_hour": 80000},
                "nightmare_zone": {"base_xp": 38, "xp_per_hour": 95000}
            },
            "magic": {
                "high_alchemy": {"base_xp": 65, "xp_per_hour": 70000},
                "bursting": {"base_xp": 85, "xp_per_hour": 120000},
                "barrage": {"base_xp": 100, "xp_per_hour": 150000}
            },
            "mining": {
                "copper": {"base_xp": 17.5, "xp_per_hour": 15000},
                "tin": {"base_xp": 17.5, "xp_per_hour": 15000},
                "iron": {"base_xp": 35, "xp_per_hour": 25000},
                "coal": {"base_xp": 50, "xp_per_hour": 35000},
                "mithril": {"base_xp": 80, "xp_per_hour": 45000},
                "adamantite": {"base_xp": 95, "xp_per_hour": 55000},
                "runite": {"base_xp": 125, "xp_per_hour": 65000}
            },
            "fishing": {
                "shrimp": {"base_xp": 10, "xp_per_hour": 10000},
                "sardine": {"base_xp": 20, "xp_per_hour": 15000},
                "herring": {"base_xp": 30, "xp_per_hour": 20000},
                "anchovies": {"base_xp": 15, "xp_per_hour": 12000},
                "mackerel": {"base_xp": 6, "xp_per_hour": 8000},
                "trout": {"base_xp": 50, "xp_per_hour": 30000},
                "salmon": {"base_xp": 70, "xp_per_hour": 40000},
                "lobster": {"base_xp": 90, "xp_per_hour": 50000},
                "shark": {"base_xp": 110, "xp_per_hour": 60000}
            },
            "woodcutting": {
                "normal": {"base_xp": 25, "xp_per_hour": 15000},
                "oak": {"base_xp": 37.5, "xp_per_hour": 25000},
                "willow": {"base_xp": 67.5, "xp_per_hour": 35000},
                "maple": {"base_xp": 100, "xp_per_hour": 45000},
                "yew": {"base_xp": 175, "xp_per_hour": 55000},
                "magic": {"base_xp": 250, "xp_per_hour": 65000}
            },
            "farming": {
                "allotment": {"base_xp": 100, "xp_per_hour": 20000},
                "herbs": {"base_xp": 150, "xp_per_hour": 30000},
                "trees": {"base_xp": 200, "xp_per_hour": 40000},
                "fruit_trees": {"base_xp": 250, "xp_per_hour": 50000}
            },
            "runecrafting": {
                "air": {"base_xp": 5, "xp_per_hour": 10000},
                "mind": {"base_xp": 5.5, "xp_per_hour": 12000},
                "water": {"base_xp": 6, "xp_per_hour": 14000},
                "earth": {"base_xp": 6.5, "xp_per_hour": 16000},
                "fire": {"base_xp": 7, "xp_per_hour": 18000},
                "body": {"base_xp": 7.5, "xp_per_hour": 20000},
                "cosmic": {"base_xp": 10, "xp_per_hour": 25000},
                "nature": {"base_xp": 11, "xp_per_hour": 30000},
                "law": {"base_xp": 12, "xp_per_hour": 35000},
                "death": {"base_xp": 13, "xp_per_hour": 40000},
                "blood": {"base_xp": 14, "xp_per_hour": 45000},
                "soul": {"base_xp": 15, "xp_per_hour": 50000}
            }
        }
    
    def _load_methods(self) -> Dict:
        """Load training methods for different skills."""
        return {
            "attack": {
                "cows": {"min_level": 1, "max_level": 20, "requirements": {}},
                "rock_crabs": {"min_level": 20, "max_level": 40, "requirements": {}},
                "ammonite_crabs": {"min_level": 40, "max_level": 70, "requirements": {"quest": "Dragon Slayer II"}},
                "nightmare_zone": {"min_level": 70, "max_level": 99, "requirements": {"quest": "Dream Mentor"}}
            },
            "strength": {
                "cows": {"min_level": 1, "max_level": 20, "requirements": {}},
                "rock_crabs": {"min_level": 20, "max_level": 40, "requirements": {}},
                "ammonite_crabs": {"min_level": 40, "max_level": 70, "requirements": {"quest": "Dragon Slayer II"}},
                "nightmare_zone": {"min_level": 70, "max_level": 99, "requirements": {"quest": "Dream Mentor"}}
            },
            "defence": {
                "cows": {"min_level": 1, "max_level": 20, "requirements": {}},
                "rock_crabs": {"min_level": 20, "max_level": 40, "requirements": {}},
                "ammonite_crabs": {"min_level": 40, "max_level": 70, "requirements": {"quest": "Dragon Slayer II"}},
                "nightmare_zone": {"min_level": 70, "max_level": 99, "requirements": {"quest": "Dream Mentor"}}
            },
            "ranged": {
                "cows": {"min_level": 1, "max_level": 20, "requirements": {}},
                "rock_crabs": {"min_level": 20, "max_level": 40, "requirements": {}},
                "ammonite_crabs": {"min_level": 40, "max_level": 70, "requirements": {"quest": "Dragon Slayer II"}},
                "nightmare_zone": {"min_level": 70, "max_level": 99, "requirements": {"quest": "Dream Mentor"}}
            },
            "magic": {
                "high_alchemy": {"min_level": 55, "max_level": 99, "requirements": {"quest": "Dragon Slayer I"}},
                "bursting": {"min_level": 70, "max_level": 99, "requirements": {"quest": "Desert Treasure"}},
                "barrage": {"min_level": 94, "max_level": 99, "requirements": {"quest": "Desert Treasure"}}
            },
            "mining": {
                "copper": {"min_level": 1, "max_level": 15, "requirements": {}},
                "tin": {"min_level": 1, "max_level": 15, "requirements": {}},
                "iron": {"min_level": 15, "max_level": 30, "requirements": {}},
                "coal": {"min_level": 30, "max_level": 50, "requirements": {}},
                "mithril": {"min_level": 50, "max_level": 70, "requirements": {}},
                "adamantite": {"min_level": 70, "max_level": 85, "requirements": {}},
                "runite": {"min_level": 85, "max_level": 99, "requirements": {}}
            },
            "fishing": {
                "shrimp": {"min_level": 1, "max_level": 5, "requirements": {}},
                "sardine": {"min_level": 5, "max_level": 10, "requirements": {}},
                "herring": {"min_level": 10, "max_level": 15, "requirements": {}},
                "anchovies": {"min_level": 15, "max_level": 20, "requirements": {}},
                "mackerel": {"min_level": 20, "max_level": 25, "requirements": {}},
                "trout": {"min_level": 25, "max_level": 35, "requirements": {}},
                "salmon": {"min_level": 35, "max_level": 50, "requirements": {}},
                "lobster": {"min_level": 50, "max_level": 70, "requirements": {}},
                "shark": {"min_level": 70, "max_level": 99, "requirements": {}}
            },
            "woodcutting": {
                "normal": {"min_level": 1, "max_level": 15, "requirements": {}},
                "oak": {"min_level": 15, "max_level": 30, "requirements": {}},
                "willow": {"min_level": 30, "max_level": 45, "requirements": {}},
                "maple": {"min_level": 45, "max_level": 60, "requirements": {}},
                "yew": {"min_level": 60, "max_level": 75, "requirements": {}},
                "magic": {"min_level": 75, "max_level": 99, "requirements": {}}
            },
            "farming": {
                "allotment": {"min_level": 1, "max_level": 30, "requirements": {}},
                "herbs": {"min_level": 30, "max_level": 60, "requirements": {}},
                "trees": {"min_level": 60, "max_level": 85, "requirements": {}},
                "fruit_trees": {"min_level": 85, "max_level": 99, "requirements": {}}
            },
            "runecrafting": {
                "air": {"min_level": 1, "max_level": 11, "requirements": {}},
                "mind": {"min_level": 11, "max_level": 22, "requirements": {}},
                "water": {"min_level": 22, "max_level": 33, "requirements": {}},
                "earth": {"min_level": 33, "max_level": 44, "requirements": {}},
                "fire": {"min_level": 44, "max_level": 55, "requirements": {}},
                "body": {"min_level": 55, "max_level": 66, "requirements": {}},
                "cosmic": {"min_level": 66, "max_level": 77, "requirements": {"quest": "Lost City"}},
                "nature": {"min_level": 77, "max_level": 88, "requirements": {"quest": "Lost City"}},
                "law": {"min_level": 88, "max_level": 95, "requirements": {"quest": "Tears of Guthix"}},
                "death": {"min_level": 95, "max_level": 99, "requirements": {"quest": "Mourning's End Part II"}},
                "blood": {"min_level": 95, "max_level": 99, "requirements": {"quest": "Sins of the Father"}},
                "soul": {"min_level": 95, "max_level": 99, "requirements": {"quest": "Sins of the Father"}}
            }
        }
    
    def save_state(self):
        """Save current XP rate model state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving XP rate model state: {str(e)}")
    
    def get_method_for_skill_level(self, skill: str, level: int) -> Dict:
        """
        Get the best training method for a skill at a given level.
        
        Args:
            skill: Name of the skill
            level: Current level
            
        Returns:
            Dictionary containing method information
        """
        if skill not in self.methods:
            return {"method": None, "xp_per_hour": 0}
        
        # Find the best method for the current level
        best_method = None
        best_xp = 0
        
        for method, info in self.methods[skill].items():
            if level >= info["min_level"] and level <= info["max_level"]:
                xp_rate = self.xp_rates[skill][method]["xp_per_hour"]
                if xp_rate > best_xp:
                    best_method = method
                    best_xp = xp_rate
        
        if best_method:
            return {
                "method": best_method,
                "xp_per_hour": best_xp,
                "requirements": self.methods[skill][best_method]["requirements"]
            }
        
        return {"method": None, "xp_per_hour": 0}
    
    def simulate_training(self, action: str, hours: float) -> Tuple[Dict[str, float], Dict[str, int]]:
        """
        Simulate training for a given action and duration.
        
        Args:
            action: Name of the action
            hours: Duration in hours
            
        Returns:
            Tuple of (xp_gained, items_gained)
        """
        # Parse action to get skill and method
        parts = action.split("_")
        if len(parts) < 2:
            return {}, {}
        
        skill = parts[0]
        method = "_".join(parts[1:])
        
        if skill not in self.xp_rates or method not in self.xp_rates[skill]:
            return {}, {}
        
        # Calculate XP gained
        xp_per_hour = self.xp_rates[skill][method]["xp_per_hour"]
        xp_gained = {skill: xp_per_hour * hours}
        
        # Calculate items gained (if applicable)
        items_gained = {}
        if method in ["cows", "rock_crabs", "ammonite_crabs"]:
            items_gained = {
                "bones": int(hours * 100),
                "cowhide": int(hours * 100) if method == "cows" else 0
            }
        elif method in ["copper", "tin", "iron", "coal", "mithril", "adamantite", "runite"]:
            items_gained = {f"{method}_ore": int(hours * 100)}
        elif method in ["shrimp", "sardine", "herring", "anchovies", "mackerel", "trout", "salmon", "lobster", "shark"]:
            items_gained = {method: int(hours * 100)}
        elif method in ["normal", "oak", "willow", "maple", "yew", "magic"]:
            items_gained = {f"{method}_logs": int(hours * 100)}
        
        # Update session tracking
        self.session_xp_gained[skill] += xp_gained[skill]
        self.session_time_spent[skill] += hours * 3600
        
        for item, amount in items_gained.items():
            if item not in self.session_items_gained[skill]:
                self.session_items_gained[skill][item] = 0
            self.session_items_gained[skill][item] += amount
        
        # Log the training session
        logger.info(f"Trained {skill} for {hours} hours using {method}")
        logger.info(f"Gained {xp_gained[skill]} XP ({xp_per_hour} XP/hr)")
        for item, amount in items_gained.items():
            logger.info(f"Gained {amount} {item}")
        
        return xp_gained, items_gained
    
    def update_best_method(self, skill: str, method: str, xp_rate: float):
        """
        Update the best method for a skill based on observed XP rate.
        
        Args:
            skill: Name of the skill
            method: Name of the method
            xp_rate: Observed XP rate
        """
        if skill not in self.state["best_methods"]:
            self.state["best_methods"][skill] = {}
        
        if method not in self.state["best_methods"][skill] or \
           xp_rate > self.state["best_methods"][skill][method]:
            self.state["best_methods"][skill][method] = xp_rate
            self.save_state()
    
    def get_best_methods(self, skill: str) -> Dict:
        """
        Get the best methods for a skill based on observed XP rates.
        
        Args:
            skill: Name of the skill
            
        Returns:
            Dictionary of methods and their XP rates
        """
        return self.state["best_methods"].get(skill, {})
    
    def get_method_history(self, skill: str, method: str) -> List[Dict]:
        """
        Get the history of XP rates for a method.
        
        Args:
            skill: Name of the skill
            method: Name of the method
            
        Returns:
            List of historical XP rates
        """
        return self.state["method_history"].get(f"{skill}_{method}", [])
    
    def add_method_history(self, skill: str, method: str, xp_rate: float):
        """
        Add an XP rate to the method history.
        
        Args:
            skill: Name of the skill
            method: Name of the method
            xp_rate: Observed XP rate
        """
        key = f"{skill}_{method}"
        if key not in self.state["method_history"]:
            self.state["method_history"][key] = []
        
        self.state["method_history"][key].append({
            "xp_rate": xp_rate,
            "timestamp": time.time()
        })
        
        # Keep only the last 100 entries
        if len(self.state["method_history"][key]) > 100:
            self.state["method_history"][key] = self.state["method_history"][key][-100:]
        
        self.save_state()
    
    def get_session_stats(self) -> Dict:
        """
        Get statistics for the current training session.
        
        Returns:
            Dictionary containing session statistics
        """
        session_duration = time.time() - self.session_start_time
        
        stats = {
            "session_duration": session_duration,
            "skills": {}
        }
        
        for skill in self.session_xp_gained:
            if self.session_time_spent[skill] > 0:
                xp_per_hour = (self.session_xp_gained[skill] / self.session_time_spent[skill]) * 3600
                stats["skills"][skill] = {
                    "xp_gained": self.session_xp_gained[skill],
                    "time_spent": self.session_time_spent[skill],
                    "xp_per_hour": int(xp_per_hour),
                    "items_gained": self.session_items_gained[skill]
                }
        
        return stats
    
    def reset_session(self):
        """Reset the current training session."""
        self.session_start_time = time.time()
        self.session_xp_gained = {skill: 0 for skill in self.xp_rates.keys()}
        self.session_time_spent = {skill: 0 for skill in self.xp_rates.keys()}
        self.session_items_gained = {skill: {} for skill in self.xp_rates.keys()}
        logger.info("Training session reset") 