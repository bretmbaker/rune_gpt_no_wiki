# memory.py - Tracks agent state and progress

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from agent.memory_types import MemoryEntry

class Memory:
    """
    Tracks the agent's memory of completed actions, NPCs talked to,
    items obtained, and skills trained.
    """
    def __init__(self, memory_entries: List[MemoryEntry] = None):
        # Initialize memory entries
        self.memory_entries = memory_entries or []
        
        # Track completed actions
        self.completed_actions: Set[str] = set()
        
        # Track NPCs talked to
        self.talked_to_npcs: Set[str] = set()
        
        # Track items obtained
        self.obtained_items: Set[str] = set()
        
        # Track skills trained
        self.trained_skills: Set[str] = set()
        
        # Track current location
        self.current_location: str = "Tutorial Island - Starting Area"
        
        # General memory storage
        self._memory_store: Dict = {}
        
        # Process initial memory entries
        for entry in self.memory_entries:
            self._process_memory_entry(entry)
    
    def _process_memory_entry(self, entry: MemoryEntry):
        """Process a memory entry and update relevant sets."""
        if entry.type == "action":
            self.completed_actions.add(entry.content)
        elif entry.type == "npc":
            self.talked_to_npcs.add(entry.content)
        elif entry.type == "item":
            self.obtained_items.add(entry.content)
        elif entry.type == "skill":
            self.trained_skills.add(entry.content)
        elif entry.type == "location":
            self.current_location = entry.content
    
    def add_memory(self, entry: MemoryEntry):
        """Add a new memory entry."""
        self.memory_entries.append(entry)
        self._process_memory_entry(entry)
    
    def get_memories(self) -> List[MemoryEntry]:
        """Get all memory entries."""
        return self.memory_entries
    
    def get_recent_memories(self, count: int = 10) -> List[MemoryEntry]:
        """Get the most recent memory entries."""
        return sorted(self.memory_entries, key=lambda x: x.timestamp, reverse=True)[:count]
    
    def has_done(self, action: str) -> bool:
        """Check if an action has been completed."""
        return action in self.completed_actions
    
    def mark_done(self, action: str):
        """Mark an action as completed."""
        self.completed_actions.add(action)
        self.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="action",
            content=action,
            tags=["action", "completed"],
            emotions={"satisfaction": 0.7}
        ))
    
    def has_talked_to(self, npc: str) -> bool:
        """Check if an NPC has been talked to."""
        return npc in self.talked_to_npcs
    
    def mark_talked_to(self, npc: str):
        """Mark an NPC as talked to."""
        self.talked_to_npcs.add(npc)
        self.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="npc",
            content=npc,
            tags=["npc", "conversation"],
            emotions={"interest": 0.6}
        ))
    
    def has_obtained(self, item: str) -> bool:
        """Check if an item has been obtained."""
        return item in self.obtained_items
    
    def mark_obtained(self, item: str):
        """Mark an item as obtained."""
        self.obtained_items.add(item)
        self.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="item",
            content=item,
            tags=["item", "obtained"],
            emotions={"satisfaction": 0.6}
        ))
    
    def has_trained(self, skill: str) -> bool:
        """Check if a skill has been trained."""
        return skill in self.trained_skills
    
    def mark_trained(self, skill: str):
        """Mark a skill as trained."""
        self.trained_skills.add(skill)
        self.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="skill",
            content=skill,
            tags=["skill", "trained"],
            emotions={"accomplishment": 0.7}
        ))
    
    def update_location(self, location: str):
        """Update the current location."""
        self.current_location = location
        self.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="location",
            content=location,
            tags=["location", "movement"],
            emotions={"curiosity": 0.6}
        ))
    
    def print_status(self):
        """Print the current memory status."""
        print("\n[RuneGPT Memory Status]")
        print(f"Current Location: {self.current_location}")
        print(f"Completed Actions: {len(self.completed_actions)}")
        print(f"Talked to NPCs: {len(self.talked_to_npcs)}")
        print(f"Obtained Items: {len(self.obtained_items)}")
        print(f"Trained Skills: {len(self.trained_skills)}")
        print(f"Tutorial Complete: {self.is_tutorial_complete()}")
        print("-" * 50)
    
    def is_tutorial_complete(self) -> bool:
        """Check if all Tutorial Island tasks are complete."""
        required_npcs = [
            "Gielinor Guide",
            "Survival Expert",
            "Master Chef",
            "Quest Guide",
            "Mining Instructor",
            "Combat Instructor",
            "Account Guide",
            "Brother Brace",
            "Magic Instructor"
        ]
        
        for npc in required_npcs:
            if not self.has_talked_to(npc):
                return False
        return True 