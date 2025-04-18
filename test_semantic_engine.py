#!/usr/bin/env python
"""
Test script for the semantic query engine
"""

import logging
from agent.semantic_query_engine import SemanticQueryEngine

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_queries():
    """Test the semantic query engine with various queries"""
    engine = SemanticQueryEngine()
    
    # Debug woodcutting data
    logger.debug("Woodcutting data loaded:")
    logger.debug(f"Trees: {list(engine.woodcutting_data['trees'].keys())}")
    logger.debug(f"Axes: {list(engine.woodcutting_data['axes'].keys())}")
    logger.debug(f"Guild info present: {'content' in engine.woodcutting_data['guild']}")
    logger.debug(f"Training info present: {'content' in engine.woodcutting_data['training']}")
    
    # Test queries
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
    
    # Run queries
    for query in queries:
        logger.info(f"\nQuery: {query}")
        result = engine.query(query)
        logger.info(f"Result: {result}")
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_queries() 