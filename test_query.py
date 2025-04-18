from knowledge.semantic_query_engine import SemanticQueryEngine

def main():
    engine = SemanticQueryEngine()
    query = "What are the stats for the Abyssal whip?"
    results = engine.query(query)
    
    if results:
        print("\nQuery Results:")
        print("-" * 50)
        for i, result in enumerate(results[:3], 1):  # Show top 3 results
            print(f"\nResult {i}:")
            print(f"Score: {result['score']:.4f}")
            print(f"Category: {result['category']}")
            print(f"Title: {result['title']}")
            print(f"Text: {result['text'][:500]}...")  # Show first 500 chars
    else:
        print("No results found")

if __name__ == "__main__":
    main() 