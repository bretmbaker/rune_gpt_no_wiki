#!/bin/bash
echo 'Cleaning up unnecessary files for sandbox mode...'

rm -rf "vector_index"
rm -rf "knowledge"
rm -rf "semantic_query_engine.py"
rm -rf "vector_index_builder.py"
rm -rf "test_query.py"
rm -rf "tools"
rm -rf "wiki_scraper.log"
rm -rf "wiki_data"

echo 'Cleanup complete.'
