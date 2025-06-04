import os
import sys
import glob
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base
from app.chat_service import ChatService
from app.config import get_settings

# Create tables
Base.metadata.create_all(bind=engine)

settings = get_settings()
chat_service = ChatService()


def ingest_hr_documents():
    """Ingest all HR documents from the hr-documents folder"""
    db = SessionLocal()
    
    # Path to HR documents
    hr_docs_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "hr-documents"
    )
    
    if not os.path.exists(hr_docs_path):
        print(f"HR documents folder not found: {hr_docs_path}")
        return
    
    print(f"Looking for documents in: {hr_docs_path}")
    
    # Find all markdown files
    md_files = glob.glob(os.path.join(hr_docs_path, "**/*.md"), recursive=True)
    
    # Filter out README
    md_files = [f for f in md_files if not f.endswith("README.md")]
    
    print(f"\nFound {len(md_files)} documents to ingest:")
    for file in md_files:
        print(f"  - {os.path.relpath(file, hr_docs_path)}")
    
    print("\nStarting ingestion...")
    
    for filepath in md_files:
        filename = os.path.relpath(filepath, hr_docs_path)
        print(f"\nIngesting: {filename}")
        
        try:
            result = chat_service.ingest_document(db, filepath, filename)
            print(f"  Status: {result['status']}")
            if result['status'] == 'success':
                print(f"  Document ID: {result['document_id']}")
                print(f"  Chunks created: {result['chunks']}")
            elif result['status'] == 'already_exists':
                print(f"  Document already exists with ID: {result['document_id']}")
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    db.close()
    print("\n✅ Document ingestion complete!")
    
    # Get index stats
    try:
        stats = chat_service.index.describe_index_stats()
        print(f"\nPinecone index stats:")
        print(f"  Total vectors: {stats.total_vector_count}")
        print(f"  Dimension: {stats.dimension}")
    except Exception as e:
        print(f"\nCould not get index stats: {e}")


def test_search():
    """Test the search functionality"""
    print("\n\nTesting search functionality...")
    
    test_queries = [
        "What is the PTO policy?",
        "How many sick days do I get?",
        "Tell me about health insurance",
        "Can I work from home?",
        "What is the 401k match?",
        "How do I submit expenses?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            results = chat_service.search_documents(query, top_k=2)
            for i, result in enumerate(results):
                print(f"  Result {i+1} (score: {result['score']:.3f}):")
                print(f"    {result['content'][:150]}...")
        except Exception as e:
            print(f"  Error: {str(e)}")


if __name__ == "__main__":
    print("HR Document Ingestion Script")
    print("=" * 50)
    
    # Check if we have an OpenAI API key for embeddings
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_key_here":
        print("\n⚠️  Warning: No OpenAI API key found.")
        print("The system will use free sentence-transformers for embeddings.")
        print("For better chat responses, add your OpenAI API key to backend/.env")
    
    ingest_hr_documents()
    
    # Optionally test search
    response = input("\nWould you like to test the search functionality? (y/n): ")
    if response.lower() == 'y':
        test_search()