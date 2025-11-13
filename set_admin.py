#!/usr/bin/env python3
"""Set admin status for user"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.core.storage import get_storage

email = 'ronanchenlopes@gmail.com'

print(f'Setting admin status for: {email}')

storage = get_storage()

# Update user to be admin
with storage.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET is_admin = 1 WHERE email = ?",
        (email,)
    )
    affected = cursor.rowcount
    conn.commit()

print(f'[OK] Updated {affected} rows')

# Verify
user = storage.get_user_by_email(email)
if user:
    print(f'Admin Status: {user.get("is_admin", False)}')
    print(f'Plan: {user.get("plan", "free")}')
else:
    print('[ERROR] User not found!')
