"""
Action Memory System for RuneGPT
Tracks action success rates and provides decision-making capabilities
"""

import json
import random
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import hashlib
import logging
import time

logger = logging.getLogger(__name__)

class ActionMemory:
    def __init__(self, player_id: str):
        self.player_id = player_id
        self.memory_file = Path("state") / player_id / "memory" / "action_stats.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty stats if file doesn't exist
        if not self.memory_file.exists():
            self.action_history = {}
            self._save_memory()
            logger.info(f"Created new action memory file for {player_id}")
        else:
            self.action_history = self._load_memory()
            logger.info(f"Loaded existing action memory for {player_id}")
        
        # Exploration vs exploitation settings
        self.exploration_rate = 0.1  # 10% chance to explore
        self.tutorial_completion_bonus = 0.2  # 20% bonus for actions that progress tutorial
        
    def _load_memory(self) -> Dict:
        """Load action statistics from JSON file"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_memory(self):
        """Save action statistics to JSON file"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.action_history, f, indent=2)
            
    def _get_context_hash(self, screen_text: str) -> str:
        """Generate a simple context identifier from screen text"""
        return hashlib.md5(screen_text.encode()).hexdigest()[:8]
    
    def record_action(self, action: str, success: bool, context: Dict):
        """Record the outcome of an action in a given context"""
        if action not in self.action_history:
            self.action_history[action] = []
            
        # Add new outcome to history
        self.action_history[action].append({
            "success": success,
            "context": context,
            "timestamp": time.time()
        })
        
        # Keep only last 10 outcomes for each action
        if len(self.action_history[action]) > 10:
            self.action_history[action] = self.action_history[action][-10:]
            
        self._save_memory()
        
    def get_best_action(self, available_actions: List[str], screen_text: str, current_step: str, current_objective: str) -> Tuple[Optional[str], float]:
        """Get the best action based on current step and objective"""
        # Initialize scores for all actions
        action_scores = {action: 50.0 for action in available_actions}  # Base score of 50
        
        # Track last successful action
        last_successful_action = None
        for action in available_actions:
            if action in self.action_history and self.action_history[action]:
                if self.action_history[action][-1]["success"]:
                    last_successful_action = action
                    break
        
        # Update scores based on history and context
        for action in available_actions:
            if action in self.action_history:
                outcomes = self.action_history[action]
                
                # Calculate success rates
                total_attempts = len(outcomes)
                total_successes = sum(1 for o in outcomes if o["success"])
                
                # Recent outcomes have more weight
                recent_outcomes = outcomes[-3:]
                recent_successes = sum(1 for o in recent_outcomes if o["success"])
                
                # Calculate weighted success rate
                if total_attempts > 0:
                    overall_rate = total_successes / total_attempts
                    recent_rate = recent_successes / len(recent_outcomes) if recent_outcomes else 0
                    success_rate = (recent_rate * 0.7) + (overall_rate * 0.3)
                    base_score = success_rate * 100
                else:
                    base_score = 50  # Default score for new actions
                
                # Apply context-based bonuses
                bonuses = 0
                
                # Bonus for actions matching current step
                if current_step and current_step.lower() in action.lower():
                    bonuses += 50
                
                # Bonus for actions matching current objective
                if current_objective and current_objective.lower() in action.lower():
                    bonuses += 100
                
                # Bonus for actions that were successful in similar contexts
                context_matches = sum(1 for o in outcomes if o["success"] and 
                                    o["context"].get("step") == current_step)
                if context_matches > 0:
                    bonuses += context_matches * 30
                
                # Apply penalties
                penalties = 0
                
                # Penalty for recent failures
                recent_failures = len(recent_outcomes) - recent_successes
                penalties += recent_failures * 20
                
                # Strong penalty for repeating the last successful action
                if action == last_successful_action:
                    penalties += 200  # Very high penalty to force trying something new
                
                # Additional penalty for repetition
                if total_attempts > 3:
                    penalties += min(100, total_attempts * 20)  # Higher growing penalty
                    
                # Calculate final score
                action_scores[action] = max(10, base_score + bonuses - penalties)  # Minimum score of 10
        
        # Random exploration with higher rate after success
        exploration_rate = self.exploration_rate
        if last_successful_action:
            exploration_rate = 0.3  # 30% chance to explore after success
        
        if random.random() < exploration_rate:
            # Exclude last successful action from exploration candidates
            candidates = [a for a in available_actions if a != last_successful_action]
            if not candidates:  # If all actions have been successful
                candidates = available_actions
            return random.choice(candidates), 0.3
        
        # Get best action and confidence
        best_action = max(action_scores.items(), key=lambda x: x[1])
        max_score = max(action_scores.values())
        min_score = min(action_scores.values())
        score_range = max_score - min_score
        
        # Calculate confidence (0.1 to 0.9)
        if score_range > 0:
            confidence = 0.1 + 0.8 * ((best_action[1] - min_score) / score_range)
        else:
            confidence = 0.5
        
        return best_action[0], confidence
        
    def _extract_objectives(self, screen_text: str) -> List[str]:
        """Extract potential objectives from screen text"""
        # Simple objective extraction - look for phrases like "you need to" or "you should"
        objectives = []
        text_lower = screen_text.lower()
        
        # Look for common objective indicators
        if "you need to" in text_lower:
            objectives.append(text_lower.split("you need to")[-1].strip())
        if "you should" in text_lower:
            objectives.append(text_lower.split("you should")[-1].strip())
        if "objective" in text_lower:
            objectives.append(text_lower.split("objective")[-1].strip())
            
        return objectives
        
    def get_action_stats(self, action: str) -> Optional[Dict]:
        """Get statistics for a specific action"""
        if action not in self.action_history:
            return None
            
        outcomes = self.action_history[action]
        total_attempts = len(outcomes)
        successes = sum(1 for outcome in outcomes if outcome["success"])
        
        return {
            "total_attempts": total_attempts,
            "successes": successes,
            "failures": total_attempts - successes,
            "success_rate": successes / total_attempts if total_attempts > 0 else 0.0
        } 