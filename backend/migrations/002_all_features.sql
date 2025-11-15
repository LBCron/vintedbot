-- Complete database migration for all 5 new features
-- Features: AI Messages, Scheduling, Price Optimizer, Image Enhancement, Advanced Analytics
-- Run with: psql -U user -d vintedbot -f backend/migrations/002_all_features.sql

-- ============================================
-- FEATURE #1: AI-Powered Messages
-- ============================================

-- Message settings
CREATE TABLE IF NOT EXISTS message_settings (
    user_id TEXT PRIMARY KEY,
    auto_reply_enabled BOOLEAN DEFAULT FALSE,
    tone TEXT DEFAULT 'friendly' CHECK (tone IN ('friendly', 'professional', 'casual')),
    mode TEXT DEFAULT 'draft' CHECK (mode IN ('auto', 'draft', 'notify')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI-generated messages log
CREATE TABLE IF NOT EXISTS ai_messages (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    message_text TEXT NOT NULL,
    article_id TEXT,
    intention TEXT,
    confidence DECIMAL(3,2),
    generated_response TEXT,
    tone TEXT DEFAULT 'friendly',
    auto_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations (for future Vinted integration)
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    buyer_name TEXT,
    article_id TEXT,
    last_message TEXT,
    unread_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual messages
CREATE TABLE IF NOT EXISTS conversation_messages (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender TEXT NOT NULL CHECK (sender IN ('buyer', 'seller')),
    message TEXT NOT NULL,
    auto_generated BOOLEAN DEFAULT FALSE,
    intention TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FEATURE #2: Intelligent Scheduling
-- ============================================

CREATE TABLE IF NOT EXISTS scheduled_publications (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    draft_id TEXT NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'published', 'failed', 'cancelled')),
    published_at TIMESTAMP,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FEATURE #3: Price Optimization
-- ============================================

-- Price history for tracking changes
CREATE TABLE IF NOT EXISTS price_history (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    draft_id TEXT NOT NULL,
    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2),
    strategy TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FEATURE #4: Image Enhancement
-- ============================================

CREATE TABLE IF NOT EXISTS image_enhancements (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    original_path TEXT NOT NULL,
    enhanced_path TEXT,
    brightness_score DECIMAL(3,1),
    sharpness_score DECIMAL(3,1),
    contrast_score DECIMAL(3,1),
    overall_score DECIMAL(3,1),
    enhancements_applied JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FEATURE #5: Advanced Analytics
-- ============================================

-- ML predictions cache
CREATE TABLE IF NOT EXISTS ml_predictions (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    prediction_type TEXT NOT NULL,
    predictions JSONB NOT NULL,
    confidence DECIMAL(3,2),
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User insights
CREATE TABLE IF NOT EXISTS user_insights (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    insight_type TEXT NOT NULL,
    title TEXT,
    message TEXT,
    priority TEXT,
    action TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- AI Messages
CREATE INDEX IF NOT EXISTS idx_ai_messages_user ON ai_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_messages_created ON ai_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_conv ON conversation_messages(conversation_id);

-- Scheduling
CREATE INDEX IF NOT EXISTS idx_scheduled_time ON scheduled_publications(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_scheduled_status ON scheduled_publications(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_user ON scheduled_publications(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_draft ON scheduled_publications(draft_id);

-- Price History
CREATE INDEX IF NOT EXISTS idx_price_history_draft ON price_history(draft_id);
CREATE INDEX IF NOT EXISTS idx_price_history_created ON price_history(created_at);

-- Image Enhancements
CREATE INDEX IF NOT EXISTS idx_image_enhancements_user ON image_enhancements(user_id);
CREATE INDEX IF NOT EXISTS idx_image_enhancements_created ON image_enhancements(created_at);

-- ML Predictions
CREATE INDEX IF NOT EXISTS idx_ml_predictions_user ON ml_predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_valid ON ml_predictions(valid_until);

-- User Insights
CREATE INDEX IF NOT EXISTS idx_user_insights_user ON user_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_user_insights_read ON user_insights(is_read);

-- ============================================
-- Comments
-- ============================================

COMMENT ON TABLE message_settings IS 'User preferences for AI-powered message automation';
COMMENT ON TABLE ai_messages IS 'Log of all AI-generated messages for analytics';
COMMENT ON TABLE scheduled_publications IS 'Intelligent scheduling system for publications';
COMMENT ON TABLE price_history IS 'Price optimization history and tracking';
COMMENT ON TABLE image_enhancements IS 'AI-powered image enhancement logs';
COMMENT ON TABLE ml_predictions IS 'Cached ML predictions for performance';
COMMENT ON TABLE user_insights IS 'AI-generated insights and recommendations';
