"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from shared.security import create_access_token, hash_password, verify_password, generate_api_key
from shared.database import DatabaseManager
from shared.config import settings

router = APIRouter(prefix="")

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str

class APIKeyResponse(BaseModel):
    api_key: str
    created_at: str

# In-memory user store for demo (replace with database in production)
users_db = {}

@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """Register a new user"""
    if request.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_id = f"user_{len(users_db) + 1}"
    hashed_password = hash_password(request.password)
    
    users_db[request.email] = {
        "user_id": user_id,
        "email": request.email,
        "name": request.name,
        "password": hashed_password
    }
    
    token = create_access_token({"sub": user_id, "email": request.email})
    
    return TokenResponse(
        access_token=token,
        user_id=user_id,
        email=request.email
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login and get access token"""
    user = users_db.get(request.email)
    
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token({"sub": user["user_id"], "email": user["email"]})
    
    return TokenResponse(
        access_token=token,
        user_id=user["user_id"],
        email=user["email"]
    )

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(current_user: dict = Depends(lambda: {"sub": "user_1"})):
    """Create a new API key"""
    from datetime import datetime
    
    api_key = generate_api_key(current_user["sub"])
    
    return APIKeyResponse(
        api_key=api_key,
        created_at=datetime.utcnow().isoformat()
    )

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(lambda: {"sub": "user_1", "email": "demo@apex.com"})):
    """Get current user information"""
    return {
        "user_id": current_user["sub"],
        "email": current_user.get("email", "demo@apex.com")
    }
