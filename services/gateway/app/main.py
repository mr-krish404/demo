"""
Gateway Service - Main API Gateway for Apex Pentest X
Handles authentication, routing, and rate limiting
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared.config import settings
from shared.security import decode_access_token
from shared.database import DatabaseManager

# Initialize FastAPI app
app = FastAPI(
    title="Apex Pentest X Gateway",
    description="API Gateway for Apex Pentest X Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
security = HTTPBearer()

# Database
db_manager = DatabaseManager(settings.database_url)

# Dependency for authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return user info"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gateway"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Apex Pentest X Gateway",
        "version": "1.0.0",
        "status": "operational"
    }

# Import routers
from app.routers import auth, projects, targets, scans, findings, evidence, agents, websocket

# Register routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(targets.router, prefix="/api/targets", tags=["Targets"])
app.include_router(scans.router, prefix="/api/scans", tags=["Scans"])
app.include_router(findings.router, prefix="/api/findings", tags=["Findings"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["Evidence"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(websocket.router, tags=["WebSocket"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    db_manager.create_tables()
    print("Gateway service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Gateway service shutting down")
