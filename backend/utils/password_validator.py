"""
Password Validation Utility

Implements strong password requirements to prevent weak passwords.

Requirements:
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character
- Not in common passwords list
"""
import re
from typing import Tuple


# Common passwords to reject (from OWASP and other sources)
COMMON_PASSWORDS = {
    "password", "password123", "123456", "12345678", "qwerty", "abc123",
    "monkey", "1234567", "letmein", "trustno1", "dragon", "baseball",
    "iloveyou", "master", "sunshine", "ashley", "bailey", "shadow",
    "123123", "654321", "superman", "qazwsx", "michael", "football",
    "password1", "welcome", "jesus", "ninja", "mustang", "password2",
    "admin", "root", "toor", "pass", "test", "guest", "changeme",
    "qwerty123", "qwertyuiop", "123456789", "1234567890", "azerty",
    "!@#$%^&*", "00000000", "11111111", "PassWord", "Password1!",
    # VintedBot specific
    "vintedbot", "vintedbot123", "vinted123",
}


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "Password is strong") if valid
        - (False, "Error message") if invalid
    """
    # Check minimum length
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"

    # Check maximum length (prevent DoS via bcrypt)
    if len(password) > 128:
        return False, "Password must be at most 128 characters long"

    # Check for uppercase letter
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)"

    # Check for lowercase letter
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)"

    # Check for number
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number (0-9)"

    # Check for special character
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]", password):
        return False, "Password must contain at least one special character (!@#$%^&* etc.)"

    # Check against common passwords (case-insensitive)
    password_lower = password.lower()
    if password_lower in COMMON_PASSWORDS:
        return False, "This password is too common. Please choose a stronger password"

    # Check for simple patterns
    if re.match(r"^(.)\1+$", password):  # All same character
        return False, "Password cannot be all the same character"

    if re.match(r"^(12345|54321|qwerty|asdfg|zxcv)", password_lower):
        return False, "Password contains a common keyboard pattern"

    # Check for sequential numbers
    if re.search(r"(0123|1234|2345|3456|4567|5678|6789|7890)", password):
        return False, "Password contains sequential numbers"

    # All checks passed
    return True, "Password is strong"


def get_password_strength(password: str) -> str:
    """
    Get password strength level

    Returns: "weak", "medium", "strong", or "very_strong"
    """
    score = 0

    # Length
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    if len(password) >= 20:
        score += 1

    # Character variety
    if re.search(r"[a-z]", password):
        score += 1
    if re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"\d", password):
        score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]", password):
        score += 1

    # Complexity
    if len(set(password)) >= len(password) * 0.7:  # High character diversity
        score += 1

    if score <= 3:
        return "weak"
    elif score <= 5:
        return "medium"
    elif score <= 7:
        return "strong"
    else:
        return "very_strong"


# For backward compatibility and convenience
def is_password_strong(password: str) -> bool:
    """Quick check if password is strong enough"""
    is_valid, _ = validate_password(password)
    return is_valid
