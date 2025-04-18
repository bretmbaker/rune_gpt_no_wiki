#!/usr/bin/env python3
"""Generate test vector index files for development."""

import numpy as np
import json
import os
from datetime import datetime

# Test documents
documents = [
    {
        "text": "Tutorial Island is where new players begin their RuneScape journey.",
        "source": "tutorial/getting_started.txt",
        "category": "tutorial",
        "title": "Getting Started"
    },
    {
        "text": "Fishing is a skill that allows players to catch fish that can be used with the Cooking skill.",
        "source": "skills/fishing.txt",
        "category": "skills",
        "title": "Fishing"
    },
    {
        "text": "Mining is a gathering skill that allows players to obtain ores and gems from rocks.",
        "source": "skills/mining.txt",
        "category": "skills",
        "title": "Mining"
    },
    {
        "text": "Combat skills include Attack, Strength, Defence, Ranged, Magic, and Prayer.",
        "source": "skills/combat.txt",
        "category": "skills",
        "title": "Combat Skills"
    },
    {
        "text": "Quests are a series of tasks that players can complete for rewards.",
        "source": "quests/overview.txt",
        "category": "quests",
        "title": "Quest Overview"
    },
    {
        "text": "The Grand Exchange is a marketplace where players can buy and sell items.",
        "source": "general/grand_exchange.txt",
        "category": "general",
        "title": "Grand Exchange"
    },
    {
        "text": "Ironman Mode is a game mode where players must be self-sufficient.",
        "source": "general/ironman.txt",
        "category": "general",
        "title": "Ironman Mode"
    },
    {
        "text": "Achievement Diaries are sets of tasks that test players' skills.",
        "source": "achievements/diaries.txt",
        "category": "achievements",
        "title": "Achievement Diaries"
    },
    {
        "text": "Slayer is a skill where players must kill specific monsters assigned by a Slayer Master.",
        "source": "skills/slayer.txt",
        "category": "skills",
        "title": "Slayer"
    },
    {
        "text": "Player-owned houses can be built and customized using the Construction skill.",
        "source": "skills/construction.txt",
        "category": "skills",
        "title": "Construction"
    }
]

# Create vector_index directory if it doesn't exist
os.makedirs("vector_index", exist_ok=True)

# Generate random embeddings (384 dimensions to match all-MiniLM-L6-v2)
embeddings = np.random.rand(len(documents), 384)
np.save("vector_index/embeddings.npy", embeddings)

# Save documents
with open("vector_index/documents.json", "w") as f:
    json.dump(documents, f, indent=2)

# Save metadata
metadata = {
    "total_documents": len(documents),
    "total_files": len(documents),
    "categories": sorted(list(set(doc["category"] for doc in documents))),
    "model": "all-MiniLM-L6-v2",
    "last_updated": datetime.now().isoformat()
}

with open("vector_index/index_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("Generated test vector index files:")
print(f"- {len(documents)} documents")
print(f"- {len(metadata['categories'])} categories: {', '.join(metadata['categories'])}")
print(f"- Embeddings shape: {embeddings.shape}") 