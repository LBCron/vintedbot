# Database Migrations

This directory contains SQL migration scripts for the VintedBot database.

## Running Migrations

### Manual Execution

```bash
# Connect to PostgreSQL
psql -U your_user -d vintedbot

# Run migration
\i backend/migrations/001_add_premium_features.sql
```

### Using Python Script

```bash
python backend/run_migrations.py
```

## Migrations

### 001_add_premium_features.sql

Adds support for:
- Stripe subscriptions (customer_id, subscription_id, plan, status)
- Admin roles (is_admin column)
- Webhooks table for external integrations
- Last login tracking
- Proper indexes for performance

### 002_rollback_premium_features.sql

Rollback script to remove all premium features (use with caution!)

## Creating New Migrations

1. Create a new file: `XXX_description.sql`
2. Add `-- Migration: Description` header
3. Use `CREATE/ALTER TABLE IF NOT EXISTS` for idempotency
4. Add proper indexes
5. Add comments for documentation
6. Test both migration and rollback

## Best Practices

- Always use parameterized queries in application code
- Use IF NOT EXISTS to make migrations idempotent
- Add indexes for frequently queried columns
- Add comments to document schema changes
- Test migrations on staging before production
- Keep backups before running migrations
