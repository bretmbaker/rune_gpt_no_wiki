#!/usr/bin/env python3
"""
Game Loop for RuneGPT
Tracks time, XP, and items while simulating realistic delays
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from .xp_rate_model import XPRateModel

logger = logging.getLogger(__name__)

@dataclass
class GameState:
    """Represents the current state of the game."""
    total_time_played: float = 0.0  # Total time played in hours
    current_action: Optional[str] = None  # Current action being performed
    action_start_time: Optional[float] = None  # When the current action started
    fatigue: float = 0.0  # Current fatigue level (0-100)
    session_stats: Dict = None  # Statistics for the current session
    
    def __post_init__(self):
        if self.session_stats is None:
            self.session_stats = {
                "xp_gained": {},
                "items_gained": {},
                "actions_completed": 0,
                "deaths": 0,
                "quests_completed": 0,
                "areas_visited": set()
            }

class GameLoop:
    """
    Manages the game loop, tracking time, XP, and items.
    Simulates realistic delays and fatigue.
    """
    
    def __init__(self, state_dir: Path):
        """
        Initialize the game loop.
        
        Args:
            state_dir: Directory for saving state
        """
        self.state_dir = state_dir
        self.state_file = state_dir / "game_loop.json"
        self.xp_model = XPRateModel(state_dir)
        self.state = self._load_state()
        
        # Constants
        self.FATIGUE_RATE = 5.0  # Fatigue points per hour
        self.REST_RATE = 10.0  # Fatigue recovery per hour
        self.MAX_FATIGUE = 100.0
        self.FATIGUE_XP_PENALTY = 0.5  # 50% XP reduction at max fatigue
        
        # Start time tracking
        self.last_update = time.time()
    
    def _load_state(self) -> GameState:
        """Load game state from file or create default."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Convert session_stats["areas_visited"] back to set
                    if "areas_visited" in data["session_stats"]:
                        data["session_stats"]["areas_visited"] = set(data["session_stats"]["areas_visited"])
                    return GameState(**data)
            except Exception as e:
                logger.error(f"Error loading game state: {str(e)}")
                return GameState()
        return GameState()
    
    def save_state(self):
        """Save current game state to file."""
        try:
            # Convert session_stats["areas_visited"] to list for JSON serialization
            state_dict = asdict(self.state)
            state_dict["session_stats"]["areas_visited"] = list(state_dict["session_stats"]["areas_visited"])
            
            with open(self.state_file, 'w') as f:
                json.dump(state_dict, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving game state: {str(e)}")
    
    def _update_time(self):
        """Update time played and fatigue."""
        current_time = time.time()
        time_diff = (current_time - self.last_update) / 3600  # Convert to hours
        self.last_update = current_time
        
        # Update total time played
        self.state.total_time_played += time_diff
        
        # Update fatigue if performing an action
        if self.state.current_action:
            self.state.fatigue = min(
                self.MAX_FATIGUE,
                self.state.fatigue + (time_diff * self.FATIGUE_RATE)
            )
    
    def start_action(self, action: str) -> bool:
        """
        Start performing an action.
        
        Args:
            action: Name of the action to perform
            
        Returns:
            True if action started successfully, False otherwise
        """
        # Check if we can perform the action
        if not self.can_perform_action(action):
            return False
        
        # Update time and fatigue
        self._update_time()
        
        # Start the action
        self.state.current_action = action
        self.state.action_start_time = time.time()
        
        logger.info(f"Started action: {action}")
        return True
    
    def end_action(self) -> Tuple[Dict[str, float], Dict[str, int]]:
        """
        End the current action and calculate rewards.
        
        Returns:
            Tuple of (xp_gained, items_gained)
        """
        if not self.state.current_action:
            return {}, {}
        
        # Update time and fatigue
        self._update_time()
        
        # Calculate action duration
        duration = (time.time() - self.state.action_start_time) / 3600  # Convert to hours
        
        # Calculate XP and items gained
        xp_gained, items_gained = self.xp_model.simulate_training(
            self.state.current_action,
            duration
        )
        
        # Apply fatigue penalty
        if self.state.fatigue >= self.MAX_FATIGUE:
            xp_gained = {skill: xp * self.FATIGUE_XP_PENALTY for skill, xp in xp_gained.items()}
        
        # Update session stats
        self.state.session_stats["actions_completed"] += 1
        for skill, xp in xp_gained.items():
            if skill not in self.state.session_stats["xp_gained"]:
                self.state.session_stats["xp_gained"][skill] = 0
            self.state.session_stats["xp_gained"][skill] += xp
        
        for item, amount in items_gained.items():
            if item not in self.state.session_stats["items_gained"]:
                self.state.session_stats["items_gained"][item] = 0
            self.state.session_stats["items_gained"][item] += amount
        
        # Clear current action
        action = self.state.current_action
        self.state.current_action = None
        self.state.action_start_time = None
        
        logger.info(f"Completed action: {action}")
        logger.info(f"Gained XP: {xp_gained}")
        logger.info(f"Gained items: {items_gained}")
        
        return xp_gained, items_gained
    
    def can_perform_action(self, action: str) -> bool:
        """
        Check if an action can be performed.
        
        Args:
            action: Name of the action to check
            
        Returns:
            True if action can be performed, False otherwise
        """
        # Update time and fatigue
        self._update_time()
        
        # Check if we're too fatigued
        if self.state.fatigue >= self.MAX_FATIGUE:
            logger.warning("Too fatigued to perform action")
            return False
        
        # Check if we're already performing an action
        if self.state.current_action:
            logger.warning("Already performing an action")
            return False
        
        return True
    
    def rest(self, hours: float) -> float:
        """
        Rest to recover fatigue.
        
        Args:
            hours: Hours to rest for
            
        Returns:
            Amount of fatigue recovered
        """
        # Update time and fatigue
        self._update_time()
        
        # Calculate fatigue recovery
        recovery = min(
            hours * self.REST_RATE,
            self.state.fatigue
        )
        
        # Apply recovery
        self.state.fatigue = max(0, self.state.fatigue - recovery)
        
        logger.info(f"Rested for {hours} hours, recovered {recovery} fatigue")
        return recovery
    
    def add_area_visited(self, area: str):
        """
        Add an area to the list of visited areas.
        
        Args:
            area: Name of the area visited
        """
        self.state.session_stats["areas_visited"].add(area)
        logger.info(f"Visited new area: {area}")
    
    def add_quest_completed(self, quest: str):
        """
        Add a quest to the list of completed quests.
        
        Args:
            quest: Name of the quest completed
        """
        self.state.session_stats["quests_completed"] += 1
        logger.info(f"Completed quest: {quest}")
    
    def add_death(self):
        """Record a player death."""
        self.state.session_stats["deaths"] += 1
        logger.info("Player died")
    
    def get_session_stats(self) -> Dict:
        """
        Get statistics for the current session.
        
        Returns:
            Dictionary containing session statistics
        """
        # Update time and fatigue
        self._update_time()
        
        # Convert areas_visited to list for easier handling
        stats = self.state.session_stats.copy()
        stats["areas_visited"] = list(stats["areas_visited"])
        
        return stats
    
    def get_current_action(self) -> Optional[str]:
        """
        Get the current action being performed.
        
        Returns:
            Name of the current action, or None if no action
        """
        return self.state.current_action
    
    def get_fatigue(self) -> float:
        """
        Get the current fatigue level.
        
        Returns:
            Current fatigue level (0-100)
        """
        # Update time and fatigue
        self._update_time()
        return self.state.fatigue
    
    def get_time_played(self) -> float:
        """
        Get the total time played.
        
        Returns:
            Total time played in hours
        """
        # Update time and fatigue
        self._update_time()
        return self.state.total_time_played 