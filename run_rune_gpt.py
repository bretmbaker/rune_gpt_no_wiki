#!/usr/bin/env python3
"""
RuneGPT - OSRS AI Agent
Main entry point for running RuneGPT with session management and proper Tutorial Island progression.
"""

import os
import sys
import argparse
from agent.rune_gpt import RuneGPT
import time

def main():
    """Main entry point for RuneGPT."""
    parser = argparse.ArgumentParser(description="RuneGPT - OSRS AI Agent")
    parser.add_argument("--session", type=str, help="Session ID for this agent instance")
    parser.add_argument("--load", action="store_true", help="Load existing session state")
    parser.add_argument("--conversation", action="store_true", help="Start in conversation mode")
    args = parser.parse_args()
    
    # Ensure state directory exists
    os.makedirs("state", exist_ok=True)
    
    if args.conversation:
        # Start conversation CLI
        from agent.conversation_cli import ConversationCLI
        cli = ConversationCLI()
        cli.run()
    else:
        # Start agent
        agent = RuneGPT(session_id=args.session, load_memory=args.load)
        
        try:
            # Start agent loop
            while True:
                # Process screen text (simulated for now)
                screen_text = "You are in Tutorial Island. The Survival Expert is waiting to teach you."
                agent.process_screen_text(screen_text)
                time.sleep(1)  # Simulate game tick
                
        except KeyboardInterrupt:
            print("\nShutting down RuneGPT agent...")
            agent.save_state()

if __name__ == "__main__":
    main() 