#!/bin/bash

echo "🐳 VINTEDBOT - ENVIRONNEMENT DE TEST VIRTUEL"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "\n${YELLOW}1. Vérification prérequis...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé${NC}"
    echo "   Install: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null &&  ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose n'est pas installé${NC}"
    echo "   Install: https://docs.docker.com/compose/install/"
    exit 1
fi

# Use 'docker compose' or 'docker-compose' based on availability
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo -e "${GREEN}✅ Docker et Docker Compose OK${NC}"

# Step 2: Clean previous test environment
echo -e "\n${YELLOW}2. Nettoyage environnement précédent...${NC}"
$DOCKER_COMPOSE -f docker-compose.test.yml down -v 2>/dev/null || true
rm -rf test-results/screenshots/* test-results/*.html test-results/*.json 2>/dev/null || true
echo -e "${GREEN}✅ Nettoyé${NC}"

# Step 3: Check .env file
echo -e "\n${YELLOW}3. Vérification configuration...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set in environment${NC}"
    echo "   AI features will be mocked during tests"
fi

# Create test results directory
mkdir -p test-results/screenshots
echo -e "${GREEN}✅ Configuration OK${NC}"

# Step 4: Build images
echo -e "\n${YELLOW}4. Build des images Docker (peut prendre 2-5 min)...${NC}"
$DOCKER_COMPOSE -f docker-compose.test.yml build --no-cache
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Images buildées${NC}"

# Step 5: Start services
echo -e "\n${YELLOW}5. Démarrage des services...${NC}"
$DOCKER_COMPOSE -f docker-compose.test.yml up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}6. Attente santé des services...${NC}"
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    # Check if containers are running
    backend_running=$($DOCKER_COMPOSE -f docker-compose.test.yml ps -q backend 2>/dev/null)
    frontend_running=$($DOCKER_COMPOSE -f docker-compose.test.yml ps -q frontend 2>/dev/null)

    if [ -z "$backend_running" ] || [ -z "$frontend_running" ]; then
        echo -e "${RED}❌ Containers not running${NC}"
        $DOCKER_COMPOSE -f docker-compose.test.yml logs --tail=50
        exit 1
    fi

    # Check health status
    backend_health=$(docker inspect --format='{{.State.Health.Status}}' vintedbot_test_backend 2>/dev/null || echo "starting")
    frontend_health=$(docker inspect --format='{{.State.Health.Status}}' vintedbot_test_frontend 2>/dev/null || echo "starting")
    postgres_health=$(docker inspect --format='{{.State.Health.Status}}' vintedbot_test_postgres 2>/dev/null || echo "starting")
    redis_health=$(docker inspect --format='{{.State.Health.Status}}' vintedbot_test_redis 2>/dev/null || echo "starting")

    echo "   ⏳ Attempt $((attempt+1))/$max_attempts - Backend: $backend_health | Frontend: $frontend_health | DB: $postgres_health | Redis: $redis_health"

    if [ "$backend_health" = "healthy" ] && [ "$frontend_health" = "healthy" ] && [ "$postgres_health" = "healthy" ] && [ "$redis_health" = "healthy" ]; then
        echo -e "${GREEN}✅ Tous les services sont opérationnels${NC}"
        break
    fi

    sleep 5
    attempt=$((attempt+1))
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Timeout: Services ne sont pas devenus healthy${NC}"
    echo -e "${YELLOW}Logs backend:${NC}"
    $DOCKER_COMPOSE -f docker-compose.test.yml logs backend --tail=100
    echo -e "${YELLOW}Logs frontend:${NC}"
    $DOCKER_COMPOSE -f docker-compose.test.yml logs frontend --tail=100
    exit 1
fi

# Step 7: Test connectivity
echo -e "\n${YELLOW}7. Test de connectivité...${NC}"

# Test backend
backend_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health)
if [ "$backend_response" = "200" ]; then
    echo -e "${GREEN}✅ Backend API: http://localhost:8001 (HTTP $backend_response)${NC}"
else
    echo -e "${RED}❌ Backend API not responding (HTTP $backend_response)${NC}"
    exit 1
fi

# Test frontend
frontend_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5174/)
if [ "$frontend_response" = "200" ]; then
    echo -e "${GREEN}✅ Frontend: http://localhost:5174 (HTTP $frontend_response)${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend not responding yet (HTTP $frontend_response)${NC}"
fi

# Step 8: Create test user
echo -e "\n${YELLOW}8. Création utilisateur de test...${NC}"
$DOCKER_COMPOSE -f docker-compose.test.yml exec -T backend python -c "
import asyncio
from backend.database import get_db_pool
from backend.core.auth import get_password_hash

async def create_test_user():
    pool = await get_db_pool()
    try:
        async with pool.acquire() as conn:
            # Check if user exists
            existing = await conn.fetchrow(
                'SELECT id FROM users WHERE email = \$1',
                'test@example.com'
            )

            if not existing:
                await conn.execute('''
                    INSERT INTO users (email, password_hash, is_active, created_at)
                    VALUES (\$1, \$2, true, NOW())
                ''', 'test@example.com', get_password_hash('Test123!'))
                print('✅ Test user created: test@example.com / Test123!')
            else:
                print('✅ Test user already exists')
    except Exception as e:
        print(f'⚠️  Could not create test user: {e}')
        print('   This is OK if database tables are not ready yet')

asyncio.run(create_test_user())
" 2>/dev/null || echo -e "${YELLOW}⚠️  User creation skipped (database may not be ready)${NC}"

# Step 9: Display final info
echo -e "\n${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                ║${NC}"
echo -e "${GREEN}║   ✅ ENVIRONNEMENT DE TEST PRÊT !             ║${NC}"
echo -e "${GREEN}║                                                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 Informations:${NC}"
echo "  - Backend API:    http://localhost:8001"
echo "  - API Docs:       http://localhost:8001/docs"
echo "  - Frontend:       http://localhost:5174"
echo "  - PostgreSQL:     localhost:5433"
echo "  - Redis:          localhost:6380"
echo ""
echo -e "${BLUE}👤 Compte de test:${NC}"
echo "  - Email:          test@example.com"
echo "  - Password:       Test123!"
echo ""
echo -e "${BLUE}🧪 Pour lancer les tests:${NC}"
echo "  ./test-environment/run-tests.sh"
echo ""
echo -e "${BLUE}📊 Pour voir les logs:${NC}"
echo "  $DOCKER_COMPOSE -f docker-compose.test.yml logs -f"
echo ""
echo -e "${BLUE}🛑 Pour arrêter:${NC}"
echo "  $DOCKER_COMPOSE -f docker-compose.test.yml down"
echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
