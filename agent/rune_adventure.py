#!/usr/bin/env python3
"""
RuneGPT Adventure - A lightweight OSRS gameplay simulator
Starts from Tutorial Island and progresses through the game
"""

import os
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("narrative.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("narrative")

class RuneAdventure:
    """Main game controller for RuneGPT Adventure"""
    
    def __init__(self, session_id: Optional[str] = None, state_dir: str = "state"):
        """Initialize a new game session"""
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        # Generate or use provided session ID
        self.session_id = session_id or f"Player_{uuid.uuid4().hex[:8]}"
        self.session_dir = self.state_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        
        # Initialize game state
        self.player = self._init_player()
        self.inventory = []
        self.location = "Tutorial Island"
        self.tutorial_steps = self._init_tutorial_steps()
        self.current_step = 0
        self.game_start_time = datetime.now()
        self.last_action_time = time.time()
        self.memory_log = []
        
        # Load existing state if available
        self.load_state()
        
        logger.info("=== Starting New RuneGPT Adventure Session ===")
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Player: {self.player['name']}")
        logger.info(f"Location: {self.location}")
        logger.info("Beginning Tutorial Island experience...")

    def _init_player(self) -> Dict[str, Any]:
        """Initialize a new player character"""
        return {
            "name": "RuneGPT",
            "skills": {
                "attack": 1,
                "strength": 1,
                "defence": 1,
                "ranged": 1,
                "prayer": 1,
                "magic": 1,
                "runecraft": 1,
                "hitpoints": 10,
                "crafting": 1,
                "mining": 1,
                "smithing": 1,
                "fishing": 1,
                "cooking": 1,
                "firemaking": 1,
                "woodcutting": 1,
                "agility": 1,
                "herblore": 1,
                "thieving": 1,
                "fletching": 1,
                "slayer": 1,
                "farming": 1,
                "construction": 1,
                "hunter": 1
            },
            "quest_points": 0,
            "total_level": 23,
            "combat_level": 3
        }

    def _init_tutorial_steps(self) -> List[Dict[str, Any]]:
        """Initialize Tutorial Island steps"""
        return [
            {
                "name": "Starting Out",
                "description": "Meet your guide and learn the basics",
                "completed": False,
                "location": "Tutorial Island - Starting Room"
            },
            {
                "name": "Survival Expert",
                "description": "Learn about survival skills and cooking",
                "completed": False,
                "location": "Tutorial Island - Survival Expert"
            },
            {
                "name": "Master Chef",
                "description": "Learn to cook food",
                "completed": False,
                "location": "Tutorial Island - Kitchen"
            },
            {
                "name": "Quest Guide",
                "description": "Learn about quests and the quest journal",
                "completed": False,
                "location": "Tutorial Island - Quest Guide"
            },
            {
                "name": "Mining Instructor",
                "description": "Learn about mining and smithing",
                "completed": False,
                "location": "Tutorial Island - Mining Area"
            },
            {
                "name": "Combat Instructor",
                "description": "Learn about combat and weapons",
                "completed": False,
                "location": "Tutorial Island - Combat Area"
            },
            {
                "name": "Banker",
                "description": "Learn about banking and managing items",
                "completed": False,
                "location": "Tutorial Island - Bank"
            },
            {
                "name": "Account Guide",
                "description": "Learn about account security and settings",
                "completed": False,
                "location": "Tutorial Island - Account Guide"
            }
        ]

    def load_state(self) -> None:
        """Load game state from files"""
        try:
            state_file = self.session_dir / "game_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.player = state.get('player', self.player)
                    self.inventory = state.get('inventory', [])
                    self.location = state.get('location', "Tutorial Island")
                    self.tutorial_steps = state.get('tutorial_steps', self.tutorial_steps)
                    self.current_step = state.get('current_step', 0)
                    self.memory_log = state.get('memory_log', [])
                    logger.info(f"Loaded existing game state for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            logger.info("Starting fresh game state")

    def save_state(self) -> None:
        """Save current game state to files"""
        try:
            state = {
                'player': self.player,
                'inventory': self.inventory,
                'location': self.location,
                'tutorial_steps': self.tutorial_steps,
                'current_step': self.current_step,
                'memory_log': self.memory_log,
                'last_save': datetime.now().isoformat()
            }
            
            with open(self.session_dir / "game_state.json", 'w') as f:
                json.dump(state, f, indent=2)
            logger.info("Game state saved successfully")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def log_memory(self, action: str, details: str) -> None:
        """Log a memory of an action"""
        memory_entry = {
            'timestamp': time.time(),
            'action': action,
            'details': details,
            'location': self.location
        }
        self.memory_log.append(memory_entry)
        self.last_action_time = time.time()
        self.save_state()

    def progress_tutorial(self) -> None:
        """Progress through Tutorial Island"""
        if self.current_step >= len(self.tutorial_steps):
            logger.info("Tutorial Island completed!")
            return
            
        current = self.tutorial_steps[self.current_step]
        logger.info(f"\n=== Tutorial Step {self.current_step + 1}: {current['name']} ===")
        logger.info(f"Location: {current['location']}")
        logger.info(f"Task: {current['description']}")
        
        # Log the action
        self.log_memory(
            f"tutorial_step_{self.current_step + 1}",
            f"Completed {current['name']} at {current['location']}"
        )
        
        # Simulate completing the step
        time.sleep(2)  # Brief pause for readability
        current['completed'] = True
        self.current_step += 1
        self.save_state()
        
        if self.current_step < len(self.tutorial_steps):
            next_step = self.tutorial_steps[self.current_step]
            logger.info(f"Moving to next step: {next_step['name']}")
            logger.info(f"New location: {next_step['location']}")
        else:
            logger.info("Congratulations! You have completed Tutorial Island!")
            logger.info("You are now ready to begin your adventure in Gielinor!")

    def get_current_state(self) -> Dict[str, Any]:
        """Get current game state for external access"""
        return {
            "session_id": self.session_id,
            "player": self.player,
            "inventory": self.inventory,
            "location": self.location,
            "tutorial_progress": {
                "current_step": self.current_step,
                "total_steps": len(self.tutorial_steps),
                "completed_steps": sum(1 for step in self.tutorial_steps if step['completed'])
            },
            "session_time": str(datetime.now() - self.game_start_time),
            "last_action": self.memory_log[-1] if self.memory_log else None
        }

def main():
    """Main entry point for RuneGPT Adventure"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RuneGPT Adventure - OSRS Gameplay Simulator')
    parser.add_argument('--session', help='Session ID to resume', default=None)
    args = parser.parse_args()
    
    try:
        # Initialize game
        game = RuneAdventure(session_id=args.session)
        
        # Progress through tutorial
        while game.current_step < len(game.tutorial_steps):
            game.progress_tutorial()
            time.sleep(1)  # Brief pause between steps
            
        logger.info("\n=== Tutorial Island Complete ===")
        logger.info("You are now ready to begin your adventure!")
        logger.info("Use conversation_cli.py to interact with your character")
        
    except KeyboardInterrupt:
        logger.info("\nGame session interrupted by user")
        game.save_state()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if 'game' in locals():
            game.save_state()

if __name__ == "__main__":
    main() 