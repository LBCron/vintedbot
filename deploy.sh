#!/bin/bash
# ============================================================================
# VintedBot - Quick Deploy Script
# ============================================================================
# Deploys the complete VintedBot stack with PostgreSQL, Redis, MinIO, and monitoring

set -e  # Exit on error

echo "🚀 VintedBot Production Deployment"
echo "=================================="
echo ""

# ============================================================================
# Check prerequisites
# ============================================================================
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites OK"
echo ""

# ============================================================================
# Environment setup
# ============================================================================
echo "⚙️ Setting up environment..."

if [ ! -f .env.production ]; then
    echo "📝 Creating .env.production from template..."
    cp .env.production.example .env.production

    # Generate secrets
    JWT_SECRET=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    REDIS_PASSWORD=$(openssl rand -hex 16)
    MINIO_ROOT_PASSWORD=$(openssl rand -hex 16)
    GRAFANA_PASSWORD=$(openssl rand -hex 16)

    # Update .env.production
    sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env.production
    sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env.production
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env.production
    sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env.production
    sed -i "s/MINIO_ROOT_PASSWORD=.*/MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD/" .env.production
    sed -i "s/GRAFANA_PASSWORD=.*/GRAFANA_PASSWORD=$GRAFANA_PASSWORD/" .env.production

    echo "✅ Secrets generated and saved to .env.production"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env.production and add:"
    echo "   - OPENAI_API_KEY"
    echo "   - STRIPE_SECRET_KEY"
    echo "   - SMTP credentials"
    echo "   - SENTRY_DSN (optional)"
    echo ""
    read -p "Press Enter when ready to continue..."
fi

# Load environment
source .env.production
echo "✅ Environment loaded"
echo ""

# ============================================================================
# Database setup
# ============================================================================
echo "🗄️ Setting up databases..."

# Create data directories
mkdir -p backend/data/backups
mkdir -p backend/data/photos
mkdir -p backend/data/temp_uploads

# Start PostgreSQL and Redis first
docker-compose up -d postgres redis

echo "⏳ Waiting for PostgreSQL to be ready..."
until docker-compose exec -T postgres pg_isready -U $POSTGRES_USER; do
    sleep 1
done
echo "✅ PostgreSQL ready"

echo "⏳ Waiting for Redis to be ready..."
until docker-compose exec -T redis redis-cli ping; do
    sleep 1
done
echo "✅ Redis ready"
echo ""

# ============================================================================
# MinIO setup
# ============================================================================
echo "📦 Setting up MinIO..."

docker-compose up -d minio

echo "⏳ Waiting for MinIO to be ready..."
sleep 5

# Create bucket
docker-compose exec -T minio mc alias set minio http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
docker-compose exec -T minio mc mb minio/$S3_BUCKET --ignore-existing

echo "✅ MinIO ready"
echo ""

# ============================================================================
# Backend setup
# ============================================================================
echo "🐍 Setting up backend..."

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run database migrations
python -c "from backend.core.database import init_db; import asyncio; asyncio.run(init_db())"

cd ..
echo "✅ Backend ready"
echo ""

# ============================================================================
# Frontend setup
# ============================================================================
echo "⚛️ Setting up frontend..."

cd frontend
npm install
npm run build
cd ..

echo "✅ Frontend ready"
echo ""

# ============================================================================
# Start all services
# ============================================================================
echo "🚀 Starting all services..."

docker-compose up -d

echo ""
echo "✅ Deployment complete!"
echo ""
echo "=========================================="
echo "📊 Service URLs:"
echo "=========================================="
echo "Backend API:      http://localhost:5000"
echo "API Docs:         http://localhost:5000/docs"
echo "Metrics:          http://localhost:5000/metrics"
echo ""
echo "Prometheus:       http://localhost:9090"
echo "Grafana:          http://localhost:3001"
echo "MinIO Console:    http://localhost:9001"
echo ""
echo "=========================================="
echo "🔐 Credentials:"
echo "=========================================="
echo "Grafana:          admin / $GRAFANA_PASSWORD"
echo "MinIO:            $MINIO_ROOT_USER / $MINIO_ROOT_PASSWORD"
echo ""
echo "=========================================="
echo "📝 Next steps:"
echo "=========================================="
echo "1. Check logs:         docker-compose logs -f"
echo "2. View services:      docker-compose ps"
echo "3. Access API docs:    http://localhost:5000/docs"
echo "4. Setup monitoring:   http://localhost:3001"
echo ""
echo "🎉 VintedBot is now running!"
