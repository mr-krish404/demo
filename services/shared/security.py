"""
Security utilities for encryption, JWT, and authentication
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from passlib.context import CryptContext
import base64
import hashlib

from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

# JWT tokens
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT access token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Encryption for credentials
def get_encryption_key() -> bytes:
    """Get or generate encryption key"""
    # Ensure key is 32 bytes for Fernet
    key = settings.encryption_key.encode()
    if len(key) < 32:
        key = key + b'0' * (32 - len(key))
    elif len(key) > 32:
        key = key[:32]
    return base64.urlsafe_b64encode(key)

cipher_suite = Fernet(get_encryption_key())

def encrypt_credential(data: str) -> str:
    """Encrypt credential data"""
    encrypted = cipher_suite.encrypt(data.encode())
    return encrypted.decode()

def decrypt_credential(encrypted_data: str) -> str:
    """Decrypt credential data"""
    decrypted = cipher_suite.decrypt(encrypted_data.encode())
    return decrypted.decode()

# API Key generation
def generate_api_key(user_id: str) -> str:
    """Generate a unique API key for a user"""
    timestamp = datetime.utcnow().isoformat()
    data = f"{user_id}:{timestamp}:{settings.jwt_secret}"
    hash_obj = hashlib.sha256(data.encode())
    return f"apex_{hash_obj.hexdigest()}"
