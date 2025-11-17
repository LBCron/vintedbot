import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import httpx

from backend.models import Session, User
from backend.utils.crypto import encrypt_blob, decrypt_blob
from backend.db import get_db_session
from backend.utils.logger import logger

router = APIRouter(prefix="/vinted/auth", tags=["authentication"])

# SECURITY FIX: Default to "false" to prevent accidental validation bypass in production
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"


class SessionCreate(BaseModel):
    cookie_value: str
    note: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: int
    valid: bool
    note: Optional[str] = None
    created_at: datetime


@router.post("/session")
async def create_session(data: SessionCreate):
    """Create and validate a Vinted session"""
    
    # Validate cookie
    valid = False
    if MOCK_MODE:
        logger.info("MOCK MODE: Simulating session validation")
        valid = True
    else:
        # Try to validate by making a request to Vinted
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.vinted.com/api/v2/users/current",
                    headers={"Cookie": data.cookie_value},
                    timeout=10.0
                )
                valid = response.status_code == 200
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            valid = False
    
    if not valid:
        return {"session_id": None, "valid": False}
    
    # Encrypt and store session
    encrypted_cookie = encrypt_blob(data.cookie_value)
    
    with get_db_session() as db:
        # Get or create user
        user = User(email=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        session = Session(
            user_id=user.id,
            encrypted_cookie=encrypted_cookie,
            note=data.note,
            last_validated_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"✅ Session {session.id} created and validated")
        
        return SessionResponse(
            session_id=session.id,
            valid=True,
            note=session.note,
            created_at=session.created_at
        )


@router.post("/logout")
async def logout_session(session_id: int):
    """Delete a session"""
    with get_db_session() as db:
        session = db.get(Session, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        db.delete(session)
        db.commit()
        
        logger.info(f"🔒 Session {session_id} logged out")
        return {"success": True, "message": "Session deleted"}


@router.get("/sessions")
async def list_sessions():
    """List all sessions (without exposing cookies)"""
    with get_db_session() as db:
        from sqlmodel import select
        sessions = db.exec(select(Session)).all()
        
        return {
            "sessions": [
                {
                    "id": s.id,
                    "user_id": s.user_id,
                    "note": s.note,
                    "last_validated_at": s.last_validated_at,
                    "created_at": s.created_at
                }
                for s in sessions
            ]
        }
