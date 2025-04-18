import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from agent.memory_types import MemoryEntry
import time

class ResilienceTracker:
    """Tracks agent resilience, learning, and persistent state."""
    
    def __init__(self, memory: MemoryEntry):
        self.memory = memory
        self.death_log = []
        self.decision_outcomes = []
        self.success_chains = []
        self.avoid_list = []
        self.confidence_scores = {}
        self.avoided_locations = set()
        self.danger_threshold = 0.7
        
        # Create state directory if it doesn't exist
        os.makedirs("state", exist_ok=True)
        
        # Load existing state
        self._load_state()
    
    def _load_state(self):
        """Load all state files."""
        try:
            with open(os.path.join("state", "death_log.json"), "r") as f:
                self.death_log = json.load(f)
        except FileNotFoundError:
            self.death_log = []
            
        try:
            with open(os.path.join("state", "decision_outcomes.json"), "r") as f:
                self.decision_outcomes = json.load(f)
        except FileNotFoundError:
            self.decision_outcomes = []
            
        try:
            with open(os.path.join("state", "success_chains.json"), "r") as f:
                self.success_chains = json.load(f)
        except FileNotFoundError:
            self.success_chains = []
            
        try:
            with open(os.path.join("state", "avoid_list.json"), "r") as f:
                self.avoid_list = json.load(f)
        except FileNotFoundError:
            self.avoid_list = []
            
        try:
            with open(os.path.join("state", "confidence_scores.json"), "r") as f:
                self.confidence_scores = json.load(f)
        except FileNotFoundError:
            self.confidence_scores = {}
    
    def _save_state(self):
        """Save all state files."""
        with open(os.path.join("state", "death_log.json"), "w") as f:
            json.dump(self.death_log, f, indent=2)
            
        with open(os.path.join("state", "decision_outcomes.json"), "w") as f:
            json.dump(self.decision_outcomes, f, indent=2)
            
        with open(os.path.join("state", "success_chains.json"), "w") as f:
            json.dump(self.success_chains, f, indent=2)
            
        with open(os.path.join("state", "avoid_list.json"), "w") as f:
            json.dump(self.avoid_list, f, indent=2)
            
        with open(os.path.join("state", "confidence_scores.json"), "w") as f:
            json.dump(self.confidence_scores, f, indent=2)
    
    def log_death(self, location: str, equipment: List[str], reason: str, timestamp: Optional[str] = None):
        """Log a death event."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
            
        death_entry = {
            "timestamp": timestamp,
            "location": location,
            "equipment": equipment,
            "reason": reason
        }
        
        self.death_log.append(death_entry)
        self._save_state()
        
        self.avoided_locations.add(location)
        
        # Add death memory
        self.memory.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="death",
            content=f"Died at {location}",
            tags=["death", "danger"],
            emotions={"fear": 0.8}
        ))
    
    def log_decision_outcome(self, action: str, success: bool, reward: float, context: Dict):
        """Log the outcome of a decision."""
        outcome = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "success": success,
            "reward": reward,
            "context": context
        }
        
        self.decision_outcomes.append(outcome)
        self._save_state()
        
        # Add decision memory
        self.memory.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="decision",
            content=f"{'Successfully' if success else 'Failed to'} {action}",
            tags=["decision", "success" if success else "failure"],
            emotions={"satisfaction" if success else "disappointment": 0.7}
        ))
    
    def add_success_chain(self, actions: List[str], total_reward: float):
        """Log a chain of successful actions."""
        chain = {
            "timestamp": datetime.now().isoformat(),
            "actions": actions,
            "total_reward": total_reward
        }
        
        self.success_chains.append(chain)
        self._save_state()
        
        # Add success chain memory
        self.memory.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="success_chain",
            content=f"Completed chain of actions: {', '.join(actions)}",
            tags=["success", "chain"],
            emotions={"accomplishment": 0.8}
        ))
    
    def add_to_avoid_list(self, location: str, reason: str, until_requirements: Dict):
        """Add a location to the avoid list with requirements to retry."""
        avoid_entry = {
            "location": location,
            "reason": reason,
            "added_at": datetime.now().isoformat(),
            "until_requirements": until_requirements
        }
        
        self.avoid_list.append(avoid_entry)
        self._save_state()
        
        self.avoided_locations.add(location)
        
        # Add avoid list memory
        self.memory.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="avoid",
            content=f"Added {location} to avoid list: {reason}",
            tags=["avoid", "danger"],
            emotions={"caution": 0.7}
        ))
    
    def update_confidence_score(self, action: str, score: float):
        """Update the confidence score for an action."""
        self.confidence_scores[action] = score
        self._save_state()
        
        # Add confidence update memory
        self.memory.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="confidence",
            content=f"Updated confidence in {action} to {score:.2f}",
            tags=["confidence", "update"],
            emotions={"confidence": score}
        ))
    
    def get_avoided_locations(self) -> List[str]:
        """Get list of locations to avoid."""
        return list(self.avoided_locations)
    
    def can_retry_location(self, location: str, current_state: Dict) -> Tuple[bool, str]:
        """Check if a location can be retried based on current state."""
        for entry in self.avoid_list:
            if entry["location"] == location:
                requirements = entry["until_requirements"]
                for req, value in requirements.items():
                    if current_state.get(req, 0) < value:
                        return False, f"Need {req} >= {value}"
                return True, "Requirements met"
        return True, "Location not in avoid list"
    
    def get_successful_chains(self, min_reward: float = 0) -> List[Dict]:
        """Get successful action chains above a minimum reward threshold."""
        return [chain for chain in self.success_chains if chain["total_reward"] >= min_reward]
    
    def get_action_confidence(self, action: str) -> float:
        """Get the confidence score for an action."""
        return self.confidence_scores.get(action, 0.5)  # Default to 0.5 if unknown
    
    def get_recent_deaths(self, count: int = 5) -> List[Dict]:
        """Get the most recent deaths."""
        return sorted(self.death_log, key=lambda x: x["timestamp"], reverse=True)[:count]
    
    def get_action_history(self, action: str, limit: int = 10) -> List[Dict]:
        """Get history of outcomes for a specific action."""
        return [outcome for outcome in self.decision_outcomes if outcome["action"] == action][-limit:]
    
    def calculate_action_score(self, action: str, context: Dict) -> float:
        """Calculate a score for an action based on history and context."""
        # Base score from confidence
        score = self.get_action_confidence(action)
        
        # Adjust based on recent outcomes
        recent_outcomes = self.get_action_history(action)
        if recent_outcomes:
            success_rate = sum(1 for o in recent_outcomes if o["success"]) / len(recent_outcomes)
            score += success_rate * 0.2  # Up to 0.2 bonus for good history
            
            avg_reward = sum(o["reward"] for o in recent_outcomes) / len(recent_outcomes)
            score += min(avg_reward / 100, 0.3)  # Up to 0.3 bonus for good rewards
        
        # Penalize if location is avoided
        if context.get("location") in self.get_avoided_locations():
            score -= 0.4
        
        # Ensure score stays in [0, 1]
        return max(0.0, min(1.0, score))
    
    def record_near_death(self, location: str) -> None:
        """Record a near-death experience"""
        self.avoided_locations.add(location)
        
        # Add near-death memory
        self.memory.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="near_death",
            content=f"Almost died at {location}",
            tags=["danger", "escape"],
            emotions={"fear": 0.6, "relief": 0.4}
        ))
    
    def is_location_safe(self, location: str) -> bool:
        """Check if a location is considered safe"""
        return location not in self.avoided_locations
    
    def get_danger_level(self, location: str) -> float:
        """Get danger level for a location"""
        if location in self.avoided_locations:
            return 1.0
        
        # Check recent deaths at this location
        location_deaths = [d for d in self.death_log if d["location"] == location]
        if location_deaths:
            # More recent deaths increase danger level
            return min(1.0, len(location_deaths) * 0.2)
        
        return 0.0 