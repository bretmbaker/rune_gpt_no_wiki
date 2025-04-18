#!/usr/bin/env python3
"""
Test script for SemanticQueryEngineV2
Tests various queries across different categories
"""

import logging
from agent.semantic_query_engine_v2 import SemanticQueryEngineV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_queries():
    """Test various queries across different categories"""
    # Initialize engine
    engine = SemanticQueryEngineV2()
    
    # Test queries
    queries = [
        # Skills queries
        "What level do I need for yew trees?",
        "Where can I find magic trees?",
        "What is the best axe for woodcutting?",
        "How much XP do I get from oak logs?",
        "What is the Woodcutting Guild?",
        "What level do I need for the Woodcutting Guild?",
        "What is the fastest way to train woodcutting?",
        "What are the requirements for the Woodcutting Guild?",
        "What is the best tree to cut at level 60?",
        "What is the best tree to cut at level 30?",
        
        # Quest queries
        "How do I start Dragon Slayer?",
        "What are the requirements for Dragon Slayer?",
        "Where do I find the map pieces for Dragon Slayer?",
        "What do I need to bring for Dragon Slayer?",
        "How do I solve the maze in Dragon Slayer?",
        
        # Bestiary queries
        "Where can I find dragons?",
        "What are the stats of the King Black Dragon?",
        "How much HP does the King Black Dragon have?",
        "What are the weaknesses of dragons?",
        "What are the drop rates for dragon bones?",
        
        # Item queries
        "What does the Abyssal whip do?",
        "Where can I get an Abyssal whip?",
        "How much does an Abyssal whip cost?",
        "What are the stats of the Abyssal whip?",
        "What are the effects of the Abyssal whip?",
        
        # Minigame queries
        "How do I play Castle Wars?",
        "What are the rewards for Castle Wars?",
        "Where is the Castle Wars area?",
        "What should I wear for Castle Wars?",
        "How do I get a Castle Wars ticket?",
        
        # Equipment queries
        "What are the stats of Bandos armour?",
        "What level do I need for Bandos armour?",
        "Where can I get Bandos armour?",
        "How much does Bandos armour cost?",
        "What are the effects of Bandos armour?",
        
        # NPC queries
        "Where is the Grand Exchange?",
        "What does the Grand Exchange do?",
        "What do I need to use the Grand Exchange?",
        "How do I talk to the Grand Exchange clerk?",
        "What are the benefits of the Grand Exchange?",
        
        # Transportation queries
        "How do I get to Karamja?",
        "Where is the Karamja boat?",
        "What do I need to use the Karamja boat?",
        "What are the destinations from Karamja?",
        "How much does the Karamja boat cost?"
    ]
    
    # Run queries
    for query in queries:
        logger.info(f"\nQuery: {query}")
        result = engine.query(query)
        logger.info(f"Result:\n{result}")
        logger.info("-" * 80)

if __name__ == "__main__":
    test_queries() 