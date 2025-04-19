"""
Narrative Logger for RuneGPT
Records the agent's journey through the tutorial in a narrative format
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class NarrativeLogger:
    """
    Records the agent's journey through the tutorial in a narrative format.
    This creates a readable story of the agent's progress and decisions.
    """
    
    def __init__(self, session_id: str):
        """
        Initialize the narrative logger.
        
        Args:
            session_id: The unique identifier for this player session
        """
        self.session_id = session_id
        self.log_dir = Path("state") / session_id / "narrative"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize log file
        self.log_file = self.log_dir / "journey.json"
        self.entries = []
        
        # Load existing entries if available
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                self.entries = json.load(f)
        
        # Start time
        self.start_time = time.time()
        
        # Add initial entry
        self._add_entry("journey_start", {
            "message": "The agent begins its journey through Tutorial Island",
            "timestamp": self.start_time
        })
        
        logger.info(f"Initialized narrative logger for session {session_id}")
    
    def _add_entry(self, entry_type: str, data: Dict[str, Any]) -> None:
        """
        Add a new entry to the narrative log.
        
        Args:
            entry_type: The type of entry (journey_start, step_complete, action_taken, etc.)
            data: Additional data for the entry
        """
        # Add timestamp if not provided
        if "timestamp" not in data:
            data["timestamp"] = time.time()
        
        # Add elapsed time
        data["elapsed_time"] = data["timestamp"] - self.start_time
        
        # Create entry
        entry = {
            "type": entry_type,
            "data": data
        }
        
        # Add to entries
        self.entries.append(entry)
        
        # Save to file
        with open(self.log_file, 'w') as f:
            json.dump(self.entries, f, indent=2)
    
    def log_step_start(self, step: str, objective: str) -> None:
        """
        Log the start of a new tutorial step.
        
        Args:
            step: The name of the tutorial step
            objective: The objective for this step
        """
        self._add_entry("step_start", {
            "step": step,
            "objective": objective,
            "message": f"The agent begins the {step} step with objective: {objective}"
        })
    
    def log_action(self, action: str, confidence: float, success: bool, reasoning: str) -> None:
        """
        Log an action taken by the agent.
        
        Args:
            action: The action taken
            confidence: The confidence in the action
            success: Whether the action was successful
            reasoning: The reasoning behind the action
        """
        outcome = "successful" if success else "unsuccessful"
        self._add_entry("action_taken", {
            "action": action,
            "confidence": confidence,
            "success": success,
            "reasoning": reasoning,
            "message": f"The agent {outcome}ly attempts to {action.lower()} (confidence: {confidence:.2f})"
        })
    
    def log_objective_complete(self, objective: str) -> None:
        """
        Log the completion of an objective.
        
        Args:
            objective: The completed objective
        """
        self._add_entry("objective_complete", {
            "objective": objective,
            "message": f"The agent completes the objective: {objective}"
        })
    
    def log_step_complete(self, step: str) -> None:
        """
        Log the completion of a tutorial step.
        
        Args:
            step: The completed step
        """
        self._add_entry("step_complete", {
            "step": step,
            "message": f"The agent completes the {step} step"
        })
    
    def log_tutorial_complete(self, reason: str, path: List[str]) -> None:
        """
        Log the completion of the tutorial.
        
        Args:
            reason: The reason for completion
            path: The path taken through the tutorial
        """
        # Calculate completion time
        completion_time = time.time() - self.start_time
        minutes = int(completion_time // 60)
        seconds = int(completion_time % 60)
        
        self._add_entry("tutorial_complete", {
            "reason": reason,
            "path": path,
            "completion_time": completion_time,
            "message": f"The agent completes the tutorial in {minutes} minutes and {seconds} seconds! Reason: {reason}"
        })
        
        # Generate narrative summary
        self._generate_narrative_summary()
    
    def _generate_narrative_summary(self) -> None:
        """Generate a narrative summary of the agent's journey."""
        summary_file = self.log_dir / "journey_summary.txt"
        
        with open(summary_file, 'w') as f:
            f.write("=" * 50 + "\n")
            f.write("RuneGPT Tutorial Journey Summary\n")
            f.write("=" * 50 + "\n\n")
            
            # Add introduction
            f.write("Once upon a time, a new RuneScape adventurer began their journey on Tutorial Island...\n\n")
            
            # Add step-by-step narrative
            current_step = None
            for entry in self.entries:
                if entry["type"] == "step_start":
                    current_step = entry["data"]["step"]
                    f.write(f"\nChapter: {current_step}\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"{entry['data']['message']}\n")
                elif entry["type"] == "action_taken" and entry["data"]["success"]:
                    f.write(f"  • {entry['data']['message']}\n")
                elif entry["type"] == "objective_complete":
                    f.write(f"  ✓ {entry['data']['message']}\n")
                elif entry["type"] == "step_complete":
                    f.write(f"\n  The agent successfully completes the {current_step} step!\n")
                elif entry["type"] == "tutorial_complete":
                    f.write("\n" + "=" * 50 + "\n")
                    f.write("The Journey's End\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"{entry['data']['message']}\n\n")
                    f.write("The agent's path through Tutorial Island:\n")
                    for i, step in enumerate(entry["data"]["path"], 1):
                        f.write(f"  {i}. {step}\n")
                    f.write("\nAnd so, our adventurer's tutorial journey comes to an end...\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("The End\n")
            f.write("=" * 50 + "\n")
        
        logger.info(f"Generated narrative summary at {summary_file}")
    
    def get_entries(self) -> List[Dict[str, Any]]:
        """Get all entries in the narrative log."""
        return self.entries
    
    def get_summary(self) -> str:
        """Get a text summary of the agent's journey."""
        summary = []
        
        # Add introduction
        summary.append("RuneGPT Tutorial Journey Summary")
        summary.append("=" * 50)
        
        # Add step-by-step summary
        current_step = None
        for entry in self.entries:
            if entry["type"] == "step_start":
                current_step = entry["data"]["step"]
                summary.append(f"\nStep: {current_step}")
                summary.append("-" * 30)
            elif entry["type"] == "action_taken" and entry["data"]["success"]:
                summary.append(f"  • {entry['data']['message']}")
            elif entry["type"] == "objective_complete":
                summary.append(f"  ✓ {entry['data']['message']}")
            elif entry["type"] == "step_complete":
                summary.append(f"\n  Completed: {current_step}")
            elif entry["type"] == "tutorial_complete":
                summary.append("\n" + "=" * 50)
                summary.append("Tutorial Complete!")
                summary.append("=" * 50)
                summary.append(f"{entry['data']['message']}")
        
        return "\n".join(summary) 