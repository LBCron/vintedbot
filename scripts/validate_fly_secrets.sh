#!/bin/bash
# SECURITY FIX Bug #55: Validate Fly.io secrets before deployment
#
# Usage:
#   ./scripts/validate_fly_secrets.sh [app-name]
#
# If app-name is not provided, uses APP_NAME environment variable
# or prompts for selection

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Required secrets for VintedBot
REQUIRED_SECRETS=(
  "DATABASE_URL"
  "REDIS_URL"
  "JWT_SECRET"
  "ENCRYPTION_KEY"
  "SECRET_KEY"
  "STRIPE_SECRET_KEY"
  "STRIPE_WEBHOOK_SECRET"
  "STRIPE_PRICE_STARTER"
  "STRIPE_PRICE_PRO"
  "STRIPE_PRICE_ENTERPRISE"
  "OPENAI_API_KEY"
)

OPTIONAL_SECRETS=(
  "S3_ACCESS_KEY"
  "S3_SECRET_KEY"
  "GOOGLE_CLIENT_ID"
  "GOOGLE_CLIENT_SECRET"
  "SENTRY_DSN"
)

# Get app name
APP_NAME="${1:-${APP_NAME}}"

if [ -z "$APP_NAME" ]; then
  echo -e "${YELLOW}ℹ️  No app name provided. Available Fly apps:${NC}"
  flyctl apps list
  echo ""
  read -p "Enter app name: " APP_NAME
fi

if [ -z "$APP_NAME" ]; then
  echo -e "${RED}❌ App name is required${NC}"
  exit 1
fi

echo "======================================================================"
echo "🔍 VALIDATING FLY.IO SECRETS FOR: $APP_NAME"
echo "======================================================================"
echo ""

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
  echo -e "${RED}❌ flyctl is not installed${NC}"
  echo "Install it from: https://fly.io/docs/hands-on/install-flyctl/"
  exit 1
fi

# Get secrets list
SECRETS_OUTPUT=$(flyctl secrets list --app "$APP_NAME" 2>&1)

if echo "$SECRETS_OUTPUT" | grep -q "Could not find App"; then
  echo -e "${RED}❌ App '$APP_NAME' not found${NC}"
  exit 1
fi

# Validate required secrets
MISSING_REQUIRED=()
for secret in "${REQUIRED_SECRETS[@]}"; do
  if ! echo "$SECRETS_OUTPUT" | grep -q "^$secret"; then
    MISSING_REQUIRED+=("$secret")
  fi
done

# Check optional secrets
MISSING_OPTIONAL=()
for secret in "${OPTIONAL_SECRETS[@]}"; do
  if ! echo "$SECRETS_OUTPUT" | grep -q "^$secret"; then
    MISSING_OPTIONAL+=("$secret")
  fi
done

# Print results
if [ ${#MISSING_REQUIRED[@]} -gt 0 ]; then
  echo -e "${RED}❌ MISSING REQUIRED SECRETS:${NC}"
  echo ""
  for secret in "${MISSING_REQUIRED[@]}"; do
    echo "  • $secret"
  done
  echo ""
  echo "To set secrets:"
  echo "  flyctl secrets set SECRET_NAME=value --app $APP_NAME"
  echo ""
  echo "To generate secure keys:"
  echo "  python backend/generate_secrets.py"
  echo ""
  exit 1
fi

if [ ${#MISSING_OPTIONAL[@]} -gt 0 ]; then
  echo -e "${YELLOW}ℹ️  MISSING OPTIONAL SECRETS:${NC}"
  echo ""
  for secret in "${MISSING_OPTIONAL[@]}"; do
    echo "  • $secret"
  done
  echo ""
  echo "These are optional - features may be disabled"
  echo ""
fi

echo -e "${GREEN}✅ ALL REQUIRED SECRETS ARE SET FOR: $APP_NAME${NC}"
echo ""
echo "Secret summary:"
echo "  Required: ${#REQUIRED_SECRETS[@]} / ${#REQUIRED_SECRETS[@]} set"
if [ ${#MISSING_OPTIONAL[@]} -gt 0 ]; then
  echo "  Optional: $((${#OPTIONAL_SECRETS[@]} - ${#MISSING_OPTIONAL[@]})) / ${#OPTIONAL_SECRETS[@]} set"
else
  echo "  Optional: ${#OPTIONAL_SECRETS[@]} / ${#OPTIONAL_SECRETS[@]} set"
fi
echo ""

exit 0
