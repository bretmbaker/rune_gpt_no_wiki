#!/usr/bin/env python3
"""
WebSocket server for RuneGPT
Handles communication between RuneLite plugin and RuneGPT AI
"""

import asyncio
import json
import logging
from typing import Dict, Set
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("state/logs/websocket.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RuneGPTServer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.game_states: Dict[str, dict] = {}

    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new client connection"""
        self.clients.add(websocket)
        logger.info(f"New client connected. Total clients: {len(self.clients)}")

    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a client connection"""
        self.clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Handle incoming messages from clients"""
        try:
            game_state = json.loads(message)
            logger.debug(f"Received game state: {game_state}")

            # Store the game state
            client_id = id(websocket)
            self.game_states[client_id] = game_state

            # Process the game state and generate a response
            response = await self.process_game_state(game_state)
            
            # Send the response back to the client
            await websocket.send(json.dumps(response))
            
        except json.JSONDecodeError:
            logger.error("Failed to parse message as JSON")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    async def process_game_state(self, game_state: dict) -> dict:
        """Process the game state and generate a response"""
        # This is where we'll integrate with the RuneGPT AI
        # For now, we'll just return a simple response based on the tutorial text
        tutorial_text = game_state.get("tutorialText", "")
        
        if "talk to" in tutorial_text.lower():
            return {
                "suggestion": "Talk to the NPC mentioned in the tutorial",
                "action": "talk",
                "target": "npc"
            }
        elif "inventory" in tutorial_text.lower():
            return {
                "suggestion": "Open your inventory",
                "action": "open_inventory"
            }
        elif "click" in tutorial_text.lower():
            return {
                "suggestion": "Click on the highlighted object",
                "action": "click"
            }
        else:
            return {
                "suggestion": "Follow the tutorial instructions",
                "action": "none"
            }

    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle WebSocket connections"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed")
        finally:
            await self.unregister(websocket)

    async def start(self):
        """Start the WebSocket server"""
        server = await websockets.serve(
            self.handler,
            self.host,
            self.port
        )
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        await server.wait_closed()

def main():
    server = RuneGPTServer()
    asyncio.run(server.start())

if __name__ == "__main__":
    main() 