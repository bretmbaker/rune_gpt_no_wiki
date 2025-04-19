"""
Tutorial Progress Engine for RuneGPT
Manages tutorial state, objectives, and progression
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class TutorialStep:
    name: str
    instructor: str
    location: str
    description: str
    objectives: List[str]
    required_items: List[str]
    required_skills: Dict[str, int]
    completion_triggers: List[str]
    next_step: Optional[str]
    xp_rewards: Dict[str, int] = None
    item_rewards: Dict[str, int] = None

class TutorialProgressEngine:
    """Manages Tutorial Island progression and state"""
    
    def __init__(self):
        self.current_step: Optional[TutorialStep] = None
        self.completed_steps: Set[str] = set()
        self.current_objective_index: int = 0
        
        # Define tutorial steps
        self.tutorial_steps = {
            "survival_expert_intro": TutorialStep(
                name="survival_expert_intro",
                instructor="Survival Expert",
                location="Tutorial Island - Survival Area",
                description="Learn basic survival skills",
                objectives=[
                    "Talk to the Survival Expert",
                    "Click on the fishing spot to catch shrimp",
                    "Light a fire",
                    "Cook the shrimp"
                ],
                required_items=[],
                required_skills={},
                completion_triggers=[
                    "You have completed the survival section",
                    "Now head through the gate to find your next instructor"
                ],
                next_step="master_chef",
                xp_rewards={
                    "fishing": 25,
                    "firemaking": 25,
                    "cooking": 25
                },
                item_rewards={
                    "shrimp": 5,
                    "logs": 5
                }
            ),
            "master_chef": TutorialStep(
                name="master_chef",
                instructor="Master Chef",
                location="Tutorial Island - Cooking Area",
                description="Learn to make bread",
                objectives=[
                    "Talk to the Master Chef",
                    "Make flour from wheat",
                    "Make bread dough",
                    "Bake bread"
                ],
                required_items=[],
                required_skills={},
                completion_triggers=[
                    "You've made bread",
                    "Move through the door to continue"
                ],
                next_step="quest_guide",
                xp_rewards={
                    "cooking": 50,
                    "crafting": 25
                },
                item_rewards={
                    "bread": 5,
                    "flour": 10,
                    "wheat": 10
                }
            ),
            "quest_guide": TutorialStep(
                name="quest_guide",
                instructor="Quest Guide",
                location="Tutorial Island - Quest Area",
                description="Learn about quests",
                objectives=[
                    "Talk to the Quest Guide",
                    "Open the quest journal",
                    "Read about quests"
                ],
                required_items=[],
                required_skills={},
                completion_triggers=[
                    "You've learned about quests",
                    "Head through the gate to continue"
                ],
                next_step="mining_instructor",
                xp_rewards={
                    "quest_points": 1
                },
                item_rewards={}
            ),
            "mining_instructor": TutorialStep(
                name="mining_instructor",
                instructor="Mining Instructor",
                location="Tutorial Island - Mining Area",
                description="Learn to mine",
                objectives=[
                    "Talk to the Mining Instructor",
                    "Mine copper and tin ore",
                    "Smelt a bronze bar",
                    "Make a bronze dagger"
                ],
                required_items=[],
                required_skills={},
                completion_triggers=[
                    "You've made a bronze dagger",
                    "Head through the gate to continue"
                ],
                next_step="combat_instructor",
                xp_rewards={
                    "mining": 50,
                    "smithing": 50,
                    "crafting": 25
                },
                item_rewards={
                    "copper_ore": 5,
                    "tin_ore": 5,
                    "bronze_bar": 3,
                    "bronze_dagger": 1
                }
            ),
            "combat_instructor": TutorialStep(
                name="combat_instructor",
                instructor="Combat Instructor",
                location="Tutorial Island - Combat Area",
                description="Learn combat basics",
                objectives=[
                    "Talk to the Combat Instructor",
                    "Equip the bronze dagger",
                    "Attack the chicken",
                    "Bury the bones"
                ],
                required_items=["bronze_dagger"],
                required_skills={},
                completion_triggers=[
                    "You've learned combat basics",
                    "Head through the gate to continue"
                ],
                next_step="banker",
                xp_rewards={
                    "attack": 25,
                    "strength": 25,
                    "defence": 25,
                    "prayer": 25
                },
                item_rewards={
                    "bones": 5,
                    "chicken": 3
                }
            ),
            "banker": TutorialStep(
                name="banker",
                instructor="Banker",
                location="Tutorial Island - Bank Area",
                description="Learn about banking",
                objectives=[
                    "Talk to the Banker",
                    "Open your bank",
                    "Deposit items",
                    "Withdraw items"
                ],
                required_items=[],
                required_skills={},
                completion_triggers=[
                    "You've learned about banking",
                    "Head through the gate to continue"
                ],
                next_step="final_gate",
                xp_rewards={},
                item_rewards={
                    "coins": 25
                }
            ),
            "final_gate": TutorialStep(
                name="final_gate",
                instructor="Gate Keeper",
                location="Tutorial Island - Final Gate",
                description="Leave Tutorial Island",
                objectives=[
                    "Talk to the Gate Keeper",
                    "Confirm you're ready to leave"
                ],
                required_items=[],
                required_skills={},
                completion_triggers=[
                    "You are now ready to leave Tutorial Island",
                    "You will be teleported to Lumbridge"
                ],
                next_step=None,
                xp_rewards={},
                item_rewards={
                    "coins": 25
                }
            )
        }
        
        # Start with first step
        self.set_current_step("survival_expert_intro")
    
    def set_current_step(self, step_name: str) -> None:
        """Set the current tutorial step"""
        if step_name in self.tutorial_steps:
            self.current_step = self.tutorial_steps[step_name]
            self.current_objective_index = 0
            logger.info(f"Starting tutorial step: {step_name}")
        else:
            logger.error(f"Unknown tutorial step: {step_name}")
    
    def get_current_objective(self) -> Optional[str]:
        """Get the current objective text"""
        if not self.current_step:
            return None
        if self.current_objective_index >= len(self.current_step.objectives):
            return None
        return self.current_step.objectives[self.current_objective_index]
    
    def _load_tutorial_data(self) -> Dict[str, Dict[str, Any]]:
        """Load tutorial data from wiki_data directory."""
        tutorial_data = {}
        
        # Load tutorial data
        wiki_dir = Path("wiki_data") / "tutorial_island"
        if not wiki_dir.exists():
            return tutorial_data
            
        # Load metadata.json
        metadata_file = wiki_dir / "metadata.json"
        if not metadata_file.exists():
            return tutorial_data
            
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                
            # Load txt files referenced in metadata
            txt_dir = wiki_dir / "txt"
            if txt_dir.exists():
                for name, data in metadata.items():
                    if data.get("type") == "walkthrough":  # Only load walkthrough type entries
                        txt_file = txt_dir / data["txt"].split("/")[-1]
                        if txt_file.exists():
                            with open(txt_file, 'r') as f:
                                content = f.read()
                                tutorial_data[name] = {
                                    "content": content,
                                    "metadata": data,
                                    "type": "walkthrough"
                                }
        except Exception as e:
            logger.error(f"Error loading tutorial data: {str(e)}")
        
        return tutorial_data
    
    def process_screen_text(self, text: str) -> Dict[str, Any]:
        """Process screen text and determine next action"""
        if not self.current_step:
            return {
                "action_required": False,
                "action_type": None,
                "next_objective": None
            }

        # Get current objective
        current_objective = self.get_current_objective()
        if not current_objective:
            return {
                "action_required": False,
                "action_type": None,
                "next_objective": None
            }

        # Check if current objective is mentioned in text
        if current_objective.lower() in text.lower():
            # Mark objective as complete and advance
            self.current_objective_index += 1
            
            # Check if step is complete
            if self.current_objective_index >= len(self.current_step.objectives):
                self.completed_steps.add(self.current_step.name)
                if self.current_step.next_step:
                    self.set_current_step(self.current_step.next_step)
                return {
                    "action_required": True,
                    "action_type": "complete_step",
                    "next_objective": f"Complete {self.current_step.name}",
                    "step_complete": True
                }
            
            # Get next objective
            next_objective = self.get_current_objective()
            return {
                "action_required": True,
                "action_type": "continue_step",
                "next_objective": next_objective,
                "step_complete": False
            }

        # If objective not found, suggest current objective
        return {
            "action_required": True,
            "action_type": "suggest_objective",
            "next_objective": current_objective,
            "step_complete": False
        }
    
    def advance_objective(self, action: str) -> bool:
        """Advance the current tutorial objective."""
        # Load tutorial data
        tutorial_data = self._load_tutorial_data()
        
        # Get current step data
        current_step = None
        for step_name, step_data in tutorial_data.items():
            if step_data["metadata"].get("npc") in self.current_npc:
                current_step = step_name
                break
        
        if not current_step:
            return False
        
        # Check if action matches required action
        if action in tutorial_data[current_step]["metadata"].get("required_actions", []):
            self.objectives_completed += 1
            return True
        
        return False
    
    def complete_current_step(self) -> bool:
        """Complete the current tutorial step."""
        # Load tutorial data
        tutorial_data = self._load_tutorial_data()
        
        # Get current step data
        current_step = None
        for step_name, step_data in tutorial_data.items():
            if step_data["metadata"].get("npc") in self.current_npc:
                current_step = step_name
                break
        
        if not current_step:
            return False
        
        # Check if all objectives are completed
        required_objectives = tutorial_data[current_step]["metadata"].get("required_objectives", 1)
        if self.objectives_completed >= required_objectives:
            self.current_step += 1
            self.objectives_completed = 0
            return True
        
        return False
    
    def is_complete(self) -> bool:
        """Check if the tutorial is complete"""
        return len(self.completed_steps) >= len(self.tutorial_steps)
    
    def get_state(self) -> dict:
        """Get the current tutorial state"""
        return {
            "current_step": self.current_step.name if self.current_step else None,
            "completed_steps": list(self.completed_steps),
            "current_objective_index": self.current_objective_index,
            "is_complete": self.is_complete()
        }
    
    def load_state(self, state: dict) -> None:
        """Load tutorial state from dict"""
        if "current_step" in state and state["current_step"]:
            self.set_current_step(state["current_step"])
        if "completed_steps" in state:
            self.completed_steps = set(state["completed_steps"])
        if "current_objective_index" in state:
            self.current_objective_index = state["current_objective_index"] 