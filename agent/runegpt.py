import json
import logging
import os
import random
import time
from typing import Dict, List, Optional, Any, Tuple

from agent.action import Action
from agent.game_state import GameState
from agent.action_memory import ActionMemory

# Configure logging
logger = logging.getLogger("RuneGPT")

class RuneGPT:
    """
    The main AI agent that processes game state and decides on the next action.
    This class integrates with the existing RuneGPT trial-and-error AI engine.
    """
    
    def __init__(self, session_id: str, load_memory: bool = True):
        """
        Initialize the RuneGPT agent.
        
        Args:
            session_id: The unique identifier for this player session
            load_memory: Whether to load existing memory for this session
        """
        self.session_id = session_id
        self.session_start_time = time.time()
        self.last_action_time = time.time()
        self.action_count = 0
        self.success_count = 0
        self.failure_count = 0
        
        # Initialize action memory
        self.action_memory = ActionMemory()
        
        # Load existing memory if requested
        if load_memory:
            self.load_memory()
        
        # Initialize state tracking
        self.current_step = ""
        self.current_objective = ""
        self.tutorial_progress = {}
        self.inventory_history = []
        self.location_history = []
        
        # Tutorial completion tracking
        self.tutorial_complete = False
        self.tutorial_completion_time = None
        self.tutorial_completion_reason = None
        self.tutorial_completion_path = []
        
        logger.info(f"Initialized RuneGPT agent for session {session_id}")
    
    def process_game_state(self, game_state: GameState) -> Action:
        """
        Process the current game state and decide on the next action.
        
        Args:
            game_state: The current state of the game
            
        Returns:
            An Action object representing the next action to take
        """
        logger.info(f"Processing game state for session {self.session_id}")
        
        # Update session ID if not set
        if not game_state.session_id:
            game_state.session_id = self.session_id
        
        # Extract key information
        screen_text = game_state.screen_text
        chatbox = game_state.chatbox
        player_location = game_state.player_location
        inventory = game_state.inventory
        step = game_state.step
        
        # Check for tutorial completion
        if not self.tutorial_complete:
            self._check_tutorial_completion(screen_text, player_location, step)
        
        # If tutorial is complete, return a special action
        if self.tutorial_complete:
            return self._create_completion_action(game_state)
        
        # Update state tracking
        if step and step != self.current_step:
            self.current_step = step
            logger.info(f"Step updated to: {self.current_step}")
            
            # Record step in completion path
            if step not in self.tutorial_completion_path:
                self.tutorial_completion_path.append(step)
        
        # Update inventory history
        if inventory:
            self.inventory_history.append((time.time(), inventory))
            # Keep only the last 10 inventory states
            if len(self.inventory_history) > 10:
                self.inventory_history.pop(0)
        
        # Update location history
        if player_location:
            self.location_history.append((time.time(), player_location))
            # Keep only the last 10 locations
            if len(self.location_history) > 10:
                self.location_history.pop(0)
        
        # Process screen text to extract information
        objective = self._extract_objective(screen_text, chatbox)
        if objective and objective != self.current_objective:
            self.current_objective = objective
            logger.info(f"Objective updated to: {self.current_objective}")
        
        # Get available actions based on the current state
        available_actions = self._get_available_actions(game_state)
        
        # Get the best action based on the current state
        action_name, confidence = self.action_memory.get_best_action(
            available_actions=available_actions,
            screen_text=screen_text,
            current_step=self.current_step,
            current_objective=self.current_objective
        )
        
        # If no action is available, return a default action
        if not action_name:
            logger.warning("No suitable action found, using default action")
            return self._create_default_action(game_state)
        
        # Create the action object
        action = self._create_action(action_name, confidence, game_state)
        
        # Update action tracking
        self.action_count += 1
        self.last_action_time = time.time()
        
        # Save memory after each action
        self.save_memory()
        
        return action
    
    def _check_tutorial_completion(self, screen_text: str, player_location: str, step: str) -> None:
        """
        Check if the tutorial is complete based on screen text or location.
        
        Args:
            screen_text: The text displayed on the screen
            player_location: The current player location
            step: The current tutorial step
        """
        # Check for completion message in screen text
        completion_messages = [
            "You have completed the Tutorial Island!",
            "Congratulations! You have completed the Tutorial Island!",
            "You are now ready to leave Tutorial Island",
            "You will be teleported to Lumbridge"
        ]
        
        for message in completion_messages:
            if message in screen_text:
                self._complete_tutorial("screen_text", message)
                return
        
        # Check for location change to Lumbridge
        if "Lumbridge" in player_location and "Tutorial Island" not in player_location:
            self._complete_tutorial("location", "Player teleported to Lumbridge")
            return
        
        # Check for final step completion
        if step == "final_gate" and "You are now ready to leave Tutorial Island" in screen_text:
            self._complete_tutorial("step", "Final gate step completed")
            return
    
    def _complete_tutorial(self, reason: str, details: str) -> None:
        """
        Mark the tutorial as complete and log celebration message.
        
        Args:
            reason: The reason for completion (screen_text, location, step)
            details: Additional details about the completion
        """
        if self.tutorial_complete:
            return  # Already completed
        
        self.tutorial_complete = True
        self.tutorial_completion_time = time.time()
        self.tutorial_completion_reason = f"{reason}: {details}"
        
        # Calculate completion time
        completion_time = self.tutorial_completion_time - self.session_start_time
        minutes = int(completion_time // 60)
        seconds = int(completion_time % 60)
        
        # Log celebration message
        logger.info("=" * 50)
        logger.info("🎉 TUTORIAL COMPLETED! 🎉")
        logger.info(f"Session: {self.session_id}")
        logger.info(f"Completion time: {minutes} minutes, {seconds} seconds")
        logger.info(f"Reason: {self.tutorial_completion_reason}")
        logger.info(f"Steps taken: {len(self.tutorial_completion_path)}")
        logger.info(f"Actions taken: {self.action_count}")
        logger.info(f"Success rate: {self.success_count / max(1, self.action_count):.2%}")
        logger.info("=" * 50)
        
        # Save completion data
        self.save_memory()
    
    def _create_completion_action(self, game_state: GameState) -> Action:
        """
        Create a special action for when the tutorial is complete.
        
        Args:
            game_state: The current state of the game
            
        Returns:
            An Action object representing the completion action
        """
        # Create a special completion action
        action = Action(
            name="Tutorial Complete",
            confidence=1.0,
            reasoning="The tutorial has been completed successfully!",
            emotion="excited"
        )
        
        # Add completion details
        action.message = "Congratulations! You have completed the Tutorial Island!"
        action.delay = 5.0  # Longer delay to allow celebration
        
        return action
    
    def _extract_objective(self, screen_text: str, chatbox: List[str]) -> str:
        """
        Extract the current objective from the screen text and chatbox.
        
        Args:
            screen_text: The text displayed on the screen
            chatbox: The messages in the chatbox
            
        Returns:
            The extracted objective, or an empty string if none found
        """
        # Combine screen text and chatbox for analysis
        full_text = screen_text + " " + " ".join(chatbox)
        
        # Look for objective indicators
        objective_indicators = [
            "talk to", "speak to", "find", "locate", "get", "obtain", "collect",
            "gather", "chop", "mine", "fish", "cook", "craft", "make", "create",
            "build", "complete", "finish", "start", "begin", "continue"
        ]
        
        for indicator in objective_indicators:
            if indicator in full_text.lower():
                # Extract the objective
                start_idx = full_text.lower().find(indicator)
                end_idx = full_text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(full_text)
                
                objective = full_text[start_idx:end_idx].strip()
                return objective
        
        return ""
    
    def _get_available_actions(self, game_state: GameState) -> List[str]:
        """
        Get the available actions based on the current game state.
        
        Args:
            game_state: The current state of the game
            
        Returns:
            A list of available action names
        """
        # This is a simplified version - in a real implementation,
        # this would be more sophisticated based on the game state
        available_actions = [
            "Talk to NPC",
            "Walk to Location",
            "Interact with Object",
            "Use Item",
            "Equip Item",
            "Drop Item",
            "Eat Food",
            "Drink Potion",
            "Cast Spell",
            "Attack Monster",
            "Chop Tree",
            "Mine Rock",
            "Fish",
            "Cook Food",
            "Craft Item",
            "Open Door",
            "Climb Ladder",
            "Cross Bridge",
            "Enter Cave",
            "Leave Cave"
        ]
        
        # Filter actions based on inventory
        if not game_state.inventory:
            available_actions = [a for a in available_actions if not any(item in a for item in ["Use", "Equip", "Drop", "Eat", "Drink"])]
        
        # Filter actions based on location
        if "Tutorial Island" in game_state.player_location:
            available_actions.extend([
                "Talk to Survival Expert",
                "Talk to Fishing Expert",
                "Talk to Mining Expert",
                "Talk to Combat Expert",
                "Talk to Quest Guide",
                "Talk to Banker",
                "Talk to Account Guide"
            ])
        
        return available_actions
    
    def _create_action(self, action_name: str, confidence: float, game_state: GameState) -> Action:
        """
        Create an Action object based on the action name and confidence.
        
        Args:
            action_name: The name of the action
            confidence: The confidence score for the action
            game_state: The current state of the game
            
        Returns:
            An Action object
        """
        # Generate reasoning based on the action and game state
        reasoning = self._generate_reasoning(action_name, game_state)
        
        # Generate emotion based on the action and confidence
        emotion = self._generate_emotion(action_name, confidence)
        
        # Create the action
        action = Action(
            name=action_name,
            confidence=confidence,
            reasoning=reasoning,
            emotion=emotion
        )
        
        # Add optional fields
        if "Talk to" in action_name:
            action.delay = 1.0
            action.message = f"Approaching {action_name.replace('Talk to ', '')}..."
        elif "Walk to" in action_name:
            action.delay = 2.0
            action.message = f"Walking to {action_name.replace('Walk to ', '')}..."
        elif "Chop" in action_name or "Mine" in action_name or "Fish" in action_name:
            action.delay = 3.0
            action.message = f"Gathering resources..."
        
        return action
    
    def _create_default_action(self, game_state: GameState) -> Action:
        """
        Create a default action when no suitable action is found.
        
        Args:
            game_state: The current state of the game
            
        Returns:
            A default Action object
        """
        # Default actions based on location
        if "Tutorial Island" in game_state.player_location:
            action_name = "Explore Tutorial Island"
            reasoning = "Exploring the island to find NPCs and objects to interact with."
        else:
            action_name = "Look Around"
            reasoning = "Looking around to find something to interact with."
        
        return Action(
            name=action_name,
            confidence=0.5,
            reasoning=reasoning,
            emotion="curious"
        )
    
    def _generate_reasoning(self, action_name: str, game_state: GameState) -> str:
        """
        Generate reasoning for the action based on the game state.
        
        Args:
            action_name: The name of the action
            game_state: The current state of the game
            
        Returns:
            A string explaining the reasoning for the action
        """
        # Base reasoning
        reasoning = f"Choosing to {action_name.lower()} because "
        
        # Add context-specific reasoning
        if self.current_objective:
            reasoning += f"the current objective is to {self.current_objective}. "
        
        if self.current_step:
            reasoning += f"We are at step '{self.current_step}'. "
        
        # Add inventory-based reasoning
        if "Use" in action_name or "Equip" in action_name:
            item = action_name.split(" ")[-1]
            if item in game_state.inventory:
                reasoning += f"We have a {item} in our inventory. "
            else:
                reasoning += f"We need to obtain a {item}. "
        
        # Add location-based reasoning
        if "Walk to" in action_name:
            location = action_name.replace("Walk to ", "")
            reasoning += f"We need to get to {location}. "
        
        # Add NPC-based reasoning
        if "Talk to" in action_name:
            npc = action_name.replace("Talk to ", "")
            reasoning += f"We need to speak with {npc} to progress. "
        
        return reasoning
    
    def _generate_emotion(self, action_name: str, confidence: float) -> str:
        """
        Generate an emotion for the action based on the action name and confidence.
        
        Args:
            action_name: The name of the action
            confidence: The confidence score for the action
            
        Returns:
            A string representing the emotion
        """
        # Base emotions
        emotions = {
            "Talk to": "friendly",
            "Walk to": "determined",
            "Interact with": "curious",
            "Use": "focused",
            "Equip": "prepared",
            "Drop": "practical",
            "Eat": "satisfied",
            "Drink": "refreshed",
            "Cast": "concentrated",
            "Attack": "brave",
            "Chop": "industrious",
            "Mine": "industrious",
            "Fish": "patient",
            "Cook": "creative",
            "Craft": "creative",
            "Open": "exploratory",
            "Climb": "adventurous",
            "Cross": "cautious",
            "Enter": "adventurous",
            "Leave": "relieved",
            "Explore": "curious",
            "Look": "observant"
        }
        
        # Find the matching emotion
        for key, emotion in emotions.items():
            if key in action_name:
                return emotion
        
        # Default emotions based on confidence
        if confidence > 0.8:
            return "confident"
        elif confidence > 0.5:
            return "hopeful"
        else:
            return "uncertain"
    
    def save_memory(self) -> None:
        """Save the agent's memory to disk."""
        # Create the session directory if it doesn't exist
        session_dir = os.path.join("state", self.session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Save action memory
        memory_dir = os.path.join(session_dir, "memory")
        os.makedirs(memory_dir, exist_ok=True)
        self.action_memory.save(memory_dir)
        
        # Save tutorial progress
        tutorial_file = os.path.join(session_dir, "tutorial_progress.json")
        with open(tutorial_file, "w") as f:
            json.dump(self.tutorial_progress, f)
        
        # Save agent state
        agent_state = {
            "session_id": self.session_id,
            "session_start_time": self.session_start_time,
            "last_action_time": self.last_action_time,
            "action_count": self.action_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "current_step": self.current_step,
            "current_objective": self.current_objective,
            "tutorial_complete": self.tutorial_complete,
            "tutorial_completion_time": self.tutorial_completion_time,
            "tutorial_completion_reason": self.tutorial_completion_reason,
            "tutorial_completion_path": self.tutorial_completion_path
        }
        
        agent_file = os.path.join(session_dir, "agent_state.json")
        with open(agent_file, "w") as f:
            json.dump(agent_state, f)
        
        logger.info(f"Saved memory for session {self.session_id}")
    
    def load_memory(self) -> None:
        """Load the agent's memory from disk."""
        # Create the session directory if it doesn't exist
        session_dir = os.path.join("state", self.session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Load action memory
        memory_dir = os.path.join(session_dir, "memory")
        if os.path.exists(memory_dir):
            self.action_memory.load(memory_dir)
        
        # Load tutorial progress
        tutorial_file = os.path.join(session_dir, "tutorial_progress.json")
        if os.path.exists(tutorial_file):
            with open(tutorial_file, "r") as f:
                self.tutorial_progress = json.load(f)
        
        # Load agent state
        agent_file = os.path.join(session_dir, "agent_state.json")
        if os.path.exists(agent_file):
            with open(agent_file, "r") as f:
                agent_state = json.load(f)
                self.session_start_time = agent_state.get("session_start_time", time.time())
                self.last_action_time = agent_state.get("last_action_time", time.time())
                self.action_count = agent_state.get("action_count", 0)
                self.success_count = agent_state.get("success_count", 0)
                self.failure_count = agent_state.get("failure_count", 0)
                self.current_step = agent_state.get("current_step", "")
                self.current_objective = agent_state.get("current_objective", "")
                self.tutorial_complete = agent_state.get("tutorial_complete", False)
                self.tutorial_completion_time = agent_state.get("tutorial_completion_time", None)
                self.tutorial_completion_reason = agent_state.get("tutorial_completion_reason", None)
                self.tutorial_completion_path = agent_state.get("tutorial_completion_path", [])
                
                # Log if tutorial was previously completed
                if self.tutorial_complete:
                    logger.info(f"Loaded previously completed tutorial for session {self.session_id}")
                    logger.info(f"Completion reason: {self.tutorial_completion_reason}")
        
        logger.info(f"Loaded memory for session {self.session_id}")
    
    def record_success(self, action_name: str) -> None:
        """
        Record a successful action.
        
        Args:
            action_name: The name of the successful action
        """
        self.action_memory.record_success(action_name)
        self.success_count += 1
        self.save_memory()
        logger.info(f"Recorded success for action: {action_name}")
    
    def record_failure(self, action_name: str) -> None:
        """
        Record a failed action.
        
        Args:
            action_name: The name of the failed action
        """
        self.action_memory.record_failure(action_name)
        self.failure_count += 1
        self.save_memory()
        logger.info(f"Recorded failure for action: {action_name}") 