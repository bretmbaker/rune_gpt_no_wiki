"""
Chat Mode for RuneGPT
Provides a conversational interface for interacting with RuneGPT agents
"""

import os
import sys
import time
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from agent.personality_config import PersonalityConfig, PersonalityConfigManager
from agent.narrative_logger import NarrativeLogger
from agent.memory import Memory
from agent.memory_types import MemoryEntry
from agent.semantic_query_engine import SemanticQueryEngine

logger = logging.getLogger(__name__)

@dataclass
class ChatResponse:
    """Represents a response from the chat interface"""
    text: str
    emotion: str
    personality_traits: Dict[str, Any]
    context: Dict[str, Any]

class ChatMode:
    """
    Handles chat interactions with RuneGPT agents.
    Provides a conversational interface for querying agent state and personality.
    """
    
    def __init__(self, character_name: str):
        """
        Initialize chat mode for a character.
        
        Args:
            character_name: Name of the character to chat with
        """
        self.logger = logging.getLogger(__name__)
        self.character_name = character_name
        
        # Initialize components
        self.personality_manager = PersonalityConfigManager()
        self.personality = self.personality_manager.load_config(character_name)
        self.narrative_logger = NarrativeLogger()
        self.memory = Memory()
        self.semantic_engine = SemanticQueryEngine()
        
        # Track conversation state
        self.conversation_history: List[Dict[str, str]] = []
        self.current_emotion = "neutral"
        
        # Initialize personality traits from config
        self.personality_traits = {
            "tone": self.personality.personality[0].get("tone", "balanced"),
            "motivation": self.personality.personality[0].get("motivation", "Progress steadily"),
            "philosophy": self.personality.personality[0].get("philosophy", "Balance efficiency with enjoyment"),
            "risk_tolerance": self.personality.risk_tolerance,
            "style": self.personality.style[0] if self.personality.style else "casual"
        }
        
        self.logger.info(f"Initialized chat mode for {character_name}")
    
    def process_input(self, user_input: str) -> ChatResponse:
        """
        Process user input and generate a response.
        
        Args:
            user_input: The user's input message
            
        Returns:
            ChatResponse object containing the agent's response
        """
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Determine response type and generate appropriate response
        response_text = ""
        emotion = self.current_emotion
        
        if "who are you" in user_input.lower():
            response_text = self._generate_identity_response()
        elif "what's your plan" in user_input.lower():
            response_text = self._generate_plan_response()
        elif "how do you feel" in user_input.lower():
            response_text = self._generate_emotional_response()
        else:
            response_text = self._generate_general_response(user_input)
            
        # Update emotional state based on response
        self._update_emotional_state(response_text)
        
        # Create response object
        response = ChatResponse(
            text=response_text,
            emotion=self.current_emotion,
            personality_traits=self.personality_traits,
            context={"conversation_history": self.conversation_history[-5:]}
        )
        
        # Update conversation history
        self.conversation_history.append({"role": "assistant", "content": response_text})
        
        return response
    
    def _generate_identity_response(self) -> str:
        """Generate a personality-driven identity response."""
        tone = self.personality_traits["tone"]
        style = self.personality_traits["style"]
        
        if style == "formal":
            response = f"I am {self.character_name}, a dedicated adventurer in the world of Gielinor."
        elif style == "casual":
            response = f"Hey there! I'm {self.character_name}, just your average RuneScape adventurer!"
        else:
            response = f"I'm {self.character_name}, exploring the world of Gielinor!"
            
        if tone == "confident":
            response += " I'm quite skilled in my chosen pursuits."
        elif tone == "humble":
            response += " I'm still learning and growing every day."
            
        return response
    
    def _generate_plan_response(self) -> str:
        """Generate a personality-driven plan response."""
        motivation = self.personality_traits["motivation"]
        goals = self.personality.long_term_goals
        
        response = "My current plans include: "
        
        if "efficiency" in motivation.lower():
            response += "optimizing my training methods and maximizing gains. "
        elif "exploration" in motivation.lower():
            response += "exploring new areas and discovering hidden secrets. "
            
        for goal in goals:
            response += f"\n- {goal}"
            
        return response
    
    def _generate_emotional_response(self) -> str:
        """Generate a personality-driven emotional response."""
        emotion = self.current_emotion
        tone = self.personality_traits["tone"]
        
        responses = {
            "happy": "I'm feeling quite cheerful today!",
            "excited": "I'm thrilled about my recent discoveries!",
            "focused": "I'm deeply focused on my current tasks.",
            "tired": "I could use a bit of rest, but I'm managing.",
            "neutral": "I'm feeling balanced and ready for whatever comes next."
        }
        
        base_response = responses.get(emotion, "I'm feeling okay.")
        
        if tone == "expressive":
            base_response += " " + self._add_emotional_detail(emotion)
            
        return base_response
    
    def _generate_general_response(self, user_input: str) -> str:
        """Generate a personality-driven general response."""
        style = self.personality_traits["style"]
        tone = self.personality_traits["tone"]
        
        # Use semantic engine to find relevant information
        relevant_info = self.semantic_engine.query(user_input)
        
        if style == "formal":
            response = f"Based on my knowledge, {relevant_info}"
        elif style == "casual":
            response = f"Oh, I know about that! {relevant_info}"
        else:
            response = relevant_info
            
        if tone == "helpful":
            response += " Is there anything specific you'd like to know more about?"
            
        return response
    
    def _update_emotional_state(self, response: str) -> None:
        """Update emotional state based on response content and personality."""
        # Simple emotion detection based on keywords
        emotion_keywords = {
            "happy": ["happy", "cheerful", "excited", "thrilled"],
            "excited": ["amazing", "incredible", "wonderful"],
            "focused": ["focus", "concentrate", "determined"],
            "tired": ["tired", "exhausted", "need rest"],
            "neutral": ["okay", "fine", "alright"]
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in response.lower() for keyword in keywords):
                self.current_emotion = emotion
                break
    
    def _add_emotional_detail(self, emotion: str) -> str:
        """Add emotional details based on personality traits."""
        details = {
            "happy": "The world feels full of possibilities!",
            "excited": "I can't wait to see what happens next!",
            "focused": "My mind is clear and ready for action.",
            "tired": "But I'll keep pushing forward.",
            "neutral": "Taking things one step at a time."
        }
        return details.get(emotion, "")

def main():
    """Main entry point for chat mode"""
    if len(sys.argv) < 2:
        print("Usage: python chat_mode.py <character_name>")
        sys.exit(1)
    
    character_name = sys.argv[1]
    chat = ChatMode(character_name)
    
    print(f"\nChatting with {character_name} (type 'exit' to quit)")
    print("-" * 50)
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == "exit":
            break
        
        response = chat.process_input(user_input)
        print(f"\n{character_name}: {response.text}")

if __name__ == "__main__":
    main() 