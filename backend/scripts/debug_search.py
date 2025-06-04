import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat_service import ChatService

chat_service = ChatService()

def debug_search():
    """Debug the search functionality"""
    print("Debugging Vector Search")
    print("=" * 50)
    
    # Test specific queries
    test_query = "what is my current pto policy"
    
    print(f"\nQuery: '{test_query}'")
    print("\nSearching for documents...")
    
    results = chat_service.search_documents(test_query, top_k=5)
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} (score: {result.get('score', 0):.3f}) ---")
        print(f"Document ID: {result.get('document_id', 'N/A')}")
        print(f"Chunk Index: {result.get('chunk_index', 'N/A')}")
        content = result.get('content', '')
        print(f"Content preview: {content[:200]}...")
    
    # Check index stats
    print("\n\nPinecone Index Stats:")
    stats = chat_service.index.describe_index_stats()
    print(f"Total vectors: {stats.total_vector_count}")
    
    # Let's also check what's actually in the index
    print("\n\nChecking actual vectors in index...")
    # Query with empty vector to see all results
    import numpy as np
    zero_vector = np.zeros(384).tolist()
    
    all_results = chat_service.index.query(
        vector=zero_vector,
        top_k=20,
        include_metadata=True
    )
    
    print(f"\nAll vectors in index:")
    for match in all_results.matches:
        print(f"  ID: {match.id}, Score: {match.score:.3f}")
        if match.metadata:
            print(f"    Content: {match.metadata.get('content', '')[:100]}...")

if __name__ == "__main__":
    debug_search()