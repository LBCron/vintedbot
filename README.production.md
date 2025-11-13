# 🚀 VintedBot - Production Deployment Guide

**The most sophisticated Vinted automation platform on the market**

## ⚡ Quick Start (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/your-username/vintedbots.git
cd vintedbots

# 2. Run deployment script
chmod +x deploy.sh
./deploy.sh

# 3. Access the application
open http://localhost:5000/docs
```

Done! VintedBot is now running with PostgreSQL, Redis, MinIO, Prometheus, and Grafana.

---

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Backup & Restore](#backup--restore)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
│                     (Nginx / Cloudflare)                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
│  Frontend      │   │  Backend API   │   │   Monitoring   │
│  (React)       │   │  (FastAPI)     │   │  (Grafana)     │
│  Vite Build    │   │  Python 3.11   │   │  Prometheus    │
└────────────────┘   └────────────────┘   └────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
│  PostgreSQL    │   │     Redis      │   │   MinIO/S3     │
│  (Database)    │   │   (Cache)      │   │   (Photos)     │
└────────────────┘   └────────────────┘   └────────────────┘
```

### Tech Stack

**Backend:**
- FastAPI 0.104.1 (Python web framework)
- PostgreSQL 16 (primary database)
- Redis 7 (cache + job queue)
- Playwright (browser automation)
- OpenAI GPT-4o/GPT-4o-mini (AI analysis)

**Frontend:**
- React 18 + TypeScript
- TailwindCSS 3
- Vite 5 (build tool)
- React Router 6

**Infrastructure:**
- Docker + Docker Compose
- MinIO (S3-compatible storage)
- Prometheus (metrics)
- Grafana (dashboards)
- Sentry (error tracking)

---

## 📦 Prerequisites

### Required

- **Docker** 24.0+ & **Docker Compose** 2.0+
- **4GB RAM minimum** (8GB recommended)
- **20GB disk space**
- **Linux/MacOS** (Windows with WSL2)

### Optional

- **Domain name** (for production)
- **SSL certificate** (Let's Encrypt recommended)
- **Sentry account** (error tracking)
- **Stripe account** (payments)

---

## 🛠 Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/your-username/vintedbots.git
cd vintedbots
```

### Step 2: Configure Environment

```bash
# Copy production config template
cp .env.production.example .env.production

# Edit with your values
nano .env.production
```

**Required environment variables:**

```bash
# OpenAI (REQUIRED)
OPENAI_API_KEY=sk_...

# Stripe (if using payments)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# SMTP (for emails)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Sentry (optional but recommended)
SENTRY_DSN=https://...@sentry.io/...
```

### Step 3: Generate Secrets

```bash
# Generate secure secrets
export JWT_SECRET=$(openssl rand -hex 32)
export ENCRYPTION_KEY=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -hex 16)
export REDIS_PASSWORD=$(openssl rand -hex 16)

# Add to .env.production
echo "JWT_SECRET=$JWT_SECRET" >> .env.production
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env.production
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> .env.production
echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> .env.production
```

### Step 4: Deploy

```bash
# Option A: Automated deployment (recommended)
chmod +x deploy.sh
./deploy.sh

# Option B: Manual deployment
docker-compose up -d

# Wait for services to be ready
docker-compose ps
docker-compose logs -f backend
```

### Step 5: Verify Installation

```bash
# Check all services are running
docker-compose ps

# Should show:
# - postgres (healthy)
# - redis (healthy)
# - minio (healthy)
# - backend (healthy)
# - prometheus (running)
# - grafana (running)

# Test API
curl http://localhost:5000/api/v1/health

# Should return: {"status": "healthy"}
```

---

## ⚙️ Configuration

### Database Connection Pooling

**PostgreSQL pool settings** (adjust based on load):

```bash
DB_POOL_SIZE=10          # Concurrent connections
DB_MAX_OVERFLOW=20       # Extra connections during spikes
DB_POOL_TIMEOUT=30       # Wait time for available connection
DB_POOL_RECYCLE=3600     # Recycle connections after 1 hour
```

**Recommended settings by user count:**

| Users | Pool Size | Max Overflow |
|-------|-----------|--------------|
| 0-100 | 5 | 10 |
| 100-500 | 10 | 20 |
| 500-1000 | 20 | 40 |
| 1000+ | 50 | 100 |

### Redis Configuration

```bash
REDIS_MAX_CONNECTIONS=50     # Connection pool size
REDIS_SOCKET_TIMEOUT=5       # Timeout for operations
```

### OpenAI Cost Management

```bash
OPENAI_COST_LIMIT_PER_USER=5.0     # $5/day per user
OPENAI_COST_LIMIT_GLOBAL=500.0     # $500/day total
```

The system automatically:
- Tracks spending per user
- Switches from GPT-4o → GPT-4o-mini when budget low
- Blocks requests when limit exceeded
- Caches responses for 24h

### Storage Configuration

**Local storage** (development):
```bash
# Photos stored in backend/data/photos
```

**S3/MinIO** (production):
```bash
S3_ENDPOINT=http://minio:9000
S3_BUCKET=vintedbots-photos
S3_ACCESS_KEY=admin
S3_SECRET_KEY=your-password
```

**AWS S3** (enterprise):
```bash
S3_ENDPOINT=https://s3.amazonaws.com
S3_REGION=us-east-1
S3_ACCESS_KEY=AKIA...
S3_SECRET_KEY=...
```

---

## 🚀 Deployment

### Local Development

```bash
# Start development server
docker-compose up

# Backend: http://localhost:5000
# Frontend: http://localhost:3000
```

### Production (Docker)

```bash
# Build and start all services
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f backend

# Scale backend workers
docker-compose up -d --scale backend=3
```

### Production (Fly.io)

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy
fly deploy

# Set secrets
fly secrets set JWT_SECRET=$(openssl rand -hex 32)
fly secrets set OPENAI_API_KEY=sk_...
fly secrets set STRIPE_SECRET_KEY=sk_live_...

# View logs
fly logs
```

### Production (AWS/GCP/Azure)

1. **Build Docker image:**
   ```bash
   docker build -t vintedbots:latest .
   docker push your-registry/vintedbots:latest
   ```

2. **Deploy to Kubernetes:**
   ```bash
   kubectl apply -f k8s/
   ```

3. **Configure load balancer** (Nginx example):
   ```nginx
   upstream backend {
       server backend1:5000;
       server backend2:5000;
       server backend3:5000;
   }

   server {
       listen 80;
       server_name api.your-domain.com;

       location / {
           proxy_pass http://backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

## 📊 Monitoring

### Prometheus Metrics

Access: `http://localhost:9090`

**Key metrics:**
- `http_requests_total` - Total HTTP requests
- `ai_cost_total_cents` - AI spending
- `vinted_automation_runs_total` - Automation executions
- `db_query_duration_seconds` - Database performance

### Grafana Dashboards

Access: `http://localhost:3001`
Login: `admin` / `<GRAFANA_PASSWORD>`

**Pre-built dashboards:**
1. **Application Overview** - Requests, errors, latency
2. **AI Usage** - Cost tracking, model usage, tokens
3. **Database Performance** - Query times, pool stats
4. **Business Metrics** - Users, revenue, listings

### Sentry Error Tracking

```bash
# Enable Sentry
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
```

Sentry automatically captures:
- Exceptions with full stack traces
- Performance metrics (APM)
- User context
- Breadcrumbs

### Health Checks

```bash
# Basic health
curl http://localhost:5000/api/v1/health

# Detailed health (includes DB, Redis, S3)
curl http://localhost:5000/api/v1/health/detailed

# Metrics
curl http://localhost:5000/metrics
```

---

## 💾 Backup & Restore

### Automated Backups

Backups run daily at 2 AM UTC:

```python
# backend/jobs.py
scheduler.add_job(
    backup_system.create_backup,
    trigger="cron",
    hour=2,
    minute=0
)
```

**Backup includes:**
- PostgreSQL database dump (compressed with gzip)
- Automatic upload to S3 (if enabled)
- 30-day retention (configurable)

### Manual Backup

```bash
# Create backup
docker-compose exec backend python -c "
from backend.core.backup_system import backup_system
import asyncio
asyncio.run(backup_system.create_backup())
"

# List backups
docker-compose exec backend python -c "
from backend.core.backup_system import backup_system
import asyncio
backups = asyncio.run(backup_system.list_backups())
for b in backups:
    print(f\"{b['filename']} - {b['size_mb']}MB\")
"
```

### Restore from Backup

```bash
# ⚠️ WARNING: This will overwrite your database!

docker-compose exec backend python -c "
from backend.core.backup_system import backup_system
import asyncio
asyncio.run(backup_system.restore_backup('vintedbots_backup_20250104_120000.sql.gz'))
"
```

### Backup to S3

```bash
# Enable S3 backups
BACKUP_TO_S3=true
S3_ENDPOINT=https://s3.amazonaws.com
S3_BUCKET=vintedbots-backups
```

---

## 📈 Scaling

### Vertical Scaling (Single Server)

**Increase resources:**
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

**Optimize database:**
```bash
# Increase pool size
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
```

### Horizontal Scaling (Multiple Servers)

**1. Load Balancer Setup** (Nginx):
```nginx
upstream backend_cluster {
    least_conn;  # Use least connections algorithm
    server backend1:5000 max_fails=3 fail_timeout=30s;
    server backend2:5000 max_fails=3 fail_timeout=30s;
    server backend3:5000 max_fails=3 fail_timeout=30s;
}
```

**2. Shared Services:**
- ✅ Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
- ✅ Use managed Redis (AWS ElastiCache, Redis Cloud)
- ✅ Use S3 for photos (not local storage)

**3. Session Management:**
- Backend is stateless ✅
- Sessions stored in database ✅
- Redis cache shared across instances ✅

### Auto-Scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vintedbots-backend
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vintedbots-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Database not ready
docker-compose exec postgres pg_isready

# 2. Missing environment variables
docker-compose exec backend env | grep -E "DATABASE_URL|REDIS_URL|OPENAI_API_KEY"

# 3. Port already in use
lsof -i :5000
```

### Database connection errors

```bash
# Test PostgreSQL connection
docker-compose exec postgres psql -U vintedbots -d vintedbots -c "SELECT 1"

# Check pool stats
curl http://localhost:5000/api/v1/health/detailed | jq .database
```

### Redis connection errors

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis info
docker-compose exec redis redis-cli INFO
```

### OpenAI API errors

```bash
# Verify API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check cost tracking
curl http://localhost:5000/api/v1/ai/stats
```

### High memory usage

```bash
# Check container stats
docker stats

# Reduce pool sizes
DB_POOL_SIZE=5
REDIS_MAX_CONNECTIONS=25

# Enable memory limits
docker-compose up -d --scale backend=1 \
  --memory="2g" --memory-swap="2g"
```

---

## 🔐 Security

### Secrets Management

**Never commit secrets!**

```bash
# Add to .gitignore
echo ".env.production" >> .gitignore
echo "backend/data/*.db" >> .gitignore
```

### Rate Limiting

```bash
# Configure rate limits
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### HTTPS/SSL

**Let's Encrypt (recommended):**
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api.your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Firewall Rules

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Database Security

```bash
# Use strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Restrict network access
# docker-compose.yml
services:
  postgres:
    networks:
      - internal  # Not exposed to public
```

---

## 📞 Support

### Documentation

- [API Documentation](http://localhost:5000/docs)
- [Architecture Guide](./ARCHITECTURE.md)
- [Deployment Guide](./DEPLOY_GUIDE.md)

### Community

- GitHub Issues: [Report bugs](https://github.com/your-username/vintedbots/issues)
- Discord: [Join community](#)

### Professional Support

For enterprise support, contact: support@vintedbots.com

---

## ⚖️ Legal Notice

**IMPORTANT:** This software automates interactions with Vinted, which violates Vinted's Terms of Service. Use at your own risk.

- ⚠️ Your Vinted account may be permanently banned
- ⚠️ We are not responsible for any account suspensions
- ⚠️ This is provided for educational purposes only

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file

---

**Built with ❤️ by the VintedBot team**
