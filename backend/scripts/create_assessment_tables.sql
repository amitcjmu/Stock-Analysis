-- Create Assessment Flow Tables in migration schema
SET search_path TO migration, public;

-- 1. Main assessment_flows table
CREATE TABLE IF NOT EXISTS assessment_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    selected_application_ids JSONB NOT NULL,
    architecture_captured BOOLEAN DEFAULT FALSE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'initialized',
    progress INTEGER DEFAULT 0 NOT NULL,
    current_phase VARCHAR(100),
    next_phase VARCHAR(100),
    pause_points JSONB DEFAULT '[]'::jsonb NOT NULL,
    user_inputs JSONB DEFAULT '{}'::jsonb NOT NULL,
    phase_results JSONB DEFAULT '{}'::jsonb NOT NULL,
    agent_insights JSONB DEFAULT '[]'::jsonb NOT NULL,
    apps_ready_for_planning JSONB DEFAULT '[]'::jsonb NOT NULL,
    last_user_interaction TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
);

-- Indexes for assessment_flows
CREATE INDEX IF NOT EXISTS idx_assessment_flows_client_account_id ON assessment_flows(client_account_id);
CREATE INDEX IF NOT EXISTS idx_assessment_flows_engagement_id ON assessment_flows(engagement_id);
CREATE INDEX IF NOT EXISTS idx_assessment_flows_status ON assessment_flows(status);
CREATE INDEX IF NOT EXISTS idx_assessment_flows_current_phase ON assessment_flows(current_phase);
CREATE INDEX IF NOT EXISTS idx_assessment_flows_selected_apps ON assessment_flows USING GIN(selected_application_ids);

-- 2. engagement_architecture_standards table
CREATE TABLE IF NOT EXISTS engagement_architecture_standards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id UUID NOT NULL,
    requirement_type VARCHAR(100) NOT NULL,
    description TEXT,
    mandatory BOOLEAN DEFAULT TRUE NOT NULL,
    supported_versions JSONB,
    requirement_details JSONB,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unique_engagement_requirement UNIQUE (engagement_id, requirement_type)
);

-- Index for engagement_architecture_standards
CREATE INDEX IF NOT EXISTS idx_engagement_architecture_standards_engagement_id ON engagement_architecture_standards(engagement_id);

-- 3. application_architecture_overrides table
CREATE TABLE IF NOT EXISTS application_architecture_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID NOT NULL REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    standard_id UUID REFERENCES engagement_architecture_standards(id) ON DELETE SET NULL,
    override_type VARCHAR(100) NOT NULL,
    override_details JSONB,
    rationale TEXT,
    approved_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_override_type CHECK (override_type IN ('exception', 'modification', 'addition'))
);

-- Indexes for application_architecture_overrides
CREATE INDEX IF NOT EXISTS idx_application_architecture_overrides_assessment_flow_id ON application_architecture_overrides(assessment_flow_id);
CREATE INDEX IF NOT EXISTS idx_application_architecture_overrides_application_id ON application_architecture_overrides(application_id);

-- 4. application_components table
CREATE TABLE IF NOT EXISTS application_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID NOT NULL REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    component_name VARCHAR(255) NOT NULL,
    component_type VARCHAR(100) NOT NULL,
    technology_stack JSONB,
    dependencies JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unique_app_component UNIQUE (assessment_flow_id, application_id, component_name)
);

-- Indexes for application_components
CREATE INDEX IF NOT EXISTS idx_application_components_assessment_flow_id ON application_components(assessment_flow_id);
CREATE INDEX IF NOT EXISTS idx_application_components_application_id ON application_components(application_id);
CREATE INDEX IF NOT EXISTS idx_application_components_technology ON application_components USING GIN(technology_stack);

-- 5. tech_debt_analysis table
CREATE TABLE IF NOT EXISTS tech_debt_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID NOT NULL REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    component_id UUID REFERENCES application_components(id) ON DELETE SET NULL,
    debt_category VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    remediation_effort_hours INTEGER,
    impact_on_migration TEXT,
    tech_debt_score FLOAT,
    detected_by_agent VARCHAR(100),
    agent_confidence FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_severity CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    CONSTRAINT valid_agent_confidence CHECK (agent_confidence >= 0 AND agent_confidence <= 1)
);

-- Indexes for tech_debt_analysis
CREATE INDEX IF NOT EXISTS idx_tech_debt_analysis_assessment_flow_id ON tech_debt_analysis(assessment_flow_id);
CREATE INDEX IF NOT EXISTS idx_tech_debt_analysis_application_id ON tech_debt_analysis(application_id);
CREATE INDEX IF NOT EXISTS idx_tech_debt_analysis_severity ON tech_debt_analysis(severity);

-- 6. component_treatments table
CREATE TABLE IF NOT EXISTS component_treatments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID NOT NULL REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    component_id UUID REFERENCES application_components(id) ON DELETE CASCADE,
    recommended_strategy VARCHAR(20) NOT NULL,
    rationale TEXT,
    compatibility_validated BOOLEAN DEFAULT FALSE NOT NULL,
    compatibility_issues JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_recommended_strategy CHECK (recommended_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')),
    CONSTRAINT unique_component_treatment UNIQUE (assessment_flow_id, component_id)
);

-- Indexes for component_treatments
CREATE INDEX IF NOT EXISTS idx_component_treatments_assessment_flow_id ON component_treatments(assessment_flow_id);
CREATE INDEX IF NOT EXISTS idx_component_treatments_recommended_strategy ON component_treatments(recommended_strategy);

-- 7. sixr_decisions table
CREATE TABLE IF NOT EXISTS sixr_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID NOT NULL REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    application_name VARCHAR(255) NOT NULL,
    overall_strategy VARCHAR(20) NOT NULL,
    confidence_score FLOAT,
    rationale TEXT,
    architecture_exceptions JSONB DEFAULT '[]'::jsonb NOT NULL,
    tech_debt_score FLOAT,
    risk_factors JSONB DEFAULT '[]'::jsonb NOT NULL,
    move_group_hints JSONB DEFAULT '[]'::jsonb NOT NULL,
    estimated_effort_hours INTEGER,
    estimated_cost NUMERIC(12, 2),
    user_modifications JSONB,
    modified_by VARCHAR(100),
    modified_at TIMESTAMP WITH TIME ZONE,
    app_on_page_data JSONB,
    decision_factors JSONB,
    ready_for_planning BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_overall_strategy CHECK (overall_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')),
    CONSTRAINT valid_confidence_score CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT unique_app_decision UNIQUE (assessment_flow_id, application_id)
);

-- Indexes for sixr_decisions
CREATE INDEX IF NOT EXISTS idx_sixr_decisions_assessment_flow_id ON sixr_decisions(assessment_flow_id);
CREATE INDEX IF NOT EXISTS idx_sixr_decisions_overall_strategy ON sixr_decisions(overall_strategy);
CREATE INDEX IF NOT EXISTS idx_sixr_decisions_ready_for_planning ON sixr_decisions(ready_for_planning);

-- 8. assessment_learning_feedback table
CREATE TABLE IF NOT EXISTS assessment_learning_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID NOT NULL REFERENCES assessment_flows(id) ON DELETE CASCADE,
    decision_id UUID NOT NULL REFERENCES sixr_decisions(id) ON DELETE CASCADE,
    original_strategy VARCHAR(20) NOT NULL,
    override_strategy VARCHAR(20) NOT NULL,
    feedback_reason TEXT,
    agent_id VARCHAR(100),
    learned_pattern JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_original_strategy CHECK (original_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')),
    CONSTRAINT valid_override_strategy CHECK (override_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain'))
);

-- Indexes for assessment_learning_feedback
CREATE INDEX IF NOT EXISTS idx_assessment_learning_feedback_assessment_flow_id ON assessment_learning_feedback(assessment_flow_id);
CREATE INDEX IF NOT EXISTS idx_assessment_learning_feedback_decision_id ON assessment_learning_feedback(decision_id);

-- Add update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at columns
CREATE TRIGGER update_assessment_flows_updated_at BEFORE UPDATE ON assessment_flows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_engagement_architecture_standards_updated_at BEFORE UPDATE ON engagement_architecture_standards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sixr_decisions_updated_at BEFORE UPDATE ON sixr_decisions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA migration TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA migration TO postgres;