#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Optional

import websockets
from websockets.server import WebSocketServerProtocol

# Import RuneGPT agent
from agent.runegpt import RuneGPT
from agent.game_state import GameState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("RuneGPTServer")

# Store active connections
active_connections: Dict[str, WebSocketServerProtocol] = {}
# Store agent instances
agents: Dict[str, RuneGPT] = {}

async def handle_connection(websocket: WebSocketServerProtocol, path: str):
    """Handle a new WebSocket connection."""
    # Generate a session ID if not provided
    session_id = str(uuid.uuid4())
    logger.info(f"New connection established. Session ID: {session_id}")
    
    # Store the connection
    active_connections[session_id] = websocket
    
    try:
        # Create a new RuneGPT agent for this session
        agents[session_id] = RuneGPT(session_id=session_id, load_memory=True)
        logger.info(f"Created new RuneGPT agent for session {session_id}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to RuneGPT AI server",
            "session_id": session_id
        }))
        
        # Process messages
        async for message in websocket:
            try:
                # Parse the message
                data = json.loads(message)
                logger.info(f"Received message from {session_id}: {data}")
                
                # Process the message and get a response
                response = await process_message(session_id, data)
                
                # Send the response
                await websocket.send(json.dumps(response))
                logger.info(f"Sent response to {session_id}: {response}")
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {session_id}: {message}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message from {session_id}: {str(e)}", exc_info=True)
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed for session {session_id}")
    except Exception as e:
        logger.error(f"Unexpected error for session {session_id}: {str(e)}", exc_info=True)
    finally:
        # Clean up
        if session_id in active_connections:
            del active_connections[session_id]
        if session_id in agents:
            # Save agent state before removing
            agents[session_id].save_memory()
            del agents[session_id]
        logger.info(f"Cleaned up resources for session {session_id}")

async def process_message(session_id: str, data: dict) -> dict:
    """Process an incoming message and return a response."""
    # Extract game state data
    screen_text = data.get("screen_text", "")
    chatbox = data.get("chatbox", [])
    player_location = data.get("player_location", "")
    inventory = data.get("inventory", [])
    step = data.get("step", "")
    
    # Create a GameState object
    game_state = GameState(
        screen_text=screen_text,
        chatbox=chatbox,
        player_location=player_location,
        inventory=inventory,
        step=step
    )
    
    # Get the agent for this session
    agent = agents.get(session_id)
    if not agent:
        logger.error(f"No agent found for session {session_id}")
        return {
            "type": "error",
            "message": "No agent found for this session"
        }
    
    # Process the game state and get the next action
    action = agent.process_game_state(game_state)
    
    # Format the response
    response = {
        "type": "action",
        "next_action": action.name,
        "confidence": action.confidence,
        "reasoning": action.reasoning,
        "emotion": action.emotion
    }
    
    # Add optional fields if available
    if hasattr(action, 'delay') and action.delay:
        response["delay"] = action.delay
    if hasattr(action, 'message') and action.message:
        response["message"] = action.message
    
    return response

async def main():
    """Start the WebSocket server."""
    host = "0.0.0.0"
    port = 8765
    
    logger.info(f"Starting RuneGPT WebSocket server on {host}:{port}")
    
    async with websockets.serve(handle_connection, host, port):
        logger.info("Server is running")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main()) 