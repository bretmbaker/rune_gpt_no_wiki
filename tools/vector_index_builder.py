#!/usr/bin/env python3
"""
Vector Index Builder for RuneGPT
Builds and maintains the vector index for semantic search
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("vector_index_builder.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vector_index_builder")

class VectorIndexBuilder:
    """Builds and maintains vector index for semantic search"""
    
    def __init__(self, wiki_data_dir: str = "wiki_data", vector_index_dir: str = "vector_index"):
        """
        Initialize the vector index builder.
        
        Args:
            wiki_data_dir: Directory containing wiki data
            vector_index_dir: Directory to store vector index
        """
        self.wiki_data_dir = Path(wiki_data_dir)
        self.vector_index_dir = Path(vector_index_dir)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Create vector index directory
        self.vector_index_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_wiki_data(self) -> dict:
        """Load all wiki data from the wiki_data directory"""
        wiki_data = {}
        
        # Iterate through all subdirectories
        for category_dir in tqdm(list(self.wiki_data_dir.iterdir()), desc="Loading wiki data"):
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
    
    def build_index(self):
        """Build the vector index from wiki data"""
        logger.info("Starting vector index build")
        
        # Load wiki data
        wiki_data = self._load_wiki_data()
        logger.info(f"Loaded {len(wiki_data)} wiki entries")
        
        # Prepare documents and embeddings
        documents = []
        embeddings = []
        
        # Process each wiki entry
        for name, data in tqdm(wiki_data.items(), desc="Building index"):
            content = data["content"]
            documents.append({
                "name": name,
                "content": content,
                "category": data["category"],
                "metadata": data["metadata"]
            })
            embeddings.append(self.model.encode(content))
        
        # Convert to numpy array
        embeddings = np.array(embeddings)
        
        # Save index
        logger.info("Saving vector index")
        np.save(self.vector_index_dir / "embeddings.npy", embeddings)
        
        with open(self.vector_index_dir / "documents.json", 'w') as f:
            json.dump(documents, f)
        
        # Save metadata
        metadata = {
            "num_documents": len(documents),
            "embedding_dim": embeddings.shape[1],
            "categories": list(set(doc["category"] for doc in documents)),
            "last_updated": str(datetime.now())
        }
        
        with open(self.vector_index_dir / "index_metadata.json", 'w') as f:
            json.dump(metadata, f)
        
        logger.info("Vector index build complete")
        return metadata
    
    def verify_index(self) -> bool:
        """Verify the vector index is valid and up-to-date"""
        try:
            # Check required files exist
            required_files = ["embeddings.npy", "documents.json", "index_metadata.json"]
            for file in required_files:
                if not (self.vector_index_dir / file).exists():
                    logger.error(f"Missing required file: {file}")
                    return False
            
            # Load and verify embeddings
            embeddings = np.load(self.vector_index_dir / "embeddings.npy")
            with open(self.vector_index_dir / "documents.json", 'r') as f:
                documents = json.load(f)
            
            # Check dimensions match
            if len(documents) != len(embeddings):
                logger.error("Number of documents and embeddings don't match")
                return False
            
            logger.info("Vector index verification successful")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying vector index: {str(e)}")
            return False

def main():
    """Main entry point"""
    builder = VectorIndexBuilder()
    
    # Verify existing index
    if builder.verify_index():
        logger.info("Existing index is valid")
    else:
        logger.info("Building new index")
        metadata = builder.build_index()
        logger.info(f"Built index with {metadata['num_documents']} documents")

if __name__ == "__main__":
    main() 