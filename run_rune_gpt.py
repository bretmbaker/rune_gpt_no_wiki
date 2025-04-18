#!/usr/bin/env python3
"""
RuneGPT - OSRS AI Agent
Main entry point for running RuneGPT with session management and proper Tutorial Island progression.
"""

import os
import sys
import argparse
import logging
from agent.rune_gpt import RuneGPT
from agent.chat_mode import ChatMode
import time

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run RuneGPT')
    parser.add_argument('--session-id', type=str, help='Session ID to load')
    parser.add_argument('--load-state', action='store_true', help='Load existing session state')
    parser.add_argument('--chat', action='store_true', help='Start in chat mode')
    parser.add_argument('--character', type=str, default='GielinorNomad', help='Character name for chat mode')
    args = parser.parse_args()

    if args.chat:
        # Initialize chat mode
        logger.info(f"Starting chat mode with character: {args.character}")
        chat = ChatMode(args.character)
        
        print(f"\nWelcome to RuneGPT Chat Mode!")
        print(f"You are chatting with {args.character}")
        print("Type 'exit' to end the conversation\n")
        
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break
                
            response = chat.process_input(user_input)
            print(f"\n{args.character}: {response.text}")
            if response.emotion != "neutral":
                print(f"[Emotion: {response.emotion}]")
    else:
        # Initialize RuneGPT agent
        logger.info("Initializing RuneGPT agent")
        agent = RuneGPT()
        
        if args.load_state and args.session_id:
            logger.info(f"Loading session state: {args.session_id}")
            agent.load_state(args.session_id)
        
        # Start the agent
        logger.info("Starting RuneGPT agent")
        agent.run()

if __name__ == "__main__":
    main() 