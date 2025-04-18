#!/usr/bin/env python3
# integrate_with_runegpt.py - Example of integrating the knowledge engine with RuneGPT

import os
import sys
import json
from semantic_query_engine import SemanticQueryEngine

# Add the parent directory to the path so we can import RuneGPT modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import RuneGPT modules (adjust these imports based on your actual RuneGPT structure)
try:
    from rune_adventure import RuneGPTAgent
    from wiki_query_engine import query_osrs_wiki
except ImportError:
    print("Warning: Could not import RuneGPT modules. This is just a demonstration.")
    RuneGPTAgent = None
    query_osrs_wiki = None

class RuneGPTKnowledgeEngine:
    """Integration of the knowledge engine with RuneGPT."""
    
    def __init__(self, vector_index_dir="vector_index"):
        """
        Initialize the knowledge engine integration.
        
        Args:
            vector_index_dir: Directory containing the vector index
        """
        self.engine = SemanticQueryEngine(vector_index_dir)
        self.cache = {}  # Simple cache to avoid repeated queries
    
    def query_knowledge_base(self, query: str, top_k: int = 3) -> str:
        """
        Query the knowledge base and return a formatted response.
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            
        Returns:
            Formatted response with knowledge
        """
        # Check cache first
        if query in self.cache:
            return self.cache[query]
        
        # Query the knowledge base
        results = self.engine.query(query, top_k=top_k)
        
        if not results:
            return "I couldn't find any relevant information in my knowledge base."
        
        # Format the response
        response = "Based on my knowledge of OSRS:\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"{i}. {result['title']}\n"
            response += f"   Source: {result['source']}\n"
            response += f"   {result['text']}\n\n"
        
        # Cache the response
        self.cache[query] = response
        
        return response
    
    def replace_wiki_query(self, query_func):
        """
        Replace the original wiki query function with our knowledge engine.
        
        Args:
            query_func: The original wiki query function
            
        Returns:
            A new function that uses the knowledge engine
        """
        def new_query_func(query):
            print(f"[Knowledge Engine]: Querying knowledge base for: {query}")
            return self.query_knowledge_base(query)
        
        return new_query_func

def demonstrate_usage():
    """Demonstrate how to use the knowledge engine."""
    # Initialize the knowledge engine
    knowledge_engine = RuneGPTKnowledgeEngine()
    
    # Example queries
    queries = [
        "How do I start fishing?",
        "What are the requirements for Dragon Slayer?",
        "How do I train Woodcutting?",
        "What is the best way to train Mining?",
        "How do I complete Tutorial Island?"
    ]
    
    print("=== RuneGPT Knowledge Engine Demo ===\n")
    
    for query in queries:
        print(f"Query: {query}")
        response = knowledge_engine.query_knowledge_base(query)
        print(f"Response:\n{response}\n")
        print("-" * 80 + "\n")

def integrate_with_runegpt():
    """Demonstrate how to integrate with RuneGPT."""
    if RuneGPTAgent is None:
        print("RuneGPT modules not available. This is just a demonstration.")
        return
    
    # Initialize the knowledge engine
    knowledge_engine = RuneGPTKnowledgeEngine()
    
    # Create a RuneGPT agent
    agent = RuneGPTAgent(load_memory=False)
    
    # Replace the wiki query function with our knowledge engine
    # This is a monkey patch - in a real implementation, you would modify the RuneGPTAgent class
    agent._process_screen_text = lambda self, screen_text: (
        knowledge_engine.replace_wiki_query(agent._process_screen_text)(screen_text)
    )
    
    print("=== RuneGPT with Knowledge Engine Integration ===\n")
    print("The agent will now use the local knowledge base instead of querying the wiki.")
    print("This is a demonstration - the agent won't actually run.")
    
    # In a real implementation, you would run the agent:
    # agent.run()

if __name__ == "__main__":
    # Demonstrate usage
    demonstrate_usage()
    
    # Show integration with RuneGPT
    integrate_with_runegpt() 