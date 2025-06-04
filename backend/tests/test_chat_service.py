import pytest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat_service_simple import ChatService


class TestChatService:
    def test_chunk_document(self):
        service = ChatService()
        content = " ".join(["word" + str(i) for i in range(1000)])
        
        chunks = service.chunk_document(content, chunk_size=100)
        
        assert len(chunks) == 10  # 1000 words / 100 words per chunk
        assert all(len(chunk.split()) <= 100 for chunk in chunks)
    
    def test_add_context_to_chunks(self):
        service = ChatService()
        chunks = ["This is chunk 1", "This is chunk 2"]
        document_title = "Test Document"
        
        contextualized = service.add_context_to_chunks(chunks, document_title)
        
        assert len(contextualized) == 2
        assert all(document_title in chunk for chunk in contextualized)
        assert "part 1 of 2" in contextualized[0]
        assert "part 2 of 2" in contextualized[1]
    
    def test_empty_document_chunking(self):
        service = ChatService()
        chunks = service.chunk_document("")
        
        assert len(chunks) == 0