"""
Secure session vault for Vinted authentication.
Uses Fernet encryption to store cookies safely.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from pydantic import BaseModel


class VintedSession(BaseModel):
    """Vinted session data model"""
    cookie: str
    user_agent: str
    username: Optional[str] = None
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()


class SessionVault:
    """Encrypted session storage"""
    
    def __init__(self, key: str, storage_path: str = "backend/data/session.enc"):
        """
        Initialize vault with encryption key
        
        Args:
            key: Fernet key (32-byte base64-encoded)
            storage_path: Path to encrypted session file
        """
        # Ensure key is properly formatted for Fernet
        if len(key) < 32:
            key = key.ljust(32, '=')[:32]
        
        # Generate Fernet key from SECRET_KEY
        import base64
        import hashlib
        key_bytes = hashlib.sha256(key.encode()).digest()
        self.fernet_key = base64.urlsafe_b64encode(key_bytes)
        self.fernet = Fernet(self.fernet_key)
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session: VintedSession) -> bool:
        """
        Encrypt and save session
        
        Args:
            session: VintedSession object
            
        Returns:
            True if saved successfully
        """
        try:
            # Convert to dict and then to JSON
            session_dict = session.model_dump(mode='json')
            session_json = json.dumps(session_dict)
            
            # Encrypt
            encrypted = self.fernet.encrypt(session_json.encode())
            
            # Save to file
            self.storage_path.write_bytes(encrypted)
            return True
        except Exception as e:
            print(f"[ERROR] Error saving session: {e}")
            return False
    
    def load_session(self) -> Optional[VintedSession]:
        """
        Load and decrypt session
        
        Returns:
            VintedSession if found and va   lid, None otherwise
        """
        try:
            if not self.storage_path.exists():
                return None
            
            # Read encrypted data
            encrypted = self.storage_path.read_bytes()
            
            # Decrypt
            decrypted = self.fernet.decrypt(encrypted)
            session_dict = json.loads(decrypted.decode())
            
            # Parse datetime strings
            if session_dict.get('expires_at'):
                session_dict['expires_at'] = datetime.fromisoformat(session_dict['expires_at'])
            if session_dict.get('created_at'):
                session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
            
            session = VintedSession(**session_dict)
            
            # Check expiration
            if session.expires_at and session.expires_at < datetime.utcnow():
                print("[WARN] Session expired")
                return None
            
            return session
        except Exception as e:
            print(f"[ERROR] Error loading session: {e}")
            return None
    
    def clear_session(self) -> bool:
        """Delete stored session"""
        try:
            if self.storage_path.exists():
                self.storage_path.unlink()
            return True
        except Exception as e:
            print(f"[ERROR] Error clearing session: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if valid session exists"""
        session = self.load_session()
        return session is not None


def get_vinted_session(user_id: int) -> Optional[VintedSession]:
    """
    Get Vinted session for a specific user from the database.
    
    This function loads sessions from the database (multi-user system),
    as opposed to SessionVault.load_session() which loads from an encrypted file
    (single-user system).
    
    Args:
        user_id: User ID to get session for
        
    Returns:
        VintedSession if found, None otherwise
    """
    from backend.core.storage import get_store
    
    store = get_store()
    session_data = store.get_vinted_session_for_user(str(user_id))
    
    if not session_data:
        return None
    
    # Convert dict to VintedSession object
    return VintedSession(
        cookie=session_data.get("cookie", ""),
        user_agent=session_data.get("user_agent", ""),
        username=None,  # Can be extracted from cookie if needed
        user_id=str(user_id),
        expires_at=None,  # Can be set if stored in database
        created_at=datetime.utcnow()
    )