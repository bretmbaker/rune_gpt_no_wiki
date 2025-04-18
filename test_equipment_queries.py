#!/usr/bin/env python3
"""
Test script for evaluating equipment-related queries with the V2 semantic engine.
"""

import logging
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_equipment_queries():
    """Test various equipment-related queries."""
    try:
        # Add the current directory to Python path
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Import the semantic engine
        logger.info("Importing SemanticQueryEngineV2...")
        from agent.semantic_query_engine_v2 import SemanticQueryEngineV2
        
        # Initialize the semantic engine
        logger.info("Initializing SemanticQueryEngineV2...")
        engine = SemanticQueryEngineV2()
        
        # List of test queries
        queries = [
            "What's the best boots for melee?",
            "What stats does a Berserker ring give?",
            "Can you wear a shield with a godsword?",
            "What level do I need for dragon boots?",
            "What are the best gloves for ranged?",
            "What is the best helmet for magic?",
            "What are the requirements for Bandos chestplate?",
            "What are the stats of an Abyssal whip?",
            "What is the best cape for melee?",
            "What is the best amulet for magic?"
        ]
        
        # Run each query and log results
        for query in queries:
            logger.info(f"\nQuery: {query}")
            try:
                result = engine.query(query)
                logger.info(f"Result: {result}")
            except Exception as e:
                logger.error(f"Error processing query '{query}': {str(e)}")
                logger.error(traceback.format_exc())
            logger.info("-" * 80)
            
    except Exception as e:
        logger.error(f"Error in test_equipment_queries: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    test_equipment_queries() 