# ============================================================================
# VintedBot - Quick Deploy Script (Windows PowerShell)
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "🚀 VintedBot Production Deployment" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Check prerequisites
# ============================================================================
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop for Windows." -ForegroundColor Red
    exit 1
}

# Check Docker Compose
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not installed." -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Environment setup
# ============================================================================
Write-Host "⚙️ Setting up environment..." -ForegroundColor Yellow

if (-not (Test-Path ".env.production")) {
    Write-Host "📝 Creating .env.production from template..." -ForegroundColor Yellow
    Copy-Item ".env.production.example" ".env.production"

    # Generate secrets
    function Generate-Secret {
        param($length = 32)
        try {
            $bytes = New-Object byte[] $length
            ([Security.Cryptography.RandomNumberGenerator]::Create()).GetBytes($bytes)
            return [BitConverter]::ToString($bytes).Replace("-", "").ToLower().Substring(0, $length * 2)
        } catch {
            return -join ((48..57) + (97..102) | Get-Random -Count ($length * 2) | % {[char]$_})
        }
    }

    $JWT_SECRET = Generate-Secret
    $ENCRYPTION_KEY = Generate-Secret
    $POSTGRES_PASSWORD = Generate-Secret -length 16
    $REDIS_PASSWORD = Generate-Secret -length 16
    $MINIO_ROOT_PASSWORD = Generate-Secret -length 16
    $GRAFANA_PASSWORD = Generate-Secret -length 16

    # Update .env.production
    $content = Get-Content ".env.production" -Raw
    $content = $content -replace "JWT_SECRET=.*", "JWT_SECRET=$JWT_SECRET"
    $content = $content -replace "ENCRYPTION_KEY=.*", "ENCRYPTION_KEY=$ENCRYPTION_KEY"
    $content = $content -replace "POSTGRES_PASSWORD=.*", "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
    $content = $content -replace "REDIS_PASSWORD=.*", "REDIS_PASSWORD=$REDIS_PASSWORD"
    $content = $content -replace "MINIO_ROOT_PASSWORD=.*", "MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD"
    $content = $content -replace "GRAFANA_PASSWORD=.*", "GRAFANA_PASSWORD=$GRAFANA_PASSWORD"
    Set-Content ".env.production" $content

    Write-Host "✅ Secrets generated and saved to .env.production" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Please edit .env.production and add:" -ForegroundColor Yellow
    Write-Host "   - OPENAI_API_KEY" -ForegroundColor Yellow
    Write-Host "   - STRIPE_SECRET_KEY" -ForegroundColor Yellow
    Write-Host "   - SMTP credentials" -ForegroundColor Yellow
    Write-Host "   - SENTRY_DSN (optional)" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter when ready to continue..."
}

# Load environment
Get-Content ".env.production" | ForEach-Object {
    if ($_ -match "^([^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# ============================================================================
# Database setup
# ============================================================================
Write-Host "🗄️ Setting up databases..." -ForegroundColor Yellow

# Create data directories
New-Item -ItemType Directory -Force -Path "backend\data\backups" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\data\photos" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\data\temp_uploads" | Out-Null

# Start PostgreSQL and Redis first
docker-compose up -d postgres redis

Write-Host "⏳ Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$maxRetries = 30
$retries = 0
while ($retries -lt $maxRetries) {
    try {
        docker-compose exec -T postgres pg_isready -U $env:POSTGRES_USER 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
    $retries++
}

if ($retries -eq $maxRetries) {
    Write-Host "❌ PostgreSQL failed to start" -ForegroundColor Red
    exit 1
}
Write-Host "✅ PostgreSQL ready" -ForegroundColor Green

Write-Host "⏳ Waiting for Redis to be ready..." -ForegroundColor Yellow
$retries = 0
while ($retries -lt $maxRetries) {
    try {
        docker-compose exec -T redis redis-cli ping 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
    $retries++
}

if ($retries -eq $maxRetries) {
    Write-Host "❌ Redis failed to start" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Redis ready" -ForegroundColor Green
Write-Host ""

# ============================================================================
# MinIO setup
# ============================================================================
Write-Host "📦 Setting up MinIO..." -ForegroundColor Yellow
docker-compose up -d minio
Start-Sleep -Seconds 5
Write-Host "✅ MinIO ready" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Start all services
# ============================================================================
Write-Host "🚀 Starting all services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📊 Service URLs:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Backend API:      http://localhost:5000" -ForegroundColor White
Write-Host "API Docs:         http://localhost:5000/docs" -ForegroundColor White
Write-Host "Metrics:          http://localhost:5000/metrics" -ForegroundColor White
Write-Host ""
Write-Host "Prometheus:       http://localhost:9090" -ForegroundColor White
Write-Host "Grafana:          http://localhost:3001" -ForegroundColor White
Write-Host "MinIO Console:    http://localhost:9001" -ForegroundColor White
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🔐 Credentials:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Grafana:          admin / $env:GRAFANA_PASSWORD" -ForegroundColor White
Write-Host "MinIO:            $env:MINIO_ROOT_USER / $env:MINIO_ROOT_PASSWORD" -ForegroundColor White
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "1. Check logs:         docker-compose logs -f" -ForegroundColor White
Write-Host "2. View services:      docker-compose ps" -ForegroundColor White
Write-Host "3. Access API docs:    http://localhost:5000/docs" -ForegroundColor White
Write-Host "4. Setup monitoring:   http://localhost:3001" -ForegroundColor White
Write-Host ""
Write-Host "🎉 VintedBot is now running!" -ForegroundColor Green
