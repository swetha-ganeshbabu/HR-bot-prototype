from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
import os

from .database import engine, get_db
from .models import Base, User, Conversation
from .auth import (
    authenticate_user, create_access_token, get_current_user, 
    create_demo_user, get_password_hash
)
from .chat_service import ChatService
from .config import get_settings

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="HR Bot API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = get_settings()
chat_service = ChatService()


# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    message_id: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    version: str


class ConversationHistory(BaseModel):
    id: int
    message: str
    response: str
    timestamp: str


# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint"""
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return LoginResponse(access_token=access_token)


# Registration is disabled for security
# To enable registration, uncomment this endpoint and add proper admin controls
# @app.post("/api/auth/register", response_model=LoginResponse)
# async def register(request: LoginRequest, db: Session = Depends(get_db)):
#     """Register endpoint - DISABLED FOR SECURITY"""
#     raise HTTPException(
#         status_code=status.HTTP_403_FORBIDDEN,
#         detail="Registration is disabled. Please contact your administrator."
#     )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat endpoint"""
    try:
        response = await chat_service.chat(db, current_user.id, request.message)
        
        # Get the latest conversation
        latest_conv = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).order_by(Conversation.id.desc()).first()
        
        return ChatResponse(
            response=response,
            message_id=latest_conv.id if latest_conv else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@app.get("/api/conversations", response_model=List[ConversationHistory])
async def get_conversation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get conversation history"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.timestamp.desc()).limit(limit).all()
    
    return [
        ConversationHistory(
            id=conv.id,
            message=conv.message,
            response=conv.response,
            timestamp=conv.timestamp.isoformat()
        )
        for conv in conversations
    ]


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create data directories
    os.makedirs("./data/hr_docs", exist_ok=True)
    
    # Create demo user
    db = next(get_db())
    create_demo_user(db)
    db.close()
    
    print("HR Bot API started successfully!")
    print("Demo credentials: admin/password")


# Serve static files in production
if not settings.debug:
    app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")