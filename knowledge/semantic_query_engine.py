#!/usr/bin/env python3
# semantic_query_engine.py - Simple semantic search engine for OSRS wiki content

import os
import json
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("semantic_query_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("semantic_query_engine")

# Paths
WIKI_DATA_DIR = "wiki_data"
VECTOR_INDEX_DIR = "vector_index"

# Model to use for embeddings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

class SemanticQueryEngine:
    """Simple semantic search engine for OSRS wiki content."""
    
    def __init__(self, vector_index_dir: str = VECTOR_INDEX_DIR):
        """
        Initialize the semantic query engine.
        
        Args:
            vector_index_dir: Directory containing the vector index
        """
        self.vector_index_dir = vector_index_dir
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.wiki_data_dir = Path(WIKI_DATA_DIR)
        
        # Load index data
        try:
            with open(os.path.join(vector_index_dir, "embeddings.npy"), 'rb') as f:
                self.embeddings = np.load(f)
            with open(os.path.join(vector_index_dir, "documents.json"), 'r') as f:
                self.documents = json.load(f)
            with open(os.path.join(vector_index_dir, "index_metadata.json"), 'r') as f:
                self.metadata = json.load(f)
            logger.info("Loaded vector index successfully")
        except Exception as e:
            logger.error(f"Error loading vector index: {str(e)}")
            self.embeddings = np.array([])
            self.documents = []
            self.metadata = {}
    
    def _load_wiki_data(self) -> Dict[str, Dict[str, Any]]:
        """Load all wiki data from the new structure."""
        wiki_data = {}
        
        # Iterate through all subdirectories
        for category_dir in self.wiki_data_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            # Load metadata.json if it exists
            metadata_file = category_dir / "metadata.json"
            if not metadata_file.exists():
                continue
                
            try:
                with open(metadata_file, 'r') as f:
                    category_metadata = json.load(f)
                    
                # Load txt files referenced in metadata
                txt_dir = category_dir / "txt"
                if txt_dir.exists():
                    for item_name, item_data in category_metadata.items():
                        txt_file = txt_dir / item_data["txt"].split("/")[-1]
                        if txt_file.exists():
                            with open(txt_file, 'r') as f:
                                content = f.read()
                                wiki_data[item_name] = {
                                    "content": content,
                                    "category": category_dir.name,
                                    "metadata": item_data
                                }
            except Exception as e:
                logger.error(f"Error loading wiki data from {category_dir}: {str(e)}")
        
        return wiki_data
    
    def query(self, query_text: str, top_k: int = 3, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query the vector index for relevant content.
        
        Args:
            query_text: Natural language query
            top_k: Number of results to return
            category_filter: Optional category to filter results by
            
        Returns:
            List of results with content and metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self.model.encode(query_text)
            
            # Calculate cosine similarities
            similarities = np.dot(self.embeddings, query_embedding) / (
                np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            
            # Get top k results
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            # Format results
            results = []
            for idx in top_indices:
                doc = self.documents[idx]
                if category_filter and doc['category'] != category_filter:
                    continue
                
                result = {
                    "text": doc['content'],
                    "category": doc['category'],
                    "metadata": doc.get('metadata', {}),
                    "similarity": float(similarities[idx])
                }
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error querying: {str(e)}")
            return []
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return [d.name for d in self.wiki_data_dir.iterdir() if d.is_dir()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the wiki data."""
        stats = {
            "total_items": len(self.documents),
            "categories": len(self.get_categories()),
            "embeddings_shape": self.embeddings.shape if len(self.embeddings) > 0 else None
        }
        return stats

# Example usage
if __name__ == "__main__":
    engine = SemanticQueryEngine()
    
    # Print index stats
    stats = engine.get_stats()
    print(f"Index contains {stats['total_items']} items from {stats['categories']} categories")
    print(f"Embeddings shape: {stats['embeddings_shape']}")
    
    # Example query
    query = "How do I start fishing?"
    results = engine.query(query)
    
    print(f"\nQuery: {query}")
    print("\nResults:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['text'][:200]}...")
        print(f"   Category: {result['category']}")
        print(f"   Similarity: {result['similarity']:.4f}") 