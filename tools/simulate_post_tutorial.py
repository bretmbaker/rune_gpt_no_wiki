#!/usr/bin/env python3
"""
RuneGPT Post-Tutorial Island Simulation

This script simulates the RuneGPT agent's behavior after completing Tutorial Island.
It tests the agent's decision-making, resilience, and learning capabilities.
"""

import os
import json
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from agent.rune_adventure import RuneGPTAgent
from agent.resilience_tracker import ResilienceTracker
from agent.death_handler import DeathHandler
from agent.decision_maker import DecisionMaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("state/logs/simulation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("simulation")

# Ensure state directories exist
os.makedirs("state/logs", exist_ok=True)
os.makedirs("state/deaths", exist_ok=True)
os.makedirs("state/decisions", exist_ok=True)
os.makedirs("state/chains", exist_ok=True)

def run_simulation(session_id: str, loop_count: int = 1):
    """
    Run a simulation of the RuneGPT agent after Tutorial Island.
    
    Args:
        session_id: Unique identifier for this simulation session
        loop_count: Number of sessions to run in sequence
    """
    logger.info(f"Starting simulation session {session_id}")
    
    # Initialize agent with post-tutorial state
    agent = RuneGPTAgent(load_memory=True)
    agent.is_tutorial_complete = True
    agent.current_location = "Lumbridge"
    agent.memory.set("current_location", "Lumbridge")
    
    # Initialize decision timeline
    decision_timeline = []
    
    # Run the specified number of sessions
    for session in range(loop_count):
        session_start = time.time()
        logger.info(f"Starting session {session+1}/{loop_count}")
        
        # Reset session-specific state
        agent.current_action_chain = []
        agent.chain_reward = 0
        
        # Run the agent for a fixed number of steps or until failure
        steps = 0
        max_steps = 100  # Limit steps per session
        
        while steps < max_steps:
            try:
                # Get current state
                state = agent._evaluate_current_state()
                
                # Log the current state
                logger.info(f"Step {steps+1}: Location={state['location']}, Health={state['health']}, Combat={state['combat_level']}")
                
                # Execute one step
                success, message = agent.step()
                
                # Record decision in timeline
                decision_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "session": session+1,
                    "step": steps+1,
                    "location": state["location"],
                    "action": agent.current_action_chain[-1] if agent.current_action_chain else "none",
                    "success": success,
                    "message": message,
                    "state": state
                }
                decision_timeline.append(decision_entry)
                
                # Save decision to timeline file
                with open("state/logs/decision_timeline.jsonl", "a") as f:
                    f.write(json.dumps(decision_entry) + "\n")
                
                # Log the outcome
                if success:
                    logger.info(f"Action successful: {message}")
                else:
                    logger.warning(f"Action failed: {message}")
                
                # Check for session completion
                if "session complete" in message.lower():
                    logger.info(f"Session {session+1} completed successfully")
                    break
                
                # Increment step counter
                steps += 1
                
                # Add a small delay to simulate real-time
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in step {steps+1}: {str(e)}")
                print(f"[Resilience] FAILURE – Reason: Invalid Step - {str(e)}")
                
                # Record failure in timeline
                decision_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "session": session+1,
                    "step": steps+1,
                    "location": agent.current_location,
                    "action": "error",
                    "success": False,
                    "message": f"Error: {str(e)}",
                    "state": agent._evaluate_current_state()
                }
                decision_timeline.append(decision_entry)
                
                # Save decision to timeline file
                with open("state/logs/decision_timeline.jsonl", "a") as f:
                    f.write(json.dumps(decision_entry) + "\n")
                
                # Attempt to recover
                recovery_success, recovery_message = agent._attempt_recovery()
                logger.info(f"Recovery attempt: {recovery_message}")
                
                # If recovery failed, end the session
                if not recovery_success:
                    logger.error(f"Recovery failed, ending session {session+1}")
                    break
        
        # Log session summary
        session_duration = time.time() - session_start
        logger.info(f"Session {session+1} completed in {session_duration:.2f} seconds with {steps} steps")
        
        # Save session memory
        agent._save_memory()
        
        # If this is the last session, dump the final memory state
        if session == loop_count - 1:
            dump_final_memory(agent)
    
    logger.info(f"Simulation session {session_id} completed")
    return decision_timeline

def dump_final_memory(agent: RuneGPTAgent):
    """Dump the final memory state for analysis."""
    # Get resilience tracker data
    resilience_data = {
        "avoided_locations": agent.resilience_tracker.get_avoided_locations(),
        "success_chains": agent.resilience_tracker.get_successful_chains(),
        "confidence_scores": agent.resilience_tracker.confidence_scores,
        "death_log": agent.resilience_tracker.death_log,
        "decision_outcomes": agent.resilience_tracker.decision_outcomes
    }
    
    # Save to file
    with open("state/logs/final_memory.json", "w") as f:
        json.dump(resilience_data, f, indent=2)
    
    logger.info("Final memory state saved to state/logs/final_memory.json")
    
    # Print summary
    print("\n=== Final Memory Summary ===")
    print(f"Avoided Locations: {len(resilience_data['avoided_locations'])}")
    print(f"Successful Action Chains: {len(resilience_data['success_chains'])}")
    print(f"Confidence Scores: {len(resilience_data['confidence_scores'])}")
    print(f"Deaths: {len(resilience_data['death_log'])}")
    print(f"Decision Outcomes: {len(resilience_data['decision_outcomes'])}")
    print("===========================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a RuneGPT post-tutorial simulation")
    parser.add_argument("--loop", type=int, default=1, help="Number of sessions to run in sequence")
    parser.add_argument("--session-id", type=str, default=datetime.now().strftime("%Y%m%d_%H%M%S"), 
                        help="Unique identifier for this simulation session")
    args = parser.parse_args()
    
    # Run the simulation
    decision_timeline = run_simulation(args.session_id, args.loop)
    
    print(f"Simulation completed. Check state/logs/ for detailed logs and decision timeline.") 