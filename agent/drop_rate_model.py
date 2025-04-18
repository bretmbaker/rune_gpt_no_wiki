"""
Drop Rate Model for RuneGPT
Simulates realistic OSRS-style drop behavior and tracks rare rewards
"""

import re
import json
import random
import logging
import math
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DropGrind:
    """Represents a rare drop grind being tracked"""
    name: str
    location: str
    rate: str
    attempts: int
    obtained: bool
    start_time: float
    last_attempt_time: float
    milestones: List[Dict[str, Any]]
    patience_score: float = 0.5  # 0.0 to 1.0, how patient the agent is with this grind

class DropRateModel:
    """Manages drop rates, rare rewards, and grind tracking"""
    
    def __init__(self, state_dir: str):
        """
        Initialize the drop rate model.
        
        Args:
            state_dir: Directory for saving state
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create drop grinds state
        self.drop_grinds: Dict[str, DropGrind] = {}
        self._load_state()
        
        # Load drop rates from wiki data
        self.drop_rates = self._load_drop_rates()
        
        # Initialize random number generator
        self.rng = random.Random()
    
    def _load_state(self) -> None:
        """Load drop grinds state from file"""
        state_file = self.state_dir / "drop_grinds.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    data = json.load(f)
                    for name, grind_data in data.items():
                        self.drop_grinds[name] = DropGrind(
                            name=name,
                            location=grind_data["location"],
                            rate=grind_data["rate"],
                            attempts=grind_data["attempts"],
                            obtained=grind_data["obtained"],
                            start_time=grind_data.get("start_time", 0.0),
                            last_attempt_time=grind_data.get("last_attempt_time", 0.0),
                            milestones=grind_data.get("milestones", []),
                            patience_score=grind_data.get("patience_score", 0.5)
                        )
                logger.info(f"Loaded {len(self.drop_grinds)} drop grinds")
            except Exception as e:
                logger.error(f"Error loading drop grinds state: {str(e)}")
    
    def save_state(self) -> None:
        """Save drop grinds state to file"""
        state_file = self.state_dir / "drop_grinds.json"
        try:
            data = {}
            for name, grind in self.drop_grinds.items():
                data[name] = {
                    "location": grind.location,
                    "rate": grind.rate,
                    "attempts": grind.attempts,
                    "obtained": grind.obtained,
                    "start_time": grind.start_time,
                    "last_attempt_time": grind.last_attempt_time,
                    "milestones": grind.milestones,
                    "patience_score": grind.patience_score
                }
            
            with open(state_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self.drop_grinds)} drop grinds")
        except Exception as e:
            logger.error(f"Error saving drop grinds state: {str(e)}")
    
    def _load_drop_rates(self) -> Dict[str, Dict[str, Any]]:
        """Load drop rates from wiki data files"""
        drop_rates = {}
        
        # Define paths to wiki data
        wiki_paths = [
            Path("wiki_data") / "bestiary",
            Path("wiki_data") / "bestiary_f2p",
            Path("wiki_data") / "pets",
            Path("wiki_data") / "collection_log"
        ]
        
        # Load drop rates from each path
        for path in wiki_paths:
            if path.exists():
                # Load metadata.json
                metadata_file = path / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            
                        # Load txt files referenced in metadata
                        txt_dir = path / "txt"
                        if txt_dir.exists():
                            for name, data in metadata.items():
                                txt_file = txt_dir / data["txt"].split("/")[-1]
                                if txt_file.exists():
                                    with open(txt_file, 'r') as f:
                                        content = f.read()
                                        
                                        # Extract drop rate from content
                                        drop_rate = self._extract_drop_rate(content)
                                        if drop_rate:
                                            drop_rates[name.lower()] = {
                                                "rate": drop_rate,
                                                "source": path.name,
                                                "category": "pet" if "pet" in name.lower() else "drop",
                                                "type": data.get("type", "general")
                                            }
                    except Exception as e:
                        logger.error(f"Error loading drop rates from {path}: {str(e)}")
        
        # Add hardcoded common drop rates if wiki data is missing
        if not drop_rates:
            drop_rates = {
                "beaver_pet": {"rate": "1/5000", "source": "woodcutting", "category": "pet", "type": "pet"},
                "heron_pet": {"rate": "1/5000", "source": "fishing", "category": "pet", "type": "pet"},
                "rocky_pet": {"rate": "1/5000", "source": "thieving", "category": "pet", "type": "pet"},
                "phoenix_pet": {"rate": "1/5000", "source": "wintertodt", "category": "pet", "type": "pet"},
                "dagannoth_rex_pet": {"rate": "1/5000", "source": "dagannoth_kings", "category": "pet", "type": "pet"},
                "dagannoth_prime_pet": {"rate": "1/5000", "source": "dagannoth_kings", "category": "pet", "type": "pet"},
                "dagannoth_supreme_pet": {"rate": "1/5000", "source": "dagannoth_kings", "category": "pet", "type": "pet"},
                "abyssal_orphan": {"rate": "1/2560", "source": "abyssal_sire", "category": "pet", "type": "pet"},
                "baby_mole": {"rate": "1/3000", "source": "giant_mole", "category": "pet", "type": "pet"},
                "callisto_cub": {"rate": "1/2000", "source": "callisto", "category": "pet", "type": "pet"},
                "chaos_ele_pet": {"rate": "1/300", "source": "chaos_elemental", "category": "pet", "type": "pet"},
                "chompy_chick": {"rate": "1/500", "source": "chompy_bird", "category": "pet", "type": "pet"},
                "corporeal_puppy": {"rate": "1/5000", "source": "corporeal_beast", "category": "pet", "type": "pet"},
                "drake_pet": {"rate": "1/5000", "source": "drakes", "category": "pet", "type": "pet"},
                "dust_pet": {"rate": "1/5000", "source": "dust_devils", "category": "pet", "type": "pet"},
                "fox_pet": {"rate": "1/5000", "source": "fox", "category": "pet", "type": "pet"},
                "gargoyle_pet": {"rate": "1/5000", "source": "gargoyles", "category": "pet", "type": "pet"},
                "hellpuppy": {"rate": "1/5000", "source": "cerberus", "category": "pet", "type": "pet"},
                "herbi_pet": {"rate": "1/6500", "source": "herbiboar", "category": "pet", "type": "pet"},
                "kalphite_princess": {"rate": "1/3000", "source": "kalphite_queen", "category": "pet", "type": "pet"},
                "kraken_pet": {"rate": "1/3000", "source": "kraken", "category": "pet", "type": "pet"},
                "lil_creator": {"rate": "1/5000", "source": "hespori", "category": "pet", "type": "pet"},
                "lil_zik": {"rate": "1/650", "source": "chambers_of_xeric", "category": "pet", "type": "pet"},
                "mole_pet": {"rate": "1/3000", "source": "giant_mole", "category": "pet", "type": "pet"},
                "noon_pet": {"rate": "1/3000", "source": "grotesque_guardians", "category": "pet", "type": "pet"},
                "olmlet": {"rate": "1/53", "source": "chambers_of_xeric", "category": "pet", "type": "pet"},
                "pet_smoke_devil": {"rate": "1/3000", "source": "thermonuclear_smoke_devil", "category": "pet", "type": "pet"},
                "pet_snakeling": {"rate": "1/4000", "source": "zulrah", "category": "pet", "type": "pet"},
                "prince_black_dragon": {"rate": "1/3000", "source": "king_black_dragon", "category": "pet", "type": "pet"},
                "rune_dragon_pet": {"rate": "1/5000", "source": "rune_dragons", "category": "pet", "type": "pet"},
                "scorpia_pet": {"rate": "1/2000", "source": "scorpia", "category": "pet", "type": "pet"},
                "skotos_pet": {"rate": "1/65", "source": "skotizo", "category": "pet", "type": "pet"},
                "snakeling_pet": {"rate": "1/4000", "source": "zulrah", "category": "pet", "type": "pet"},
                "tumeken_pet": {"rate": "1/5000", "source": "tombs_of_amascut", "category": "pet", "type": "pet"},
                "venenatis_spiderling": {"rate": "1/2000", "source": "venenatis", "category": "pet", "type": "pet"},
                "vetion_jr": {"rate": "1/2000", "source": "vetion", "category": "pet", "type": "pet"},
                "vorki_pet": {"rate": "1/3000", "source": "vorkath", "category": "pet", "type": "pet"},
                "wyrm_pet": {"rate": "1/5000", "source": "wyrms", "category": "pet", "type": "pet"},
                "youngllef_pet": {"rate": "1/1000", "source": "gauntlet", "category": "pet", "type": "pet"},
                "zilyana_pet": {"rate": "1/5000", "source": "commander_zilyana", "category": "pet", "type": "pet"},
                "zuk_pet": {"rate": "1/5000", "source": "tzKal-Zuk", "category": "pet", "type": "pet"}
            }
        
        logger.info(f"Loaded {len(drop_rates)} drop rates")
        return drop_rates
    
    def _extract_drop_rate(self, content: str) -> Optional[str]:
        """Extract drop rate from content."""
        try:
            # Look for common drop rate patterns
            patterns = [
                r"(\d+/\d+) \(~[\d.]+%\) chance",  # e.g., "1/5000 (~0.02%) chance"
                r"(\d+/\d+) chance",  # e.g., "1/5000 chance"
                r"(\d+/\d+) \(~[\d.]+%\)",  # e.g., "1/5000 (~0.02%)"
                r"(\d+/\d+)",  # e.g., "1/5000"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    return matches[0]
            
            return None
        except Exception as e:
            logger.error(f"Error extracting drop rate: {str(e)}")
            return None
    
    def parse_drop_rate(self, rate_str: str) -> float:
        """
        Parse a drop rate string into a float probability.
        
        Args:
            rate_str: Drop rate string (e.g., "1/2000")
            
        Returns:
            Float probability
        """
        try:
            # Handle common formats
            if "/" in rate_str:
                parts = rate_str.split("/")
                if len(parts) == 2:
                    return float(parts[0]) / float(parts[1])
            
            # Handle percentage format
            if "%" in rate_str:
                return float(rate_str.replace("%", "")) / 100.0
            
            # Handle decimal format
            return float(rate_str)
        except Exception as e:
            logger.error(f"Error parsing drop rate '{rate_str}': {str(e)}")
            return 0.0
    
    def calculate_probability(self, chance: str, attempts: int) -> float:
        """
        Calculate the probability of getting a drop after a certain number of attempts.
        
        Args:
            chance: Drop rate string (e.g., "1/2000")
            attempts: Number of attempts
            
        Returns:
            Probability of getting the drop after the attempts
        """
        try:
            # Parse the drop rate
            drop_rate = self.parse_drop_rate(chance)
            
            # Calculate probability using the formula: P = 1 - (1 - p)^n
            # where p is the drop rate and n is the number of attempts
            probability = 1 - (1 - drop_rate) ** attempts
            
            return probability
        except Exception as e:
            logger.error(f"Error calculating probability for '{chance}' after {attempts} attempts: {str(e)}")
            return 0.0
    
    def simulate_drop(self, chance: str, attempts: int) -> Dict[str, Any]:
        """
        Simulate a drop based on the given chance and number of attempts.
        
        Args:
            chance: Drop rate string (e.g., "1/2000")
            attempts: Number of attempts
            
        Returns:
            Dictionary with simulation results
        """
        try:
            # Parse the drop rate
            drop_rate = self.parse_drop_rate(chance)
            
            # Calculate expected attempts (average)
            expected_attempts = int(1 / drop_rate) if drop_rate > 0 else 0
            
            # Simulate the drop
            success = False
            for _ in range(attempts):
                if self.rng.random() < drop_rate:
                    success = True
                    break
            
            # Calculate probability of getting the drop
            probability = self.calculate_probability(chance, attempts)
            
            return {
                "success": success,
                "total_attempts": attempts,
                "drop_rate": drop_rate,
                "expected_attempts": expected_attempts,
                "probability": probability,
                "luck_factor": attempts / expected_attempts if expected_attempts > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error simulating drop for '{chance}' after {attempts} attempts: {str(e)}")
            return {
                "success": False,
                "total_attempts": attempts,
                "drop_rate": 0.0,
                "expected_attempts": 0,
                "probability": 0.0,
                "luck_factor": 0.0,
                "error": str(e)
            }
    
    def start_grind(self, name: str, location: str, rate: str) -> bool:
        """
        Start tracking a new drop grind.
        
        Args:
            name: Name of the drop (e.g., "beaver_pet")
            location: Location where the drop can be obtained
            rate: Drop rate string (e.g., "1/5000")
            
        Returns:
            True if the grind was started, False otherwise
        """
        try:
            # Check if the grind already exists
            if name in self.drop_grinds:
                logger.warning(f"Grind '{name}' already exists")
                return False
            
            # Create a new grind
            import time
            current_time = time.time()
            
            self.drop_grinds[name] = DropGrind(
                name=name,
                location=location,
                rate=rate,
                attempts=0,
                obtained=False,
                start_time=current_time,
                last_attempt_time=current_time,
                milestones=[],
                patience_score=0.5
            )
            
            # Save state
            self.save_state()
            
            logger.info(f"Started new grind: {name} at {location} with rate {rate}")
            return True
        except Exception as e:
            logger.error(f"Error starting grind '{name}': {str(e)}")
            return False
    
    def update_grind(self, name: str, attempts: int = 1, obtained: bool = False) -> Dict[str, Any]:
        """
        Update a drop grind with new attempts.
        
        Args:
            name: Name of the drop grind
            attempts: Number of new attempts to add
            obtained: Whether the drop was obtained
            
        Returns:
            Dictionary with updated grind information
        """
        try:
            # Check if the grind exists
            if name not in self.drop_grinds:
                logger.warning(f"Grind '{name}' does not exist")
                return {"error": f"Grind '{name}' does not exist"}
            
            # Get the grind
            grind = self.drop_grinds[name]
            
            # Update the grind
            import time
            current_time = time.time()
            
            # Update attempts
            grind.attempts += attempts
            grind.last_attempt_time = current_time
            
            # Check if the drop was obtained
            if obtained:
                grind.obtained = True
            
            # Calculate expected attempts
            expected_attempts = int(1 / self.parse_drop_rate(grind.rate))
            
            # Calculate luck factor
            luck_factor = grind.attempts / expected_attempts if expected_attempts > 0 else 0
            
            # Check for milestones
            milestone = None
            if grind.attempts % 1000 == 0 or grind.attempts == expected_attempts or obtained:
                milestone = {
                    "attempts": grind.attempts,
                    "expected_attempts": expected_attempts,
                    "luck_factor": luck_factor,
                    "obtained": obtained,
                    "time": current_time
                }
                grind.milestones.append(milestone)
            
            # Update patience score based on attempts vs expected
            if luck_factor > 2.0:  # Very unlucky
                grind.patience_score = max(0.0, grind.patience_score - 0.1)
            elif luck_factor < 0.5:  # Very lucky
                grind.patience_score = min(1.0, grind.patience_score + 0.1)
            
            # Save state
            self.save_state()
            
            # Return updated grind information
            return {
                "name": grind.name,
                "location": grind.location,
                "rate": grind.rate,
                "attempts": grind.attempts,
                "obtained": grind.obtained,
                "expected_attempts": expected_attempts,
                "luck_factor": luck_factor,
                "patience_score": grind.patience_score,
                "milestone": milestone
            }
        except Exception as e:
            logger.error(f"Error updating grind '{name}': {str(e)}")
            return {"error": str(e)}
    
    def get_grind(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a drop grind.
        
        Args:
            name: Name of the drop grind
            
        Returns:
            Dictionary with grind information, or None if not found
        """
        try:
            # Check if the grind exists
            if name not in self.drop_grinds:
                logger.warning(f"Grind '{name}' does not exist")
                return None
            
            # Get the grind
            grind = self.drop_grinds[name]
            
            # Calculate expected attempts
            expected_attempts = int(1 / self.parse_drop_rate(grind.rate))
            
            # Calculate luck factor
            luck_factor = grind.attempts / expected_attempts if expected_attempts > 0 else 0
            
            # Return grind information
            return {
                "name": grind.name,
                "location": grind.location,
                "rate": grind.rate,
                "attempts": grind.attempts,
                "obtained": grind.obtained,
                "expected_attempts": expected_attempts,
                "luck_factor": luck_factor,
                "patience_score": grind.patience_score,
                "milestones": grind.milestones
            }
        except Exception as e:
            logger.error(f"Error getting grind '{name}': {str(e)}")
            return None
    
    def get_all_grinds(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all drop grinds.
        
        Returns:
            Dictionary with all grind information
        """
        try:
            grinds = {}
            for name, grind in self.drop_grinds.items():
                grinds[name] = self.get_grind(name)
            return grinds
        except Exception as e:
            logger.error(f"Error getting all grinds: {str(e)}")
            return {}
    
    def should_continue_grind(self, name: str) -> Dict[str, Any]:
        """
        Determine if the agent should continue a grind based on patience and luck.
        
        Args:
            name: Name of the drop grind
            
        Returns:
            Dictionary with decision information
        """
        try:
            # Check if the grind exists
            if name not in self.drop_grinds:
                logger.warning(f"Grind '{name}' does not exist")
                return {"continue": False, "reason": f"Grind '{name}' does not exist"}
            
            # Get the grind
            grind = self.drop_grinds[name]
            
            # If the drop is already obtained, don't continue
            if grind.obtained:
                return {"continue": False, "reason": "Drop already obtained"}
            
            # Calculate expected attempts
            expected_attempts = int(1 / self.parse_drop_rate(grind.rate))
            
            # Calculate luck factor
            luck_factor = grind.attempts / expected_attempts if expected_attempts > 0 else 0
            
            # Determine if the agent should continue based on patience and luck
            if luck_factor > 3.0 and grind.patience_score < 0.3:
                # Very unlucky and low patience
                return {"continue": False, "reason": "Too unlucky and low patience"}
            elif luck_factor > 5.0:
                # Extremely unlucky
                return {"continue": False, "reason": "Extremely unlucky"}
            elif luck_factor < 0.2:
                # Very lucky, might want to continue
                return {"continue": True, "reason": "Very lucky, might get another"}
            else:
                # Normal luck, continue based on patience
                return {"continue": grind.patience_score > 0.3, "reason": "Based on patience score"}
        except Exception as e:
            logger.error(f"Error deciding whether to continue grind '{name}': {str(e)}")
            return {"continue": False, "reason": str(e)}
    
    def get_drop_rate(self, name: str) -> Optional[str]:
        """
        Get the drop rate for a specific drop.
        
        Args:
            name: Name of the drop
            
        Returns:
            Drop rate string, or None if not found
        """
        try:
            # Check if the drop exists in the drop rates
            if name.lower() in self.drop_rates:
                return self.drop_rates[name.lower()]["rate"]
            
            # Check if the drop exists in the drop grinds
            if name in self.drop_grinds:
                return self.drop_grinds[name].rate
            
            logger.warning(f"Drop rate for '{name}' not found")
            return None
        except Exception as e:
            logger.error(f"Error getting drop rate for '{name}': {str(e)}")
            return None 