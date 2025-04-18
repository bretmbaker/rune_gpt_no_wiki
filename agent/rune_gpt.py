#!/usr/bin/env python3
"""
RuneGPT - OSRS AI Agent
Main entry point for running RuneGPT with session management and proper Tutorial Island progression.
"""

import os
import time
import json
import random
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass

from agent.memory import Memory
from agent.memory_types import MemoryEntry
from agent.skills import Skills
from agent.inventory import Inventory
from agent.decision_maker import DecisionMaker
from agent.resilience_tracker import ResilienceTracker
from agent.narrative_logger import NarrativeLogger
from agent.conversation_engine import ConversationEngine
from knowledge.semantic_query_engine import SemanticQueryEngine
from agent.tutorial_engine import TutorialProgressEngine
from agent.main_game_engine import MainGameEngine, GameAction
from agent.conversation_cli import ConversationCLI
from agent.player_mode import PlayerMode, PlayerModeManager
from agent.game_loop import GameLoop
from agent.xp_rate_model import XPRateModel
from agent.personality_config import PersonalityConfig, PersonalityConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("state/logs/rune_gpt.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rune_gpt")

@dataclass
class Action:
    """Represents an action that can be taken by the agent."""
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

class RuneGPT:
    def __init__(self, session_id: Optional[str] = None, load_memory: bool = False):
        """
        Initialize RuneGPT agent with session-based state management.
        
        Args:
            session_id: Unique identifier for this agent session (e.g., Player_001)
            load_memory: Whether to load existing memory for this session
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = self._generate_session_id()
        
        self.session_id = session_id
        self.state_dir = Path("state") / session_id
        
        # Create session-specific directories
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / "logs").mkdir(exist_ok=True)
        (self.state_dir / "memory").mkdir(exist_ok=True)
        (self.state_dir / "inventory").mkdir(exist_ok=True)
        (self.state_dir / "narrative").mkdir(exist_ok=True)
        
        # Initialize core components
        self.memory = Memory()  # Initialize with empty memory
        self.skills = Skills()
        self.inventory = Inventory()
        self.wiki_engine = SemanticQueryEngine()  # Initialize wiki engine
        self.tutorial_engine = TutorialProgressEngine()  # Initialize tutorial engine
        self.decision_maker = DecisionMaker(
            skills=self.skills,
            inventory=self.inventory,
            memory=self.memory,
            wiki_engine=self.wiki_engine
        )
        self.resilience_tracker = ResilienceTracker(self.memory)
        self.narrative_logger = NarrativeLogger(
            log_dir=str(self.state_dir / "narrative"),
            enabled=True,
            verbosity=2
        )
        self.conversation_engine = ConversationEngine(
            memory=self.memory,
            skills=self.skills,
            inventory=self.inventory,
            wiki_engine=self.wiki_engine
        )
        
        # Initialize game loop and XP rate model
        self.game_loop = GameLoop(self.state_dir)
        self.xp_model = XPRateModel(self.state_dir)
        
        # Initialize player mode manager
        self.player_mode_manager = PlayerModeManager()
        
        # Initialize main game engine
        self.main_game_engine = MainGameEngine(
            memory=self.memory,
            skills=self.skills,
            inventory=self.inventory,
            decision_maker=self.decision_maker,
            resilience_tracker=self.resilience_tracker,
            narrative_logger=self.narrative_logger,
            wiki_engine=self.wiki_engine,
            state_dir=self.state_dir,
            player_mode=self.player_mode_manager
        )
        
        # Game state variables
        self.tutorial_complete = False
        self.current_location = "Tutorial Island"
        self.quest_points = 0
        self.exploration_score = 0.0
        self.experimentation_score = 0.0
        self.action_stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "exploration_actions": 0,
            "skill_actions": 0,
            "quest_actions": 0
        }
        
        # Load personality config
        self.personality_manager = PersonalityConfigManager()
        self.personality = self.personality_manager.load_config(session_id)
        
        # Set player mode based on personality
        if self.personality.mode == "ironman":
            self.player_mode_manager.set_mode(PlayerMode.IRONMAN)
        else:
            self.player_mode_manager.set_mode(PlayerMode.REGULAR)
        
        # Load existing state or initialize new character
        if load_memory:
            self.load_state()
        else:
            self._initialize_new_character()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for a new character."""
        state_dir = Path("state")
        existing_sessions = [d for d in state_dir.iterdir() if d.is_dir() and d.name.startswith("Player_")]
        if not existing_sessions:
            return "Player_001"
        
        # Find the next available number
        numbers = [int(s.name.split("_")[1]) for s in existing_sessions]
        next_num = max(numbers) + 1
        return f"Player_{next_num:03d}"
    
    def _initialize_new_character(self):
        """Initialize a new character with default state."""
        # Generate random character name
        first_names = ["Adventurer", "Hero", "Warrior", "Mage", "Ranger"]
        last_names = ["of Gielinor", "the Brave", "the Wise", "the Swift", "the Bold"]
        character_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Log character creation
        self.narrative_logger.log_emotion(
            "excitement",
            f"Welcome to Gielinor, {character_name}! Your journey begins on Tutorial Island.",
            self.current_location
        )
        
        # Initialize memory with character creation
        self.memory.add_memory(MemoryEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type="creation",
            content=f"Created new character: {character_name}",
            tags=["creation", "tutorial"],
            emotions={"excitement": 0.8, "curiosity": 0.6}
        ))
        
        # Set initial tutorial state
        self.tutorial_engine.set_current_step("survival_expert_intro")
        
        # Save initial state
        self.save_state()
    
    def load_state(self):
        """Load agent state from session directory."""
        try:
            # Load memory
            memory_file = self.state_dir / "memory" / "memory.json"
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)
                    for entry_data in memory_data:
                        entry = MemoryEntry(**entry_data)
                        self.memory.add_memory(entry)
            
            # Load skills
            skills_file = self.state_dir / "skills.json"
            if skills_file.exists():
                with open(skills_file, 'r') as f:
                    self.skills.load_state(json.load(f))
            
            # Load inventory
            inventory_file = self.state_dir / "inventory" / "inventory.json"
            if inventory_file.exists():
                with open(inventory_file, 'r') as f:
                    self.inventory.load_state(json.load(f))
            
            # Load tutorial state
            tutorial_file = self.state_dir / "tutorial_progress.json"
            if tutorial_file.exists():
                with open(tutorial_file, 'r') as f:
                    self.tutorial_engine.load_state(json.load(f))
            
            # Load game state
            state_file = self.state_dir / "agent_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.tutorial_complete = state.get("is_tutorial_complete", False)
                    self.current_location = state.get("current_location", "Tutorial Island")
                    self.quest_points = state.get("quest_points", 0)
                    self.exploration_score = state.get("exploration_score", 0.0)
                    self.experimentation_score = state.get("experimentation_score", 0.0)
                    self.action_stats = state.get("action_stats", {
                        "total_actions": 0,
                        "successful_actions": 0,
                        "failed_actions": 0,
                        "exploration_actions": 0,
                        "skill_actions": 0,
                        "quest_actions": 0
                    })
            
            logger.info(f"Loaded state for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error loading state: {str(e)}")
            # Initialize new character if loading fails
            self._initialize_new_character()
    
    def save_state(self):
        """Save agent state to session directory."""
        try:
            # Save memory
            memory_data = [entry.__dict__ for entry in self.memory.get_memories()]
            with open(self.state_dir / "memory" / "memory.json", 'w') as f:
                json.dump(memory_data, f, indent=2)
            
            # Save skills
            with open(self.state_dir / "skills.json", 'w') as f:
                json.dump(self.skills.get_state(), f, indent=2)
            
            # Save inventory
            with open(self.state_dir / "inventory" / "inventory.json", 'w') as f:
                json.dump(self.inventory.get_state(), f, indent=2)
            
            # Save tutorial state
            with open(self.state_dir / "tutorial_progress.json", 'w') as f:
                json.dump(self.tutorial_engine.get_state(), f, indent=2)
            
            # Save game state
            state = {
                "is_tutorial_complete": self.tutorial_complete,
                "current_location": self.current_location,
                "quest_points": self.quest_points,
                "exploration_score": self.exploration_score,
                "experimentation_score": self.experimentation_score,
                "action_stats": self.action_stats
            }
            with open(self.state_dir / "agent_state.json", 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Saved state for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
    
    def perceive(self, screen_text: str) -> Dict[str, Any]:
        """
        Universal perception system that processes screen text and game state.
        
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
                self.current_location = location
            
            # Extract items from screen text
            items = self._extract_items(screen_text)
            for item in items:
                self.inventory.add_item(item, 1)
            
            # Extract skills from screen text
            skills = self._extract_skills(screen_text)
            for skill in skills:
                self.skills.add_xp(skill, 1)
            
            # Update exploration score
            self._update_exploration_score()
            
            # Create perception state
            perception = {
                "screen_text": screen_text,
                "location": self.current_location,
                "items": list(self.inventory.get_items()),
                "skills": list(self.skills.get_skills()),
                "exploration_score": self.exploration_score,
                "experimentation_score": self.experimentation_score,
                "is_tutorial_complete": self.tutorial_complete,
                "tutorial_progress": self.tutorial_engine.get_state() if not self.tutorial_complete else None
            }
            
            return perception
            
        except Exception as e:
            logger.error(f"Error in perception: {str(e)}")
            return {"screen_text": screen_text, "error": str(e)}
    
    def _extract_location(self, screen_text: str) -> Optional[str]:
        """Extract location from screen text."""
        # Check for known locations
        known_locations = ["Tutorial Island", "Lumbridge", "Varrock", "Falador", "Port Sarim", 
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
        location_score = len(self.game_loop.state.session_stats["areas_visited"]) / 20  # Assuming 20 major locations
        item_score = len(self.inventory.get_items()) / 100  # Assuming 100 major items
        skill_score = len(self.skills.get_skills()) / 23  # 23 skills in OSRS
        
        # Weighted average
        self.exploration_score = (location_score * 0.4) + (item_score * 0.3) + (skill_score * 0.3)
        
        # Ensure score is between 0 and 1
        self.exploration_score = max(0.0, min(1.0, self.exploration_score))
    
    def decide(self, perception: Dict[str, Any]) -> Optional[Action]:
        """
        Universal decision-making system that chooses actions based on perception.
        
        Args:
            perception: Dictionary containing the perceived state
            
        Returns:
            The chosen action or None if no suitable action is found
        """
        try:
            # Check if we're in tutorial and not complete
            if not self.tutorial_complete and perception.get("tutorial_progress"):
                # Use tutorial engine for decision making
                tutorial_result = self.tutorial_engine.process_screen_text(perception["screen_text"])
                
                if tutorial_result["action_required"]:
                    # Convert tutorial action to universal action
                    return self._convert_tutorial_action(tutorial_result)
            
            # Update decision maker with current state
            self.decision_maker.evaluate_current_state()
            
            # Query wiki for area information
            area_query = f"What can I do in {perception['location']}?"
            area_results = self.wiki_engine.query(area_query)
            
            # Query wiki for item information
            item_queries = []
            for item in perception["items"]:
                item_queries.append(f"What is {item} used for?")
            
            # Query wiki for skill information
            skill_queries = []
            for skill in perception["skills"]:
                skill_queries.append(f"Where can I use {skill} skill?")
            
            # Combine all queries
            all_queries = [area_query] + item_queries + skill_queries
            
            # Get possible actions
            actions = self.decision_maker.get_possible_actions()
            
            # Add exploration actions if experimentation score is high
            if self.experimentation_score > 0.5:
                exploration_actions = self._generate_exploration_actions(perception)
                actions.extend(exploration_actions)
            
            # Choose the best action
            chosen_action = self.decision_maker.choose_action()
            
            return chosen_action
            
        except Exception as e:
            logger.error(f"Error in decision making: {str(e)}")
        return None
    
    def _convert_tutorial_action(self, tutorial_result: Dict[str, Any]) -> Action:
        """Convert tutorial action to universal action format."""
        action_type = tutorial_result["action_type"]
        
        if action_type == "talk_to_npc":
            npc = tutorial_result["npc"]
            return Action(
                name=f"Talk to {npc}",
                description=f"Talk to {npc} to learn about the game",
                category="tutorial",
                location=self.current_location,
                required_items=[],
                required_skills={},
                expected_rewards=["knowledge", "tutorial progress"],
                risks=[],
                reasoning=f"I need to talk to {npc} to progress through the tutorial",
                priority=0.9
            )
        elif action_type == "continue_step":
            next_obj = tutorial_result.get("next_objective", "Continue tutorial")
            return Action(
                name="Continue Tutorial",
                description=next_obj,
                category="tutorial",
                location=self.current_location,
                required_items=[],
                required_skills={},
                expected_rewards=["tutorial progress"],
                risks=[],
                reasoning=f"I need to {next_obj} to progress through the tutorial",
                priority=0.8
            )
        elif action_type == "move_to_next_step":
            next_step = tutorial_result.get("next_step", "Next tutorial step")
            return Action(
                name="Move to Next Tutorial Step",
                description=f"Move to {next_step}",
                category="tutorial",
                location=self.current_location,
                required_items=[],
                required_skills={},
                expected_rewards=["tutorial progress"],
                risks=[],
                reasoning=f"I need to move to {next_step} to continue the tutorial",
                priority=0.7
            )
        else:
            # Default action
            return Action(
                name="Continue Tutorial",
                description="Continue with the tutorial",
                category="tutorial",
                location=self.current_location,
                required_items=[],
                required_skills={},
                expected_rewards=["tutorial progress"],
                risks=[],
                reasoning="I need to continue with the tutorial to learn about the game",
                priority=0.6
            )
    
    def _generate_exploration_actions(self, perception: Dict[str, Any]) -> List[Action]:
        """Generate exploration actions based on current state."""
        exploration_actions = []
        
        # Query wiki for nearby locations
        location_query = f"What locations are near {perception['location']}?"
        location_results = self.wiki_engine.query(location_query)
        
        if location_results:
            for result in location_results:
                if "locations" in result:
                    for location in result["locations"]:
                        if location not in self.game_loop.state.session_stats["areas_visited"]:
                            exploration_actions.append(Action(
                                name=f"Explore {location}",
                                description=f"Travel to {location} to discover new content",
                                category="exploration",
                                location=perception["location"],
                                required_items=[],
                                required_skills={},
                                expected_rewards=["discovery", "knowledge"],
                                risks=["getting lost"],
                                reasoning=f"I should explore {location} to discover new content",
                                priority=0.5 + (self.experimentation_score * 0.3)
                            ))
        
        # Query wiki for interesting items in the area
        item_query = f"What interesting items can be found in {perception['location']}?"
        item_results = self.wiki_engine.query(item_query)
        
        if item_results:
            for result in item_results:
                if "items" in result:
                    for item in result["items"]:
                        if item not in self.inventory.get_items():
                            exploration_actions.append(Action(
                                name=f"Find {item}",
                                description=f"Look for {item} in {perception['location']}",
                                category="exploration",
                                location=perception["location"],
                                required_items=[],
                                required_skills={},
                                expected_rewards=[item, "discovery"],
                                risks=[],
                                reasoning=f"I should look for {item} to discover new items",
                                priority=0.4 + (self.experimentation_score * 0.3)
                            ))
        
        return exploration_actions
    
    def act(self, action: Action) -> Dict[str, Any]:
        """
        Execute an action and return the result.
        
        Args:
            action: The action to execute
            
        Returns:
            Dictionary containing the result of the action
        """
        logger.info(f"Executing action: {action.name}")
        logger.info(f"Reasoning: {action.reasoning}")
        
        # Start the action in the game loop
        if not self.game_loop.start_action(action.name):
            logger.warning(f"Could not start action: {action.name}")
            return {
                "success": False,
                "message": "Could not start action",
                "action": action.name
            }
        
        # Execute the appropriate action based on tutorial completion
        if not self.tutorial_complete:
            result = self._execute_tutorial_action(action)
        else:
            result = self._execute_game_action(action)
        
        # End the action in the game loop and get rewards
        xp_gained, items_gained = self.game_loop.end_action()
        
        # Add XP and items to the result
        if xp_gained:
            result["xp_gained"] = xp_gained
            # Update skills with gained XP
            for skill, xp in xp_gained.items():
                self.skills.add_xp(skill, xp)
        
        if items_gained:
            result["items_gained"] = items_gained
            # Add items to inventory
            for item, amount in items_gained.items():
                self.inventory.add_item(item, amount)
        
        # Update action statistics
        self.action_stats["total_actions"] += 1
        if result.get("success", False):
            self.action_stats["successful_actions"] += 1
        else:
            self.action_stats["failed_actions"] += 1
        
        if action.category == "exploration":
            self.action_stats["exploration_actions"] += 1
        elif action.category == "skill":
            self.action_stats["skill_actions"] += 1
        elif action.category == "quest":
            self.action_stats["quest_actions"] += 1
        
        # Log the action result
        self.narrative_logger.log_action(action.name, result)
        
        # Save state after action
        self.save_state()
        
        return result
    
    def _execute_tutorial_action(self, action: Action) -> Dict[str, Any]:
        """Execute a tutorial action."""
        try:
            # Check if tutorial is complete
            if len(self.tutorial_engine.completed_steps) >= len(self.tutorial_engine.tutorial_steps):
                self.tutorial_complete = True
                self.narrative_logger.log_emotion(
                    "pride",
                    "Tutorial Island completed! Ready to begin the main adventure.",
                    self.current_location
                )
                return {"success": True, "tutorial_complete": True}
            
            # Execute tutorial action
            if "Talk to" in action.name:
                npc = action.name.split("Talk to ")[1]
                return {"success": True, "npc": npc}
            elif "Continue Tutorial" in action.name:
                return {"success": True, "progress": True}
            elif "Move to Next Tutorial Step" in action.name:
                return {"success": True, "next_step": True}
            else:
                return {"success": True}
                
        except Exception as e:
            logger.error(f"Error executing tutorial action: {str(e)}")
            return {"success": False, "reason": str(e)}
    
    def _execute_game_action(self, action: Action) -> Dict[str, Any]:
        """Execute a game action."""
        try:
            # Simulate action execution (replace with actual game logic)
            success = random.random() > 0.1  # 90% success rate for now
            
            if success:
                # Generate rewards
                rewards = []
                if "combat" in action.category:
                    rewards.append("combat experience")
                elif "skilling" in action.category:
                    rewards.append(f"{action.category} experience")
                elif "exploration" in action.category:
                    rewards.append("discovery")
                
                # Update experimentation score
                self.experimentation_score = min(1.0, self.experimentation_score + 0.05)
                
                return {
                    "success": True,
                    "rewards": rewards,
                    "death": False
                }
            else:
                # Simulate failure
                death = random.random() > 0.7  # 30% chance of death on failure
                
                if death:
                    self.resilience_tracker.increase_death_count()
                
                # Update experimentation score
                self.experimentation_score = max(0.0, self.experimentation_score - 0.02)
                
                return {
                    "success": False,
                    "death": death,
                    "reason": "Action failed"
                }
                
        except Exception as e:
            logger.error(f"Error executing game action: {str(e)}")
            return {"success": False, "reason": str(e)}
    
    def reflect(self, action: Action, result: Dict[str, Any]):
        """
        Universal reflection system that learns from actions and outcomes.
        
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
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                type="reflection",
                content=f"Reflected on {action.name}: {'success' if result['success'] else 'failure'}",
                tags=["reflection", "success" if result["success"] else "failure", action.category],
                emotions={"satisfaction" if result["success"] else "disappointment": 0.7}
            ))
            
            # Check for tutorial completion
            if result.get("tutorial_complete", False):
                self.tutorial_complete = True
                self.narrative_logger.log_emotion(
                    "pride",
                    "Tutorial Island completed! Ready to begin the main adventure.",
                    self.current_location
                )
            
            # Save state after reflection
            self.save_state()
            
        except Exception as e:
            logger.error(f"Error in reflection: {str(e)}")
    
    def process_screen_text(self, screen_text: str):
        """
        Process screen text through the perception-decision-action-reflection cycle.
        
        Args:
            screen_text: Text from the game screen
        """
        # Update game loop time
        self.game_loop._update_time()
        
        # Perceive the current state
        perception = self.perceive(screen_text)
        
        # Update game loop with new area if visited
        if perception.get("location") and perception["location"] not in self.game_loop.state.session_stats["areas_visited"]:
            self.game_loop.add_area_visited(perception["location"])
        
        # Decide on an action
        action = self.decide(perception)
        
        if action:
            # Execute the action
            result = self.act(action)
            
            # Reflect on the action and result
            self.reflect(action, result)
            
            # Check for tutorial completion
            if not self.tutorial_complete and self.tutorial_engine.is_complete():
                logger.info("Tutorial completed! Transitioning to main game...")
                self.tutorial_complete = True
                self.main_game_engine.transition_from_tutorial()
                self.current_location = "Lumbridge"
                
                # Add Lumbridge to visited areas
                self.game_loop.add_area_visited("Lumbridge")
                
                # Save state after tutorial completion
                self.save_state()
        else:
            logger.warning("No action decided based on perception")

def main():
    """Main entry point for RuneGPT."""
    try:
    parser = argparse.ArgumentParser(description="RuneGPT - OSRS AI Agent")
    parser.add_argument("--session", type=str, help="Session ID for this agent instance")
    parser.add_argument("--load", action="store_true", help="Load existing session state")
    args = parser.parse_args()
        
        logger.info("Initializing RuneGPT agent...")
    
    # Initialize agent
    agent = RuneGPT(session_id=args.session, load_memory=args.load)
        
        logger.info("Starting agent loop...")
    
    # Start agent loop
    try:
        while True:
            # Process screen text (simulated for now)
            screen_text = "You are in Tutorial Island. The Survival Expert is waiting to teach you."
            agent.process_screen_text(screen_text)
            time.sleep(1)  # Simulate game tick
            
    except KeyboardInterrupt:
        logger.info("Shutting down RuneGPT agent...")
        agent.save_state()
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 