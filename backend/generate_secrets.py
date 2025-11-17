#!/usr/bin/env python3
"""
Generate secure secrets for VintedBot

Run this script to generate strong encryption keys for production:
    python backend/generate_secrets.py

Copy the output to your .env file.
"""
import secrets


def generate_encryption_key():
    """Generate 32-byte encryption key (base64 URL-safe)"""
    return secrets.token_urlsafe(32)


def generate_secret_key():
    """Generate 64-byte secret key (base64 URL-safe)"""
    return secrets.token_urlsafe(64)


def generate_jwt_secret():
    """Generate 64-byte JWT secret key (base64 URL-safe)"""
    return secrets.token_urlsafe(64)


if __name__ == "__main__":
    print("=" * 70)
    print("🔐 VINTEDBOT SECURITY KEYS GENERATOR")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT:")
    print("   - Copy these keys to your .env file")
    print("   - NEVER commit these keys to Git")
    print("   - Store them securely (password manager, secrets vault)")
    print("   - Generate NEW keys for each environment (dev, staging, prod)")
    print()
    print("=" * 70)
    print()

    encryption_key = generate_encryption_key()
    secret_key = generate_secret_key()
    jwt_secret = generate_jwt_secret()

    print("# Add these to your .env file:")
    print()
    print(f"ENCRYPTION_KEY={encryption_key}")
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()
    print("=" * 70)
    print()
    print("✅ Keys generated successfully!")
    print()
    print("Next steps:")
    print("1. Copy the keys above to your .env file")
    print("2. Restart your application")
    print("3. Delete this output (don't save it anywhere unsecure)")
    print()
    print("=" * 70)
