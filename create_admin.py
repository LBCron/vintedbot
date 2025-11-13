#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to create admin account
Email: ronanchenlopes@gmail.com
Password: 2007312Ron
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.core.auth import hash_password
from backend.core.storage import get_storage

def create_admin_account():
    """Create admin account with specified credentials"""
    email = "ronanchenlopes@gmail.com"
    password = "2007312Ron"
    name = "Ronan Chen Lopes"

    print(f"Creating admin account for: {email}")

    # Hash password using Argon2
    hashed_password = hash_password(password)
    print(f"[OK] Password hashed successfully")

    # Get storage instance
    storage = get_storage()

    # Check if user already exists
    existing_user = storage.get_user_by_email(email)
    if existing_user:
        print(f"[WARNING] User already exists with ID: {existing_user['id']}")
        print(f"   Email: {existing_user['email']}")
        print(f"   Admin: {existing_user.get('is_admin', False)}")
        print(f"   Status: {existing_user.get('status', 'unknown')}")
        print(f"   Plan: {existing_user.get('plan', 'unknown')}")

        # Update password if user exists
        print(f"\n[UPDATING] Updating password for existing user...")
        try:
            with storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET hashed_password = ?,
                        is_admin = 1,
                        status = 'active'
                    WHERE email = ?
                """, (hashed_password, email))
                conn.commit()
            print(f"[OK] Password updated successfully!")
            print(f"[OK] Admin privileges confirmed!")
        except Exception as e:
            print(f"[ERROR] Failed to update password: {e}")
            return False
    else:
        # Create new user
        print(f"Creating new admin user...")
        try:
            user = storage.create_user(
                email=email,
                hashed_password=hashed_password,
                name=name,
                plan="pro"  # Give admin pro plan
            )
            print(f"[OK] Admin account created successfully!")
            print(f"   User ID: {user['id']}")
            print(f"   Email: {user['email']}")
            print(f"   Admin: {user.get('is_admin', False)}")
            print(f"   Plan: {user.get('plan', 'free')}")
        except Exception as e:
            print(f"[ERROR] Failed to create user: {e}")
            return False

    # Verify login works
    print(f"\n[VERIFYING] Verifying credentials...")
    from backend.core.auth import verify_password

    user = storage.get_user_by_email(email)
    if user and verify_password(password, user['hashed_password']):
        print(f"[OK] Login credentials verified successfully!")
        print(f"\n" + "="*60)
        print(f"ADMIN ACCOUNT READY:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  Admin Status: {user.get('is_admin', False)}")
        print(f"  Plan: {user.get('plan', 'free')}")
        print(f"="*60)
        return True
    else:
        print(f"[ERROR] Login verification failed!")
        return False

if __name__ == "__main__":
    success = create_admin_account()
    sys.exit(0 if success else 1)
