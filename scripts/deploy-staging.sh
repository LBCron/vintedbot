#!/bin/bash
set -e

echo "🚀 DEPLOYING VINTEDBOT TO FLY.IO STAGING"
echo "========================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo -e "${RED}❌ flyctl not installed!${NC}"
    echo "Install: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo -e "${RED}❌ Not logged in to Fly.io${NC}"
    echo "Run: flyctl auth login"
    exit 1
fi

echo -e "${BLUE}Step 1: Running pre-deployment checks...${NC}"

# Check required files
required_files=("Dockerfile" "fly.staging.toml" "backend/requirements.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Missing required file: $file${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ All required files present${NC}"

echo -e "${BLUE}Step 2: Building Chrome extension...${NC}"
cd chrome-extension
zip -r ../dist/vintedbot-extension.zip . -x "*.git*" "README.md" "*.DS_Store" "__MACOSX/*" > /dev/null 2>&1
cd ..
echo -e "${GREEN}✅ Chrome extension built${NC}"

echo -e "${BLUE}Step 3: Deploying to Fly.io...${NC}"

# Deploy using fly.staging.toml
flyctl deploy --config fly.staging.toml --yes

echo -e "${GREEN}✅ Deployment successful!${NC}"

echo -e "${BLUE}Step 4: Running database migrations...${NC}"

# Run migrations on deployed app
flyctl ssh console --config fly.staging.toml -C "python backend/run_migrations.py"

echo -e "${GREEN}✅ Migrations completed${NC}"

echo -e "${BLUE}Step 5: Checking application health...${NC}"

# Wait for health check
sleep 5

# Get app URL
app_url="https://vintedbot-staging.fly.dev"

# Check health endpoint
if curl -f -s "${app_url}/health" > /dev/null; then
    echo -e "${GREEN}✅ Application is healthy!${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "Check logs: flyctl logs --config fly.staging.toml"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo ""
echo "Application URL: ${app_url}"
echo "Logs: flyctl logs --config fly.staging.toml"
echo "SSH: flyctl ssh console --config fly.staging.toml"
echo ""
echo -e "${YELLOW}⚠️  Remember to set secrets:${NC}"
echo "flyctl secrets set STRIPE_SECRET_KEY=sk_xxx --config fly.staging.toml"
