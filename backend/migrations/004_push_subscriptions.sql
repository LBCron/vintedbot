-- Migration: Push Subscriptions for PWA
-- Creates table for storing web push notification subscriptions

CREATE TABLE IF NOT EXISTS push_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    keys JSONB NOT NULL, -- { p256dh, auth }
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Ensure one subscription per endpoint per user
    UNIQUE(user_id, endpoint)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_enabled ON push_subscriptions(user_id, enabled);

-- Comments
COMMENT ON TABLE push_subscriptions IS 'Web push notification subscriptions for PWA';
COMMENT ON COLUMN push_subscriptions.endpoint IS 'Push service endpoint URL';
COMMENT ON COLUMN push_subscriptions.keys IS 'Encryption keys (p256dh, auth)';
COMMENT ON COLUMN push_subscriptions.enabled IS 'Whether subscription is active';
