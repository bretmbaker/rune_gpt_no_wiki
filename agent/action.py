from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Action:
    """
    Represents an action that the AI wants to take in response to the game state.
    This class contains all the information needed to communicate the action to the RuneLite plugin.
    """
    name: str
    confidence: float
    reasoning: str
    emotion: str = "neutral"
    delay: Optional[float] = None
    message: Optional[str] = None
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    
    # Additional metadata
    action_type: str = "general"
    target: Optional[str] = None
    location: Optional[str] = None
    required_items: List[str] = field(default_factory=list)
    expected_outcome: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the Action to a dictionary."""
        result = {
            "next_action": self.name,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "emotion": self.emotion,
            "timestamp": self.timestamp,
            "action_type": self.action_type
        }
        
        # Add optional fields if they have values
        if self.delay is not None:
            result["delay"] = self.delay
        if self.message is not None:
            result["message"] = self.message
        if self.target is not None:
            result["target"] = self.target
        if self.location is not None:
            result["location"] = self.location
        if self.required_items:
            result["required_items"] = self.required_items
        if self.expected_outcome is not None:
            result["expected_outcome"] = self.expected_outcome
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create an Action from a dictionary."""
        return cls(
            name=data.get("next_action", ""),
            confidence=data.get("confidence", 0.0),
            reasoning=data.get("reasoning", ""),
            emotion=data.get("emotion", "neutral"),
            delay=data.get("delay"),
            message=data.get("message"),
            timestamp=data.get("timestamp", __import__('time').time()),
            action_type=data.get("action_type", "general"),
            target=data.get("target"),
            location=data.get("location"),
            required_items=data.get("required_items", []),
            expected_outcome=data.get("expected_outcome")
        )
    
    def __str__(self) -> str:
        """Return a string representation of the Action."""
        return (
            f"Action(name='{self.name}', "
            f"confidence={self.confidence:.2f}, "
            f"emotion='{self.emotion}')"
        ) 