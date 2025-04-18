# skills.py - Tracks skill levels and experience

from typing import Dict, List, Optional

class Skills:
    """
    Tracks the agent's skill levels and experience points.
    """
    def __init__(self):
        # Initialize all skills to level 1
        self.skills = {
            "attack": {"level": 1, "xp": 0},
            "strength": {"level": 1, "xp": 0},
            "defence": {"level": 1, "xp": 0},
            "ranged": {"level": 1, "xp": 0},
            "prayer": {"level": 1, "xp": 0},
            "magic": {"level": 1, "xp": 0},
            "runecrafting": {"level": 1, "xp": 0},
            "construction": {"level": 1, "xp": 0},
            "hitpoints": {"level": 10, "xp": 1154},  # Start with 10 HP
            "agility": {"level": 1, "xp": 0},
            "herblore": {"level": 1, "xp": 0},
            "thieving": {"level": 1, "xp": 0},
            "crafting": {"level": 1, "xp": 0},
            "fletching": {"level": 1, "xp": 0},
            "slayer": {"level": 1, "xp": 0},
            "hunter": {"level": 1, "xp": 0},
            "mining": {"level": 1, "xp": 0},
            "smithing": {"level": 1, "xp": 0},
            "fishing": {"level": 1, "xp": 0},
            "cooking": {"level": 1, "xp": 0},
            "firemaking": {"level": 1, "xp": 0},
            "woodcutting": {"level": 1, "xp": 0},
            "farming": {"level": 1, "xp": 0}
        }
    
    def get_level(self, skill: str) -> int:
        """Get the current level of a skill."""
        return self.skills[skill.lower()]["level"]
    
    def get_xp(self, skill: str) -> int:
        """Get the current XP of a skill."""
        return self.skills[skill.lower()]["xp"]
    
    def add_xp(self, skill: str, xp: int):
        """
        Add experience points to a skill and update its level.
        
        Args:
            skill: The skill to add XP to
            xp: Amount of XP to add
        """
        skill = skill.lower()
        if skill not in self.skills:
            return
        
        # Add XP
        self.skills[skill]["xp"] += xp
        
        # Calculate new level
        new_level = self._xp_to_level(self.skills[skill]["xp"])
        
        # Update level if it increased
        if new_level > self.skills[skill]["level"]:
            old_level = self.skills[skill]["level"]
            self.skills[skill]["level"] = new_level
            print(f"[Skills]: {skill.capitalize()} level increased from {old_level} to {new_level}!")
    
    def _xp_to_level(self, xp: int) -> int:
        """
        Convert XP to level using the OSRS formula.
        
        Args:
            xp: Experience points
            
        Returns:
            Level corresponding to the XP
        """
        level = 1
        for i in range(1, 100):  # Max level is 99
            if xp < self._level_to_xp(i):
                break
            level = i
        return level
    
    def _level_to_xp(self, level: int) -> int:
        """
        Convert level to XP using the OSRS formula.
        
        Args:
            level: Level to convert
            
        Returns:
            XP required for the level
        """
        total = 0
        for i in range(1, level):
            total += int(i + 300 * (2 ** (i / 7.0)))
        return total // 4
    
    def print_status(self):
        """Print the current skill levels."""
        print("\n[RuneGPT Skills]")
        for skill, data in self.skills.items():
            print(f"{skill.capitalize()}: Level {data['level']} ({data['xp']} XP)")
        print("-" * 50)

    def get_state(self) -> dict:
        """
        Get a serializable state representation of all skills.
        
        Returns:
            Dictionary containing all skill levels and experience points
        """
        return self.skills.copy()
    
    def load_state(self, state: dict):
        """
        Load skills state from a dictionary.
        
        Args:
            state: Dictionary containing skill levels and experience points
        """
        for skill, data in state.items():
            if skill in self.skills:
                self.skills[skill] = data.copy()

# Create a global skills instance
skills = Skills() 