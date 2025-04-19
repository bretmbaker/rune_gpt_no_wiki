#!/usr/bin/env python3
"""
Sandbox Loop for RuneGPT
Implements trial-and-error learning for game tutorial
"""

import time
import logging
import os
import sys
import random
import traceback
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from agent.runegpt import RuneGPT
from agent.action_memory import ActionMemory
from agent.tutorial_engine import TutorialEngine
from agent.game_state import GameState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sandbox.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Define available tutorial actions
TUTORIAL_ACTIONS = [
    "Talk to Survival Expert",
    "Talk to Master Chef",
    "Talk to Quest Guide",
    "Talk to Mining Instructor",
    "Talk to Combat Instructor",
    "Talk to Banker",
    "Talk to Gate Keeper",
    "Click on Fishing Spot",
    "Chop Tree",
    "Light Fire",
    "Use Tinderbox on Logs",
    "Cook Shrimp",
    "Make Flour",
    "Make Bread Dough",
    "Bake Bread",
    "Open Quest Journal",
    "Mine Copper Ore",
    "Mine Tin Ore",
    "Smelt Bronze Bar",
    "Make Bronze Dagger",
    "Equip Bronze Dagger",
    "Attack Chicken",
    "Bury Bones",
    "Open Bank",
    "Deposit Items",
    "Withdraw Items",
    "Confirm Leave Tutorial",
    "Walk to Lumbridge"
]

class SandboxLoop:
    def __init__(self, player_id: str):
        self.player_id = player_id
        self.agent = RuneGPT(player_id)
        self.memory = ActionMemory(player_id)
        self.tutorial = TutorialEngine()
        
        # Track state
        self.current_step = None
        self.current_objective = None
        self.last_action = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        
        # Initialize state
        self._update_tutorial_state()
        
        # Terminal display settings
        self.terminal_width = 80
        self.terminal_height = 24
        self.display_buffer = []
        
    def _update_tutorial_state(self):
        """Update current tutorial step and objective"""
        self.current_step = self.tutorial.get_current_step()
        self.current_objective = self.tutorial.get_current_objective()
        logger.info(f"Tutorial state updated - Step: {self.current_step}, Objective: {self.current_objective}")
        
    def _get_available_actions(self, screen_text: str) -> List[str]:
        """Get list of available actions based on screen text"""
        # This would be replaced with actual action extraction logic
        return self.agent.get_available_actions(screen_text)
        
    def _process_action_result(self, action: str, success: bool, screen_text: str):
        """Process the result of an action"""
        # Record action in memory
        context = {
            "step": self.current_step,
            "objective": self.current_objective,
            "screen_text": screen_text
        }
        self.memory.record_action(action, success, context)
        
        # Update failure tracking
        if not success:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
            
        # Check if tutorial should progress
        if success and self.tutorial.should_progress(screen_text):
            self.tutorial.progress()
            self._update_tutorial_state()
            logger.info("Tutorial progressed to next step")
            
    def run_iteration(self, screen_text: str) -> Tuple[str, float]:
        """Run one iteration of the sandbox loop"""
        # Get available actions
        available_actions = self._get_available_actions(screen_text)
        if not available_actions:
            logger.warning("No available actions found")
            return None, 0.0
            
        # Get best action with confidence
        action, confidence = self.memory.get_best_action(
            available_actions,
            screen_text,
            self.current_step,
            self.current_objective
        )
        
        # Handle excessive failures
        if self.consecutive_failures >= self.max_consecutive_failures:
            logger.warning("Too many consecutive failures, resetting tutorial")
            self.tutorial.reset()
            self._update_tutorial_state()
            self.consecutive_failures = 0
            return None, 0.0
            
        # Store action for result processing
        self.last_action = action
        return action, confidence
        
    def process_result(self, success: bool, screen_text: str):
        """Process the result of the last action"""
        if self.last_action:
            self._process_action_result(self.last_action, success, screen_text)
            self.last_action = None
            
    def _update_terminal_display(self, screen_text: str, action: str, confidence: float, success: bool):
        """Update the terminal display with current state"""
        # Clear the display buffer
        self.display_buffer = []
        
        # Add header
        self.display_buffer.append("=" * self.terminal_width)
        self.display_buffer.append(f"RuneGPT Sandbox Loop - {datetime.now().strftime('%H:%M:%S')}")
        self.display_buffer.append("=" * self.terminal_width)
        
        # Add screen text (truncated if too long)
        screen_text_display = screen_text[:self.terminal_width - 20] + "..." if len(screen_text) > self.terminal_width - 20 else screen_text
        self.display_buffer.append(f"Screen Text: {screen_text_display}")
        
        # Add current step and objective
        self.display_buffer.append(f"Current Step: {self.current_step or 'None'}")
        self.display_buffer.append(f"Objective: {self.current_objective or 'None'}")
        
        # Add action and confidence
        self.display_buffer.append(f"Selected Action: {action or 'None'}")
        self.display_buffer.append(f"Confidence: {confidence:.2f}")
        
        # Add success/failure
        outcome = "SUCCESS" if success else "FAILURE"
        self.display_buffer.append(f"Outcome: {outcome}")
        
        # Add tutorial completion status
        if self.agent.tutorial_complete:
            self.display_buffer.append("=" * self.terminal_width)
            self.display_buffer.append("🎉 TUTORIAL COMPLETED! 🎉")
            self.display_buffer.append(f"Reason: {self.agent.tutorial_completion_reason}")
            self.display_buffer.append("=" * self.terminal_width)
        
        # Add footer
        self.display_buffer.append("=" * self.terminal_width)
        self.display_buffer.append("Press Ctrl+C to exit")
        self.display_buffer.append("=" * self.terminal_width)
        
        # Clear the terminal and print the display buffer
        os.system('cls' if os.name == 'nt' else 'clear')
        for line in self.display_buffer:
            print(line)

def main():
    # Initialize agent and action memory
    agent = RuneGPT("sandbox_session")
    action_memory = ActionMemory(agent.session_id)
    logger.info(f"Starting sandbox loop with memory-based learning for {agent.session_id}")
    
    # Initialize sandbox loop
    sandbox = SandboxLoop(agent.session_id)
    
    # Initialize tutorial progress tracking
    tutorial_progress_score = 0
    last_tutorial_step = None
    last_action = None
    action_count = 0
    
    try:
        while not agent.tutorial_complete:
            # Get current tutorial state
            tutorial_state = agent.tutorial_engine.get_state()
            current_step = tutorial_state.get("current_step")
            
            # Track tutorial progress
            if current_step != last_tutorial_step and current_step is not None:
                tutorial_progress_score += 1
                last_tutorial_step = current_step
                logger.info(f"Tutorial progress: Step {current_step} | Score: {tutorial_progress_score}")
            
            # Generate current context
            context = f"Tutorial Island - {current_step}" if current_step else "Tutorial Island"
            screen_text = f"You are in {context}. What would you like to do?"
            
            # Choose best action based on memory
            chosen_action, confidence = action_memory.get_best_action(
                available_actions=TUTORIAL_ACTIONS,
                screen_text=screen_text,
                current_step=current_step
            )
            
            # Add some randomness to prevent getting stuck
            if chosen_action == last_action and action_count > 3:
                # Force a different action after 3 repetitions
                available_actions = [a for a in TUTORIAL_ACTIONS if a != chosen_action]
                if available_actions:
                    chosen_action = random.choice(available_actions)
                    confidence = 0.5  # Lower confidence for forced actions
                    logger.info(f"Forcing different action: {chosen_action}")
            
            # Update action tracking
            if chosen_action == last_action:
                action_count += 1
            else:
                action_count = 1
                last_action = chosen_action
            
            # Log decision process
            logger.info(f"Context: {context}")
            logger.info(f"Chosen action: {chosen_action} (confidence: {confidence:.2f})")
            
            # Process screen text and attempt action
            tutorial_result = agent.tutorial_engine.process_screen_text(screen_text)
            
            # Determine success based on tutorial step requirements
            success = False
            if current_step == "survival_expert_intro":
                success = chosen_action in [
                    "Talk to Survival Expert",
                    "Click on Fishing Spot",
                    "Light Fire"
                ]
            elif "fishing" in str(current_step).lower():
                success = chosen_action in ["Click on Fishing Spot"]
            elif "fire" in str(current_step).lower():
                success = chosen_action in ["Chop Tree", "Light Fire", "Use Tinderbox on Logs"]
            else:
                # Default success check
                success = tutorial_result.get("action_required", False)
            
            # Record action outcome
            action_memory.record_action(
                action=chosen_action,
                success=success,
                context={
                    "step": current_step,
                    "screen_text": screen_text
                }
            )
            
            # Update terminal display
            sandbox._update_terminal_display(screen_text, chosen_action, confidence, success)
            
            # Log outcome (using ASCII characters instead of Unicode)
            outcome = "[SUCCESS]" if success else "[FAILURE]"
            logger.info(f"Action outcome: {outcome}")
            
            # Check for tutorial completion
            if "You have completed the Tutorial Island!" in screen_text or "Lumbridge" in context:
                # Create a game state to check for completion
                game_state = GameState(
                    screen_text=screen_text,
                    player_location=context,
                    step=current_step
                )
                agent.process_game_state(game_state)
                
                if agent.tutorial_complete:
                    logger.info("Tutorial completed! Pausing for review.")
                    # Pause for review
                    time.sleep(5)
                    break
            
            # Wait for state to update
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("Sandbox loop interrupted by user")
    except Exception as e:
        logger.error(f"Error in sandbox loop: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        logger.info(f"Sandbox loop ended. Final tutorial progress score: {tutorial_progress_score}")
        logger.info("Final action statistics:")
        for action, stats in action_memory.action_history.items():
            logger.info(f"{action}: {stats}")
        
        # Display final tutorial completion status
        if agent.tutorial_complete:
            logger.info("=" * 50)
            logger.info("🎉 TUTORIAL COMPLETED! 🎉")
            logger.info(f"Session: {agent.session_id}")
            logger.info(f"Completion time: {agent.tutorial_completion_time - agent.session_start_time:.2f} seconds")
            logger.info(f"Reason: {agent.tutorial_completion_reason}")
            logger.info(f"Steps taken: {len(agent.tutorial_completion_path)}")
            logger.info(f"Actions taken: {agent.action_count}")
            logger.info(f"Success rate: {agent.success_count / max(1, agent.action_count):.2%}")
            logger.info("=" * 50)
        else:
            logger.info("Tutorial was not completed.")

if __name__ == "__main__":
    main() 