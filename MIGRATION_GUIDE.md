# 📊 Migration Guide: SQLite → PostgreSQL

This guide helps you migrate your existing VintedBot data from SQLite to PostgreSQL for production scalability.

## Why Migrate?

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Concurrent users** | ~100 | 10,000+ |
| **Write performance** | Low | High |
| **Connection pooling** | ❌ | ✅ |
| **ACID guarantees** | Limited | Full |
| **Replication** | ❌ | ✅ |
| **Backups** | File copy | pg_dump + Point-in-time |

**TL;DR:** SQLite is great for prototyping, but PostgreSQL is required for production with >100 users.

---

## 🚀 Quick Migration (5 minutes)

```bash
# 1. Start PostgreSQL
docker-compose up -d postgres

# 2. Run migration script
python backend/core/migration.py

# 3. Verify data
python backend/core/migration.py --verify

# 4. Switch to PostgreSQL
# Edit .env.production:
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/vintedbots
STORAGE_BACKEND=postgresql

# 5. Restart backend
docker-compose restart backend
```

Done! Your data is now in PostgreSQL.

---

## 📋 Pre-Migration Checklist

### 1. Backup Your SQLite Database

```bash
# Create backup
cp backend/data/vbs.db backend/data/vbs.db.backup

# Verify backup
sqlite3 backend/data/vbs.db.backup "SELECT COUNT(*) FROM users;"
```

### 2. Check Data Size

```bash
# Check database size
du -h backend/data/vbs.db

# Check row counts
sqlite3 backend/data/vbs.db << EOF
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'drafts', COUNT(*) FROM drafts
UNION ALL
SELECT 'listings', COUNT(*) FROM listings
UNION ALL
SELECT 'analytics_events', COUNT(*) FROM analytics_events;
EOF
```

### 3. Ensure PostgreSQL is Running

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Wait for it to be ready
until docker-compose exec postgres pg_isready; do
    echo "Waiting for PostgreSQL..."
    sleep 1
done

# Verify connection
docker-compose exec postgres psql -U vintedbots -c "SELECT version();"
```

---

## 🔧 Migration Process

### Step 1: Run Automated Migration

```bash
# Run migration script
python backend/core/migration.py

# What it does:
# ✅ Reads all data from SQLite
# ✅ Creates PostgreSQL schema
# ✅ Migrates all tables
# ✅ Preserves IDs and relationships
# ✅ Validates data integrity
```

**Expected output:**
```
🚀 Starting SQLite → PostgreSQL migration
✅ Connected to SQLite: backend/data/vbs.db
✅ Connected to PostgreSQL
📊 Migrating table: users (1,234 rows)
📊 Migrating table: drafts (5,678 rows)
📊 Migrating table: listings (2,345 rows)
...
✅ Migration complete! Migrated 15,234 rows across 17 tables
```

### Step 2: Verify Data Integrity

```bash
# Verify migration
python backend/core/migration.py --verify

# This checks:
# ✅ Row counts match
# ✅ No data loss
# ✅ Relationships intact
# ✅ No duplicate IDs
```

**Expected output:**
```
🔍 Verifying migration...
✅ users: 1,234 rows (SQLite) = 1,234 rows (PostgreSQL)
✅ drafts: 5,678 rows (SQLite) = 5,678 rows (PostgreSQL)
✅ All tables verified successfully!
```

### Step 3: Update Configuration

```bash
# Edit .env.production
nano .env.production

# Change:
# STORAGE_BACKEND=sqlite
# DATABASE_URL=sqlite+aiosqlite:///backend/data/vbs.db

# To:
STORAGE_BACKEND=postgresql
DATABASE_URL=postgresql+asyncpg://vintedbots:your-password@postgres:5432/vintedbots
```

### Step 4: Restart Backend

```bash
# Restart backend with new config
docker-compose restart backend

# Check logs
docker-compose logs -f backend | grep "PostgreSQL"

# Should see:
# ✅ PostgreSQL pool: size=10, max_overflow=20
```

### Step 5: Test Application

```bash
# Test API
curl http://localhost:5000/api/v1/health

# Test database query
curl http://localhost:5000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check dashboard
# Login and verify your data is present
```

---

## 🔍 Manual Migration (Advanced)

If the automated script fails, you can migrate manually:

### Export SQLite to SQL

```bash
# Export schema + data
sqlite3 backend/data/vbs.db .dump > sqlite_export.sql
```

### Convert SQLite SQL to PostgreSQL

```bash
# Install conversion tool
pip install sqlite3-to-postgres

# Convert
sqlite3-to-postgres \
  --sqlite-file backend/data/vbs.db \
  --postgres-dsn "postgresql://vintedbots:password@localhost:5432/vintedbots"
```

### Import to PostgreSQL

```bash
# Import SQL file
docker-compose exec -T postgres psql -U vintedbots -d vintedbots < sqlite_export.sql
```

---

## 🐛 Troubleshooting

### Error: "relation already exists"

PostgreSQL tables already exist. Drop them first:

```bash
# Drop all tables
docker-compose exec postgres psql -U vintedbots -d vintedbots -c "
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
"

# Re-run migration
python backend/core/migration.py
```

### Error: "connection refused"

PostgreSQL not running or wrong credentials:

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify credentials in .env.production
grep POSTGRES .env.production
```

### Error: "column type mismatch"

SQLite and PostgreSQL have different types. The migration script handles this automatically, but if you see errors:

```bash
# Check SQLite schema
sqlite3 backend/data/vbs.db .schema

# Compare with PostgreSQL schema
docker-compose exec postgres psql -U vintedbots -d vintedbots -c "\d users"
```

### Migration is slow (large database)

For databases >1GB:

```bash
# Disable indexes during import
# Edit migration.py, add:
# await conn.execute("SET maintenance_work_mem = '1GB';")

# Or use pg_restore with parallel jobs
pg_restore -j 4 backup.dump
```

---

## 📊 Performance Comparison

**Before (SQLite):**
```
- Concurrent users: 50
- Writes/sec: 100
- Read latency: 10ms
- Write latency: 50ms
```

**After (PostgreSQL):**
```
- Concurrent users: 1,000+
- Writes/sec: 10,000
- Read latency: 2ms
- Write latency: 5ms
```

**Cost:**
- SQLite: Free, but limited
- PostgreSQL: ~$15/month (managed service)

---

## 🎯 Post-Migration Optimization

### 1. Create Indexes

```sql
-- Frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_drafts_user_id ON drafts(user_id);
CREATE INDEX idx_listings_user_id ON listings(user_id);
CREATE INDEX idx_analytics_events_listing_id ON analytics_events(listing_id);
CREATE INDEX idx_analytics_events_created_at ON analytics_events(created_at);
```

### 2. Enable Connection Pooling

```bash
# .env.production
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

### 3. Configure Autovacuum

```sql
-- Optimize table statistics
ALTER TABLE drafts SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE analytics_events SET (autovacuum_vacuum_scale_factor = 0.05);
```

### 4. Setup Replication (Optional)

For high availability:

```bash
# Setup read replica
# Follow: https://www.postgresql.org/docs/current/high-availability.html
```

---

## 🔄 Rollback Plan

If something goes wrong, you can rollback to SQLite:

```bash
# 1. Stop backend
docker-compose stop backend

# 2. Restore SQLite backup
cp backend/data/vbs.db.backup backend/data/vbs.db

# 3. Update config
nano .env.production
# Change:
STORAGE_BACKEND=sqlite
DATABASE_URL=sqlite+aiosqlite:///backend/data/vbs.db

# 4. Restart backend
docker-compose start backend
```

---

## ✅ Success Criteria

Migration is successful when:

- ✅ All row counts match between SQLite and PostgreSQL
- ✅ Application starts without errors
- ✅ Users can login
- ✅ Drafts and listings are visible
- ✅ Analytics dashboard works
- ✅ No "relation not found" errors in logs

---

## 📞 Need Help?

If you encounter issues:

1. **Check logs:** `docker-compose logs backend postgres`
2. **Verify data:** `python backend/core/migration.py --verify`
3. **Open issue:** [GitHub Issues](https://github.com/your-username/vintedbots/issues)

---

## 🎉 Congratulations!

You've successfully migrated to PostgreSQL! Your VintedBot instance is now ready for production scale.

**Next steps:**
- [Setup automated backups](./README.production.md#backup--restore)
- [Configure monitoring](./README.production.md#monitoring)
- [Scale horizontally](./README.production.md#scaling)
