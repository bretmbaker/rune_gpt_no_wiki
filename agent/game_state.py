from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class GameState:
    """
    Represents the current state of the game as reported by the RuneLite plugin.
    This class safely parses and stores the incoming game state data.
    """
    screen_text: str = ""
    chatbox: List[str] = field(default_factory=list)
    player_location: str = ""
    inventory: List[str] = field(default_factory=list)
    step: str = ""
    session_id: Optional[str] = None
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    
    # Additional fields that might be useful
    skills: Dict[str, int] = field(default_factory=dict)
    equipment: List[str] = field(default_factory=list)
    quest_points: int = 0
    combat_level: int = 0
    health: int = 100
    prayer: int = 99
    energy: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the GameState to a dictionary."""
        return {
            "screen_text": self.screen_text,
            "chatbox": self.chatbox,
            "player_location": self.player_location,
            "inventory": self.inventory,
            "step": self.step,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "skills": self.skills,
            "equipment": self.equipment,
            "quest_points": self.quest_points,
            "combat_level": self.combat_level,
            "health": self.health,
            "prayer": self.prayer,
            "energy": self.energy
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """Create a GameState from a dictionary."""
        return cls(
            screen_text=data.get("screen_text", ""),
            chatbox=data.get("chatbox", []),
            player_location=data.get("player_location", ""),
            inventory=data.get("inventory", []),
            step=data.get("step", ""),
            session_id=data.get("session_id"),
            timestamp=data.get("timestamp", __import__('time').time()),
            skills=data.get("skills", {}),
            equipment=data.get("equipment", []),
            quest_points=data.get("quest_points", 0),
            combat_level=data.get("combat_level", 0),
            health=data.get("health", 100),
            prayer=data.get("prayer", 99),
            energy=data.get("energy", 100)
        )
    
    def __str__(self) -> str:
        """Return a string representation of the GameState."""
        return (
            f"GameState(screen_text='{self.screen_text[:50]}...', "
            f"location='{self.player_location}', "
            f"step='{self.step}', "
            f"inventory_size={len(self.inventory)})"
        ) 