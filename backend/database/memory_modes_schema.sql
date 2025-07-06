-- Memory Modes Database Schema
-- This migration adds support for Memory Modes feature in RELATRIX

-- Memory configurations per session
CREATE TABLE IF NOT EXISTS memory_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('cache_first', 'always_fresh', 'smart_triggers', 'test_mode')),
    config JSONB NOT NULL DEFAULT '{}'::jsonb, -- Full MemoryConfig as JSON
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_active_session_config UNIQUE (session_id, is_active) -- Only one active config per session
);

-- Memory metrics for tracking and optimization
CREATE TABLE IF NOT EXISTS memory_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    mode VARCHAR(20) NOT NULL,
    retrieval_count INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    total_tokens_retrieved INTEGER DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0.0000,
    avg_retrieval_time_ms FLOAT DEFAULT 0.0,
    triggers_fired JSONB DEFAULT '{}'::jsonb, -- {"message_count": 5, "emotion_spike": 2, ...}
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Global memory configuration (default settings)
CREATE TABLE IF NOT EXISTS memory_global_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode VARCHAR(20) NOT NULL DEFAULT 'cache_first',
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_by UUID, -- Admin who set this
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add memory_mode column to chat_sessions for quick access
ALTER TABLE chat_sessions 
ADD COLUMN IF NOT EXISTS memory_mode VARCHAR(20) DEFAULT 'cache_first';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_memory_configs_session_id ON memory_configs(session_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_memory_configs_mode ON memory_configs(mode);
CREATE INDEX IF NOT EXISTS idx_memory_metrics_session_id ON memory_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_metrics_started_at ON memory_metrics(started_at);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_memory_mode ON chat_sessions(memory_mode);

-- Create triggers for updated_at
CREATE TRIGGER update_memory_configs_updated_at 
    BEFORE UPDATE ON memory_configs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memory_global_config_updated_at 
    BEFORE UPDATE ON memory_global_config 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default global configuration
INSERT INTO memory_global_config (mode, config, is_active) 
VALUES (
    'cache_first',
    '{
        "cache_ttl": 1800,
        "max_context_tokens": 2000,
        "max_memories_per_retrieval": 10,
        "save_on_session_end": true,
        "triggers": {
            "message_count": {"enabled": true, "threshold": 5},
            "time_elapsed": {"enabled": true, "minutes": 15},
            "agent_transfer": {"enabled": true},
            "emotion_spike": {"enabled": true},
            "topic_change": {"enabled": false},
            "important_info": {"enabled": true}
        }
    }'::jsonb,
    true
) ON CONFLICT DO NOTHING;

-- View for active memory configurations with metrics
CREATE OR REPLACE VIEW active_memory_sessions AS
SELECT 
    cs.id as session_id,
    cs.user_id,
    cs.memory_mode,
    mc.config as custom_config,
    mm.retrieval_count,
    mm.cache_hits,
    mm.cache_misses,
    CASE 
        WHEN (mm.cache_hits + mm.cache_misses) > 0 
        THEN ROUND(mm.cache_hits::numeric / (mm.cache_hits + mm.cache_misses) * 100, 2)
        ELSE 0
    END as cache_hit_rate,
    mm.total_cost,
    mm.avg_retrieval_time_ms,
    mm.triggers_fired,
    cs.created_at as session_start,
    mm.last_updated as last_activity
FROM chat_sessions cs
LEFT JOIN memory_configs mc ON cs.id = mc.session_id AND mc.is_active = true
LEFT JOIN memory_metrics mm ON cs.id = mm.session_id
WHERE cs.ended_at IS NULL;

-- Function to get memory config for a session (with fallback to global)
CREATE OR REPLACE FUNCTION get_session_memory_config(p_session_id UUID)
RETURNS JSONB AS $$
DECLARE
    session_config JSONB;
    global_config JSONB;
BEGIN
    -- Try to get session-specific config
    SELECT config INTO session_config
    FROM memory_configs
    WHERE session_id = p_session_id AND is_active = true
    LIMIT 1;
    
    IF session_config IS NOT NULL THEN
        RETURN session_config;
    END IF;
    
    -- Fallback to global config
    SELECT config INTO global_config
    FROM memory_global_config
    WHERE is_active = true
    ORDER BY created_at DESC
    LIMIT 1;
    
    RETURN COALESCE(global_config, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Function to update memory metrics
CREATE OR REPLACE FUNCTION update_memory_metrics(
    p_session_id UUID,
    p_operation VARCHAR,
    p_value INTEGER DEFAULT 1,
    p_cost DECIMAL DEFAULT 0,
    p_time_ms FLOAT DEFAULT 0
) RETURNS void AS $$
BEGIN
    -- Insert or update metrics
    INSERT INTO memory_metrics (session_id, mode, retrieval_count, cache_hits, cache_misses)
    SELECT 
        p_session_id,
        COALESCE(cs.memory_mode, 'cache_first'),
        0, 0, 0
    FROM chat_sessions cs
    WHERE cs.id = p_session_id
    ON CONFLICT (session_id) DO NOTHING;
    
    -- Update based on operation type
    CASE p_operation
        WHEN 'retrieval' THEN
            UPDATE memory_metrics 
            SET 
                retrieval_count = retrieval_count + 1,
                total_tokens_retrieved = total_tokens_retrieved + p_value,
                total_cost = total_cost + p_cost,
                avg_retrieval_time_ms = 
                    CASE 
                        WHEN retrieval_count = 0 THEN p_time_ms
                        ELSE (avg_retrieval_time_ms * retrieval_count + p_time_ms) / (retrieval_count + 1)
                    END,
                last_updated = NOW()
            WHERE session_id = p_session_id;
            
        WHEN 'cache_hit' THEN
            UPDATE memory_metrics 
            SET 
                cache_hits = cache_hits + 1,
                last_updated = NOW()
            WHERE session_id = p_session_id;
            
        WHEN 'cache_miss' THEN
            UPDATE memory_metrics 
            SET 
                cache_misses = cache_misses + 1,
                last_updated = NOW()
            WHERE session_id = p_session_id;
            
        WHEN 'trigger' THEN
            UPDATE memory_metrics 
            SET 
                triggers_fired = jsonb_set(
                    triggers_fired,
                    ARRAY[p_value::text],
                    COALESCE(triggers_fired->p_value::text, '0')::int + 1::text::jsonb
                ),
                last_updated = NOW()
            WHERE session_id = p_session_id;
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust based on your user setup)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;