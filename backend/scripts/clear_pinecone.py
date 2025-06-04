import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pinecone import Pinecone
from app.config import get_settings
from app.database import SessionLocal
from app.models import Document, DocumentChunk

settings = get_settings()

def clear_pinecone_and_db():
    """Clear all vectors from Pinecone and database"""
    # Initialize Pinecone
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index("hr-docs")
    
    # Delete all vectors
    print("Clearing Pinecone index...")
    index.delete(delete_all=True)
    
    # Clear database
    print("Clearing database records...")
    db = SessionLocal()
    db.query(DocumentChunk).delete()
    db.query(Document).delete()
    db.commit()
    db.close()
    
    print("✅ Cleared all data!")

if __name__ == "__main__":
    clear_pinecone_and_db()