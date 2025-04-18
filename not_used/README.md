# RuneGPT Knowledge Engine

A local knowledge base for RuneGPT that allows it to instantly reference any OSRS knowledge, offline, without relying on fragile real-time wiki lookups.

## Overview

This engine powers everything from Tutorial Island to Max Cape by providing RuneGPT with a comprehensive, searchable knowledge base of OSRS content. The system consists of three main components:

1. **Wiki Scraper**: Scrapes and saves clean OSRS wiki content into categorized .txt files
2. **Vector Index Builder**: Embeds all .txt files using Sentence Transformers and indexes them with ChromaDB
3. **Semantic Query Engine**: Provides natural language search capabilities for the indexed content

## Directory Structure

```
RuneGPT_KnowledgeCore/
├── wiki_data/
│   ├── skills/
│   ├── quests/
│   ├── minigames/
│   ├── diaries/
│   ├── items/
│   ├── bestiary/
│   ├── achievements/
│   └── collection/
├── vector_index/
├── wiki_scraper.py
├── vector_index_builder.py
├── semantic_query_engine.py
└── requirements.txt
```

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### 1. Scrape Wiki Content

Run the wiki scraper to download and clean OSRS wiki content:

```
python wiki_scraper.py
```

This will create categorized .txt files in the `wiki_data/` directory.

### 2. Build Vector Index

Create embeddings and index the wiki content:

```
python vector_index_builder.py
```

This will create a ChromaDB index in the `vector_index/` directory.

### 3. Query the Knowledge Base

Use the semantic query engine to search the knowledge base:

```python
from semantic_query_engine import SemanticQueryEngine

# Initialize the engine
engine = SemanticQueryEngine()

# Query the knowledge base
results = engine.query("How do I start fishing?", top_k=3)

# Print results
for result in results:
    print(f"Title: {result['title']}")
    print(f"Source: {result['source']}")
    print(f"Content: {result['text'][:200]}...")
    print(f"Score: {result['score']}")
    print()
```

## Updating the Knowledge Base

To update the knowledge base with the latest OSRS content:

1. Run the wiki scraper again to download updated content
2. Rebuild the vector index

## License

This project is for educational purposes only. OSRS and RuneScape are trademarks of Jagex Ltd.

## Acknowledgements

- OSRS Wiki for providing the content
- Sentence Transformers for the embedding models
- ChromaDB for the vector database 