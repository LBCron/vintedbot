"""
Authentication utilities for VintedBot SaaS
Handles JWT tokens, password hashing, and user verification
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import os

# Load environment variables FIRST
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "CHANGEME_IN_PRODUCTION_USE_SECURE_RANDOM_KEY":
    import sys
    print("❌ FATAL: JWT_SECRET_KEY not set!")
    print("⚠️  Generate a secure key:")
    print("    python3 -c \"import secrets; print(f'JWT_SECRET_KEY={secrets.token_urlsafe(64)}')\"")
    print("    Then add it to your .env file")
    sys.exit(1)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing (Argon2 - modern, secure, fast)
pwd_hasher = PasswordHasher()


# ========== Pydantic Models ==========

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None

class UserProfile(BaseModel):
    id: int
    email: str
    name: Optional[str]
    plan: str
    status: str
    created_at: str
    quotas_used: dict = {}
    quotas_limit: dict = {}


# ========== Password Hashing ==========

def hash_password(password: str) -> str:
    """Hash a password using Argon2"""
    return pwd_hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its Argon2 hash"""
    try:
        return pwd_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


# ========== JWT Token Management ==========

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Payload to encode (should include user_id, email)
        expires_delta: Custom expiration time (default: 7 days)
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and verify a JWT token
    
    Args:
        token: JWT token to decode
    
    Returns:
        TokenData if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        email = payload.get("email")
        
        if user_id is None:
            return None
            
        return TokenData(user_id=int(user_id), email=str(email) if email else None)
    
    except JWTError:
        return None
