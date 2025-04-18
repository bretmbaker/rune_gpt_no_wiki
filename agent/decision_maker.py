import json
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from agent.skills import Skills
from agent.inventory import Inventory
from agent.memory_types import MemoryEntry
from knowledge.semantic_query_engine import SemanticQueryEngine
from agent.resilience_tracker import ResilienceTracker
import time
import logging
import random
import os
from datetime import datetime
from .personality_config import PersonalityConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("decision_maker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("decision_maker")

@dataclass
class Action:
    """Represents a possible action the agent can take"""
    name: str
    description: str
    category: str  # combat, skilling, quest, exploration, etc.
    location: str
    required_items: List[str]
    required_skills: Dict[str, int]
    expected_rewards: List[str]
    risks: List[str]
    reasoning: str
    priority: float = 0.0

@dataclass
class DecisionContext:
    """Context for making decisions"""
    current_location: str
    skill_levels: Dict[str, int]
    inventory: Dict[str, int]
    quest_points: int
    wealth: int
    exploration_score: float
    experimentation_score: float
    personality: PersonalityConfig
    discovered_locations: List[str]
    discovered_items: List[str]
    discovered_skills: List[str]

class DecisionMaker:
    """
    Handles post-tutorial decision making for RuneGPT agent.
    Evaluates current state and determines optimal next actions.
    """
    def __init__(self, skills: Skills, inventory: Inventory, memory: MemoryEntry, wiki_engine: SemanticQueryEngine, personality: PersonalityConfig):
        self.skills = skills
        self.inventory = inventory
        self.memory = memory
        self.wiki_engine = wiki_engine
        self.resilience_tracker = ResilienceTracker(memory)
        self.personality = personality
        
        # Personality traits that evolve over time
        self.curiosity_level = 0.7  # High initial curiosity
        self.efficiency_preference = 0.3  # Low initial efficiency preference
        self.risk_tolerance = 0.5  # Moderate initial risk tolerance
        
        # Track learned preferences
        self.preferred_actions = {}  # Actions that worked well
        self.avoided_actions = {}  # Actions that didn't work well
        self.exploration_history = []  # Track exploration patterns
        
        # Cache for actions
        self.action_cache = {}
        self.cache_expiry = 300  # 5 minutes
        
        # Track action history
        self.action_history = []
        
        # Track goals
        self.goals = {
            "short_term": [],
            "long_term": []
        }
        
        # Load personality and preferences
        self._load_preferences()
        self._load_cache()
        self._load_action_history()
        self._load_goals()
    
    def _load_preferences(self):
        """Load agent preferences from memory."""
        # Initialize default preferences
        self.preferences = {
            "risk_tolerance": 0.5,  # 0 = very cautious, 1 = very risky
            "exploration_rate": 0.7,  # 0 = exploit only, 1 = explore only
            "goal_focus": 0.6,  # 0 = easily distracted, 1 = highly focused
            "resource_management": 0.5,  # 0 = spender, 1 = hoarder
            "combat_style": "balanced",  # aggressive, defensive, balanced
            "training_priority": "balanced"  # efficiency, variety, balanced
        }
        
        # Store preferences in memory content
        self.memory.content = json.dumps({
            "preferences": self.preferences,
            "memory_entry": MemoryEntry(
                timestamp=time.time(),
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                type="preferences",
                content="Initialized agent preferences",
                tags=["preferences", "initialization"],
                emotions={"neutral": 0.5}
            ).__dict__
        })
    
    def _save_preferences(self):
        """Save current preferences and personality traits to memory"""
        prefs = {
            "curiosity_level": self.curiosity_level,
            "efficiency_preference": self.efficiency_preference,
            "risk_tolerance": self.risk_tolerance,
            "preferred_actions": self.preferred_actions,
            "avoided_actions": self.avoided_actions,
            "exploration_history": self.exploration_history
        }
        
        # Store updated preferences in memory content
        self.memory.content = json.dumps({
            "preferences": prefs,
            "memory_entry": MemoryEntry(
                timestamp=time.time(),
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                type="preferences",
                content="Updated agent preferences",
                tags=["preferences", "update"],
                emotions={"neutral": 0.5}
            ).__dict__
        })
    
    def _load_cache(self):
        """Load action cache from file"""
        try:
            if os.path.exists("state/decision_cache/action_cache.json"):
                with open("state/decision_cache/action_cache.json", "r") as f:
                    cache_data = json.load(f)
                
                # Convert cache data to Action objects
                for key, action_data in cache_data.items():
                    self.action_cache[key] = Action(**action_data)
                
                # Check if cache is expired
                if "timestamp" in cache_data and time.time() - cache_data["timestamp"] > self.cache_expiry:
                    self.action_cache = {}
        except Exception as e:
            print(f"Error loading action cache: {e}")
            self.action_cache = {}
    
    def _save_cache(self):
        """Save action cache to file"""
        try:
            # Convert Action objects to dictionaries
            cache_data = {}
            for key, action in self.action_cache.items():
                cache_data[key] = action.__dict__
            
            # Add timestamp
            cache_data["timestamp"] = time.time()
            
            with open("state/decision_cache/action_cache.json", "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Error saving action cache: {e}")
    
    def _load_action_history(self):
        """Load action history from memory"""
        self.action_history = []
        
        # Store action history in memory content
        self.memory.content = json.dumps({
            "action_history": self.action_history,
            "memory_entry": MemoryEntry(
                timestamp=time.time(),
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                type="action_history",
                content="Initialized action history",
                tags=["actions", "initialization"],
                emotions={"neutral": 0.5}
            ).__dict__
        })
    
    def _save_action_history(self):
        """Save action history to memory"""
        # Store updated action history in memory content
        self.memory.content = json.dumps({
            "action_history": self.action_history,
            "memory_entry": MemoryEntry(
                timestamp=time.time(),
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                type="action_history",
                content="Updated action history",
                tags=["actions", "update"],
                emotions={"neutral": 0.5}
            ).__dict__
        })
    
    def _load_goals(self):
        """Load goals from memory"""
        # Initialize default goals
        self.goals = {
            "short_term": [
                {
                    "name": "Complete Tutorial Island",
                    "description": "Learn the basics of RuneScape",
                    "progress": 0,
                    "completed": False
                }
            ],
            "long_term": [
                {
                    "name": "Reach Combat Level 30",
                    "description": "Train combat skills to level 30",
                    "progress": 0,
                    "completed": False,
                    "requirements": {
                        "attack": 30,
                        "strength": 30,
                        "defence": 30
                    }
                }
            ]
        }
        
        # Load quest goals
        self.quest_goals = {
            "active": [],
            "completed": [],
            "available": []
        }
        
        # Query wiki for available quests
        quest_query = "What quests are available for a new player?"
        quest_results = self.wiki_engine.query(quest_query)
        
        for result in quest_results:
            if "quest" in result:
                quest = result["quest"]
                if self._meets_quest_requirements(quest):
                    self.quest_goals["available"].append(quest)
        
        # Store goals in memory content
        self.memory.content = json.dumps({
            "goals": self.goals,
            "quest_goals": self.quest_goals,
            "memory_entry": MemoryEntry(
                timestamp=time.time(),
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                type="goals",
                content="Initialized agent goals",
                tags=["goals", "initialization"],
                emotions={"determination": 0.7}
            ).__dict__
        })
    
    def _save_goals(self):
        """Save goals to memory"""
        # Store updated goals in memory content
        self.memory.content = json.dumps({
            "goals": self.goals,
            "quest_goals": self.quest_goals,
            "memory_entry": MemoryEntry(
                timestamp=time.time(),
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                type="goals",
                content="Updated agent goals",
                tags=["goals", "update"],
                emotions={"determination": 0.7}
            ).__dict__
        })
    
    def evaluate_current_state(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Evaluate the current game state.
        
        Args:
            context: Current decision context
        
        Returns:
            Dictionary containing state evaluation
        """
        evaluation = {
            "location_score": self._evaluate_location(context),
            "skill_score": self._evaluate_skills(context),
            "wealth_score": self._evaluate_wealth(context),
            "exploration_score": context.exploration_score,
            "experimentation_score": context.experimentation_score,
            "goal_progress": self._evaluate_goals(context),
            "restriction_violations": self._check_restrictions(context)
        }
        
        return evaluation
    
    def get_possible_actions(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """
        Get list of possible actions based on current state.
        
        Args:
            context: Current decision context
        
        Returns:
            List of possible actions
        """
        actions = []
        
        # Add actions based on personality style
        if "sweaty_pvmer" in self.personality.style:
            actions.extend(self._get_pvm_actions(context))
        if "explorer" in self.personality.style:
            actions.extend(self._get_exploration_actions(context))
        if "casual_skiller" in self.personality.style:
            actions.extend(self._get_skilling_actions(context))
        if "lore_seeker" in self.personality.style:
            actions.extend(self._get_quest_actions(context))
        if "money_maker" in self.personality.style:
            actions.extend(self._get_money_making_actions(context))
        if "completionist" in self.personality.style:
            actions.extend(self._get_completion_actions(context))
        if "pet_hunter" in self.personality.style:
            actions.extend(self._get_pet_hunting_actions(context))
        
        # Filter actions based on restrictions
        filtered_actions = []
        for action in actions:
            if not self._violates_restrictions(action, context):
                filtered_actions.append(action)
        
        # Sort actions by priority
        filtered_actions.sort(key=lambda a: self._calculate_action_priority(a, context), reverse=True)
        
        return filtered_actions
    
    def _evaluate_location(self, context: DecisionContext) -> float:
        """Evaluate current location based on personality."""
        score = 0.5  # Base score
        
        # Adjust based on personality style
        if "explorer" in self.personality.style:
            if context.current_location not in context.discovered_locations:
                score += 0.3
        if "sweaty_pvmer" in self.personality.style:
            if "boss" in context.current_location.lower():
                score += 0.3
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_skills(self, context: DecisionContext) -> float:
        """Evaluate skill levels based on personality."""
        score = 0.5  # Base score
        
        # Calculate average skill level
        if context.skill_levels:
            avg_level = sum(context.skill_levels.values()) / len(context.skill_levels)
            score += avg_level / 99.0  # Max level is 99
        
        # Adjust based on personality style
        if "skiller_pure" in self.personality.style:
            if all(level >= 90 for level in context.skill_levels.values()):
                score += 0.2
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_wealth(self, context: DecisionContext) -> float:
        """Evaluate wealth based on personality."""
        score = 0.5  # Base score
        
        # Adjust based on personality style
        if "money_maker" in self.personality.style:
            if context.wealth > 1000000:  # 1M gp
                score += 0.3
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_goals(self, context: DecisionContext) -> Dict[str, float]:
        """Evaluate progress towards personality goals."""
        progress = {}
        
        for goal in self.personality.long_term_goals:
            if "max" in goal.lower():
                # Skill-based goal
                progress[goal] = self._evaluate_skills(context)
            elif "pet" in goal.lower():
                # Pet hunting goal
                progress[goal] = 0.5  # Placeholder
            elif "quest" in goal.lower():
                # Quest-based goal
                progress[goal] = context.quest_points / 300.0  # Max quest points
        else:
                # Generic goal
                progress[goal] = 0.5
        
        return progress
    
    def _check_restrictions(self, context: DecisionContext) -> List[str]:
        """Check for restriction violations."""
        violations = []
        
        for restriction in self.personality.restrictions:
            if "ge" in restriction.lower() and context.wealth > 0:
                violations.append("Using Grand Exchange")
            if "trading" in restriction.lower() and context.wealth > 0:
                violations.append("Trading with other players")
        
        return violations
    
    def _get_pvm_actions(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get PVM-related actions."""
        actions = []
        
        # Add boss-specific actions
        if "boss" in context.current_location.lower():
            actions.append({
                "name": "fight_boss",
                "description": "Fight the boss in this area",
                "category": "combat",
                "requirements": {
                    "combat_level": 70,
                    "items": ["food", "potions"]
                }
            })
        
        return actions
    
    def _get_exploration_actions(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get exploration-related actions."""
        actions = []
        
        # Add area exploration actions
        for location in context.discovered_locations:
            if location != context.current_location:
                actions.append({
                    "name": f"explore_{location.lower().replace(' ', '_')}",
                    "description": f"Explore {location}",
                    "category": "exploration",
                    "requirements": {}
                })
        
        return actions
    
    def _get_skilling_actions(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get skilling-related actions."""
        actions = []
        
        # Add skill training actions
        for skill, level in context.skill_levels.items():
            if level < 99:  # Max level
                actions.append({
                    "name": f"train_{skill.lower()}",
                    "description": f"Train {skill}",
                    "category": "skilling",
                    "requirements": {skill: level}
                })
        
        return actions
    
    def _get_quest_actions(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get quest-related actions."""
        actions = []
        
        # Add quest actions based on strategy
        if self.personality.quest_strategy == "follow_guide":
            actions.append({
                "name": "follow_quest_guide",
                "description": "Follow the quest guide",
                "category": "questing",
                "requirements": {}
            })
        elif self.personality.quest_strategy == "explore":
            actions.append({
                "name": "explore_quest",
                "description": "Explore the quest area",
                "category": "questing",
                "requirements": {}
            })
        
        return actions
    
    def _get_money_making_actions(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get money-making actions."""
        actions = []
        
        # Add money-making actions
        if context.wealth < 1000000:  # 1M gp
            actions.append({
                "name": "make_money",
                "description": "Focus on money-making activities",
                "category": "money_making",
                "requirements": {}
            })
        
        return actions
    
    def _get_completion_actions(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get completion-related actions."""
        actions = []
        
        # Add completion actions
        actions.append({
            "name": "check_completion",
            "description": "Check completion status",
            "category": "completion",
            "requirements": {}
        })
        
        return actions
    
    def _get_pet_hunting_actions(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get pet hunting actions."""
        actions = []
        
        # Add pet hunting actions
        actions.append({
            "name": "hunt_pets",
            "description": "Focus on pet hunting",
            "category": "pet_hunting",
            "requirements": {}
        })
        
        return actions
    
    def _violates_restrictions(self, action: Dict[str, Any], context: DecisionContext) -> bool:
        """Check if an action violates personality restrictions."""
        for restriction in self.personality.restrictions:
            if restriction.lower() in action["name"].lower():
                return True
            if "ge" in restriction.lower() and "grand_exchange" in action["name"].lower():
                return True
            if "trading" in restriction.lower() and "trade" in action["name"].lower():
                return True
        
        return False
    
    def _calculate_action_priority(self, action: Dict[str, Any], context: DecisionContext) -> float:
        """Calculate priority score for an action."""
        priority = 0.5  # Base priority
        
        # Adjust based on personality style
        if "sweaty_pvmer" in self.personality.style:
            if action["category"] in ["combat", "boss", "pvm"]:
                priority += 0.3
        if "explorer" in self.personality.style:
            if action["category"] == "exploration":
                priority += 0.3
        if "casual_skiller" in self.personality.style:
            if action["category"] == "skilling":
                priority += 0.3
        
        # Adjust based on goals
        for goal in self.personality.long_term_goals:
            if goal.lower() in action["name"].lower():
                priority += 0.2
        
        # Adjust based on risk tolerance
        if self.personality.risk_tolerance == "high":
            if "dangerous" in action.get("description", "").lower():
                priority += 0.2
        elif self.personality.risk_tolerance == "low":
            if "dangerous" in action.get("description", "").lower():
                priority -= 0.2
        
        return priority
    
    def choose_action(self) -> Optional[Action]:
        """
        Choose the best action based on the current state.
        
        Returns:
            The chosen action or None if no suitable action is found
        """
        # Get possible actions
        actions = self.get_possible_actions()
        
        if not actions:
            return None
        
        # Filter out actions with requirements we don't meet
        feasible_actions = [action for action in actions if self._meets_requirements(action.required_items, action.required_skills)]
        
        if not feasible_actions:
            # If no feasible actions, return the highest priority action
            return max(actions, key=lambda a: a.priority)
        
        # Choose the highest priority feasible action
        chosen_action = max(feasible_actions, key=lambda a: a.priority)
        
        # Add to action history
        self.action_history.append({
            "timestamp": time.time(),
            "action": chosen_action.name,
            "location": chosen_action.location,
            "priority": chosen_action.priority
        })
        self._save_action_history()
        
        return chosen_action
    
    def record_action_result(self, action: str, success: bool, rewards: List[str] = None, death: bool = False, location: str = None):
        """Record the result of an action for future decision making"""
        result = {
            "action": action,
            "success": success,
            "rewards": rewards or [],
            "death": death,
            "location": location,
            "timestamp": time.time()
        }
        
        self.action_history.append(result)
        
        # Update preferences based on result
        if success:
            self.preferred_actions[action] = self.preferred_actions.get(action, 0) + 1
        else:
            self.avoided_actions[action] = self.avoided_actions.get(action, 0) + 1
        
        # Store action result in memory content
        self.memory.content = json.dumps({
            "action_result": result,
            "memory_entry": MemoryEntry(
                timestamp=time.time(),
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                type="action_result",
                content=f"Recorded result for action: {action}",
                tags=["actions", "results"],
                emotions={"satisfaction" if success else "disappointment": 0.7}
            ).__dict__
        })
        
        self._save_preferences()
        self._save_action_history()
        
        # Update resilience tracker if death occurred and location is known
        if death and location:
            self.resilience_tracker.record_death(location)
    
    def add_goal(self, name: str, description: str, goal_type: str = "short_term", 
                requirements: Optional[Dict[str, int]] = None):
        """
        Add a new goal.
        
        Args:
            name: Goal name
            description: Goal description
            goal_type: Goal type ("short_term" or "long_term")
            requirements: Goal requirements
        """
        if goal_type not in ["short_term", "long_term"]:
            goal_type = "short_term"
        
        goal = {
            "name": name,
            "description": description,
            "progress": 0,
            "completed": False,
            "requirements": requirements or {},
            "created_date": time.time()
        }
        
        self.goals[goal_type].append(goal)
        self._save_goals()
    
    def update_goal_progress(self, goal_name: str, progress: float):
        """
        Update the progress of a goal.
        
        Args:
            goal_name: Goal name
            progress: Progress percentage (0.0 to 1.0)
        """
        # Find the goal
        for goal_type in ["short_term", "long_term"]:
            for i, goal in enumerate(self.goals[goal_type]):
                if goal["name"] == goal_name:
                    # Update progress
                    self.goals[goal_type][i]["progress"] = progress
                    
                    # Check if completed
                    if progress >= 1.0 and not self.goals[goal_type][i]["completed"]:
                        self.goals[goal_type][i]["completed"] = True
                        self.goals[goal_type][i]["completed_date"] = time.time()
                    
                    # Save goals
                    self._save_goals()
                    return
        
        # Goal not found
        print(f"Goal not found: {goal_name}")
    
    def get_goals(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all goals.
        
        Returns:
            Dictionary of goals
        """
        return self.goals 

    def _meets_quest_requirements(self, quest: Dict[str, Any]) -> bool:
        """
        Check if the agent meets the requirements for a quest.
        
        Args:
            quest: Quest information
            
        Returns:
            True if requirements are met, False otherwise
        """
        # Check skill requirements
        for skill, level in quest.get("required_skills", {}).items():
            if self.skills.get_level(skill) < level:
                return False
        
        # Check quest point requirements
        if quest.get("required_quest_points", 0) > self.memory.get("quest_points", 0):
            return False
        
        # Check item requirements
        for item in quest.get("required_items", []):
            if item not in self.inventory.get_all_items():
                return False
        
        return True

    def add_quest_goal(self, quest_name: str):
        """
        Add a quest as a goal.
        
        Args:
            quest_name: Name of the quest
        """
        # Query wiki for quest information
        quest_query = f"What is the quest {quest_name} about?"
        quest_results = self.wiki_engine.query(quest_query)
        
        if quest_results:
            quest = quest_results[0]
            
            # Create quest goal
            goal = {
                "name": f"Complete {quest_name}",
                "description": quest.get("description", f"Complete the {quest_name} quest"),
                "progress": 0,
                "completed": False,
                "requirements": quest.get("required_skills", {}),
                "rewards": quest.get("rewards", []),
                "quest_name": quest_name
            }
            
            # Add to active quests
            self.quest_goals["active"].append(goal)
            
            # Add to short-term goals
            self.goals["short_term"].append(goal)
            
            # Save goals
            self._save_goals()

    def update_quest_progress(self, quest_name: str, progress: float):
        """
        Update the progress of a quest.
        
        Args:
            quest_name: Name of the quest
            progress: Progress percentage (0.0 to 1.0)
        """
        # Update quest goal
        for i, quest in enumerate(self.quest_goals["active"]):
            if quest["quest_name"] == quest_name:
                # Update progress
                self.quest_goals["active"][i]["progress"] = progress
                
                # Check if completed
                if progress >= 1.0 and not self.quest_goals["active"][i]["completed"]:
                    self.quest_goals["active"][i]["completed"] = True
                    self.quest_goals["active"][i]["completed_date"] = time.time()
                    
                    # Move to completed quests
                    self.quest_goals["completed"].append(self.quest_goals["active"][i])
                    self.quest_goals["active"].pop(i)
                    
                    # Update quest points
                    self.memory.content = json.dumps({
                        "quest_points": self.memory.get("quest_points", 0) + 1,
                        "memory_entry": MemoryEntry(
                            timestamp=time.time(),
                            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            type="quest_completion",
                            content=f"Completed quest: {quest_name}",
                            tags=["quest", "completion"],
                            emotions={"pride": 0.8}
                        ).__dict__
                    })
                
                # Save goals
                self._save_goals()
                return
        
        # Quest not found
        print(f"Quest not found: {quest_name}")

    def get_available_quests(self) -> List[Dict[str, Any]]:
        """
        Get a list of available quests.
        
        Returns:
            List of available quests
        """
        return self.quest_goals["available"]

    def get_active_quests(self) -> List[Dict[str, Any]]:
        """
        Get a list of active quests.
        
        Returns:
            List of active quests
        """
        return self.quest_goals["active"]

    def get_completed_quests(self) -> List[Dict[str, Any]]:
        """
        Get a list of completed quests.
        
        Returns:
            List of completed quests
        """
        return self.quest_goals["completed"]

    def _meets_requirements(self, required_items: List[str], required_skills: Dict[str, int]) -> bool:
        """
        Check if the agent meets the requirements for an action.
        
        Args:
            required_items: Required items
            required_skills: Required skills
            
        Returns:
            True if requirements are met, False otherwise
        """
        # Check items
        for item in required_items:
            if item not in self.inventory.get_all_items():
                return False
        
        # Check skills
        for skill, level in required_skills.items():
            if self.skills.get_level(skill) < level:
                return False
        
        return True

    def _apply_personality_influence(self, actions: List[Dict[str, Any]], context: DecisionContext) -> List[Dict[str, Any]]:
        """
        Apply personality traits to influence action selection.
        
        Args:
            actions: List of possible actions
            context: Current decision context
            
        Returns:
            List of actions with personality-influenced scores
        """
        # Get personality traits
        traits = context.personality_traits
        
        # Calculate base scores for each action
        for action in actions:
            # Start with base score
            score = action.get("base_score", 0.5)
            
            # Apply risk tolerance influence
            if "risk_level" in action:
                risk_factor = action["risk_level"] - 0.5  # Normalize to [-0.5, 0.5]
                score += risk_factor * traits.risk_tolerance
            
            # Apply efficiency vs. enjoyment tradeoff
            if "efficiency" in action and "enjoyment" in action:
                efficiency_factor = action["efficiency"] - 0.5
                enjoyment_factor = action["enjoyment"] - 0.5
                score += (efficiency_factor * traits.efficiency_focus + 
                         enjoyment_factor * (1 - traits.efficiency_focus))
            
            # Apply social preference influence
            if "social" in action:
                social_factor = action["social"] - 0.5
                score += social_factor * traits.social_preference
            
            # Apply exploration vs. exploitation tradeoff
            if "exploration" in action:
                exploration_factor = action["exploration"] - 0.5
                score += exploration_factor * traits.exploration_preference
            
            # Apply goal orientation influence
            if "goal_progress" in action:
                goal_factor = action["goal_progress"] - 0.5
                score += goal_factor * traits.goal_orientation
            
            # Normalize score to [0, 1]
            score = max(0.0, min(1.0, score))
            action["personality_score"] = score
        
        # Sort actions by personality score
        actions.sort(key=lambda x: x["personality_score"], reverse=True)
        return actions

    def _evaluate_action_requirements(self, action: Dict[str, Any], context: DecisionContext) -> bool:
        """
        Evaluate if an action's requirements are met.
        
        Args:
            action: Action to evaluate
            context: Current decision context
            
        Returns:
            True if requirements are met, False otherwise
        """
        # Check area requirements
        if "required_area" in action and action["required_area"] != context.current_area:
            return False
        
        # Check quest requirements
        if "required_quest" in action:
            quest_name = action["required_quest"]
            if quest_name not in context.completed_quests:
                return False
        
        # Check skill requirements
        if "required_skills" in action:
            for skill, level in action["required_skills"].items():
                if context.skills.get(skill, 0) < level:
                    return False
        
        # Check wealth requirements
        if "required_wealth" in action and context.wealth < action["required_wealth"]:
            return False
        
        # Check item requirements
        if "required_items" in action:
            for item, count in action["required_items"].items():
                if context.inventory.get(item, 0) < count:
                    return False
        
        # Check personality-based requirements
        if "personality_requirements" in action:
            reqs = action["personality_requirements"]
            traits = context.personality_traits
            
            # Check risk tolerance requirement
            if "min_risk_tolerance" in reqs and traits.risk_tolerance < reqs["min_risk_tolerance"]:
                return False
            
            # Check efficiency focus requirement
            if "min_efficiency_focus" in reqs and traits.efficiency_focus < reqs["min_efficiency_focus"]:
                return False
            
            # Check social preference requirement
            if "min_social_preference" in reqs and traits.social_preference < reqs["min_social_preference"]:
                return False
        
        return True

    def select_action(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Select the best action based on current context and personality.
        
        Args:
            context: Current decision context
            
        Returns:
            Selected action
        """
        # Get available actions
        actions = self.get_possible_actions(context)
        
        # Filter actions based on requirements
        valid_actions = [
            action for action in actions 
            if self._evaluate_action_requirements(action, context)
        ]
        
        if not valid_actions:
            return {"type": "wait", "reason": "No valid actions available"}
        
        # Apply personality influence
        scored_actions = self._apply_personality_influence(valid_actions, context)
        
        # Select top action
        selected_action = scored_actions[0]
        
        # Log decision
        self.logger.info(
            f"Selected action: {selected_action['name']} "
            f"(score: {selected_action['personality_score']:.2f})"
        )
        
        return selected_action 