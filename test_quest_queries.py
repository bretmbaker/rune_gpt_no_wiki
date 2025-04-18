#!/usr/bin/env python3
"""
Test script for evaluating quest-related queries using the V2 semantic engine.
Tests various aspects of quest information retrieval including basic info,
requirements, rewards, mechanics, and difficulty levels.
"""

import logging
from agent.semantic_query_engine_v2 import SemanticQueryEngineV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def test_quest_queries():
    """Run a series of quest-related test queries and log the results."""
    engine = SemanticQueryEngineV2()
    
    # Test queries covering different aspects of quests
    test_queries = [
        "How do I start Dragon Slayer?",
        "What are the requirements for Recipe for Disaster?",
        "What items do I need for Desert Treasure?",
        "How do I solve the light puzzle in Mourning's End Part II?",
        "What level requirements are needed for Dragon Slayer II?",
        "Where do I start Monkey Madness?",
        "What are the rewards for completing Underground Pass?",
        "How do I complete the Temple of Light puzzle?",
        "What items should I bring for Fight Caves?",
        "What skills do I need for Song of the Elves?"
    ]
    
    logger = logging.getLogger(__name__)
    logger.info("Starting quest query tests...")
    
    for query in test_queries:
        logger.info("\nTesting query: %s", query)
        try:
            result = engine.query(query)
            logger.info("Result: %s", result)
        except Exception as e:
            logger.error("Error processing query '%s': %s", query, str(e))
        logger.info("-" * 80)
    
    logger.info("Quest query tests completed.")

if __name__ == "__main__":
    test_quest_queries() 