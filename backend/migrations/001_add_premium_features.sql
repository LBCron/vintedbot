-- Migration: Add Premium Features Support
-- Date: 2025-11-16
-- Description: Add columns for Stripe subscriptions, admin roles, and webhooks

-- ============================================================================
-- 1. Add Stripe subscription columns to users table
-- ============================================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(50) DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'inactive';

-- ============================================================================
-- 2. Add admin role column to users table
-- ============================================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- ============================================================================
-- 3. Add last login tracking
-- ============================================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;

-- ============================================================================
-- 4. Create webhooks table for external integrations
-- ============================================================================

CREATE TABLE IF NOT EXISTS webhooks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,  -- Array of event types
    description TEXT,
    secret TEXT NOT NULL,  -- HMAC secret for verification
    is_active BOOLEAN DEFAULT TRUE,
    delivery_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered_at TIMESTAMP
);

-- Create indexes for webhooks
CREATE INDEX IF NOT EXISTS idx_webhooks_user_id ON webhooks(user_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_is_active ON webhooks(is_active);

-- ============================================================================
-- 5. Add indexes for subscription queries
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_users_subscription_plan ON users(subscription_plan);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);
CREATE INDEX IF NOT EXISTS idx_users_last_login_at ON users(last_login_at);

-- ============================================================================
-- 6. Set first user as admin (for initial setup)
-- ============================================================================

-- Note: This should be run manually or configured via environment variable
-- UPDATE users SET is_admin = TRUE WHERE id = 1;

COMMENT ON COLUMN users.stripe_customer_id IS 'Stripe customer ID for billing';
COMMENT ON COLUMN users.stripe_subscription_id IS 'Active Stripe subscription ID';
COMMENT ON COLUMN users.subscription_plan IS 'Current plan: free, starter, pro, enterprise';
COMMENT ON COLUMN users.subscription_status IS 'Subscription status: active, canceled, past_due, etc.';
COMMENT ON COLUMN users.is_admin IS 'Admin role flag for platform administration';
COMMENT ON COLUMN users.last_login_at IS 'Timestamp of last successful login';

COMMENT ON TABLE webhooks IS 'External webhook integrations (Zapier, Make, custom)';
