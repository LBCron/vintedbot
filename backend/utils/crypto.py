import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# SECURITY FIX: No default key, require explicit configuration
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Validate encryption key
ENV = os.getenv("ENV", "development")
if not ENCRYPTION_KEY:
    if ENV == "production":
        raise ValueError(
            "ENCRYPTION_KEY environment variable must be set in production. "
            "Run: python backend/generate_secrets.py"
        )
    else:
        # Allow default only in development with warning
        import warnings
        warnings.warn(
            "⚠️ Using default ENCRYPTION_KEY in development. "
            "DO NOT use this in production!",
            UserWarning
        )
        ENCRYPTION_KEY = "default-32-byte-key-change-this!"

# Additional validation: reject known weak keys in production
if ENV == "production" and ENCRYPTION_KEY in [
    "default-32-byte-key-change-this!",
    "dev-secret",
    "changeme",
    "test",
]:
    raise ValueError(
        f"Weak ENCRYPTION_KEY detected in production. "
        "Generate a strong key with: python backend/generate_secrets.py"
    )


def get_key() -> bytes:
    """Get or derive encryption key"""
    key_str = ENCRYPTION_KEY
    
    # If key is base64/hex encoded
    if len(key_str) == 44 and key_str.endswith('='):
        try:
            return base64.b64decode(key_str)
        except:
            pass
    
    if len(key_str) == 64:
        try:
            return bytes.fromhex(key_str)
        except:
            pass
    
    # Derive key from string using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'vintedbot-salt',
        iterations=100000,
    )
    return kdf.derive(key_str.encode())


def encrypt_blob(plaintext: str) -> str:
    """Encrypt plaintext using AES-GCM and return base64 encoded ciphertext"""
    key = get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    
    # Combine nonce + ciphertext and base64 encode
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode()


def decrypt_blob(ciphertext_b64: str) -> str:
    """Decrypt base64 encoded ciphertext and return plaintext"""
    key = get_key()
    aesgcm = AESGCM(key)
    
    # Decode and split nonce + ciphertext
    combined = base64.b64decode(ciphertext_b64)
    nonce = combined[:12]
    ciphertext = combined[12:]
    
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()
