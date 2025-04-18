from dataclasses import dataclass
from typing import Dict, Optional, List

@dataclass
class MemoryEntry:
    """Represents a single memory entry in the agent's journal"""
    timestamp: float
    date: str
    type: str  # quest, skill, combat, discovery, goal, death, travel, reflection
    content: str
    location: Optional[str] = None
    emotions: Optional[Dict[str, float]] = None
    tags: Optional[List[str]] = None 