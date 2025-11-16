#!/bin/bash
set -e

echo "🚀 DÉPLOIEMENT STAGING AUTOMATIQUE"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo -e "${RED}❌ flyctl not found. Install it first: https://fly.io/docs/hands-on/install-flyctl/${NC}"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo -e "${RED}❌ Not logged in to Fly.io. Run: flyctl auth login${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Creating Fly.io apps if not exist...${NC}"

# Create staging app if not exists
if ! flyctl apps list | grep -q "vintedbot-staging"; then
    echo -e "${GREEN}✅ Creating vintedbot-staging app${NC}"
    flyctl apps create vintedbot-staging --org personal
else
    echo -e "${GREEN}✅ vintedbot-staging app already exists${NC}"
fi

# Create PostgreSQL database if not exists
echo -e "${BLUE}📊 Setting up PostgreSQL...${NC}"
if ! flyctl postgres list | grep -q "vintedbot-staging-db"; then
    echo -e "${GREEN}✅ Creating PostgreSQL database${NC}"
    flyctl postgres create --name vintedbot-staging-db --region cdg --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1

    # Attach to app
    flyctl postgres attach vintedbot-staging-db --app vintedbot-staging
else
    echo -e "${GREEN}✅ PostgreSQL database already exists${NC}"
fi

# Create Redis if needed (optional - using Upstash)
echo -e "${BLUE}🔴 Redis setup (manual step)${NC}"
echo "For Redis, create an Upstash Redis database:"
echo "1. Go to https://upstash.com/"
echo "2. Create a database in EU-WEST-1 (Paris)"
echo "3. Copy the REDIS_URL"
echo "4. Set secret: flyctl secrets set REDIS_URL=<your-redis-url> --app vintedbot-staging"
echo ""

# Set required secrets
echo -e "${BLUE}🔑 Setting secrets...${NC}"
echo "Make sure to set these secrets manually if not already set:"
echo "  flyctl secrets set OPENAI_API_KEY=<key> --app vintedbot-staging"
echo "  flyctl secrets set JWT_SECRET_KEY=<key> --app vintedbot-staging"
echo "  flyctl secrets set REDIS_URL=<url> --app vintedbot-staging"
echo ""

# Deploy backend
echo -e "${BLUE}🚀 Deploying backend to staging...${NC}"
cd "$(dirname "$0")/.."

flyctl deploy \
    --config fly.staging.toml \
    --dockerfile backend/Dockerfile.production \
    --app vintedbot-staging \
    --strategy rolling

echo -e "${GREEN}✅ Backend deployed successfully!${NC}"

# Get app URL
APP_URL=$(flyctl info --app vintedbot-staging --json | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4)

echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo ""
echo -e "Staging URL: ${BLUE}https://${APP_URL}${NC}"
echo -e "Health check: ${BLUE}https://${APP_URL}/health${NC}"
echo ""
echo "Next steps:"
echo "1. Run staging validation: python test-environment/staging_validator.py"
echo "2. Check logs: flyctl logs --app vintedbot-staging"
echo "3. Monitor: flyctl status --app vintedbot-staging"
echo ""
