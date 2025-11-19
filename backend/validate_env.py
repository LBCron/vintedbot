#!/usr/bin/env python3
"""
Environment Variables Validation Script
Ensures all required environment variables are set before deployment

Usage:
    python backend/validate_env.py

Exit codes:
    0: All required variables are set
    1: One or more required variables are missing
"""
import os
import sys
from typing import List, Tuple

# SECURITY FIX Bug #54: Environment validation before deployment
REQUIRED_PRODUCTION_VARS = [
    # Database
    ("DATABASE_URL", "PostgreSQL connection string"),
    ("REDIS_URL", "Redis connection string"),

    # Security & Auth
    ("JWT_SECRET", "JWT token signing key (min 64 chars)"),
    ("ENCRYPTION_KEY", "AES-256 encryption key (min 32 chars)"),
    ("SECRET_KEY", "Application secret key (min 32 chars)"),

    # Payment
    ("STRIPE_SECRET_KEY", "Stripe secret key (sk_live_...)"),
    ("STRIPE_WEBHOOK_SECRET", "Stripe webhook signing secret"),
    ("STRIPE_PRICE_STARTER", "Stripe price ID for Starter plan"),
    ("STRIPE_PRICE_PRO", "Stripe price ID for Pro plan"),
    ("STRIPE_PRICE_ENTERPRISE", "Stripe price ID for Enterprise plan"),

    # AI
    ("OPENAI_API_KEY", "OpenAI API key for GPT features"),
]

OPTIONAL_VARS = [
    ("S3_ACCESS_KEY", "AWS S3 access key (optional: local storage fallback)"),
    ("S3_SECRET_KEY", "AWS S3 secret key (optional: local storage fallback)"),
    ("GOOGLE_CLIENT_ID", "Google OAuth client ID (optional: disable Google login)"),
    ("GOOGLE_CLIENT_SECRET", "Google OAuth secret (optional: disable Google login)"),
    ("SENTRY_DSN", "Sentry error tracking DSN (optional: no error tracking)"),
]


def validate_environment(env: str = "production") -> Tuple[bool, List[str], List[str]]:
    """
    Validate required environment variables

    Args:
        env: Environment name ("production", "staging", or "development")

    Returns:
        Tuple of (success, missing_required, missing_optional)
    """
    missing_required = []
    missing_optional = []

    # Skip validation in development
    if env == "development":
        print("ℹ️  Development environment - skipping strict validation")
        return True, [], []

    # Check required variables
    for var_name, description in REQUIRED_PRODUCTION_VARS:
        value = os.getenv(var_name)
        if not value:
            missing_required.append(f"{var_name} - {description}")
        else:
            # Additional validation for specific variables
            if var_name == "JWT_SECRET" and len(value) < 64:
                print(f"⚠️  WARNING: {var_name} should be at least 64 characters (currently {len(value)})")
            elif var_name == "ENCRYPTION_KEY" and len(value) < 32:
                print(f"⚠️  WARNING: {var_name} should be at least 32 characters (currently {len(value)})")
            elif var_name == "SECRET_KEY" and len(value) < 32:
                print(f"⚠️  WARNING: {var_name} should be at least 32 characters (currently {len(value)})")
            elif var_name.startswith("STRIPE_") and value.startswith(("sk_test_", "whsec_test_")):
                print(f"⚠️  WARNING: {var_name} appears to be a test key (production should use live keys)")

    # Check optional variables
    for var_name, description in OPTIONAL_VARS:
        value = os.getenv(var_name)
        if not value:
            missing_optional.append(f"{var_name} - {description}")

    success = len(missing_required) == 0
    return success, missing_required, missing_optional


def main():
    """Main validation function"""
    env = os.getenv("ENV", "development")

    print("=" * 70)
    print(f"🔍 ENVIRONMENT VALIDATION - {env.upper()}")
    print("=" * 70)
    print()

    success, missing_required, missing_optional = validate_environment(env)

    # Print results
    if missing_required:
        print("❌ MISSING REQUIRED ENVIRONMENT VARIABLES:")
        print()
        for var in missing_required:
            print(f"  • {var}")
        print()

    if missing_optional:
        print("ℹ️  MISSING OPTIONAL ENVIRONMENT VARIABLES:")
        print()
        for var in missing_optional:
            print(f"  • {var}")
        print()

    if success and not missing_optional:
        print("✅ ALL ENVIRONMENT VARIABLES ARE SET")
        print()
        sys.exit(0)
    elif success:
        print("✅ ALL REQUIRED ENVIRONMENT VARIABLES ARE SET")
        print(f"ℹ️  {len(missing_optional)} optional variables are missing (features may be disabled)")
        print()
        sys.exit(0)
    else:
        print(f"❌ VALIDATION FAILED: {len(missing_required)} required variables missing")
        print()
        print("To generate secure keys, run:")
        print("  python backend/generate_secrets.py")
        print()
        print("Then set the variables in your deployment environment")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
