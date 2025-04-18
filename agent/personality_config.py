"""
Personality Configuration System for RuneGPT
Handles loading and parsing of personality config files
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PersonalityTraits:
    """Represents personality traits that influence agent behavior"""
    tone: str
    motivation: str
    philosophy: str
    risk_tolerance: float
    efficiency_focus: float
    social_preference: float
    exploration_drive: float
    goal_orientation: float

@dataclass
class PersonalityConfig:
    """Configuration for a RuneGPT agent's personality"""
    name: str
    mode: str
    style: List[str]
    playtime_hours_per_day: int
    bond_priority: bool
    personality: List[Dict[str, str]]
    long_term_goals: List[str]
    restrictions: List[str]
    quest_strategy: str
    pvm_style: str
    risk_tolerance: str
    use_guides: bool

class PersonalityConfigManager:
    """Manages personality configurations for RuneGPT agents"""
    
    SUPPORTED_STYLES = {
        "explorer", "sweaty_pvmer", "casual_skiller", "lore_seeker", 
        "pure_pker", "realist", "clue_chaser", "money_maker", 
        "completionist", "collector", "socialite", "hardcore_survivor", 
        "high_risk_rusher", "skiller_pure", "master_quester", 
        "pet_hunter", "speedrunner"
    }
    
    SUPPORTED_MODES = {"ironman", "regular"}
    SUPPORTED_RISK_LEVELS = {"low", "medium", "high"}
    SUPPORTED_QUEST_STRATEGIES = {"follow_guide", "explore", "efficient"}
    SUPPORTED_PVM_STYLES = {"aggressive", "defensive", "balanced"}
    
    def __init__(self, config_dir: str = "config/personalities"):
        """
        Initialize the personality config manager.
        
        Args:
            config_dir: Directory containing personality config files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self.default_config = PersonalityConfig(
            name="DefaultAI",
            mode="regular",
            style=["realist"],
            playtime_hours_per_day=4,
            bond_priority=False,
            personality=[{
                "tone": "balanced",
                "motivation": "Progress steadily through the game",
                "philosophy": "Balance efficiency with enjoyment"
            }],
            long_term_goals=["Reach end-game content"],
            restrictions=[],
            quest_strategy="follow_guide",
            pvm_style="balanced",
            risk_tolerance="medium",
            use_guides=True
        )
    
    def load_config(self, character_name: str) -> PersonalityConfig:
        """
        Load personality configuration for a character.
        
        Args:
            character_name: Name of the character to load config for
            
        Returns:
            PersonalityConfig object for the character
        """
        config_path = self.config_dir / f"{character_name}.txt"
        
        if not config_path.exists():
            logger.warning(f"No config file found for {character_name}, using default")
            return self.default_config
        
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
            
            # Validate and parse config
            return self._parse_config(config_data)
            
        except Exception as e:
            logger.error(f"Error loading config for {character_name}: {e}")
            return self.default_config
    
    def _parse_config(self, data: Dict[str, Any]) -> PersonalityConfig:
        """
        Parse and validate configuration data.
        
        Args:
            data: Raw configuration data
            
        Returns:
            Validated PersonalityConfig object
        """
        # Validate required fields
        required_fields = {
            "name", "mode", "style", "playtime_hours_per_day", 
            "bond_priority", "personality", "long_term_goals", 
            "restrictions", "quest_strategy", "pvm_style", 
            "risk_tolerance", "use_guides"
        }
        
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return self.default_config
        
        # Validate mode
        if data["mode"] not in self.SUPPORTED_MODES:
            logger.warning(f"Invalid mode: {data['mode']}, using regular")
            data["mode"] = "regular"
        
        # Validate styles
        valid_styles = [s for s in data["style"] if s in self.SUPPORTED_STYLES]
        if not valid_styles:
            logger.warning("No valid styles found, using realist")
            valid_styles = ["realist"]
        data["style"] = valid_styles
        
        # Validate playtime
        try:
            playtime = int(data["playtime_hours_per_day"])
            if playtime < 1 or playtime > 24:
                logger.warning("Invalid playtime, using 4 hours")
                playtime = 4
            data["playtime_hours_per_day"] = playtime
        except (ValueError, TypeError):
            logger.warning("Invalid playtime format, using 4 hours")
            data["playtime_hours_per_day"] = 4
        
        # Validate bond priority
        data["bond_priority"] = bool(data["bond_priority"])
        
        # Validate personality
        if not isinstance(data["personality"], list):
            logger.warning("Invalid personality format, using default")
            data["personality"] = self.default_config.personality
        else:
            valid_personality = []
            for p in data["personality"]:
                if all(k in p for k in ["tone", "motivation", "philosophy"]):
                    valid_personality.append(p)
            if not valid_personality:
                logger.warning("No valid personality traits found, using default")
                valid_personality = self.default_config.personality
            data["personality"] = valid_personality
        
        # Validate lists
        for field in ["long_term_goals", "restrictions"]:
            if not isinstance(data[field], list):
                logger.warning(f"Invalid {field} format, using empty list")
                data[field] = []
        
        # Validate quest strategy
        if data["quest_strategy"] not in self.SUPPORTED_QUEST_STRATEGIES:
            logger.warning(f"Invalid quest strategy: {data['quest_strategy']}, using follow_guide")
            data["quest_strategy"] = "follow_guide"
        
        # Validate PVM style
        if data["pvm_style"] not in self.SUPPORTED_PVM_STYLES:
            logger.warning(f"Invalid PVM style: {data['pvm_style']}, using balanced")
            data["pvm_style"] = "balanced"
        
        # Validate risk tolerance
        if data["risk_tolerance"] not in self.SUPPORTED_RISK_LEVELS:
            logger.warning(f"Invalid risk tolerance: {data['risk_tolerance']}, using medium")
            data["risk_tolerance"] = "medium"
        
        # Validate use guides
        data["use_guides"] = bool(data["use_guides"])
        
        return PersonalityConfig(**data)
    
    def save_config(self, config: PersonalityConfig, character_name: str) -> bool:
        """
        Save a personality configuration to file.
        
        Args:
            config: PersonalityConfig object to save
            character_name: Name of the character
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_path = self.config_dir / f"{character_name}.txt"
            
            # Convert config to dictionary
            config_data = {
                "name": config.name,
                "mode": config.mode,
                "style": config.style,
                "playtime_hours_per_day": config.playtime_hours_per_day,
                "bond_priority": config.bond_priority,
                "personality": config.personality,
                "long_term_goals": config.long_term_goals,
                "restrictions": config.restrictions,
                "quest_strategy": config.quest_strategy,
                "pvm_style": config.pvm_style,
                "risk_tolerance": config.risk_tolerance,
                "use_guides": config.use_guides
            }
            
            # Save to file
            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving config for {character_name}: {e}")
            return False
    
    def list_configs(self) -> List[str]:
        """
        List available personality configurations.
        
        Returns:
            List of character names with configs
        """
        configs = []
        for filename in os.listdir(self.config_dir):
            if filename.endswith(".txt"):
                configs.append(filename[:-4])  # Remove .txt extension
        return configs
    
    def create_config(self, name: str, mode: str, style: List[str],
                     playtime_hours: int, bond_priority: bool,
                     personality: List[Dict[str, str]], goals: List[str],
                     restrictions: List[str], quest_strategy: str,
                     pvm_style: str, risk_tolerance: str,
                     use_guides: bool) -> PersonalityConfig:
        """
        Create a new personality configuration.
        
        Args:
            name: Character name
            mode: Game mode (regular, ironman, etc.)
            style: List of playstyle descriptors
            playtime_hours: Hours played per day
            bond_priority: Whether bond maintenance is a priority
            personality: List of personality trait dictionaries
            goals: List of long-term goals
            restrictions: List of self-imposed restrictions
            quest_strategy: Approach to questing
            pvm_style: Combat approach
            risk_tolerance: Risk tolerance level
            use_guides: Whether to use guides
            
        Returns:
            New PersonalityConfig object
        """
        config = PersonalityConfig(
            name=name,
            mode=mode,
            style=style,
            playtime_hours_per_day=playtime_hours,
            bond_priority=bond_priority,
            personality=personality,
            long_term_goals=goals,
            restrictions=restrictions,
            quest_strategy=quest_strategy,
            pvm_style=pvm_style,
            risk_tolerance=risk_tolerance,
            use_guides=use_guides
        )
        
        self.save_config(config, name)
        return config 