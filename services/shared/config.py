"""
Shared configuration management
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://apex_user:apex_password_dev@localhost:5432/apex_pentest")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # MinIO/S3
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "apex_minio")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "apex_minio_password_dev")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    minio_bucket: str = os.getenv("MINIO_BUCKET", "apex-evidence")
    
    # ChromaDB
    chroma_url: str = os.getenv("CHROMA_URL", "http://localhost:8000")
    
    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "dev_jwt_secret_change_in_production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # AI/LLM
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-2.5-pro")
    
    # Agent Configuration
    agent_timeout_seconds: int = int(os.getenv("AGENT_TIMEOUT_SECONDS", "300"))
    agent_memory_limit_mb: int = int(os.getenv("AGENT_MEMORY_LIMIT_MB", "2048"))
    agent_max_retries: int = int(os.getenv("AGENT_MAX_RETRIES", "3"))
    
    # Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Security
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "dev_encryption_key_32_bytes_long!")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
