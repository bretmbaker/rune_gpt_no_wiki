#!/usr/bin/env python3
"""
Main Game Engine for RuneGPT
Manages full-game logic once tutorial is complete
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

from agent.memory import Memory
from agent.memory_types import MemoryEntry
from agent.skills import Skills
from agent.inventory import Inventory
from agent.decision_maker import DecisionMaker
from agent.resilience_tracker import ResilienceTracker
from agent.narrative_logger import NarrativeLogger
from knowledge.semantic_query_engine import SemanticQueryEngine
from .player_mode import PlayerMode, PlayerModeManager
from .game_loop import GameLoop
from .xp_rate_model import XPRateModel
from .drop_rate_model import DropRateModel

logger = logging.getLogger(__name__)

@dataclass
class GameAction:
    """Represents an action that can be taken in the main game."""
    name: str
    description: str
    category: str
    location: str
    required_items: List[str]
    required_skills: Dict[str, int]
    expected_rewards: List[str]
    risks: List[str]
    reasoning: str
    priority: float
    confidence: float = 0.5
    requirements: Dict[str, any] = None
    xp_gain: Dict[str, int] = None
    item_gain: Dict[str, int] = None
    item_cost: Dict[str, int] = None

@dataclass
class GameState:
    """Represents the current state of the main game."""
    current_location: str
    quest_points: int
    total_level: int
    combat_level: int
    wealth: Dict[str, int]
    achievements: List[str]
    active_quests: List[str]
    completed_quests: List[str]
    unlocked_areas: List[str]
    last_death: Optional[str]
    death_count: int
    membership_days_remaining: Optional[int]
    last_bond_purchase: Optional[Dict]
    last_ge_transaction: Optional[Dict]
    active_grinds: List[str]  # Track ongoing drop grinds
    last_membership_check: Optional[float] = None
    is_member: bool = False

class MainGameEngine:
    """Manages full-game logic once tutorial is complete"""
    
    def __init__(self, 
                 memory: Memory,
                 skills: Skills,
                 inventory: Inventory,
                 decision_maker: DecisionMaker,
                 resilience_tracker: ResilienceTracker,
                 narrative_logger: NarrativeLogger,
                 wiki_engine: SemanticQueryEngine,
                 state_dir: Path,
                 player_mode: PlayerModeManager):
        """
        Initialize the main game engine.
        
        Args:
            memory: Memory component for storing experiences
            skills: Skills component for tracking skill levels
            inventory: Inventory component for managing items
            decision_maker: Decision maker for choosing actions
            resilience_tracker: Tracker for learning from failures
            narrative_logger: Logger for immersive storytelling
            wiki_engine: Semantic query engine for knowledge
            state_dir: Directory for saving state
            player_mode: Player mode manager for handling player mode-specific logic
        """
        self.memory = memory
        self.skills = skills
        self.inventory = inventory
        self.decision_maker = decision_maker
        self.resilience_tracker = resilience_tracker
        self.narrative_logger = narrative_logger
        self.wiki_engine = wiki_engine
        self.state_dir = state_dir
        self.player_mode = player_mode
        self.state_file = state_dir / "game_state.json"
        
        # Game state
        self.state = self._load_state()
        
        # Exploration and experimentation tracking
        self.exploration_score = 0.0  # 0.0 to 1.0, tracks how much of the game has been explored
        self.experimentation_score = 0.0  # 0.0 to 1.0, tracks willingness to try new things
        self.discovered_locations = set()  # Set of locations the agent has visited
        self.discovered_items = set()  # Set of items the agent has encountered
        self.discovered_skills = set()  # Set of skills the agent has used
        
        # Action chains tracking
        self.current_action_chain = []
        self.chain_start_time = time.time()
        
        # Initialize game loop and XP model
        self.game_loop = GameLoop(state_dir)
        self.xp_model = XPRateModel(state_dir)
        
        # Initialize action tracking
        self.action_stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "deaths": 0,
            "quests_completed": 0,
            "areas_unlocked": 0
        }
        
        self.drop_model = DropRateModel(state_dir)
    
    def _load_state(self) -> GameState:
        """Load game state from file or create default."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                return GameState(**data)
        return self._create_default_state()
    
    def _create_default_state(self) -> GameState:
        """Create default game state for a new character."""
        return GameState(
            current_location="Lumbridge",
            quest_points=0,
            total_level=32,  # Starting total level
            combat_level=3,  # Starting combat level
            wealth={'gp': 0, 'items_value': 0},
            achievements=[],
            active_quests=[],
            completed_quests=[],
            unlocked_areas=["Lumbridge", "Lumbridge Swamp", "Draynor Village"],
            last_death=None,
            death_count=0,
            membership_days_remaining=None,
            last_bond_purchase=None,
            last_ge_transaction=None,
            last_membership_check=None,
            is_member=False,
            active_grinds=[]
        )
    
    def save_state(self):
        """Save current game state to file."""
        data = {
            'current_location': self.state.current_location,
            'quest_points': self.state.quest_points,
            'total_level': self.state.total_level,
            'combat_level': self.state.combat_level,
            'wealth': self.state.wealth,
            'achievements': self.state.achievements,
            'active_quests': self.state.active_quests,
            'completed_quests': self.state.completed_quests,
            'unlocked_areas': self.state.unlocked_areas,
            'last_death': self.state.last_death,
            'death_count': self.state.death_count,
            'membership_days_remaining': self.state.membership_days_remaining,
            'last_bond_purchase': self.state.last_bond_purchase,
            'last_ge_transaction': self.state.last_ge_transaction,
            'last_membership_check': self.state.last_membership_check,
            'is_member': self.state.is_member,
            'active_grinds': self.state.active_grinds
        }
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def perceive(self, screen_text: str) -> Dict[str, Any]:
        """
        Process screen text and game state to create a perception.
        
        Args:
            screen_text: Text from the game screen
            
        Returns:
            Dictionary containing the perceived state
        """
        try:
            # Log screen text
            logger.info(f"Processing screen text: {screen_text}")
            
            # Extract location from screen text
            location = self._extract_location(screen_text)
            if location:
                self.state.current_location = location
                self.discovered_locations.add(location)
            
            # Extract items from screen text
            items = self._extract_items(screen_text)
            for item in items:
                self.discovered_items.add(item)
            
            # Extract skills from screen text
            skills = self._extract_skills(screen_text)
            for skill in skills:
                self.discovered_skills.add(skill)
            
            # Update exploration score
            self._update_exploration_score()
            
            # Create perception state
            perception = {
                "screen_text": screen_text,
                "location": self.state.current_location,
                "items": list(self.discovered_items),
                "skills": list(self.discovered_skills),
                "exploration_score": self.exploration_score,
                "experimentation_score": self.experimentation_score,
                "skill_levels": self.skills.get_state(),
                "inventory": self.inventory.get_state(),
                "quest_points": self.state.quest_points,
                "death_count": self.state.death_count,
                "current_action_chain": self.current_action_chain
            }
            
            return perception
            
        except Exception as e:
            logger.error(f"Error in perception: {str(e)}")
            return {"screen_text": screen_text, "error": str(e)}
    
    def _extract_location(self, screen_text: str) -> Optional[str]:
        """Extract location from screen text."""
        # Check for known locations
        known_locations = ["Lumbridge", "Varrock", "Falador", "Port Sarim", 
                          "Draynor Village", "Al Kharid", "Edgeville", "Barbarian Village"]
        
        for location in known_locations:
            if location in screen_text:
                return location
        
        # Query wiki for location information
        query = f"What location is described in this text: {screen_text}"
        results = self.wiki_engine.query(query)
        
        if results and "location" in results[0]:
            return results[0]["location"]
        
        return None
    
    def _extract_items(self, screen_text: str) -> List[str]:
        """Extract items from screen text."""
        items = []
        
        # Query wiki for item information
        query = f"What items are mentioned in this text: {screen_text}"
        results = self.wiki_engine.query(query)
        
        if results:
            for result in results:
                if "items" in result:
                    items.extend(result["items"])
        
        return items
    
    def _extract_skills(self, screen_text: str) -> List[str]:
        """Extract skills from screen text."""
        skills = []
        
        # Known skills
        known_skills = ["attack", "strength", "defence", "ranged", "prayer", "magic", 
                       "runecrafting", "construction", "hitpoints", "agility", "herblore", 
                       "thieving", "crafting", "fletching", "slayer", "hunter", "mining", 
                       "smithing", "fishing", "cooking", "firemaking", "woodcutting", "farming"]
        
        for skill in known_skills:
            if skill in screen_text.lower():
                skills.append(skill)
        
        # Query wiki for skill information
        query = f"What skills are mentioned in this text: {screen_text}"
        results = self.wiki_engine.query(query)
        
        if results:
            for result in results:
                if "skills" in result:
                    skills.extend(result["skills"])
        
        return skills
    
    def _update_exploration_score(self):
        """Update exploration score based on discovered content."""
        # Calculate exploration score based on discovered locations, items, and skills
        location_score = len(self.discovered_locations) / 20  # Assuming 20 major locations
        item_score = len(self.discovered_items) / 100  # Assuming 100 major items
        skill_score = len(self.discovered_skills) / 23  # 23 skills in OSRS
        
        # Weighted average
        self.exploration_score = (location_score * 0.4) + (item_score * 0.3) + (skill_score * 0.3)
        
        # Ensure score is between 0 and 1
        self.exploration_score = max(0.0, min(1.0, self.exploration_score))
    
    def decide(self, perception: Dict[str, Any]) -> Optional[GameAction]:
        """
        Decide on the next action based on perception.
        
        Args:
            perception: Dictionary containing the perceived state
            
        Returns:
            The chosen action or None if no suitable action is found
        """
        try:
            # Update decision maker with current state
            self.decision_maker.evaluate_current_state()
            
            # Query wiki for area information
            area_query = f"What can I do in {perception['location']}?"
            area_results = self.wiki_engine.query(area_query)
            
            # Query wiki for skill-based activities
            skill_query = f"What should I do at level {self.skills.get_highest_level()} with these items: {', '.join(self.inventory.get_items())}?"
            skill_results = self.wiki_engine.query(skill_query)
            
            # Query wiki for quest information
            quest_query = f"What quests are available near {perception['location']}?"
            quest_results = self.wiki_engine.query(quest_query)
            
            # Get possible actions from decision maker
            actions = self.decision_maker.get_possible_actions()
            
            # Add exploration actions if experimentation score is high
            if self.experimentation_score > 0.5:
                exploration_actions = self._generate_exploration_actions(perception)
                actions.extend(exploration_actions)
            
            # Add skill-based actions
            skill_actions = self._generate_skill_actions(perception)
            actions.extend(skill_actions)
            
            # Add quest actions
            quest_actions = self._generate_quest_actions(perception)
            actions.extend(quest_actions)
            
            # Filter out actions in avoided locations
            filtered_actions = []
            for action in actions:
                location = action.location
                can_retry, reason = self.resilience_tracker.can_retry_location(
                    location, 
                    {"attack": self.skills.get_level("attack"), 
                     "defence": self.skills.get_level("defence"),
                     "hitpoints": self.skills.get_level("hitpoints")}
                )
                
                if can_retry:
                    # Calculate confidence score
                    confidence = self.resilience_tracker.calculate_action_score(
                        action.name, 
                        {"location": location, "skills": self.skills.get_state()}
                    )
                    
                    # Create game action with confidence
                    game_action = GameAction(
                        name=action.name,
                        description=action.description,
                        category=action.category,
                        location=action.location,
                        required_items=action.required_items,
                        required_skills=action.required_skills,
                        expected_rewards=action.expected_rewards,
                        risks=action.risks,
                        reasoning=action.reasoning,
                        priority=action.priority,
                        confidence=confidence
                    )
                    
                    filtered_actions.append(game_action)
            
            # Sort by priority and confidence
            filtered_actions.sort(key=lambda a: a.priority * a.confidence, reverse=True)
            
            # Choose the best action
            if filtered_actions:
                chosen_action = filtered_actions[0]
                
                # Log the decision
                self.narrative_logger.log_action(
                    "decision",
                    f"Deciding to: {chosen_action.name}",
                    f"Reasoning: {chosen_action.reasoning} (Confidence: {chosen_action.confidence:.2f})"
                )
                
                return chosen_action
            
            return None
            
        except Exception as e:
            logger.error(f"Error in decision making: {str(e)}")
            return None
    
    def _generate_exploration_actions(self, perception: Dict[str, Any]) -> List[GameAction]:
        """Generate exploration actions based on current state."""
        exploration_actions = []
        
        # Query wiki for nearby locations
        location_query = f"What locations are near {perception['location']}?"
        location_results = self.wiki_engine.query(location_query)
        
        if location_results:
            for result in location_results:
                if "locations" in result:
                    for location in result["locations"]:
                        if location not in self.discovered_locations:
                            # Check if location is safe
                            can_retry, reason = self.resilience_tracker.can_retry_location(
                                location, 
                                {"attack": self.skills.get_level("attack"), 
                                 "defence": self.skills.get_level("defence"),
                                 "hitpoints": self.skills.get_level("hitpoints")}
                            )
                            
                            if can_retry:
                                exploration_actions.append(GameAction(
                                    name=f"Explore {location}",
                                    description=f"Travel to {location} to discover new content",
                                    category="exploration",
                                    location=perception["location"],
                                    required_items=[],
                                    required_skills={},
                                    expected_rewards=["discovery", "knowledge"],
                                    risks=["getting lost"],
                                    reasoning=f"I should explore {location} to discover new content",
                                    priority=0.5 + (self.experimentation_score * 0.3),
                                    confidence=0.7
                                ))
        
        # Query wiki for interesting items in the area
        item_query = f"What interesting items can be found in {perception['location']}?"
        item_results = self.wiki_engine.query(item_query)
        
        if item_results:
            for result in item_results:
                if "items" in result:
                    for item in result["items"]:
                        if item not in self.discovered_items:
                            exploration_actions.append(GameAction(
                                name=f"Find {item}",
                                description=f"Look for {item} in {perception['location']}",
                                category="exploration",
                                location=perception["location"],
                                required_items=[],
                                required_skills={},
                                expected_rewards=[item, "discovery"],
                                risks=[],
                                reasoning=f"I should look for {item} to discover new items",
                                priority=0.4 + (self.experimentation_score * 0.3),
                                confidence=0.8
                            ))
        
        return exploration_actions
    
    def _generate_skill_actions(self, perception: Dict[str, Any]) -> List[GameAction]:
        """Generate skill-based actions based on current state."""
        skill_actions = []
        
        # Get current skill levels
        skill_levels = self.skills.get_state()
        
        # Query wiki for skill training opportunities
        for skill, level in skill_levels.items():
            if level < 99:  # Max level is 99
                query = f"How can I train {skill} at level {level} near {perception['location']}?"
                results = self.wiki_engine.query(query)
                
                if results:
                    for result in results:
                        if "training_methods" in result:
                            for method in result["training_methods"]:
                                # Check if we have required items
                                required_items = method.get("required_items", [])
                                has_items = all(item in self.inventory.get_items() for item in required_items)
                                
                                if has_items:
                                    skill_actions.append(GameAction(
                                        name=f"Train {skill}",
                                        description=f"Train {skill} using {method.get('method', 'this method')}",
                                        category="skilling",
                                        location=perception["location"],
                                        required_items=required_items,
                                        required_skills={skill: level},
                                        expected_rewards=[f"{skill} experience"],
                                        risks=method.get("risks", []),
                                        reasoning=f"I should train {skill} to improve my abilities",
                                        priority=0.6 + (level / 99) * 0.3,  # Higher priority for lower levels
                                        confidence=0.8
                                    ))
        
        return skill_actions
    
    def _generate_quest_actions(self, perception: Dict[str, Any]) -> List[GameAction]:
        """Generate quest-related actions based on current state."""
        quest_actions = []
        
        # Query wiki for available quests
        query = f"What quests are available near {perception['location']}?"
        results = self.wiki_engine.query(query)
        
        if results:
            for result in results:
                if "quests" in result:
                    for quest in result["quests"]:
                        # Check if we meet requirements
                        required_skills = quest.get("required_skills", {})
                        meets_requirements = all(
                            self.skills.get_level(skill) >= level 
                            for skill, level in required_skills.items()
                        )
                        
                        if meets_requirements:
                            quest_actions.append(GameAction(
                                name=f"Start {quest['name']}",
                                description=f"Begin the {quest['name']} quest",
                                category="quest",
                                location=perception["location"],
                                required_items=quest.get("required_items", []),
                                required_skills=required_skills,
                                expected_rewards=["quest points", "experience", "rewards"],
                                risks=quest.get("risks", []),
                                reasoning=f"I should start the {quest['name']} quest to earn quest points",
                                priority=0.7,
                                confidence=0.9
                            ))
        
        return quest_actions
    
    def act(self, action: GameAction) -> Dict:
        """
        Execute a game action and return the results.
        
        Args:
            action: GameAction object to execute
            
        Returns:
            Dict containing action results and state updates
        """
        # Check if action can be performed
        can_perform, reason = self.can_perform_action(action)
        if not can_perform:
            return {
                'success': False,
                'message': reason,
                'state_updates': {}
            }
        
        # Execute action based on category
        if action.category == "membership":
            if action.name == "buy_bond":
                success = self.buy_bond()
                return {
                    'success': success,
                    'message': "Successfully bought bond" if success else "Failed to buy bond",
                    'state_updates': {
                        'wealth': self.state.wealth,
                        'last_bond_purchase': self.state.last_bond_purchase,
                        'last_ge_transaction': self.state.last_ge_transaction
                    }
                }
            elif action.name == "check_membership":
                membership_changed = self.check_membership_status()
                return {
                    'success': True,
                    'message': f"Membership days remaining: {self.state.membership_days_remaining}",
                    'state_updates': {
                        'membership_days_remaining': self.state.membership_days_remaining
                    } if membership_changed else {}
                }
            elif action.name == "redeem_bond":
                success = self.redeem_bond()
                return {
                    'success': success,
                    'message': "Successfully redeemed bond" if success else "Failed to redeem bond",
                    'state_updates': {
                        'membership_days_remaining': self.state.membership_days_remaining
                    }
                }
        
        # Handle other action categories
        elif action.category == "exploration":
            # Implement exploration logic
            pass
        elif action.category == "questing":
            # Implement quest logic
            pass
        elif action.category == "training":
            # Implement skill training logic
            pass
        
        return {
            'success': False,
            'message': f"Unknown action category: {action.category}",
            'state_updates': {}
        }
    
    def reflect(self, action: GameAction, result: Dict[str, Any]):
        """
        Reflect on an action and its result.
        
        Args:
            action: The action that was executed
            result: The result of the action
        """
        try:
            # Log reflection
            self.narrative_logger.log_action(
                "reflection",
                f"Reflecting on: {action.name}",
                f"The action was {'successful' if result['success'] else 'unsuccessful'}"
            )
            
            # Update memory with reflection
            self.memory.add_memory(MemoryEntry(
                timestamp=time.time(),
                date=time.strftime("%Y-%m-%d %H:%M:%S"),
                type="reflection",
                content=f"Reflected on {action.name}: {'success' if result['success'] else 'failure'}",
                tags=["reflection", "success" if result["success"] else "failure", action.category],
                emotions={"satisfaction" if result["success"] else "disappointment": 0.7}
            ))
            
            # Save state after reflection
            self.save_state()
            
        except Exception as e:
            logger.error(f"Error in reflection: {str(e)}")
    
    def process_screen_text(self, screen_text: str):
        """
        Process game screen text using the universal perception → decision → action → reflection system.
        
        Args:
            screen_text: Text from the game screen
        """
        try:
            # Perception
            perception = self.perceive(screen_text)
            
            # Decision
            action = self.decide(perception)
            
            # Action
            if action and time.time() - self.chain_start_time >= 300:
                result = self.act(action)
                
                # Reflection
                self.reflect(action, result)
            
            # Save state after processing
            self.save_state()
            
        except Exception as e:
            logger.error(f"Error processing screen text: {str(e)}")
    
    def transition_from_tutorial(self):
        """Handle transition from Tutorial Island to main game."""
        self.logger.info("Transitioning from Tutorial Island to main game")
        self.state.current_location = "Lumbridge"
        self.state.total_level = self.skills.get_total_level()
        self.state.combat_level = self.skills.get_combat_level()
        self.save_state()
        
        # Add initial game knowledge to memory
        self.memory.add_memory(
            "Tutorial Island completed",
            "I have completed the tutorial and arrived in Lumbridge. "
            "I should explore the area and look for quests to begin my adventure."
        )
    
    def update_state(self, screen_text: str):
        """Update game state based on screen text and current actions."""
        # Update levels
        self.state.total_level = self.skills.get_total_level()
        self.state.combat_level = self.skills.get_combat_level()
        
        # Update wealth
        self.state.wealth = self.player_mode.status.wealth
        
        # Check for deaths
        if "Oh dear, you are dead!" in screen_text:
            self._handle_death()
        
        self.save_state()
    
    def _handle_death(self):
        """Handle player death and associated consequences."""
        self.state.death_count += 1
        self.state.last_death = "Recent death"
        
        # Handle mode-specific death consequences
        if self.player_mode.status.mode == PlayerMode.HARDCORE_IRONMAN:
            self.logger.warning("Hardcore Ironman death - losing status")
            self.player_mode.set_mode(PlayerMode.REGULAR)
        elif self.player_mode.status.mode == PlayerMode.ULTIMATE_IRONMAN:
            self.logger.warning("Ultimate Ironman death - losing status")
            self.player_mode.set_mode(PlayerMode.REGULAR)
        
        # Add death memory
        self.memory.add_memory(
            f"Death #{self.state.death_count}",
            f"I have died. This is my {self.state.death_count}th death. "
            "I should be more careful and better prepare for dangerous situations."
        )
    
    def get_available_actions(self) -> List[GameAction]:
        """
        Get list of available actions based on current game state.
        
        Returns:
            List[GameAction]: List of available actions
        """
        actions = []
        
        # Add membership-related actions
        if self.state.membership_days_remaining is None:
            # F2P player actions
            if self.can_buy_bond():
                actions.append(GameAction(
                    name="buy_bond",
                    description="Buy a bond from the Grand Exchange",
                    category="membership",
                    requirements={"wealth": 5000000},
                    reasoning="I need to buy a bond to become a member"
                ))
        else:
            # Member actions
            actions.append(GameAction(
                name="check_membership",
                description="Check membership status",
                category="membership",
                requirements={},
                reasoning="I should check my membership status"
            ))
            
            if self.inventory.has_item("Bond"):
                actions.append(GameAction(
                    name="redeem_bond",
                    description="Redeem a bond for membership",
                    category="membership",
                    requirements={"item": "Bond"},
                    reasoning="I can redeem my bond to extend membership"
                ))
        
        # Add exploration actions
        for area in self.state.unlocked_areas:
            actions.append(GameAction(
                name=f"explore_{area.lower()}",
                description=f"Explore {area}",
                category="exploration",
                location=area,
                required_items=[],
                required_skills={},
                expected_rewards=["discovery", "knowledge"],
                risks=["getting lost"],
                reasoning=f"I should explore {area} to unlock new content",
                priority=0.5,
                confidence=0.7
            ))
        
        # Add quest actions
        for quest in self._get_available_quests():
            actions.append(GameAction(
                name=f"start_quest_{quest.lower()}",
                description=f"Start {quest} quest",
                category="questing",
                location=quest,
                required_items=self._get_quest_requirements(quest)["items"],
                required_skills=self._get_quest_requirements(quest)["skills"],
                expected_rewards=["quest points", "experience", "rewards"],
                risks=self._get_quest_requirements(quest)["risks"],
                reasoning=f"I should start the {quest} quest",
                priority=0.7,
                confidence=0.9
            ))
        
        # Add training actions
        for skill, level in self._get_trainable_skills().items():
            method = self.xp_model.get_method_for_skill_level(skill, level)
            if method:
                actions.append(GameAction(
                    name=f"train_{skill.lower()}_{method['name'].lower()}",
                    description=f"Train {skill} using {method['name']}",
                    category="training",
                    location=skill,
                    required_items=method["requirements"],
                    required_skills={skill: level},
                    expected_rewards=method["xp_gain"],
                    risks=method.get("risks", []),
                    reasoning=f"I should train my {skill} level",
                    priority=0.6 + (level / 99) * 0.3,
                    confidence=0.8
                ))
        
        return actions
    
    def can_perform_action(self, action: GameAction) -> bool:
        """
        Check if an action can be performed based on current game state.
        
        Args:
            action (GameAction): The action to check
            
        Returns:
            bool: True if the action can be performed, False otherwise
        """
        # Check membership requirements
        if action.category == "membership":
            if action.name == "buy_bond":
                return self.can_buy_bond()
            elif action.name == "redeem_bond":
                return self.inventory.has_item("Bond")
            elif action.name == "check_membership":
                return self.state.membership_days_remaining is not None
        
        # Check area requirements
        if "area" in action.requirements:
            area = action.requirements["area"]
            if not self.state.unlocked_areas or area not in self.state.unlocked_areas:
                return False
        
        # Check quest requirements
        if "quest" in action.requirements:
            quest = action.requirements["quest"]
            if not self._get_available_quests() or quest not in self._get_available_quests():
                return False
            if quest in self.state.completed_quests:
                return False
        
        # Check skill requirements
        if "skills" in action.requirements:
            for skill, level in action.requirements["skills"].items():
                if self.skills.get_level(skill) < level:
                    return False
        
        # Check wealth requirements
        if "wealth" in action.requirements:
            if self.state.wealth < action.requirements["wealth"]:
                return False
        
        # Check item requirements
        if "items" in action.requirements:
            for item, amount in action.requirements["items"].items():
                if not self.inventory.has_item(item, amount):
                    return False
        
        return True

    def check_membership_status(self) -> bool:
        """
        Check and update the player's membership status.
        
        Returns:
            bool: True if the player is a member, False otherwise
        """
        current_time = time.time()
        if (self.state.last_membership_check and 
            current_time - self.state.last_membership_check < 3600):  # 1 hour cooldown
            return self.state.is_member
        
        self.state.last_membership_check = current_time
        
        if self.state.membership_days_remaining is None:
            self.state.is_member = False
            return False
        
        if self.state.membership_days_remaining <= 0:
            self.state.is_member = False
            self.state.membership_days_remaining = None
            return False
        
        # Update membership days remaining
        days_elapsed = (current_time - self.state.last_membership_check) / 86400
        self.state.membership_days_remaining = max(0, self.state.membership_days_remaining - days_elapsed)
        self.state.is_member = self.state.membership_days_remaining > 0
        
        return self.state.is_member

    def can_buy_bond(self) -> bool:
        """
        Check if the player can buy a bond.
        
        Returns:
            bool: True if the player can buy a bond, False otherwise
        """
        if self.state.is_member:
            return False
        
        current_time = time.time()
        if (self.state.last_bond_purchase and 
            current_time - self.state.last_bond_purchase < 86400):  # 24 hour cooldown
            return False
        
        return self.state.wealth >= self.BOND_COST

    def buy_bond(self) -> bool:
        """
        Attempt to buy a bond from the Grand Exchange.
        
        Returns:
            bool: True if the bond was purchased successfully, False otherwise
        """
        if not self.can_buy_bond():
            return False
        
        self.state.wealth -= self.BOND_COST
        self.inventory.add_item("Bond")
        self.state.last_bond_purchase = time.time()
        return True

    def redeem_bond(self) -> bool:
        """
        Attempt to redeem a bond for membership.
        
        Returns:
            bool: True if the bond was redeemed successfully, False otherwise
        """
        if not self.inventory.has_item("Bond"):
            return False
        
        self.inventory.remove_item("Bond")
        self.state.is_member = True
        self.state.membership_days_remaining = 14  # 14 days of membership
        return True

    def _get_available_quests(self) -> List[str]:
        """Get list of available quests based on requirements"""
        # This would be expanded based on quest requirements
        return ["Cook's Assistant", "Sheep Shearer"]

    def _get_quest_requirements(self, quest: str) -> Dict[str, any]:
        """Get requirements for a specific quest"""
        # This would be expanded with actual quest requirements
        return {
            "quest_points": 0,
            "skills": {},
            "items": [],
            "risks": []
        }

    def _get_trainable_skills(self) -> Dict[str, int]:
        """Get skills that can be trained at current level"""
        # This would be expanded with actual skill levels
        return {
            "attack": 1,
            "strength": 1,
            "defence": 1,
            "mining": 1,
            "fishing": 1,
            "cooking": 1
        }

    def start_grind(self, name: str, location: str, rate: str) -> bool:
        """Start tracking a new drop grind."""
        if name not in self.state.active_grinds:
            success = self.drop_model.start_grind(name, location, rate)
            if success:
                self.state.active_grinds.append(name)
                self.save_state()
            return success
        return False

    def update_grind(self, name: str, attempts: int, obtained: bool) -> Dict[str, Any]:
        """Update progress on a drop grind."""
        if name in self.state.active_grinds:
            result = self.drop_model.update_grind(name, attempts, obtained)
            if obtained:
                self.state.active_grinds.remove(name)
                self.save_state()
            return result
        return {}

    def get_grind_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific grind."""
        return self.drop_model.get_grind(name)

    def should_continue_grind(self, name: str) -> bool:
        """Determine if we should continue a grind based on patience and luck."""
        return self.drop_model.should_continue_grind(name)

    def simulate_drop(self, chance: str, attempts: int) -> Dict[str, Any]:
        """Simulate a drop with the given chance and attempts."""
        return self.drop_model.simulate_drop(chance, attempts)

    def get_available_actions(self) -> List[Dict[str, Any]]:
        """Get list of available actions based on current state."""
        actions = []
        
        # Load wiki data
        wiki_data = self._load_wiki_data()
        
        # Add exploration actions
        for area in self.state.unlocked_areas:
            area_data = wiki_data.get(area, {})
            if area_data:
                actions.append({
                    "type": "explore",
                    "target": area,
                    "requirements": {
                        "area": area,
                        "quest": area_data.get("metadata", {}).get("quest_requirement"),
                        "skill": area_data.get("metadata", {}).get("skill_requirement"),
                        "item": area_data.get("metadata", {}).get("item_requirement")
                    }
                })
        
        # Add quest actions
        for quest in self.state.active_quests:
            quest_data = wiki_data.get(quest, {})
            if quest_data:
                actions.append({
                    "type": "quest",
                    "target": quest,
                    "requirements": {
                        "quest": quest,
                        "skill": quest_data.get("metadata", {}).get("skill_requirement"),
                        "item": quest_data.get("metadata", {}).get("item_requirement")
                    }
                })
        
        # Add training actions
        for skill in self.skills.skills:
            skill_data = wiki_data.get(f"training_{skill}", {})
            if skill_data:
                actions.append({
                    "type": "train",
                    "target": skill,
                    "requirements": {
                        "skill": skill,
                        "item": skill_data.get("metadata", {}).get("item_requirement")
                    }
                })
        
        # Add membership actions
        if not self.player_mode.is_member:
            actions.append({
                "type": "membership",
                "target": "buy_bond",
                "requirements": {
                    "wealth": 7000000  # Default bond price
                }
            })
        
        return actions

    def can_perform_action(self, action: Dict[str, Any]) -> bool:
        """Check if an action can be performed based on requirements."""
        # Check membership requirements
        if action["type"] in ["buy_bond", "redeem_bond", "check_membership"]:
            return True  # These actions are always available
        
        # Check area requirements
        if "area" in action["requirements"]:
            if action["requirements"]["area"] not in self.state.unlocked_areas:
                return False
        
        # Check quest requirements
        if "quest" in action["requirements"]:
            if action["requirements"]["quest"] not in self.state.completed_quests:
                return False
        
        # Check skill requirements
        if "skill" in action["requirements"]:
            skill_req = action["requirements"]["skill"]
            if isinstance(skill_req, dict):
                for skill, level in skill_req.items():
                    if self.skills.get_level(skill) < level:
                        return False
            elif isinstance(skill_req, str):
                if self.skills.get_level(skill_req) < 1:
                    return False
        
        # Check wealth requirements
        if "wealth" in action["requirements"]:
            if self.state.wealth < action["requirements"]["wealth"]:
                return False
        
        # Check item requirements
        if "item" in action["requirements"]:
            item_req = action["requirements"]["item"]
            if isinstance(item_req, list):
                for item in item_req:
                    if not self.inventory.has_item(item):
                        return False
            elif isinstance(item_req, str):
                if not self.inventory.has_item(item_req):
                    return False
        
        return True

    def update_state(self, screen_text: str) -> Dict[str, Any]:
        """Update game state based on screen text."""
        # Handle player death
        if "Oh dear, you are dead!" in screen_text:
            self.state.last_death = datetime.now().isoformat()
            self.state.death_count += 1
            self.save_state()
            return {"death": True, "death_count": self.state.death_count}

        # Handle grind updates
        for grind_name in self.state.active_grinds[:]:  # Copy list to allow modification during iteration
            grind_info = self.get_grind_info(grind_name)
            if grind_info and "obtained" in screen_text.lower():
                self.update_grind(grind_name, 1, True)
                return {"grind_complete": True, "item": grind_name}

        return {"death": False, "grind_complete": False}

    def transition_from_tutorial(self):
        """Handle transition from Tutorial Island to main game."""
        self.state.current_location = "Lumbridge"
        self.save_state()
        return {
            "success": True,
            "message": "Welcome to the mainland! You find yourself in Lumbridge.",
            "location": "Lumbridge"
        }

    def _load_wiki_data(self) -> Dict[str, Dict[str, Any]]:
        """Load game data from wiki_data directory."""
        wiki_data = {}
        
        # Define paths to wiki data categories
        wiki_categories = [
            "quests",
            "minigames",
            "achievement_diaries",
            "combat_achievements",
            "training_guides",
            "tutorial_island",
            "skills",
            "items",
            "npcs",
            "bosses",
            "bestiary",
            "bestiary_f2p",
            "pets",
            "collection_log",
            "clue_scrolls",
            "shops",
            "teleport_methods",
            "shortcuts"
        ]
        
        # Load data from each category
        for category in wiki_categories:
            wiki_dir = Path("wiki_data") / category
            if not wiki_dir.exists():
                continue
                
            # Load metadata.json
            metadata_file = wiki_dir / "metadata.json"
            if not metadata_file.exists():
                continue
                
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                # Load txt files referenced in metadata
                txt_dir = wiki_dir / "txt"
                if txt_dir.exists():
                    for name, data in metadata.items():
                        txt_file = txt_dir / data["txt"].split("/")[-1]
                        if txt_file.exists():
                            with open(txt_file, 'r') as f:
                                content = f.read()
                                wiki_data[name] = {
                                    "content": content,
                                    "category": category,
                                    "metadata": data,
                                    "type": data.get("type", "general")
                                }
            except Exception as e:
                logger.error(f"Error loading wiki data from {category}: {str(e)}")
        
        return wiki_data 