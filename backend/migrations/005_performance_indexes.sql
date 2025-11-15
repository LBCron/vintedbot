-- Migration: Performance Optimization Indexes
-- Creates indexes to improve query performance across all tables

-- ============================================
-- USERS TABLE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);

-- ============================================
-- DRAFTS TABLE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_drafts_user_status ON drafts(user_id, status);
CREATE INDEX IF NOT EXISTS idx_drafts_published_at ON drafts(published_at DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_drafts_created_at ON drafts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_drafts_sold ON drafts(sold, user_id);

-- ============================================
-- MESSAGES TABLE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_unread ON messages(user_id, read) WHERE read = false;

-- ============================================
-- SCHEDULED PUBLICATIONS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_scheduled_time_status ON scheduled_publications(scheduled_time, status);
CREATE INDEX IF NOT EXISTS idx_scheduled_user ON scheduled_publications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_scheduled_pending ON scheduled_publications(scheduled_time) WHERE status = 'pending';

-- ============================================
-- AI MESSAGES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_ai_messages_user ON ai_messages(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_messages_intention ON ai_messages(intention, created_at DESC);

-- ============================================
-- CONVERSATIONS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_draft ON conversations(draft_id);

-- ============================================
-- PRICE HISTORY
-- ============================================
CREATE INDEX IF NOT EXISTS idx_price_history_draft ON price_history(draft_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_user ON price_history(user_id, created_at DESC);

-- ============================================
-- IMAGE ENHANCEMENTS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_image_enhancements_draft ON image_enhancements(draft_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_image_enhancements_quality ON image_enhancements(overall_score DESC);

-- ============================================
-- ML PREDICTIONS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_ml_predictions_user ON ml_predictions(user_id, prediction_date DESC);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_type ON ml_predictions(prediction_type, prediction_date DESC);

-- ============================================
-- USER INSIGHTS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_user_insights_user ON user_insights(user_id, updated_at DESC);

-- ============================================
-- ACCOUNTS TABLE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(user_id, status);

-- ============================================
-- AUTOMATION RUNS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_automation_runs_user ON automation_runs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_automation_runs_type ON automation_runs(automation_type, status);

-- ============================================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- ============================================

-- Drafts dashboard query optimization
CREATE INDEX IF NOT EXISTS idx_drafts_dashboard ON drafts(user_id, status, created_at DESC);

-- Messages inbox optimization
CREATE INDEX IF NOT EXISTS idx_messages_inbox ON messages(user_id, read, created_at DESC);

-- Analytics queries optimization
CREATE INDEX IF NOT EXISTS idx_drafts_analytics ON drafts(user_id, published_at, price, sold) WHERE published_at IS NOT NULL;

-- Scheduling optimization
CREATE INDEX IF NOT EXISTS idx_scheduled_publications_active ON scheduled_publications(user_id, scheduled_time, status) WHERE status IN ('pending', 'processing');

-- ============================================
-- ANALYZE TABLES FOR QUERY PLANNER
-- ============================================
ANALYZE users;
ANALYZE drafts;
ANALYZE messages;
ANALYZE scheduled_publications;
ANALYZE ai_messages;
ANALYZE conversations;
ANALYZE price_history;
ANALYZE image_enhancements;
ANALYZE ml_predictions;
ANALYZE user_insights;

-- ============================================
-- VACUUM FOR PERFORMANCE
-- ============================================
-- Note: VACUUM cannot be run inside a transaction
-- Run manually: VACUUM ANALYZE;

-- ============================================
-- COMMENTS
-- ============================================
COMMENT ON INDEX idx_drafts_user_status IS 'Optimize drafts list queries by user and status';
COMMENT ON INDEX idx_messages_inbox IS 'Optimize messages inbox queries';
COMMENT ON INDEX idx_scheduled_pending IS 'Optimize scheduled publications cron job queries';
COMMENT ON INDEX idx_drafts_analytics IS 'Optimize analytics dashboard queries';
