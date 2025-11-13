#!/usr/bin/env python3
"""Create admin account on production"""
import sys
sys.path.insert(0, '/app/backend')
from backend.core.auth import hash_password, verify_password
from backend.core.storage import get_storage

email = 'ronanchenlopes@gmail.com'
password = '2007312Ron'

print(f'Creating admin account for: {email}')

# Hash password
hashed_password = hash_password(password)
print('[OK] Password hashed')

# Get storage
storage = get_storage()

# Check if user exists
existing_user = storage.get_user_by_email(email)
if existing_user:
    print(f'[WARNING] User exists with ID {existing_user["id"]}, updating password...')
    with storage.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET hashed_password = ?, is_admin = 1, status = 'active' WHERE email = ?",
            (hashed_password, email)
        )
        conn.commit()
    print('[OK] Password updated and admin privileges set')
else:
    print('[CREATING] Creating new user...')
    user = storage.create_user(
        email=email,
        hashed_password=hashed_password,
        name='Ronan Chen Lopes',
        plan='pro'
    )
    print(f'[OK] User created with ID: {user["id"]}')

# Verify
user = storage.get_user_by_email(email)
if user and verify_password(password, user['hashed_password']):
    print('[OK] Login verified!')
    print(f'Admin Status: {user.get("is_admin", False)}')
    print(f'Plan: {user.get("plan", "free")}')
else:
    print('[ERROR] Login verification failed!')
    sys.exit(1)
