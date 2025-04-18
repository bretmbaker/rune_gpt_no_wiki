#!/usr/bin/env python3
"""
Test script for evaluating woodcutting queries with the V2 semantic engine.
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

def test_woodcutting_queries():
    """Test various woodcutting-related queries."""
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
            "What level do I need for yew trees?",
            "Where can I find magic trees?",
            "What is the best axe for woodcutting?",
            "How much XP do I get from oak logs?",
            "What is the Woodcutting Guild?",
            "What level do I need for the Woodcutting Guild?",
            "What is the fastest way to train woodcutting?",
            "What are the requirements for the Woodcutting Guild?",
            "What is the best tree to cut at level 60?",
            "What is the best tree to cut at level 30?"
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
        logger.error(f"Error in test_woodcutting_queries: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    test_woodcutting_queries() 