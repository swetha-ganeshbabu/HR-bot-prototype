import os
import hashlib
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from sqlalchemy.orm import Session
from .config import get_settings
from .models import Document, DocumentChunk, Conversation

settings = get_settings()


class ChatService:
    def __init__(self):
        # Initialize embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize vector database
        pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index = pc.Index("hr-docs")
        
        # LLM will be initialized when needed
    
    def chunk_document(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split document into overlapping chunks by sections"""
        chunks = []
        
        # Split by double newlines to preserve sections
        sections = content.split('\n\n')
        
        current_chunk = ""
        
        for section in sections:
            # If adding this section would exceed chunk size, save current chunk
            if current_chunk and len(current_chunk.split()) + len(section.split()) > chunk_size:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap from previous
                words = current_chunk.split()
                if len(words) > overlap:
                    current_chunk = ' '.join(words[-overlap:]) + '\n\n' + section
                else:
                    current_chunk = section
            else:
                # Add section to current chunk
                if current_chunk:
                    current_chunk += '\n\n' + section
                else:
                    current_chunk = section
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If we have very few chunks, split large chunks further
        final_chunks = []
        for chunk in chunks:
            words = chunk.split()
            if len(words) > chunk_size * 1.5:
                # This chunk is too large, split it
                for i in range(0, len(words), chunk_size - overlap):
                    sub_chunk = ' '.join(words[i:i + chunk_size])
                    final_chunks.append(sub_chunk)
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def add_context_to_chunks(self, chunks: List[str], document_title: str) -> List[str]:
        """Add context to chunks for better retrieval"""
        contextualized_chunks = []
        
        # Extract key topic from filename
        topic_map = {
            "california-pto-policy": "PTO policy, paid time off, vacation days, sick leave",
            "california-sick-leave": "sick leave, illness, medical appointments",
            "remote-work-policy": "remote work, work from home, hybrid schedule",
            "expense-reimbursement": "expenses, reimbursement, travel, meals",
            "401k-retirement": "401k, retirement, matching, savings plan",
            "health-benefits": "health insurance, medical, dental, vision, benefits",
            "code-of-conduct": "code of conduct, ethics, behavior, policies"
        }
        
        # Get relevant keywords for this document
        doc_keywords = ""
        for key, keywords in topic_map.items():
            if key in document_title.lower():
                doc_keywords = keywords
                break
        
        for i, chunk in enumerate(chunks):
            # Add document context and keywords
            context = f"Document: {document_title}. Topics: {doc_keywords}. Section {i+1} of {len(chunks)}.\n\n"
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
        
        # Chunk the document
        chunks = self.chunk_document(content)
        contextualized_chunks = self.add_context_to_chunks(chunks, filename)
        
        # Store chunks and embeddings
        for i, (chunk, ctx_chunk) in enumerate(zip(chunks, contextualized_chunks)):
            # Generate embedding
            embedding = self.embedder.encode(ctx_chunk).tolist()
            
            # Store in vector database
            vector_id = f"{doc.id}_{i}"
            
            self.index.upsert([(vector_id, embedding, {
                "document_id": doc.id,
                "chunk_index": i,
                "content": chunk
            })])
            
            # Store chunk in database
            db_chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk,
                contextualized_content=ctx_chunk,
                vector_id=vector_id
            )
            db.add(db_chunk)
        
        doc.chunk_count = len(chunks)
        db.commit()
        
        return {"status": "success", "document_id": doc.id, "chunks": len(chunks)}
    
    def search_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant document chunks"""
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        contexts = []
        for match in results.matches:
            contexts.append({
                "content": match.metadata["content"],
                "score": match.score,
                "document_id": match.metadata["document_id"],
                "chunk_index": match.metadata["chunk_index"]
            })
        
        return contexts
    
    def generate_response(self, question: str, contexts: List[Dict]) -> str:
        """Generate response using LLM or return context directly"""
        if not contexts:
            return "I couldn't find specific information about that in our HR documents. Please contact HR directly for assistance."
        
        # Prepare context
        context_text = "\n\n".join([f"Context {i+1}: {ctx['content']}" for i, ctx in enumerate(contexts)])
        
        # If we have Gemini configured, use it
        if settings.llm_provider == "gemini" and settings.google_gemini_api_key and settings.google_gemini_api_key != "your_gemini_key_here":
            try:
                import google.generativeai as genai
                
                genai.configure(api_key=settings.google_gemini_api_key)
                model = genai.GenerativeModel(settings.llm_model)
                
                prompt = f"""You are an HR assistant. Use the following context to answer the question.
                
Context:
{context_text}

Question: {question}

Answer the question based on the context provided. Be conversational and helpful. If the answer is not in the context, say so politely."""
                
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Gemini error: {e}")
                # Fall back to OpenAI if available
        
        # If we have OpenAI configured, use it
        if settings.llm_provider == "openai" and settings.openai_api_key and settings.openai_api_key != "your_openai_key_here":
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.openai_api_key)
                
                prompt = f"""You are an HR assistant. Use the following context to answer the question.
                
Context:
{context_text}

Question: {question}

Answer the question based on the context provided. If the answer is not in the context, say so politely."""
                
                response = client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful HR assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI error: {e}")
                # Fall back to returning context
        
        # If no LLM available, return the best matching context
        best_context = contexts[0]['content']
        
        # Remove the document context prefix we added for search
        if "Document:" in best_context and "\n\n" in best_context:
            parts = best_context.split("\n\n", 1)
            if len(parts) > 1:
                best_context = parts[1]
        
        # Clean up for better readability
        # Keep markdown formatting but clean up extra whitespace
        best_context = best_context.strip()
        
        # If it's too long, try to find a good breaking point
        if len(best_context) > 800:
            # Try to break at a paragraph
            paragraphs = best_context[:800].split('\n\n')
            if len(paragraphs) > 1:
                # Keep all but the last (potentially incomplete) paragraph
                best_context = '\n\n'.join(paragraphs[:-1]) + "..."
            else:
                best_context = best_context[:800] + "..."
        
        return f"Based on our HR documentation:\n\n{best_context}"
    
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