#!/usr/bin/env python3
"""
RuneGPT Session Manager
Main entry point for running RuneGPT with Tutorial Island progression and concurrent conversation support.
"""

import os
import sys
import argparse
import time
import threading
import signal
import json
from typing import Dict, Optional
from agent.rune_adventure import RuneGPTAgent
from agent.conversation_cli import ConversationCLI

# Global flag to control the game loop
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully shut down the game."""
    global running
    print("\nShutting down RuneGPT...")
    running = False

def game_loop(agent: RuneGPTAgent):
    """Run the main game loop for the agent."""
    global running
    
    # Tutorial Island progression
    tutorial_steps = [
        "talk_to_survival_expert",
        "chop_tree",
        "light_logs",
        "talk_to_master_chef",
        "cook_shrimp",
        "talk_to_fishing_instructor",
        "catch_shrimp",
        "talk_to_quest_guide",
        "talk_to_mining_instructor",
        "mine_copper",
        "talk_to_combat_instructor",
        "equip_weapon",
        "attack_chicken",
        "talk_to_banker",
        "deposit_items",
        "talk_to_brother_brace",
        "talk_to_magic_instructor",
        "cast_wind_strike",
        "talk_to_master_navigator",
        "talk_to_financial_advisor",
        "complete_tutorial"
    ]
    
    current_step_index = 0
    
    # Main game loop
    while running:
        try:
            # Get current tutorial step
            current_step = tutorial_steps[current_step_index]
            
            # Generate appropriate screen text based on the current step
            screen_text = generate_screen_text(current_step, agent)
            
            # Process the screen text
            agent._process_screen_text(screen_text)
            
            # Check if the step was completed
            if current_step in agent.tutorial_progress["completed_steps"]:
                current_step_index += 1
                
                # Check if tutorial is complete
                if current_step_index >= len(tutorial_steps):
                    print("Tutorial Island completed!")
                    agent.is_tutorial_complete = True
                    agent.tutorial_progress["tutorial_complete"] = True
                    agent.save_state()
                    break
            
            # Simulate game tick
            time.sleep(2)
            
        except Exception as e:
            print(f"Error in game loop: {str(e)}")
            time.sleep(1)
    
    # Save state when exiting
    agent.save_state()

def generate_screen_text(step: str, agent: RuneGPTAgent) -> str:
    """Generate appropriate screen text based on the current tutorial step."""
    if step == "talk_to_survival_expert":
        return "You are in Tutorial Island. The Survival Expert is waiting to teach you about the basics of survival."
    elif step == "chop_tree":
        return "The Survival Expert has taught you about woodcutting. You need to chop down a tree to get some logs."
    elif step == "light_logs":
        return "You have some logs. Now you need to light them to create a fire."
    elif step == "talk_to_master_chef":
        return "You've learned about firemaking. Now the Master Chef wants to teach you about cooking."
    elif step == "cook_shrimp":
        return "The Master Chef has given you some raw shrimp. You need to cook them on the fire."
    elif step == "talk_to_fishing_instructor":
        return "You've learned about cooking. Now the Fishing Instructor wants to teach you about fishing."
    elif step == "catch_shrimp":
        return "The Fishing Instructor has taught you about fishing. You need to catch some shrimp."
    elif step == "talk_to_quest_guide":
        return "You've learned about fishing. Now the Quest Guide wants to teach you about quests."
    elif step == "talk_to_mining_instructor":
        return "You've learned about quests. Now the Mining Instructor wants to teach you about mining."
    elif step == "mine_copper":
        return "The Mining Instructor has taught you about mining. You need to mine some copper ore."
    elif step == "talk_to_combat_instructor":
        return "You've learned about mining. Now the Combat Instructor wants to teach you about combat."
    elif step == "equip_weapon":
        return "The Combat Instructor has given you a bronze sword. You need to equip it."
    elif step == "attack_chicken":
        return "You've equipped your weapon. Now you need to attack a chicken to learn about combat."
    elif step == "talk_to_banker":
        return "You've learned about combat. Now the Banker wants to teach you about banking."
    elif step == "deposit_items":
        return "The Banker has taught you about banking. You need to deposit your items in the bank."
    elif step == "talk_to_brother_brace":
        return "You've learned about banking. Now Brother Brace wants to teach you about prayer."
    elif step == "talk_to_magic_instructor":
        return "You've learned about prayer. Now the Magic Instructor wants to teach you about magic."
    elif step == "cast_wind_strike":
        return "The Magic Instructor has taught you about magic. You need to cast Wind Strike on a chicken."
    elif step == "talk_to_master_navigator":
        return "You've learned about magic. Now the Master Navigator wants to teach you about navigation."
    elif step == "talk_to_financial_advisor":
        return "You've learned about navigation. Now the Financial Advisor wants to teach you about finances."
    elif step == "complete_tutorial":
        return "You have completed all the tutorials on Tutorial Island. You are now ready to begin your adventure in Gielinor!"
    else:
        return "You are in Tutorial Island. An instructor is waiting to teach you."

def main():
    """Main entry point for RuneGPT with concurrent conversation support."""
    parser = argparse.ArgumentParser(description="RuneGPT - OSRS AI Agent with Concurrent Conversation")
    parser.add_argument("--session", type=str, default="Player_001", help="Session ID for this agent instance")
    parser.add_argument("--load", action="store_true", help="Load existing session state")
    parser.add_argument("--conversation-only", action="store_true", help="Start only in conversation mode")
    args = parser.parse_args()
    
    # Ensure state directory exists
    os.makedirs("state", exist_ok=True)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    if args.conversation_only:
        # Start only the conversation CLI
        print("Starting RuneGPT Conversation CLI...")
        cli = ConversationCLI()
        cli.run()
    else:
        # Start the agent in a separate thread
        print(f"Starting RuneGPT agent with session ID: {args.session}")
        agent = RuneGPTAgent(session_id=args.session, load_memory=args.load)
        
        # Start the game loop in a separate thread
        game_thread = threading.Thread(target=game_loop, args=(agent,))
        game_thread.daemon = True
        game_thread.start()
        
        # Start the conversation CLI in the main thread
        print("Starting RuneGPT Conversation CLI...")
        cli = ConversationCLI()
        
        # Connect to the active session
        if cli.connect_to_active_session(args.session):
            print(f"Connected to active session: {args.session}")
        else:
            print(f"Could not connect to active session: {args.session}")
            print("Starting a new conversation session...")
        
        # Run the conversation CLI
        cli.run()
        
        # Wait for the game thread to finish
        game_thread.join()

if __name__ == "__main__":
    main() 