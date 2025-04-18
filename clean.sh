#!/bin/bash
echo "Cleaning up unnecessary files for sandbox mode..."

# Remove directories
rm -rf tools/
rm -rf vector_index/
rm -rf knowledge/

# Remove files
rm -f semantic_query_engine.py
rm -f wiki_scraper.log
rm -f test_query.py

echo "Cleanup complete."
