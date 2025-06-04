import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
from app.auth import get_password_hash
from app.models import User

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create test user
    test_user = User(
        username="testuser",
        hashed_password=get_password_hash("testpass")
    )
    db.add(test_user)
    db.commit()
    
    yield db
    
    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)


def get_auth_headers(username: str = "testuser", password: str = "testpass"):
    """Helper function to get authentication headers"""
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuthentication:
    def test_register_new_user(self, test_db):
        response = client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "newpass"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_register_existing_user(self, test_db):
        response = client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "testpass"}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_valid_credentials(self, test_db):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, test_db):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpass"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, test_db):
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "anypass"}
        )
        assert response.status_code == 401


class TestChatEndpoints:
    def test_chat_authenticated(self, test_db):
        headers = get_auth_headers()
        response = client.post(
            "/api/chat",
            json={"message": "What is the PTO policy?"},
            headers=headers
        )
        assert response.status_code == 200
        assert "response" in response.json()
    
    def test_chat_unauthenticated(self):
        response = client.post(
            "/api/chat",
            json={"message": "What is the PTO policy?"}
        )
        assert response.status_code == 403
    
    def test_conversation_history_authenticated(self, test_db):
        headers = get_auth_headers()
        
        # First, send a chat message
        client.post(
            "/api/chat",
            json={"message": "Test message"},
            headers=headers
        )
        
        # Then get history
        response = client.get(
            "/api/conversations",
            headers=headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_conversation_history_unauthenticated(self):
        response = client.get("/api/conversations")
        assert response.status_code == 403


class TestAuth:
    def test_password_hashing(self):
        from app.auth import get_password_hash, verify_password
        
        password = "testpassword"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)
    
    def test_jwt_token_creation(self):
        from app.auth import create_access_token, verify_token
        
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"