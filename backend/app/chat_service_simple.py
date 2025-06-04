import hashlib
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from .config import get_settings
from .models import Document, DocumentChunk, Conversation

settings = get_settings()


class ChatService:
    def __init__(self):
        # Simple in-memory storage for demo
        self.documents = {}
        self.demo_responses = {
            "pto": "Our PTO policy provides 15 days of paid time off per year, increasing to 20 days after 3 years and 25 days after 5 years. You can carry over up to 10 unused days to the next year.",
            "benefits": "We offer comprehensive health insurance through Blue Cross Blue Shield (company covers 80% of premiums), 401(k) with company match up to 3%, life insurance, FSA, gym membership reimbursement, and $1,500 annual professional development budget.",
            "remote": "Eligible employees may work remotely up to 3 days per week with manager approval. We provide a $500 home office setup stipend and $50 monthly internet reimbursement.",
            "expense": "Submit expense reports within 30 days with receipts. Meal limits: Breakfast $20, Lunch $30, Dinner $50. Hotels up to $200/night. Use the company expense system for reimbursement.",
            "training": "Each employee has a $1,500 annual professional development budget. This covers online courses, certifications, conferences, and books. You also get 40 hours per year for training during work hours.",
            "default": "I'm here to help with HR questions. You can ask me about PTO policies, benefits, remote work, expenses, or training opportunities."
        }
    
    def chunk_document(self, content: str, chunk_size: int = 500) -> List[str]:
        """Split document into chunks"""
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def add_context_to_chunks(self, chunks: List[str], document_title: str) -> List[str]:
        """Add context to chunks for better retrieval"""
        contextualized_chunks = []
        
        for i, chunk in enumerate(chunks):
            context = f"From document: {document_title}, part {i+1} of {len(chunks)}. "
            contextualized_chunk = context + chunk
            contextualized_chunks.append(contextualized_chunk)
        
        return contextualized_chunks
    
    def ingest_document(self, db: Session, filepath: str, filename: str):
        """Process and store a document"""
        # Read document content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if document already exists
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        existing_doc = db.query(Document).filter(Document.content_hash == content_hash).first()
        
        if existing_doc:
            return {"status": "already_exists", "document_id": existing_doc.id}
        
        # Create document record
        doc = Document(
            filename=filename,
            content_hash=content_hash
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Store in memory for simple demo
        self.documents[filename] = content
        
        # Chunk the document
        chunks = self.chunk_document(content)
        
        # Store chunks in database
        for i, chunk in enumerate(chunks):
            db_chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk,
                contextualized_content=chunk,
                vector_id=f"{doc.id}_{i}"
            )
            db.add(db_chunk)
        
        doc.chunk_count = len(chunks)
        db.commit()
        
        return {"status": "success", "document_id": doc.id, "chunks": len(chunks)}
    
    def search_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """Simple keyword-based search for demo"""
        query_lower = query.lower()
        
        # Simple keyword matching
        if any(word in query_lower for word in ["pto", "vacation", "time off", "leave"]):
            return [{"content": self.demo_responses["pto"], "score": 0.9}]
        elif any(word in query_lower for word in ["benefit", "insurance", "401k", "health"]):
            return [{"content": self.demo_responses["benefits"], "score": 0.9}]
        elif any(word in query_lower for word in ["remote", "work from home", "wfh"]):
            return [{"content": self.demo_responses["remote"], "score": 0.9}]
        elif any(word in query_lower for word in ["expense", "reimburse", "travel"]):
            return [{"content": self.demo_responses["expense"], "score": 0.9}]
        elif any(word in query_lower for word in ["training", "development", "course", "learn"]):
            return [{"content": self.demo_responses["training"], "score": 0.9}]
        
        return [{"content": self.demo_responses["default"], "score": 0.5}]
    
    def generate_response(self, question: str, contexts: List[Dict]) -> str:
        """Generate response based on contexts"""
        if contexts and contexts[0]["score"] > 0.7:
            return contexts[0]["content"]
        return self.demo_responses["default"]
    
    async def chat(self, db: Session, user_id: int, message: str) -> str:
        """Main chat function"""
        # Search for relevant documents
        contexts = self.search_documents(message)
        
        # Generate response
        response = self.generate_response(message, contexts)
        
        # Save conversation
        conversation = Conversation(
            user_id=user_id,
            message=message,
            response=response
        )
        db.add(conversation)
        db.commit()
        
        return response