# Database Schema Changes for Asset Enrichment

## Overview

This document details the database schema changes required to support intelligent asset enrichment. The changes extend the existing asset table with enrichment-specific fields while maintaining backward compatibility.

## Extended Asset Table Schema

### **Core Enrichment Fields**

```sql
-- Extend existing assets table with enrichment capabilities
ALTER TABLE assets ADD COLUMN IF NOT EXISTS asset_subtype VARCHAR(50);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS application_version VARCHAR(50);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS end_of_support_date DATE;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS data_classification VARCHAR(20);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS compliance_requirements JSONB DEFAULT '[]';
ALTER TABLE assets ADD COLUMN IF NOT EXISTS availability_requirement VARCHAR(10);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS container_ready BOOLEAN DEFAULT FALSE;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS api_maturity_level VARCHAR(20);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS middleware_stack JSONB DEFAULT '{}';
ALTER TABLE assets ADD COLUMN IF NOT EXISTS database_type VARCHAR(50);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS business_value_score INTEGER CHECK (business_value_score >= 1 AND business_value_score <= 10);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS license_info JSONB DEFAULT '{}';
ALTER TABLE assets ADD COLUMN IF NOT EXISTS security_profile JSONB DEFAULT '{}';

-- Enrichment metadata
ALTER TABLE assets ADD COLUMN IF NOT EXISTS enrichment_status VARCHAR(20) DEFAULT 'basic' CHECK (enrichment_status IN ('basic', 'enhanced', 'complete'));
ALTER TABLE assets ADD COLUMN IF NOT EXISTS enrichment_score INTEGER DEFAULT 0 CHECK (enrichment_score >= 0 AND enrichment_score <= 100);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS ai_confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (ai_confidence_score >= 0.0 AND ai_confidence_score <= 1.0);
ALTER TABLE assets ADD COLUMN IF NOT EXISTS user_reviewed_fields JSONB DEFAULT '[]';
ALTER TABLE assets ADD COLUMN IF NOT EXISTS enrichment_timestamp TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE assets ADD COLUMN IF NOT EXISTS last_enrichment_attempt TIMESTAMPTZ;
```

### **Asset Subtype Enumerations**

```sql
-- Create enum types for common subtypes
CREATE TYPE asset_subtype_enum AS ENUM (
    -- Server subtypes
    'web_server', 'application_server', 'database_server', 
    'file_server', 'mail_server', 'dns_server', 'dhcp_server',
    'load_balancer', 'proxy_server', 'backup_server',
    
    -- Application subtypes  
    'web_application', 'desktop_application', 'mobile_application',
    'api_service', 'microservice', 'batch_process', 'workflow_engine',
    'reporting_tool', 'monitoring_tool', 'security_tool',
    
    -- Database subtypes
    'relational_database', 'nosql_database', 'data_warehouse',
    'cache_database', 'search_database', 'time_series_database',
    
    -- Network device subtypes
    'router', 'switch', 'firewall', 'wireless_access_point',
    'vpn_gateway', 'network_attached_storage'
);

-- Data classification levels
CREATE TYPE data_classification_enum AS ENUM (
    'public', 'internal', 'confidential', 'restricted'
);

-- API maturity levels
CREATE TYPE api_maturity_enum AS ENUM (
    'none', 'legacy', 'soap', 'rest', 'graphql', 'grpc'
);
```

## New Enrichment Support Tables

### **1. Asset Enrichment History**

```sql
CREATE TABLE asset_enrichment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    enrichment_phase VARCHAR(50) NOT NULL, -- 'classification', 'business_context', 'risk_assessment'
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    confidence_score DECIMAL(3,2),
    source VARCHAR(50) NOT NULL, -- 'ai_analysis', 'user_input', 'pattern_matching'
    user_id UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(asset_id, enrichment_phase, field_name, created_at)
);

CREATE INDEX idx_enrichment_history_asset_id ON asset_enrichment_history(asset_id);
CREATE INDEX idx_enrichment_history_phase ON asset_enrichment_history(enrichment_phase);
CREATE INDEX idx_enrichment_history_created_at ON asset_enrichment_history(created_at);
```

### **2. Agent Question Templates**

```sql
CREATE TABLE agent_question_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_type VARCHAR(50) NOT NULL, -- 'asset_classification', 'business_value', 'compliance'
    template_name VARCHAR(100) NOT NULL,
    question_template TEXT NOT NULL,
    options_template JSONB, -- Array of option templates
    context_requirements JSONB NOT NULL, -- Required context fields
    priority_level VARCHAR(10) DEFAULT 'medium',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO agent_question_templates (question_type, template_name, question_template, options_template, context_requirements) VALUES
('asset_classification', 'hostname_classification', 
 'Based on hostname ''{hostname}'' and system analysis, what type of asset is this?',
 '["Web Server", "Application Server", "Database Server", "Load Balancer", "Network Device", "Storage System", "Other"]',
 '{"required": ["hostname"], "optional": ["operating_system", "detected_ports"]}'),
 
('business_value', 'application_criticality',
 'How critical is ''{application_name}'' to business operations?',
 '["Low (1-3) - Internal tools, development systems", "Medium (4-6) - Supporting business operations", "High (7-8) - Important business functions", "Critical (9-10) - Revenue generating, customer-facing"]',
 '{"required": ["application_name"], "optional": ["detected_integrations", "business_indicators"]}'),
 
('compliance_requirement', 'data_compliance',
 'What compliance requirements apply to ''{asset_name}''?',
 '["PCI-DSS (Payment card data)", "HIPAA (Health information)", "SOX (Financial reporting)", "GDPR (EU personal data)", "None/Internal use only", "Multiple (please specify in follow-up)"]',
 '{"required": ["asset_name"], "optional": ["asset_type", "detected_data_types"]}');
```

### **3. Enrichment Pattern Learning**

```sql
CREATE TABLE enrichment_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(50) NOT NULL, -- 'hostname', 'application_name', 'port_analysis'
    pattern_value VARCHAR(255) NOT NULL,
    suggested_classification VARCHAR(100),
    confidence_weight DECIMAL(3,2) DEFAULT 0.5,
    success_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    last_used TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(pattern_type, pattern_value, suggested_classification)
);

CREATE INDEX idx_enrichment_patterns_type ON enrichment_patterns(pattern_type);
CREATE INDEX idx_enrichment_patterns_confidence ON enrichment_patterns(confidence_weight DESC);

-- Seed data for common patterns
INSERT INTO enrichment_patterns (pattern_type, pattern_value, suggested_classification, confidence_weight) VALUES
('hostname', 'web%', 'web_server', 0.85),
('hostname', 'app%', 'application_server', 0.80),
('hostname', 'db%', 'database_server', 0.90),
('hostname', '%sql%', 'database_server', 0.85),
('hostname', 'lb%', 'load_balancer', 0.88),
('application_name', '%portal%', 'web_application', 0.75),
('application_name', '%api%', 'api_service', 0.80),
('application_name', '%payment%', 'high_business_value', 0.85),
('port_analysis', '80,443', 'web_server', 0.90),
('port_analysis', '3306', 'database_server', 0.95),
('port_analysis', '1433', 'database_server', 0.95),
('port_analysis', '5432', 'database_server', 0.95);
```

## Enhanced Flow State Management

### **Flow Enrichment Status**

```sql
CREATE TABLE flow_enrichment_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID NOT NULL REFERENCES discovery_flows(id) ON DELETE CASCADE,
    phase VARCHAR(50) NOT NULL, -- 'classification', 'business_context', 'risk_assessment'
    total_assets INTEGER NOT NULL DEFAULT 0,
    enriched_assets INTEGER NOT NULL DEFAULT 0,
    pending_questions INTEGER NOT NULL DEFAULT 0,
    completion_percentage INTEGER GENERATED ALWAYS AS (
        CASE WHEN total_assets = 0 THEN 0 
        ELSE (enriched_assets * 100) / total_assets 
        END
    ) STORED,
    can_proceed BOOLEAN DEFAULT FALSE,
    blockers JSONB DEFAULT '[]',
    estimated_completion_minutes INTEGER,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(flow_id, phase)
);

CREATE INDEX idx_flow_enrichment_flow_id ON flow_enrichment_status(flow_id);
CREATE INDEX idx_flow_enrichment_phase ON flow_enrichment_status(phase);
```

## Indexes for Performance

### **Enrichment-Specific Indexes**

```sql
-- Asset enrichment status lookups
CREATE INDEX idx_assets_enrichment_status ON assets(enrichment_status);
CREATE INDEX idx_assets_enrichment_score ON assets(enrichment_score DESC);
CREATE INDEX idx_assets_business_value ON assets(business_value_score DESC) WHERE business_value_score IS NOT NULL;

-- Asset classification queries
CREATE INDEX idx_assets_subtype ON assets(asset_type, asset_subtype) WHERE asset_subtype IS NOT NULL;
CREATE INDEX idx_assets_compliance ON assets USING GIN(compliance_requirements) WHERE compliance_requirements != '[]';

-- Flow-based asset queries  
CREATE INDEX idx_assets_flow_enrichment ON assets(flow_id, enrichment_status);

-- Performance optimization for large datasets
CREATE INDEX idx_assets_enrichment_timestamp ON assets(enrichment_timestamp DESC) WHERE enrichment_timestamp IS NOT NULL;
```

### **Compound Indexes for Common Queries**

```sql
-- Flow assets with enrichment status
CREATE INDEX idx_assets_flow_enrichment_complete ON assets(flow_id, enrichment_status, asset_type) 
WHERE enrichment_status IN ('enhanced', 'complete');

-- Business critical assets
CREATE INDEX idx_assets_business_critical ON assets(business_value_score, availability_requirement) 
WHERE business_value_score >= 8;

-- Compliance-sensitive assets
CREATE INDEX idx_assets_compliance_data_classification ON assets(data_classification) 
WHERE data_classification IN ('confidential', 'restricted');
```

## Data Migration Strategy

### **Migration Script Template**

```sql
-- Migration: Add enrichment fields to existing assets
-- Version: 001_add_asset_enrichment_fields.sql

BEGIN;

-- Add enrichment fields (already shown above)

-- Set default enrichment status based on existing data completeness
UPDATE assets SET 
    enrichment_status = CASE 
        WHEN asset_type IS NOT NULL AND hostname IS NOT NULL THEN 'enhanced'
        WHEN asset_type IS NOT NULL THEN 'basic'
        ELSE 'basic'
    END,
    enrichment_score = CASE
        WHEN asset_type IS NOT NULL AND hostname IS NOT NULL THEN 60
        WHEN asset_type IS NOT NULL THEN 30
        ELSE 10
    END,
    enrichment_timestamp = NOW()
WHERE enrichment_status IS NULL;

-- Initialize flow enrichment status for existing flows
INSERT INTO flow_enrichment_status (flow_id, phase, total_assets, enriched_assets)
SELECT 
    df.id as flow_id,
    phase.phase_name,
    COUNT(a.id) as total_assets,
    COUNT(CASE WHEN a.enrichment_status != 'basic' THEN 1 END) as enriched_assets
FROM discovery_flows df
CROSS JOIN (VALUES ('classification'), ('business_context'), ('risk_assessment')) AS phase(phase_name)
LEFT JOIN assets a ON a.flow_id = df.id
WHERE df.status = 'active'
GROUP BY df.id, phase.phase_name
ON CONFLICT (flow_id, phase) DO NOTHING;

COMMIT;
```

## Data Validation and Constraints

### **Enrichment Validation Functions**

```sql
-- Validate enrichment completeness
CREATE OR REPLACE FUNCTION validate_enrichment_completeness(asset_row assets)
RETURNS INTEGER AS $$
DECLARE
    score INTEGER := 0;
    required_fields TEXT[];
BEGIN
    -- Base score for having asset_type
    IF asset_row.asset_type IS NOT NULL THEN
        score := score + 20;
    END IF;
    
    -- Asset subtype adds detail
    IF asset_row.asset_subtype IS NOT NULL THEN
        score := score + 15;
    END IF;
    
    -- Business context fields
    IF asset_row.business_value_score IS NOT NULL THEN
        score := score + 25;
    END IF;
    
    IF asset_row.availability_requirement IS NOT NULL THEN
        score := score + 20;
    END IF;
    
    -- Compliance and security
    IF asset_row.data_classification IS NOT NULL THEN
        score := score + 10;
    END IF;
    
    IF asset_row.compliance_requirements IS NOT NULL AND 
       jsonb_array_length(asset_row.compliance_requirements) > 0 THEN
        score := score + 10;
    END IF;
    
    RETURN LEAST(score, 100);
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update enrichment score
CREATE OR REPLACE FUNCTION update_enrichment_score_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.enrichment_score := validate_enrichment_completeness(NEW);
    NEW.enrichment_timestamp := NOW();
    
    -- Update enrichment status based on score
    NEW.enrichment_status := CASE
        WHEN NEW.enrichment_score >= 85 THEN 'complete'
        WHEN NEW.enrichment_score >= 60 THEN 'enhanced'  
        ELSE 'basic'
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_asset_enrichment_score
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_enrichment_score_trigger();
```

## Query Performance Optimization

### **Common Query Patterns**

```sql
-- Get assets needing enrichment for a specific phase
PREPARE get_assets_needing_enrichment(UUID, TEXT) AS
SELECT a.*, 
       validate_enrichment_completeness(a) as calculated_score
FROM assets a
WHERE a.flow_id = $1 
  AND (
    ($2 = 'classification' AND (a.asset_type IS NULL OR a.asset_subtype IS NULL)) OR
    ($2 = 'business_context' AND (a.business_value_score IS NULL OR a.availability_requirement IS NULL)) OR
    ($2 = 'risk_assessment' AND (a.data_classification IS NULL OR a.compliance_requirements = '[]'))
  )
ORDER BY a.business_value_score DESC NULLS LAST, a.name;

-- Get enrichment progress for flow dashboard
PREPARE get_flow_enrichment_progress(UUID) AS
SELECT 
    f.id as flow_id,
    f.status as flow_status,
    json_build_object(
        'overall_completion', AVG(fes.completion_percentage),
        'phase_status', json_object_agg(fes.phase, json_build_object(
            'completion_percentage', fes.completion_percentage,
            'can_proceed', fes.can_proceed,
            'pending_questions', fes.pending_questions,
            'blockers', fes.blockers
        ))
    ) as enrichment_status
FROM discovery_flows f
LEFT JOIN flow_enrichment_status fes ON fes.flow_id = f.id
WHERE f.id = $1
GROUP BY f.id, f.status;
```

### **Monitoring and Analytics Views**

```sql
-- Enrichment completion analytics
CREATE VIEW enrichment_analytics AS
SELECT 
    DATE_TRUNC('day', enrichment_timestamp) as date,
    enrichment_status,
    COUNT(*) as asset_count,
    AVG(enrichment_score) as avg_score,
    AVG(ai_confidence_score) as avg_confidence
FROM assets 
WHERE enrichment_timestamp IS NOT NULL
GROUP BY DATE_TRUNC('day', enrichment_timestamp), enrichment_status
ORDER BY date DESC;

-- Question effectiveness tracking
CREATE VIEW question_effectiveness AS
SELECT 
    qt.question_type,
    qt.template_name,
    COUNT(aeh.id) as times_used,
    AVG(aeh.confidence_score) as avg_confidence,
    COUNT(CASE WHEN aeh.source = 'user_input' THEN 1 END) as user_corrections
FROM agent_question_templates qt
LEFT JOIN asset_enrichment_history aeh ON aeh.field_name LIKE '%' || qt.question_type || '%'
GROUP BY qt.question_type, qt.template_name
ORDER BY times_used DESC;
```

---

*Next: [06_api_specifications.md](06_api_specifications.md)*