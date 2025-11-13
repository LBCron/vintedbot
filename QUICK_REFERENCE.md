# 🚀 VintedBot - Quick Reference

## Nouveaux Endpoints API

### Health & Monitoring
```bash
GET  /api/v1/health                      # Basic health check
GET  /api/v1/health/detailed             # Comprehensive health
GET  /api/v1/metrics                     # System metrics
GET  /api/v1/health/jobs                 # Background jobs stats
GET  /api/v1/health/circuit-breakers     # Circuit breaker status
```

### Admin (TODO: Add auth protection)
```bash
POST /api/v1/admin/backup/create         # Create database backup
POST /api/v1/admin/backup/restore        # Restore from backup
GET  /api/v1/admin/backup/list           # List all backups
GET  /api/v1/admin/backup/info           # Backup system info
POST /api/v1/admin/export                # Export DB (JSON/SQL)
GET  /api/v1/admin/system/health         # Admin health view
POST /api/v1/admin/jobs/reset-stats      # Reset job statistics
```

### Legal Documents
```bash
GET /api/v1/legal/terms                  # Terms of Service
GET /api/v1/legal/privacy                # Privacy Policy
GET /api/v1/legal/disclaimer             # Service Disclaimer ⚠️
GET /api/v1/legal/acceptable-use         # Acceptable Use Policy
```

---

## Nouveaux Modules Python

### 1. Circuit Breaker
```python
from backend.core.circuit_breaker import vinted_api_breaker

result = await vinted_api_breaker.call_async(my_function, args)
```

### 2. Job Wrapper
```python
from backend.core.job_wrapper import isolated_job

@isolated_job("my_job", max_retries=2, timeout=300)
async def my_job():
    # Your code
    pass
```

### 3. Monitoring
```python
from backend.core.monitoring import get_system_health, get_system_metrics

health = await get_system_health()
metrics = await get_system_metrics()
```

### 4. Backup
```python
from backend.core.backup import create_backup, restore_backup, list_backups

result = create_backup(compress=True)
backups = list_backups()
```

### 5. Enhanced Auth
```python
from backend.core.auth_enhanced import EnhancedAuthManager, AuthConfig

config = AuthConfig(jwt_secret=SECRET)
auth_manager = EnhancedAuthManager(config)

tokens = auth_manager.create_token_pair(user_id, email)
auth_manager.set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
```

### 6. Cost Tracker
```python
from backend.core.cost_tracker import cost_tracker

usage = cost_tracker.track_usage(
    user_id=123,
    model="gpt-4o",
    prompt_tokens=1500,
    completion_tokens=200,
    request_type="photo_analysis"
)

summary = cost_tracker.get_user_cost_summary(user_id=123, days=30)
```

### 7. Error Handling
```python
from backend.middleware.error_handler import error_handler_middleware, register_exception_handlers

app.middleware("http")(error_handler_middleware)
register_exception_handlers(app)
```

### 8. Migration
```bash
# CLI commands
python -m backend.core.migration export_schema
python -m backend.core.migration generate_postgresql
python -m backend.core.migration migration_guide
```

---

## Configuration (.env)

```bash
# Auth Enhanced
JWT_SECRET=your-secret-here
USE_HTTPONLY_COOKIES=true
CSRF_PROTECTION=true
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Backup
BACKUP_DIR=backend/data/backups
MAX_BACKUPS=7

# Cost Tracking
COST_TRACKING_ENABLED=true

# Monitoring
ENABLE_SYSTEM_MONITORING=true
```

---

## Daily Checks

1. **Health Status**
   ```bash
   curl http://localhost:5000/api/v1/health/detailed
   ```

2. **Job Health**
   ```bash
   curl http://localhost:5000/api/v1/health/jobs
   ```

3. **Circuit Breakers**
   ```bash
   curl http://localhost:5000/api/v1/health/circuit-breakers
   ```

4. **Backups**
   ```bash
   curl http://localhost:5000/api/v1/admin/backup/list
   ```

---

## Automatic Backup Setup

### Linux/Mac (crontab)
```bash
# Daily backup at 2 AM
0 2 * * * curl -X POST http://localhost:5000/api/v1/admin/backup/create
```

### Windows (Task Scheduler)
```powershell
# Create daily task
$action = New-ScheduledTaskAction -Execute "curl" -Argument "-X POST http://localhost:5000/api/v1/admin/backup/create"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "VintedBot Backup"
```

---

## Migration to PostgreSQL (When Ready)

```bash
# 1. Backup current database
curl -X POST http://localhost:5000/api/v1/admin/backup/create

# 2. Export schema
python -m backend.core.migration export_schema

# 3. Generate PostgreSQL schema
python -m backend.core.migration generate_postgresql

# 4. Export data
curl -X POST http://localhost:5000/api/v1/admin/export \
  -H "Content-Type: application/json" \
  -d '{"output_path": "export.json", "format": "json"}'

# 5. Follow migration guide
python -m backend.core.migration migration_guide
```

---

## Troubleshooting

### Circuit Breaker Open
```python
from backend.core.circuit_breaker import vinted_api_breaker
vinted_api_breaker.state = CircuitState.CLOSED  # Force close (use carefully)
```

### Reset Job Stats
```bash
curl -X POST http://localhost:5000/api/v1/admin/jobs/reset-stats
```

### Database Restore
```bash
curl -X POST http://localhost:5000/api/v1/admin/backup/restore \
  -H "Content-Type: application/json" \
  -d '{"backup_path": "backend/data/backups/vbs_backup_20240101_120000.db.gz"}'
```

---

## Key Improvements Summary

| Feature | Impact | Status |
|---------|--------|--------|
| Circuit Breakers | ⭐⭐⭐⭐⭐ | ✅ |
| Job Isolation | ⭐⭐⭐⭐⭐ | ✅ |
| Monitoring | ⭐⭐⭐⭐⭐ | ✅ |
| Backups | ⭐⭐⭐⭐ | ✅ |
| Enhanced Security | ⭐⭐⭐⭐ | ✅ |
| Error Handling | ⭐⭐⭐⭐⭐ | ✅ |
| Legal Docs | ⭐⭐⭐⭐⭐ | ✅ |
| Cost Tracking | ⭐⭐⭐⭐ | ✅ |
| Migration Tools | ⭐⭐⭐⭐ | ✅ |

---

## Urgent TODOs

1. ⚠️ **Add admin authentication** to `/admin/*` endpoints
2. ⚠️ **Display disclaimer** on first user login (frontend)
3. ⚠️ **Setup automatic daily backups**
4. ⚠️ **Test all new endpoints**
5. ⚠️ **Review legal docs with lawyer**

---

For full documentation, see: [IMPROVEMENTS.md](./IMPROVEMENTS.md)
