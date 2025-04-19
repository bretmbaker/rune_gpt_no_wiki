#!/usr/bin/env python3
"""
RuneGPT - OSRS AI Agent (Sandbox)
Core boot for Tutorial Island interaction sandbox with stripped components.
"""

import os
import time
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional
import random

from agent.skills import Skills
from agent.inventory import Inventory
from agent.memory import Memory
from agent.memory_types import MemoryEntry
from agent.tutorial_engine import TutorialProgressEngine
from agent.narrative_logger import NarrativeLogger

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("state/logs/rune_gpt.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rune_gpt")

class RuneGPT:
    def __init__(self, session_id: Optional[str] = None, load_existing: bool = False):
        self.session_id = session_id or self._generate_session_id()
        self.state_dir = Path("state") / self.session_id

        for sub in ["memory", "inventory", "narrative", "logs"]:
            (self.state_dir / sub).mkdir(parents=True, exist_ok=True)

        self.skills = Skills()
        self.inventory = Inventory()
        self.memory = Memory()
        self.tutorial_engine = TutorialProgressEngine()
        self.narrative_logger = NarrativeLogger(str(self.state_dir / "narrative"), enabled=True, verbosity=2)

        self.tutorial_complete = False
        self.tutorial_progress_score = 0

        if load_existing:
            self._load_state()
        else:
            self._init_new_agent()

    def _generate_session_id(self) -> str:
        base = Path("state")
        existing = sorted([int(p.name.split('_')[1]) for p in base.glob("Player_*") if p.name.split('_')[1].isdigit()])
        next_id = max(existing, default=0) + 1
        return f"Player_{next_id:03d}"

    def _init_new_agent(self):
        self.memory.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="creation",
            content="Spawned on Tutorial Island",
            tags=["tutorial", "spawn"],
            emotions={"curiosity": 1.0}
        ))
        self.tutorial_engine.set_current_step("survival_expert_intro")
        self._save_state()

    def _save_state(self):
        """Save all agent state including tutorial progress"""
        json.dump([m.__dict__ for m in self.memory.get_memories()], open(self.state_dir / "memory" / "memory.json", 'w'))
        json.dump(self.skills.get_state(), open(self.state_dir / "skills.json", 'w'))
        json.dump(self.inventory.get_state(), open(self.state_dir / "inventory" / "inventory.json", 'w'))
        
        # Save tutorial state with progress score
        tutorial_state = self.tutorial_engine.get_state()
        tutorial_state["progress_score"] = self.tutorial_progress_score
        json.dump(tutorial_state, open(self.state_dir / "tutorial_progress.json", 'w'))

    def _load_state(self):
        """Load all agent state including tutorial progress"""
        try:
            mem_file = self.state_dir / "memory" / "memory.json"
            if mem_file.exists():
                for m in json.load(open(mem_file)):
                    self.memory.add_memory(MemoryEntry(**m))
            self.skills.load_state(json.load(open(self.state_dir / "skills.json")))
            self.inventory.load_state(json.load(open(self.state_dir / "inventory" / "inventory.json")))
            
            # Load tutorial state with progress score
            tutorial_state = json.load(open(self.state_dir / "tutorial_progress.json"))
            self.tutorial_progress_score = tutorial_state.pop("progress_score", 0)
            self.tutorial_engine.load_state(tutorial_state)
        except Exception as e:
            logger.warning(f"State loading failed, starting fresh: {e}")
            self._init_new_agent()

    def step(self, screen_text: str):
        """Process a step in the sandbox mode"""
        logger.info(f"Screen text: {screen_text}")
        tutorial_result = self.tutorial_engine.process_screen_text(screen_text)

        if tutorial_result.get("action_required"):
            action_type = tutorial_result.get("action_type")
            next_objective = tutorial_result.get("next_objective")
            
            # Log the action attempt
            logger.info(f"Attempting action: {action_type} | Objective: {next_objective}")
            
            # Store action in memory using MemoryEntry class
            self.memory.add_memory(MemoryEntry(
                timestamp=time.time(),
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                type="action",
                content=f"Performed action: {action_type}",
                tags=["tutorial", action_type],
                emotions={"hopeful": 0.7}
            ))
            
            # Save state after each action
            self._save_state()
        else:
            logger.info("No clear action parsed. Agent observes and waits.")

    def update_tutorial_progress(self, completed_step: bool = False):
        """Update tutorial progress score"""
        if completed_step:
            self.tutorial_progress_score += 1
            logger.info(f"Tutorial progress increased: {self.tutorial_progress_score}")
            
            # Check for tutorial completion
            if self.tutorial_engine.is_complete():
                self.tutorial_complete = True
                logger.info("🎉 Tutorial Island completed!")
                
                # Add completion memory
                self.memory.add_memory(MemoryEntry(
                    timestamp=time.time(),
                    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    type="achievement",
                    content="Completed Tutorial Island!",
                    tags=["tutorial", "completion"],
                    emotions={"joy": 1.0, "pride": 0.9}
                ))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=str, help="Session ID")
    parser.add_argument("--load", action="store_true")
    args = parser.parse_args()

    agent = RuneGPT(session_id=args.session, load_existing=args.load)

    try:
        while True:
            screen_text = input("[Game Text]: ")
            if screen_text.lower() in ["exit", "quit"]:
                break
            agent.step(screen_text)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting RuneGPT.")

if __name__ == "__main__":
    main()