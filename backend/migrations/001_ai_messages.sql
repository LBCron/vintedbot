-- Migration for AI-powered messaging feature
-- Run with: psql -U user -d vintedbot -f backend/migrations/001_ai_messages.sql

-- Message settings table
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

-- Conversations table (for future Vinted integration)
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

-- Individual messages in conversations
CREATE TABLE IF NOT EXISTS conversation_messages (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender TEXT NOT NULL CHECK (sender IN ('buyer', 'seller')),
    message TEXT NOT NULL,
    auto_generated BOOLEAN DEFAULT FALSE,
    intention TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_messages_user ON ai_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_messages_created ON ai_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation ON conversation_messages(conversation_id);

-- Comments
COMMENT ON TABLE message_settings IS 'User preferences for AI-powered message automation';
COMMENT ON TABLE ai_messages IS 'Log of all AI-generated messages for analytics';
COMMENT ON TABLE conversations IS 'Message conversations with buyers';
COMMENT ON TABLE conversation_messages IS 'Individual messages within conversations';
