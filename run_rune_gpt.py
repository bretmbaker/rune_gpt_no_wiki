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
    parser.add_argument('--mode', type=str, default='play', choices=['play', 'sandbox'], help="Agent mode: 'play' or 'sandbox'")
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
        # Determine mode
        mode = ChatMode.SANDBOX if args.mode == "sandbox" else ChatMode.PLAY

        # Initialize RuneGPT agent
        logger.info(f"Initializing RuneGPT agent in {args.mode.upper()} mode")
        agent = RuneGPT(
            session_id=args.session_id,
            load_existing=args.load_state,
            chat=args.chat,
            character=args.character,
            mode=mode
        )

        # Start the agent
        logger.info("Starting RuneGPT agent")
        agent.run()

if __name__ == "__main__":
    main()
