import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pinecone import Pinecone, ServerlessSpec
from app.config import get_settings

settings = get_settings()

def setup_pinecone_index():
    """Create Pinecone index if it doesn't exist"""
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        
        index_name = "hr-docs"
        
        # Check if index already exists
        existing_indexes = pc.list_indexes()
        index_exists = any(index.name == index_name for index in existing_indexes)
        
        if index_exists:
            print(f"Index '{index_name}' already exists.")
            # Get index info
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"Current vectors: {stats.total_vector_count}")
        else:
            print(f"Creating index '{index_name}'...")
            
            # Create index with serverless spec
            pc.create_index(
                name=index_name,
                dimension=384,  # all-MiniLM-L6-v2 dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            
            # Wait for index to be ready
            print("Waiting for index to be ready...")
            time.sleep(5)
            
            # Verify index creation
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"Index created successfully! Dimension: {stats.dimension}")
            
    except Exception as e:
        print(f"Error setting up Pinecone: {e}")
        print("Make sure your Pinecone API key is valid and you have access to create indexes.")
        return False
    
    return True

if __name__ == "__main__":
    if setup_pinecone_index():
        print("\nPinecone index is ready for document ingestion!")
    else:
        print("\nFailed to set up Pinecone index.")