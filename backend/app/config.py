from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./data/database.db"
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_gemini_api_key: Optional[str] = None
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = "gcp-starter"
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24  # 24 hours
    
    # Application
    hr_docs_path: str = "./data/hr_docs"
    debug: bool = True
    
    # Vector DB
    vector_db_type: str = "pinecone"  # Only pinecone is supported
    
    # LLM
    llm_provider: str = "openai"  # "openai", "anthropic", or "gemini"
    llm_model: str = "gpt-3.5-turbo"  # or "claude-3-haiku-20240307" or "gemini-pro"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()