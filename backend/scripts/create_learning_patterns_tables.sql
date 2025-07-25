-- Create Learning Patterns Tables
-- This script creates the learning pattern tables for the AI learning system

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create mapping_learning_patterns table
CREATE TABLE IF NOT EXISTS migration.mapping_learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id VARCHAR(255) NOT NULL,
    engagement_id VARCHAR(255),

    -- Source field information
    source_field_name VARCHAR(255) NOT NULL,
    source_field_embedding VECTOR(1536) NOT NULL,
    source_sample_values JSONB,
    source_sample_embedding VECTOR(1536),

    -- Target field information
    target_field_name VARCHAR(255) NOT NULL,
    target_field_type VARCHAR(100),

    -- Pattern metadata
    pattern_context JSONB,
    confidence_score FLOAT DEFAULT 0.0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Learning metadata
    learned_from_user BOOLEAN DEFAULT TRUE,
    learning_source VARCHAR(100),

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255)
);

-- Create indexes for mapping_learning_patterns
CREATE INDEX IF NOT EXISTS idx_mapping_patterns_client_source
    ON migration.mapping_learning_patterns(client_account_id, source_field_name);
CREATE INDEX IF NOT EXISTS idx_mapping_patterns_target
    ON migration.mapping_learning_patterns(target_field_name);
CREATE INDEX IF NOT EXISTS idx_mapping_patterns_confidence
    ON migration.mapping_learning_patterns(confidence_score);
CREATE INDEX IF NOT EXISTS idx_mapping_patterns_embedding
    ON migration.mapping_learning_patterns USING ivfflat (source_field_embedding vector_cosine_ops);

-- Create asset_classification_patterns table
CREATE TABLE IF NOT EXISTS migration.asset_classification_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id VARCHAR(255) NOT NULL,
    engagement_id VARCHAR(255),

    -- Pattern information
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100) NOT NULL,

    -- Asset name pattern
    asset_name_pattern VARCHAR(500),
    asset_name_embedding VECTOR(1536),

    -- Metadata patterns
    metadata_patterns JSONB,
    metadata_embedding VECTOR(1536),

    -- Classification results
    predicted_asset_type VARCHAR(100) NOT NULL,
    predicted_application_type VARCHAR(100),
    predicted_technology_stack JSONB,

    -- Pattern performance
    confidence_score FLOAT DEFAULT 0.0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    accuracy_rate FLOAT DEFAULT 0.0,

    -- Learning metadata
    learned_from_assets JSONB,
    learning_source VARCHAR(100),
    last_applied_at TIMESTAMP WITH TIME ZONE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255)
);

-- Create indexes for asset_classification_patterns
CREATE INDEX IF NOT EXISTS idx_classification_patterns_client_type
    ON migration.asset_classification_patterns(client_account_id, pattern_type);
CREATE INDEX IF NOT EXISTS idx_classification_patterns_asset_type
    ON migration.asset_classification_patterns(predicted_asset_type);
CREATE INDEX IF NOT EXISTS idx_classification_patterns_confidence
    ON migration.asset_classification_patterns(confidence_score);
CREATE INDEX IF NOT EXISTS idx_classification_patterns_name_embedding
    ON migration.asset_classification_patterns USING ivfflat (asset_name_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_classification_patterns_metadata_embedding
    ON migration.asset_classification_patterns USING ivfflat (metadata_embedding vector_cosine_ops);

-- Create confidence_thresholds table
CREATE TABLE IF NOT EXISTS migration.confidence_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id VARCHAR(255) NOT NULL,
    engagement_id VARCHAR(255),

    -- Threshold configuration
    operation_type VARCHAR(100) NOT NULL,
    threshold_name VARCHAR(100) NOT NULL,
    threshold_value FLOAT NOT NULL,

    -- Adaptation metadata
    initial_value FLOAT NOT NULL,
    adjustment_count INTEGER DEFAULT 0,
    last_adjustment TIMESTAMP WITH TIME ZONE,

    -- Performance tracking
    true_positives INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    true_negatives INTEGER DEFAULT 0,
    false_negatives INTEGER DEFAULT 0,

    -- Calculated metrics
    precision FLOAT DEFAULT 0.0,
    recall FLOAT DEFAULT 0.0,
    f1_score FLOAT DEFAULT 0.0,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255)
);

-- Create indexes for confidence_thresholds
CREATE INDEX IF NOT EXISTS idx_confidence_thresholds_client_operation
    ON migration.confidence_thresholds(client_account_id, operation_type);
CREATE INDEX IF NOT EXISTS idx_confidence_thresholds_operation_name
    ON migration.confidence_thresholds(operation_type, threshold_name);

-- Create user_feedback_events table
CREATE TABLE IF NOT EXISTS migration.user_feedback_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id VARCHAR(255) NOT NULL,
    engagement_id VARCHAR(255),

    -- Feedback context
    feedback_type VARCHAR(100) NOT NULL,
    operation_id VARCHAR(255),

    -- Original suggestion
    original_suggestion JSONB NOT NULL,
    original_confidence FLOAT,

    -- User correction
    user_correction JSONB NOT NULL,
    correction_type VARCHAR(100) NOT NULL,

    -- Pattern references
    related_patterns JSONB,

    -- Learning impact
    pattern_updates_applied BOOLEAN DEFAULT FALSE,
    threshold_updates_applied BOOLEAN DEFAULT FALSE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255)
);

-- Create indexes for user_feedback_events
CREATE INDEX IF NOT EXISTS idx_feedback_events_client_type
    ON migration.user_feedback_events(client_account_id, feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_events_operation
    ON migration.user_feedback_events(operation_id);
CREATE INDEX IF NOT EXISTS idx_feedback_events_created
    ON migration.user_feedback_events(created_at);

-- Create learning_statistics table
CREATE TABLE IF NOT EXISTS migration.learning_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id VARCHAR(255) NOT NULL,
    engagement_id VARCHAR(255),

    -- Statistics scope
    statistic_type VARCHAR(100) NOT NULL,
    time_period VARCHAR(50) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Performance metrics
    total_operations INTEGER DEFAULT 0,
    successful_operations INTEGER DEFAULT 0,
    failed_operations INTEGER DEFAULT 0,
    user_corrections INTEGER DEFAULT 0,

    -- Accuracy metrics
    accuracy_rate FLOAT DEFAULT 0.0,
    improvement_rate FLOAT DEFAULT 0.0,

    -- Pattern metrics
    patterns_created INTEGER DEFAULT 0,
    patterns_updated INTEGER DEFAULT 0,
    patterns_retired INTEGER DEFAULT 0,

    -- Confidence metrics
    average_confidence FLOAT DEFAULT 0.0,
    threshold_adjustments INTEGER DEFAULT 0,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for learning_statistics
CREATE INDEX IF NOT EXISTS idx_learning_stats_client_type_period
    ON migration.learning_statistics(client_account_id, statistic_type, time_period);
CREATE INDEX IF NOT EXISTS idx_learning_stats_period_start
    ON migration.learning_statistics(period_start);

-- Insert default confidence thresholds for common operations
INSERT INTO migration.confidence_thresholds (
    client_account_id, operation_type, threshold_name, threshold_value, initial_value
) VALUES
    ('default', 'field_mapping', 'auto_apply', 0.9, 0.9),
    ('default', 'field_mapping', 'suggest', 0.6, 0.6),
    ('default', 'field_mapping', 'reject', 0.3, 0.3),
    ('default', 'asset_classification', 'auto_apply', 0.85, 0.85),
    ('default', 'asset_classification', 'suggest', 0.6, 0.6),
    ('default', 'asset_classification', 'reject', 0.3, 0.3),
    ('default', 'app_detection', 'auto_apply', 0.8, 0.8),
    ('default', 'app_detection', 'suggest', 0.5, 0.5),
    ('default', 'app_detection', 'reject', 0.2, 0.2)
ON CONFLICT DO NOTHING;

-- Print success message
SELECT 'Learning patterns tables created successfully!' as result;
