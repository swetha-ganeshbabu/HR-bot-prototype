import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat_service import ChatService

chat_service = ChatService()

def test_search():
    """Test the search functionality"""
    print("Testing HR Document Search")
    print("=" * 50)
    
    test_queries = [
        "What is the PTO policy?",
        "How many sick days do I get?",
        "Tell me about health insurance",
        "Can I work from home?",
        "What is the 401k match?",
        "How do I submit expenses?",
        "What are the remote work requirements?",
        "Tell me about bereavement leave",
        "What is the code of conduct?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        try:
            results = chat_service.search_documents(query, top_k=2)
            if results:
                for i, result in enumerate(results):
                    print(f"\n  Result {i+1} (score: {result.get('score', 0):.3f}):")
                    content = result.get('content', '')
                    # Show first 200 characters
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(f"    {preview}")
            else:
                print("  No results found")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Check Pinecone stats
    print("\n\n📊 Pinecone Index Stats:")
    try:
        stats = chat_service.index.describe_index_stats()
        print(f"  Total vectors: {stats.total_vector_count}")
        print(f"  Dimension: {stats.dimension}")
    except Exception as e:
        print(f"  Error getting stats: {e}")

if __name__ == "__main__":
    test_search()