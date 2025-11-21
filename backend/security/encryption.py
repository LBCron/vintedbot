"""
Mobile App Security: AES-256 Encryption for Sensitive Data
Encrypts/decrypts credentials, tokens, and sensitive user data
"""
import os
import base64
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger


class EncryptionService:
    """
    AES-256-GCM encryption service for sensitive data

    Features:
    - AES-256-GCM authenticated encryption
    - PBKDF2 key derivation
    - Random IV generation per encryption
    - Authentication tags for integrity
    """

    # AES-256 requires 32-byte key
    KEY_SIZE = 32

    # GCM nonce size (12 bytes recommended)
    NONCE_SIZE = 12

    # PBKDF2 iterations (100k for good security)
    PBKDF2_ITERATIONS = 100_000

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption service

        Args:
            master_key: Master encryption key (base64). If None, reads from env ENCRYPTION_KEY
        """
        if master_key:
            self.master_key = base64.b64decode(master_key)
        else:
            # Try to get from environment
            env_key = os.getenv('ENCRYPTION_KEY')
            if env_key:
                self.master_key = base64.b64decode(env_key)
            else:
                # Generate new key (WARN: will lose ability to decrypt existing data!)
                logger.warning("No ENCRYPTION_KEY found, generating new key (existing encrypted data will be unrecoverable)")
                self.master_key = os.urandom(self.KEY_SIZE)

                # Print for saving to env (only in dev)
                if os.getenv('ENV') != 'production':
                    key_b64 = base64.b64encode(self.master_key).decode('utf-8')
                    logger.info(f"Generated ENCRYPTION_KEY (save this to .env):\n{key_b64}")

        if len(self.master_key) != self.KEY_SIZE:
            raise ValueError(f"Master key must be {self.KEY_SIZE} bytes")

    def derive_key(self, salt: bytes) -> bytes:
        """
        Derive encryption key from master key using PBKDF2

        Args:
            salt: Random salt (should be unique per encryption)

        Returns:
            Derived key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
            backend=default_backend()
        )

        return kdf.derive(self.master_key)

    def encrypt(self, plaintext: str, context: str = "") -> str:
        """
        Encrypt plaintext using AES-256-GCM

        Args:
            plaintext: Text to encrypt
            context: Optional context string (e.g., user_id) for additional security

        Returns:
            Base64-encoded encrypted data: salt:nonce:ciphertext:tag
        """
        try:
            # Generate random salt and nonce
            salt = os.urandom(16)
            nonce = os.urandom(self.NONCE_SIZE)

            # Derive encryption key
            key = self.derive_key(salt)

            # Prepare AAD (authenticated additional data) - adds context without encrypting it
            aad = context.encode('utf-8') if context else b''

            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce),
                backend=default_backend()
            )

            encryptor = cipher.encryptor()

            # Add AAD if provided
            if aad:
                encryptor.authenticate_additional_data(aad)

            # Encrypt
            ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()

            # Get authentication tag
            tag = encryptor.tag

            # Combine: salt:nonce:ciphertext:tag
            encrypted_data = salt + nonce + ciphertext + tag

            # Return as base64
            return base64.b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str, context: str = "") -> str:
        """
        Decrypt AES-256-GCM encrypted data

        Args:
            encrypted_data: Base64-encoded encrypted data
            context: Same context used during encryption

        Returns:
            Decrypted plaintext

        Raises:
            ValueError: If decryption fails (wrong key, corrupted data, etc.)
        """
        try:
            # Decode base64
            data = base64.b64decode(encrypted_data)

            # Extract components
            salt = data[:16]
            nonce = data[16:16 + self.NONCE_SIZE]
            tag = data[-16:]  # GCM tag is 16 bytes
            ciphertext = data[16 + self.NONCE_SIZE:-16]

            # Derive key
            key = self.derive_key(salt)

            # Prepare AAD
            aad = context.encode('utf-8') if context else b''

            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )

            decryptor = cipher.decryptor()

            # Add AAD if provided
            if aad:
                decryptor.authenticate_additional_data(aad)

            # Decrypt
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext.decode('utf-8')

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - invalid key or corrupted data")


def encrypt_credentials(email: str, password: str, user_id: str) -> str:
    """
    Encrypt Vinted credentials for storage

    Args:
        email: Vinted email
        password: Vinted password
        user_id: User ID (used as context for additional security)

    Returns:
        Encrypted credentials string
    """
    service = EncryptionService()

    # Combine email:password
    credentials = f"{email}:{password}"

    # Encrypt with user_id as context
    encrypted = service.encrypt(credentials, context=user_id)

    logger.info(f"Encrypted credentials for user {user_id}")

    return encrypted


def decrypt_credentials(encrypted_credentials: str, user_id: str) -> Tuple[str, str]:
    """
    Decrypt Vinted credentials

    Args:
        encrypted_credentials: Encrypted credentials string
        user_id: User ID (used as context)

    Returns:
        (email, password) tuple

    Raises:
        ValueError: If decryption fails
    """
    service = EncryptionService()

    # Decrypt
    credentials = service.decrypt(encrypted_credentials, context=user_id)

    # Split email:password
    parts = credentials.split(':', 1)
    if len(parts) != 2:
        raise ValueError("Invalid credentials format")

    email, password = parts

    logger.info(f"Decrypted credentials for user {user_id}")

    return (email, password)


def encrypt_token(token: str, user_id: str) -> str:
    """Encrypt authentication token"""
    service = EncryptionService()
    return service.encrypt(token, context=user_id)


def decrypt_token(encrypted_token: str, user_id: str) -> str:
    """Decrypt authentication token"""
    service = EncryptionService()
    return service.decrypt(encrypted_token, context=user_id)


# Generate new master key (run once, save to .env)
def generate_master_key() -> str:
    """
    Generate a new master encryption key

    Returns:
        Base64-encoded key (save this as ENCRYPTION_KEY in .env)
    """
    key = os.urandom(EncryptionService.KEY_SIZE)
    key_b64 = base64.b64encode(key).decode('utf-8')

    print("=" * 80)
    print("NEW ENCRYPTION KEY (SAVE THIS TO .env AS ENCRYPTION_KEY)")
    print("=" * 80)
    print(key_b64)
    print("=" * 80)
    print("[WARN] WARNING: If you lose this key, all encrypted data will be unrecoverable!")
    print("=" * 80)

    return key_b64


if __name__ == "__main__":
    # Test encryption
    print("Testing encryption...")

    # Generate key
    key = generate_master_key()

    # Test encrypt/decrypt
    service = EncryptionService(key)

    test_data = "sensitive_password_123"
    encrypted = service.encrypt(test_data, context="user_42")
    print(f"\nEncrypted: {encrypted}")

    decrypted = service.decrypt(encrypted, context="user_42")
    print(f"Decrypted: {decrypted}")

    assert test_data == decrypted, "Encryption/decryption failed"
    print("\n[OK] Encryption test passed!")
