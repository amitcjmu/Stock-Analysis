--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8 (Debian 16.8-1.pgdg120+1)
-- Dumped by pg_dump version 16.8 (Debian 16.8-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: migration; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA migration;


ALTER SCHEMA migration OWNER TO postgres;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: access_audit_log; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.access_audit_log (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    action_type character varying(50) NOT NULL,
    resource_type character varying(50),
    resource_id character varying(255),
    client_account_id uuid,
    engagement_id uuid,
    result character varying(20) NOT NULL,
    reason text,
    ip_address character varying(45),
    user_agent text,
    details json DEFAULT '{}'::json,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE migration.access_audit_log OWNER TO postgres;

--
-- Name: agent_discovered_patterns; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.agent_discovered_patterns (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    pattern_type character varying(50) NOT NULL,
    pattern_name character varying(200) NOT NULL,
    pattern_description text,
    pattern_data jsonb NOT NULL,
    confidence_score double precision NOT NULL,
    evidence_count integer DEFAULT 1 NOT NULL,
    discovered_by_agent character varying(100) NOT NULL,
    discovery_context jsonb,
    flow_id uuid,
    times_referenced integer DEFAULT 0 NOT NULL,
    last_referenced_at timestamp with time zone,
    validation_status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    validated_by_user uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    CONSTRAINT agent_discovered_patterns_confidence_score_check CHECK (((confidence_score >= (0.0)::double precision) AND (confidence_score <= (1.0)::double precision)))
);


ALTER TABLE migration.agent_discovered_patterns OWNER TO postgres;

--
-- Name: alembic_version; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE migration.alembic_version OWNER TO postgres;

--
-- Name: application_architecture_overrides; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.application_architecture_overrides (
    id uuid NOT NULL,
    assessment_flow_id uuid NOT NULL,
    application_id uuid NOT NULL,
    standard_id uuid,
    override_type character varying(100) NOT NULL,
    override_details jsonb,
    rationale text,
    approved_by character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT valid_override_type CHECK (((override_type)::text = ANY ((ARRAY['exception'::character varying, 'modification'::character varying, 'addition'::character varying])::text[])))
);


ALTER TABLE migration.application_architecture_overrides OWNER TO postgres;

--
-- Name: application_components; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.application_components (
    id uuid NOT NULL,
    assessment_flow_id uuid NOT NULL,
    application_id uuid NOT NULL,
    component_name character varying(255) NOT NULL,
    component_type character varying(100) NOT NULL,
    technology_stack jsonb,
    dependencies jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE migration.application_components OWNER TO postgres;

--
-- Name: assessment_flows; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.assessment_flows (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    selected_application_ids jsonb NOT NULL,
    architecture_captured boolean NOT NULL,
    status character varying(50) NOT NULL,
    progress integer NOT NULL,
    current_phase character varying(100),
    next_phase character varying(100),
    pause_points jsonb NOT NULL,
    user_inputs jsonb NOT NULL,
    phase_results jsonb NOT NULL,
    agent_insights jsonb NOT NULL,
    apps_ready_for_planning jsonb NOT NULL,
    last_user_interaction timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    CONSTRAINT valid_progress CHECK (((progress >= 0) AND (progress <= 100)))
);


ALTER TABLE migration.assessment_flows OWNER TO postgres;

--
-- Name: assessment_learning_feedback; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.assessment_learning_feedback (
    id uuid NOT NULL,
    assessment_flow_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    original_strategy character varying(20) NOT NULL,
    override_strategy character varying(20) NOT NULL,
    feedback_reason text,
    agent_id character varying(100),
    learned_pattern jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT valid_original_strategy CHECK (((original_strategy)::text = ANY ((ARRAY['rewrite'::character varying, 'rearchitect'::character varying, 'refactor'::character varying, 'replatform'::character varying, 'rehost'::character varying, 'repurchase'::character varying, 'retire'::character varying, 'retain'::character varying])::text[]))),
    CONSTRAINT valid_override_strategy CHECK (((override_strategy)::text = ANY ((ARRAY['rewrite'::character varying, 'rearchitect'::character varying, 'refactor'::character varying, 'replatform'::character varying, 'rehost'::character varying, 'repurchase'::character varying, 'retire'::character varying, 'retain'::character varying])::text[])))
);


ALTER TABLE migration.assessment_learning_feedback OWNER TO postgres;

--
-- Name: assessments; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.assessments (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    migration_id uuid NOT NULL,
    asset_id uuid,
    assessment_type character varying(50) NOT NULL,
    status character varying(50) DEFAULT 'PENDING'::character varying,
    title character varying(255) NOT NULL,
    description text,
    overall_score double precision,
    risk_level character varying(20),
    confidence_level double precision,
    recommended_strategy character varying(50),
    alternative_strategies json,
    strategy_rationale text,
    current_cost double precision,
    estimated_migration_cost double precision,
    estimated_target_cost double precision,
    cost_savings_potential double precision,
    roi_months integer,
    identified_risks json,
    risk_mitigation json,
    blockers json,
    dependencies_impact json,
    technical_complexity character varying(20),
    compatibility_score double precision,
    modernization_opportunities json,
    performance_impact json,
    business_criticality character varying(20),
    downtime_requirements json,
    user_impact text,
    compliance_considerations json,
    ai_insights json,
    ai_confidence double precision,
    ai_model_version character varying(50),
    estimated_effort_hours integer,
    estimated_duration_days integer,
    recommended_wave integer,
    prerequisites json,
    assessor character varying(100),
    assessment_date timestamp with time zone DEFAULT now(),
    review_date timestamp with time zone,
    approval_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.assessments OWNER TO postgres;

--
-- Name: asset_dependencies; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.asset_dependencies (
    id uuid NOT NULL,
    asset_id uuid NOT NULL,
    depends_on_asset_id uuid NOT NULL,
    dependency_type character varying(50) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE migration.asset_dependencies OWNER TO postgres;

--
-- Name: asset_embeddings; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.asset_embeddings (
    id uuid NOT NULL,
    asset_id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    embedding text,
    source_text text,
    embedding_model character varying(100) DEFAULT 'text-embedding-ada-002'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.asset_embeddings OWNER TO postgres;

--
-- Name: asset_tags; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.asset_tags (
    id uuid NOT NULL,
    asset_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    confidence_score double precision,
    assigned_method character varying(50),
    assigned_by uuid,
    is_validated boolean DEFAULT false,
    validated_by uuid,
    validated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.asset_tags OWNER TO postgres;

--
-- Name: assets; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.assets (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    flow_id uuid,
    migration_id uuid,
    master_flow_id uuid,
    discovery_flow_id uuid,
    assessment_flow_id uuid,
    planning_flow_id uuid,
    execution_flow_id uuid,
    source_phase character varying(50) DEFAULT 'discovery'::character varying,
    current_phase character varying(50) DEFAULT 'discovery'::character varying,
    phase_context json DEFAULT '{}'::json,
    name character varying(255) NOT NULL,
    asset_name character varying(255),
    hostname character varying(255),
    asset_type character varying(50) NOT NULL,
    description text,
    ip_address character varying(45),
    fqdn character varying(255),
    mac_address character varying(17),
    environment character varying(50),
    location character varying(100),
    datacenter character varying(100),
    rack_location character varying(50),
    availability_zone character varying(50),
    operating_system character varying(100),
    os_version character varying(50),
    cpu_cores integer,
    memory_gb double precision,
    storage_gb double precision,
    business_owner character varying(255),
    technical_owner character varying(255),
    department character varying(100),
    application_name character varying(255),
    technology_stack character varying(255),
    criticality character varying(20),
    business_criticality character varying(20),
    custom_attributes json,
    six_r_strategy character varying(50),
    mapping_status character varying(20),
    migration_priority integer DEFAULT 5,
    migration_complexity character varying(20),
    migration_wave integer,
    sixr_ready character varying(50),
    status character varying(50) DEFAULT 'active'::character varying,
    migration_status character varying(50) DEFAULT 'DISCOVERED'::character varying,
    dependencies json,
    related_assets json,
    discovery_method character varying(50),
    discovery_source character varying(100),
    discovery_timestamp timestamp with time zone,
    cpu_utilization_percent double precision,
    memory_utilization_percent double precision,
    disk_iops double precision,
    network_throughput_mbps double precision,
    completeness_score double precision,
    quality_score double precision,
    current_monthly_cost double precision,
    estimated_cloud_cost double precision,
    imported_by uuid,
    imported_at timestamp with time zone,
    source_filename character varying(255),
    raw_data json,
    field_mappings_used json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    updated_by uuid,
    business_value_score integer,
    enrichment_status character varying(20) DEFAULT 'basic'::character varying,
    risk_assessment character varying(20),
    modernization_potential character varying(20),
    cloud_readiness_score integer,
    enrichment_reasoning text,
    last_enriched_at timestamp with time zone,
    last_enriched_by_agent character varying(100)
);


ALTER TABLE migration.assets OWNER TO postgres;

--
-- Name: client_access; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.client_access (
    id uuid NOT NULL,
    user_profile_id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    access_level character varying(20) NOT NULL,
    permissions json DEFAULT '{"can_view_data": true, "can_import_data": false, "can_export_data": false, "can_manage_engagements": false, "can_configure_client_settings": false, "can_manage_client_users": false}'::json,
    restricted_environments json DEFAULT '[]'::json,
    restricted_data_types json DEFAULT '[]'::json,
    granted_at timestamp with time zone DEFAULT now(),
    granted_by uuid NOT NULL,
    expires_at timestamp with time zone,
    is_active boolean DEFAULT true,
    last_accessed_at timestamp with time zone,
    access_count integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE migration.client_access OWNER TO postgres;

--
-- Name: client_accounts; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.client_accounts (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    industry character varying(100),
    company_size character varying(50),
    headquarters_location character varying(255),
    primary_contact_name character varying(255),
    primary_contact_email character varying(255),
    primary_contact_phone character varying(50),
    contact_email character varying(255),
    contact_phone character varying(50),
    address text,
    timezone character varying(50),
    subscription_tier character varying(50) DEFAULT 'standard'::character varying,
    billing_contact_email character varying(255),
    subscription_start_date timestamp with time zone,
    subscription_end_date timestamp with time zone,
    max_users integer,
    max_engagements integer,
    features_enabled json DEFAULT '{}'::json,
    agent_configuration json DEFAULT '{}'::json,
    storage_quota_gb integer,
    api_quota_monthly integer,
    settings json DEFAULT '{}'::json,
    branding json DEFAULT '{}'::json,
    business_objectives json DEFAULT '{"primary_goals": [], "timeframe": "", "success_metrics": [], "constraints": []}'::json,
    agent_preferences json DEFAULT '{"discovery_depth": "comprehensive", "automation_level": "assisted", "risk_tolerance": "moderate", "preferred_clouds": [], "compliance_requirements": [], "custom_rules": []}'::json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    is_active boolean DEFAULT true NOT NULL,
    it_guidelines json,
    decision_criteria json,
    created_by uuid
);


ALTER TABLE migration.client_accounts OWNER TO postgres;

--
-- Name: cmdb_sixr_analyses; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.cmdb_sixr_analyses (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    analysis_name character varying(255) NOT NULL,
    description text,
    status character varying(50) DEFAULT 'in_progress'::character varying,
    total_assets integer DEFAULT 0,
    rehost_count integer DEFAULT 0,
    replatform_count integer DEFAULT 0,
    refactor_count integer DEFAULT 0,
    rearchitect_count integer DEFAULT 0,
    retire_count integer DEFAULT 0,
    retain_count integer DEFAULT 0,
    total_current_cost double precision,
    total_estimated_cost double precision,
    potential_savings double precision,
    analysis_results json,
    recommendations json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid
);


ALTER TABLE migration.cmdb_sixr_analyses OWNER TO postgres;

--
-- Name: component_treatments; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.component_treatments (
    id uuid NOT NULL,
    assessment_flow_id uuid NOT NULL,
    application_id uuid NOT NULL,
    component_id uuid,
    recommended_strategy character varying(20) NOT NULL,
    rationale text,
    compatibility_validated boolean NOT NULL,
    compatibility_issues jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT valid_recommended_strategy CHECK (((recommended_strategy)::text = ANY ((ARRAY['rewrite'::character varying, 'rearchitect'::character varying, 'refactor'::character varying, 'replatform'::character varying, 'rehost'::character varying, 'repurchase'::character varying, 'retire'::character varying, 'retain'::character varying])::text[])))
);


ALTER TABLE migration.component_treatments OWNER TO postgres;

--
-- Name: crewai_flow_state_extensions; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.crewai_flow_state_extensions (
    id uuid NOT NULL,
    flow_id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    flow_type character varying(50) NOT NULL,
    flow_name character varying(255),
    flow_status character varying(50) DEFAULT 'initialized'::character varying NOT NULL,
    flow_configuration jsonb DEFAULT '{}'::jsonb NOT NULL,
    flow_persistence_data jsonb DEFAULT '{}'::jsonb NOT NULL,
    agent_collaboration_log jsonb DEFAULT '[]'::jsonb,
    memory_usage_metrics jsonb DEFAULT '{}'::jsonb,
    knowledge_base_analytics jsonb DEFAULT '{}'::jsonb,
    phase_execution_times jsonb DEFAULT '{}'::jsonb,
    agent_performance_metrics jsonb DEFAULT '{}'::jsonb,
    crew_coordination_analytics jsonb DEFAULT '{}'::jsonb,
    learning_patterns jsonb DEFAULT '[]'::jsonb,
    user_feedback_history jsonb DEFAULT '[]'::jsonb,
    adaptation_metrics jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    phase_transitions jsonb DEFAULT '[]'::jsonb,
    error_history jsonb DEFAULT '[]'::jsonb,
    retry_count integer DEFAULT 0 NOT NULL,
    parent_flow_id uuid,
    child_flow_ids jsonb DEFAULT '[]'::jsonb,
    flow_metadata jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT chk_retry_count_positive CHECK ((retry_count >= 0)),
    CONSTRAINT chk_valid_flow_status CHECK (((flow_status)::text = ANY ((ARRAY['initialized'::character varying, 'active'::character varying, 'processing'::character varying, 'paused'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying, 'waiting_for_approval'::character varying])::text[]))),
    CONSTRAINT chk_valid_flow_type CHECK (((flow_type)::text = ANY ((ARRAY['discovery'::character varying, 'assessment'::character varying, 'planning'::character varying, 'execution'::character varying, 'modernize'::character varying, 'finops'::character varying, 'observability'::character varying, 'decommission'::character varying])::text[])))
);


ALTER TABLE migration.crewai_flow_state_extensions OWNER TO postgres;

--
-- Name: COLUMN crewai_flow_state_extensions.phase_transitions; Type: COMMENT; Schema: migration; Owner: postgres
--

COMMENT ON COLUMN migration.crewai_flow_state_extensions.phase_transitions IS 'History of phase transitions with timestamps';


--
-- Name: COLUMN crewai_flow_state_extensions.error_history; Type: COMMENT; Schema: migration; Owner: postgres
--

COMMENT ON COLUMN migration.crewai_flow_state_extensions.error_history IS 'History of errors with recovery attempts';


--
-- Name: COLUMN crewai_flow_state_extensions.retry_count; Type: COMMENT; Schema: migration; Owner: postgres
--

COMMENT ON COLUMN migration.crewai_flow_state_extensions.retry_count IS 'Number of retry attempts for current phase';


--
-- Name: COLUMN crewai_flow_state_extensions.parent_flow_id; Type: COMMENT; Schema: migration; Owner: postgres
--

COMMENT ON COLUMN migration.crewai_flow_state_extensions.parent_flow_id IS 'Reference to parent flow for hierarchical flows';


--
-- Name: COLUMN crewai_flow_state_extensions.child_flow_ids; Type: COMMENT; Schema: migration; Owner: postgres
--

COMMENT ON COLUMN migration.crewai_flow_state_extensions.child_flow_ids IS 'List of child flow IDs for hierarchical flows';


--
-- Name: COLUMN crewai_flow_state_extensions.flow_metadata; Type: COMMENT; Schema: migration; Owner: postgres
--

COMMENT ON COLUMN migration.crewai_flow_state_extensions.flow_metadata IS 'Additional flow-specific metadata';


--
-- Name: custom_target_fields; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.custom_target_fields (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    field_name character varying NOT NULL,
    field_type character varying NOT NULL,
    description text,
    is_required boolean DEFAULT false,
    is_critical boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    created_by uuid,
    validation_schema json,
    default_value character varying,
    allowed_values json
);


ALTER TABLE migration.custom_target_fields OWNER TO postgres;

--
-- Name: data_import_sessions; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.data_import_sessions (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    session_name character varying(255) NOT NULL,
    session_display_name character varying(255),
    description text,
    is_default boolean DEFAULT false NOT NULL,
    parent_session_id uuid,
    session_type character varying(50) DEFAULT 'DATA_IMPORT'::character varying NOT NULL,
    auto_created boolean DEFAULT true NOT NULL,
    source_filename character varying(255),
    status character varying(20) DEFAULT 'ACTIVE'::character varying NOT NULL,
    progress_percentage integer DEFAULT 0,
    total_imports integer DEFAULT 0,
    total_assets_processed integer DEFAULT 0,
    total_records_imported integer DEFAULT 0,
    data_quality_score integer DEFAULT 0,
    session_config json DEFAULT '{"deduplication_strategy": "engagement_level", "quality_thresholds": {"minimum_completeness": 0.7, "minimum_accuracy": 0.8}, "processing_preferences": {"auto_classify": true, "auto_deduplicate": true, "require_manual_review": false}}'::json,
    business_context json DEFAULT '{"import_purpose": "", "data_source_description": "", "expected_changes": [], "validation_notes": []}'::json,
    agent_insights json DEFAULT '{"classification_confidence": 0.0, "data_quality_issues": [], "recommendations": [], "learning_outcomes": []}'::json,
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    last_activity_at timestamp with time zone DEFAULT now(),
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.data_import_sessions OWNER TO postgres;

--
-- Name: data_imports; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.data_imports (
    id uuid NOT NULL,
    client_account_id uuid,
    engagement_id uuid,
    master_flow_id uuid,
    import_name character varying(255) NOT NULL,
    import_type character varying(50) NOT NULL,
    description text,
    filename character varying(255) NOT NULL,
    file_size integer,
    mime_type character varying(100),
    source_system character varying(100),
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    progress_percentage double precision DEFAULT '0'::double precision,
    total_records integer,
    processed_records integer DEFAULT 0,
    failed_records integer DEFAULT 0,
    imported_by uuid NOT NULL,
    error_message text,
    error_details json,
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.data_imports OWNER TO postgres;

--
-- Name: discovery_flows; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.discovery_flows (
    id uuid NOT NULL,
    flow_id uuid NOT NULL,
    master_flow_id uuid,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    user_id character varying NOT NULL,
    data_import_id uuid,
    flow_name character varying(255) NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    progress_percentage double precision DEFAULT '0'::double precision NOT NULL,
    data_import_completed boolean DEFAULT false NOT NULL,
    field_mapping_completed boolean DEFAULT false NOT NULL,
    data_cleansing_completed boolean DEFAULT false NOT NULL,
    asset_inventory_completed boolean DEFAULT false NOT NULL,
    dependency_analysis_completed boolean DEFAULT false NOT NULL,
    tech_debt_assessment_completed boolean DEFAULT false NOT NULL,
    learning_scope character varying(50) DEFAULT 'engagement'::character varying NOT NULL,
    memory_isolation_level character varying(20) DEFAULT 'strict'::character varying NOT NULL,
    assessment_ready boolean DEFAULT false NOT NULL,
    phase_state jsonb DEFAULT '{}'::jsonb NOT NULL,
    agent_state jsonb DEFAULT '{}'::jsonb NOT NULL,
    flow_type character varying(100),
    current_phase character varying(100),
    phases_completed json,
    flow_state json DEFAULT '{}'::json,
    crew_outputs json,
    field_mappings json,
    discovered_assets json,
    dependencies json,
    tech_debt_analysis json,
    crewai_persistence_id uuid,
    crewai_state_data jsonb DEFAULT '{}'::jsonb NOT NULL,
    error_message text,
    error_phase character varying(100),
    error_details json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone
);


ALTER TABLE migration.discovery_flows OWNER TO postgres;

--
-- Name: engagement_access; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.engagement_access (
    id uuid NOT NULL,
    user_profile_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    access_level character varying(20) NOT NULL,
    engagement_role character varying(100),
    permissions json DEFAULT '{"can_view_data": true, "can_import_data": false, "can_export_data": false, "can_manage_sessions": false, "can_configure_agents": false, "can_approve_migration_decisions": false, "can_access_sensitive_data": false}'::json,
    restricted_sessions json DEFAULT '[]'::json,
    allowed_session_types json DEFAULT '["data_import", "validation_run"]'::json,
    granted_at timestamp with time zone DEFAULT now(),
    granted_by uuid NOT NULL,
    expires_at timestamp with time zone,
    is_active boolean DEFAULT true,
    last_accessed_at timestamp with time zone,
    access_count integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE migration.engagement_access OWNER TO postgres;

--
-- Name: engagement_architecture_standards; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.engagement_architecture_standards (
    id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    requirement_type character varying(100) NOT NULL,
    description text,
    mandatory boolean NOT NULL,
    supported_versions jsonb,
    requirement_details jsonb,
    created_by character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE migration.engagement_architecture_standards OWNER TO postgres;

--
-- Name: engagements; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.engagements (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    engagement_type character varying(50) DEFAULT 'migration'::character varying,
    status character varying(50) DEFAULT 'active'::character varying,
    priority character varying(20) DEFAULT 'medium'::character varying,
    start_date timestamp with time zone,
    target_completion_date timestamp with time zone,
    actual_completion_date timestamp with time zone,
    engagement_lead_id uuid,
    client_contact_name character varying(255),
    client_contact_email character varying(255),
    settings json DEFAULT '{}'::json,
    migration_scope json DEFAULT '{"target_clouds": [], "migration_strategies": [], "excluded_systems": [], "included_environments": [], "business_units": [], "geographic_scope": [], "timeline_constraints": {}}'::json,
    team_preferences json DEFAULT '{"stakeholders": [], "decision_makers": [], "technical_leads": [], "communication_style": "formal", "reporting_frequency": "weekly", "preferred_meeting_times": [], "escalation_contacts": [], "project_methodology": "agile"}'::json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    is_active boolean DEFAULT true
);


ALTER TABLE migration.engagements OWNER TO postgres;

--
-- Name: enhanced_access_audit_log; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.enhanced_access_audit_log (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    action_type character varying(50) NOT NULL,
    resource_type character varying(50),
    resource_id character varying(255),
    client_account_id uuid,
    engagement_id uuid,
    result character varying(20) NOT NULL,
    reason text,
    ip_address character varying(45),
    user_agent text,
    details json DEFAULT '{}'::json,
    user_role_level character varying(30),
    user_data_scope character varying(20),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE migration.enhanced_access_audit_log OWNER TO postgres;

--
-- Name: enhanced_user_profiles; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.enhanced_user_profiles (
    user_id uuid NOT NULL,
    status character varying(20) DEFAULT 'PENDING_APPROVAL'::character varying NOT NULL,
    role_level character varying(30) DEFAULT 'VIEWER'::character varying NOT NULL,
    data_scope character varying(20) DEFAULT 'DEMO_ONLY'::character varying NOT NULL,
    scope_client_account_id uuid,
    scope_engagement_id uuid,
    registration_reason text,
    organization character varying(255),
    role_description character varying(255),
    phone_number character varying(20),
    manager_email character varying(255),
    approval_requested_at timestamp with time zone DEFAULT now(),
    approved_at timestamp with time zone,
    approved_by uuid,
    last_login_at timestamp with time zone,
    login_count integer DEFAULT 0,
    failed_login_attempts integer DEFAULT 0,
    is_deleted boolean DEFAULT false,
    deleted_at timestamp with time zone,
    deleted_by uuid,
    delete_reason text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.enhanced_user_profiles OWNER TO postgres;

--
-- Name: feedback; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.feedback (
    id uuid NOT NULL,
    feedback_type character varying(50) NOT NULL,
    page character varying(255),
    rating integer,
    comment text,
    category character varying(50) DEFAULT 'general'::character varying,
    breadcrumb character varying(500),
    filename character varying(255),
    original_analysis json,
    user_corrections json,
    asset_type_override character varying(100),
    status character varying(20) DEFAULT 'new'::character varying,
    processed boolean DEFAULT false,
    user_agent character varying(500),
    user_timestamp character varying(50),
    client_ip character varying(45),
    client_account_id uuid,
    engagement_id uuid,
    learning_patterns_extracted json,
    confidence_impact double precision DEFAULT '0'::double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    processed_at timestamp with time zone
);


ALTER TABLE migration.feedback OWNER TO postgres;

--
-- Name: feedback_summaries; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.feedback_summaries (
    id uuid NOT NULL,
    feedback_type character varying(50) NOT NULL,
    page character varying(255),
    time_period character varying(20) DEFAULT 'all_time'::character varying,
    total_feedback integer DEFAULT 0,
    average_rating double precision DEFAULT '0'::double precision,
    status_counts json,
    rating_distribution json,
    category_counts json,
    feedback_trend json,
    rating_trend json,
    client_account_id uuid,
    engagement_id uuid,
    last_calculated timestamp with time zone DEFAULT now(),
    calculation_duration_ms integer
);


ALTER TABLE migration.feedback_summaries OWNER TO postgres;

--
-- Name: flow_deletion_audit; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.flow_deletion_audit (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    flow_id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    user_id character varying NOT NULL,
    deletion_type character varying NOT NULL,
    deletion_reason text,
    deletion_method character varying NOT NULL,
    data_deleted jsonb DEFAULT '{}'::jsonb NOT NULL,
    deletion_impact jsonb DEFAULT '{}'::jsonb NOT NULL,
    cleanup_summary jsonb DEFAULT '{}'::jsonb NOT NULL,
    shared_memory_cleaned boolean DEFAULT false NOT NULL,
    knowledge_base_refs_cleaned jsonb DEFAULT '[]'::jsonb NOT NULL,
    agent_memory_cleaned boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_by character varying NOT NULL,
    deletion_duration_ms integer,
    recovery_possible boolean DEFAULT false NOT NULL,
    recovery_data jsonb DEFAULT '{}'::jsonb NOT NULL
);


ALTER TABLE migration.flow_deletion_audit OWNER TO postgres;

--
-- Name: import_field_mappings; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.import_field_mappings (
    id uuid NOT NULL,
    data_import_id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    master_flow_id uuid,
    source_field character varying(255) NOT NULL,
    target_field character varying(255) NOT NULL,
    match_type character varying(50) DEFAULT 'direct'::character varying NOT NULL,
    confidence_score double precision,
    status character varying(20) DEFAULT 'suggested'::character varying,
    suggested_by character varying(50) DEFAULT 'ai_mapper'::character varying,
    approved_by character varying(255),
    approved_at timestamp with time zone,
    transformation_rules json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE migration.import_field_mappings OWNER TO postgres;

--
-- Name: import_processing_steps; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.import_processing_steps (
    id uuid NOT NULL,
    data_import_id uuid NOT NULL,
    step_name character varying(100) NOT NULL,
    step_order integer NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    description text,
    input_data json,
    output_data json,
    error_details json,
    records_processed integer,
    duration_seconds double precision,
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);


ALTER TABLE migration.import_processing_steps OWNER TO postgres;

--
-- Name: llm_model_pricing; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.llm_model_pricing (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    provider character varying(100) NOT NULL,
    model_name character varying(255) NOT NULL,
    model_version character varying(100),
    input_cost_per_1k_tokens numeric(10,6) NOT NULL,
    output_cost_per_1k_tokens numeric(10,6) NOT NULL,
    currency character varying(10) DEFAULT 'USD'::character varying NOT NULL,
    effective_from timestamp with time zone NOT NULL,
    effective_to timestamp with time zone,
    is_active boolean DEFAULT true NOT NULL,
    source character varying(255),
    notes text
);


ALTER TABLE migration.llm_model_pricing OWNER TO postgres;

--
-- Name: llm_usage_logs; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.llm_usage_logs (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    client_account_id uuid,
    engagement_id uuid,
    user_id integer,
    username character varying(255),
    flow_id character varying(255),
    request_id character varying(255),
    endpoint character varying(500),
    page_context character varying(255),
    feature_context character varying(255),
    llm_provider character varying(100) NOT NULL,
    model_name character varying(255) NOT NULL,
    model_version character varying(100),
    input_tokens integer,
    output_tokens integer,
    total_tokens integer,
    input_cost numeric(10,6),
    output_cost numeric(10,6),
    total_cost numeric(10,6),
    cost_currency character varying(10) DEFAULT 'USD'::character varying NOT NULL,
    response_time_ms integer,
    success boolean DEFAULT true NOT NULL,
    error_type character varying(255),
    error_message text,
    request_data jsonb,
    response_data jsonb,
    additional_metadata jsonb,
    ip_address character varying(45),
    user_agent character varying(500)
);


ALTER TABLE migration.llm_usage_logs OWNER TO postgres;

--
-- Name: llm_usage_summary; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.llm_usage_summary (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    period_type character varying(20) NOT NULL,
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    client_account_id uuid,
    engagement_id uuid,
    user_id integer,
    llm_provider character varying(100),
    model_name character varying(255),
    page_context character varying(255),
    feature_context character varying(255),
    total_requests integer DEFAULT 0 NOT NULL,
    successful_requests integer DEFAULT 0 NOT NULL,
    failed_requests integer DEFAULT 0 NOT NULL,
    total_input_tokens bigint DEFAULT '0'::bigint NOT NULL,
    total_output_tokens bigint DEFAULT '0'::bigint NOT NULL,
    total_tokens bigint DEFAULT '0'::bigint NOT NULL,
    total_cost numeric(12,6) DEFAULT '0'::numeric NOT NULL,
    avg_response_time_ms integer,
    min_response_time_ms integer,
    max_response_time_ms integer
);


ALTER TABLE migration.llm_usage_summary OWNER TO postgres;

--
-- Name: migration_logs; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.migration_logs (
    id integer NOT NULL,
    migration_id uuid NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    level character varying(20) DEFAULT 'INFO'::character varying,
    message text NOT NULL,
    details json,
    phase character varying(50),
    user_id character varying(100),
    action character varying(100)
);


ALTER TABLE migration.migration_logs OWNER TO postgres;

--
-- Name: migration_logs_id_seq; Type: SEQUENCE; Schema: migration; Owner: postgres
--

CREATE SEQUENCE migration.migration_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE migration.migration_logs_id_seq OWNER TO postgres;

--
-- Name: migration_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: migration; Owner: postgres
--

ALTER SEQUENCE migration.migration_logs_id_seq OWNED BY migration.migration_logs.id;


--
-- Name: migration_waves; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.migration_waves (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    wave_number integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    status character varying(50) DEFAULT 'planned'::character varying,
    planned_start_date timestamp with time zone,
    planned_end_date timestamp with time zone,
    actual_start_date timestamp with time zone,
    actual_end_date timestamp with time zone,
    total_assets integer DEFAULT 0,
    completed_assets integer DEFAULT 0,
    failed_assets integer DEFAULT 0,
    estimated_cost double precision,
    actual_cost double precision,
    estimated_effort_hours double precision,
    actual_effort_hours double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid
);


ALTER TABLE migration.migration_waves OWNER TO postgres;

--
-- Name: migrations; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.migrations (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    status character varying(50) DEFAULT 'PLANNING'::character varying,
    current_phase character varying(50) DEFAULT 'DISCOVERY'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    start_date timestamp with time zone,
    target_completion_date timestamp with time zone,
    actual_completion_date timestamp with time zone,
    source_environment character varying(100),
    target_environment character varying(100),
    migration_strategy character varying(50),
    progress_percentage integer DEFAULT 0,
    total_assets integer DEFAULT 0,
    migrated_assets integer DEFAULT 0,
    ai_recommendations json,
    risk_assessment json,
    cost_estimates json,
    settings json
);


ALTER TABLE migration.migrations OWNER TO postgres;

--
-- Name: raw_import_records; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.raw_import_records (
    id uuid NOT NULL,
    data_import_id uuid NOT NULL,
    client_account_id uuid,
    engagement_id uuid,
    master_flow_id uuid,
    row_number integer NOT NULL,
    raw_data json NOT NULL,
    cleansed_data json,
    validation_errors json,
    processing_notes text,
    is_processed boolean DEFAULT false,
    is_valid boolean DEFAULT true,
    asset_id uuid,
    created_at timestamp with time zone DEFAULT now(),
    processed_at timestamp with time zone
);


ALTER TABLE migration.raw_import_records OWNER TO postgres;

--
-- Name: role_change_approvals; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.role_change_approvals (
    id uuid NOT NULL,
    requested_by character varying(36) NOT NULL,
    target_user_id character varying(36) NOT NULL,
    "current_role" character varying(50) NOT NULL,
    requested_role character varying(50) NOT NULL,
    justification text,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    approved_by character varying(36),
    approval_notes text,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    approved_at timestamp with time zone,
    expires_at timestamp with time zone
);


ALTER TABLE migration.role_change_approvals OWNER TO postgres;

--
-- Name: role_permissions; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.role_permissions (
    id uuid NOT NULL,
    role_level character varying(30) NOT NULL,
    can_manage_platform_settings boolean DEFAULT false,
    can_manage_all_clients boolean DEFAULT false,
    can_manage_all_users boolean DEFAULT false,
    can_purge_deleted_data boolean DEFAULT false,
    can_view_system_logs boolean DEFAULT false,
    can_create_clients boolean DEFAULT false,
    can_modify_client_settings boolean DEFAULT false,
    can_manage_client_users boolean DEFAULT false,
    can_delete_client_data boolean DEFAULT false,
    can_create_engagements boolean DEFAULT false,
    can_modify_engagement_settings boolean DEFAULT false,
    can_manage_engagement_users boolean DEFAULT false,
    can_delete_engagement_data boolean DEFAULT false,
    can_import_data boolean DEFAULT false,
    can_export_data boolean DEFAULT false,
    can_view_analytics boolean DEFAULT false,
    can_modify_data boolean DEFAULT false,
    can_configure_agents boolean DEFAULT false,
    can_view_agent_insights boolean DEFAULT false,
    can_approve_agent_decisions boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.role_permissions OWNER TO postgres;

--
-- Name: security_audit_logs; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.security_audit_logs (
    id uuid NOT NULL,
    event_type character varying(100) NOT NULL,
    event_category character varying(50) NOT NULL,
    severity character varying(20) DEFAULT 'INFO'::character varying NOT NULL,
    actor_user_id character varying(36) NOT NULL,
    actor_email character varying(255),
    actor_role character varying(50),
    target_user_id character varying(36),
    target_email character varying(255),
    ip_address character varying(45),
    user_agent text,
    request_path character varying(500),
    request_method character varying(10),
    description text NOT NULL,
    details jsonb,
    is_suspicious boolean DEFAULT false,
    requires_review boolean DEFAULT false,
    is_blocked boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    reviewed_at timestamp with time zone,
    reviewed_by character varying(36)
);


ALTER TABLE migration.security_audit_logs OWNER TO postgres;

--
-- Name: sixr_analyses; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.sixr_analyses (
    id uuid NOT NULL,
    migration_id uuid,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    status character varying(50) DEFAULT 'PENDING'::character varying NOT NULL,
    priority integer DEFAULT 3,
    application_ids json,
    application_data json,
    current_iteration integer DEFAULT 1,
    progress_percentage double precision DEFAULT '0'::double precision,
    estimated_completion timestamp with time zone,
    final_recommendation character varying(50),
    confidence_score double precision,
    created_by character varying(100),
    updated_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    analysis_config json
);


ALTER TABLE migration.sixr_analyses OWNER TO postgres;

--
-- Name: sixr_analysis_parameters; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.sixr_analysis_parameters (
    id uuid NOT NULL,
    analysis_id uuid NOT NULL,
    iteration_number integer NOT NULL,
    business_value double precision DEFAULT '3'::double precision NOT NULL,
    technical_complexity double precision DEFAULT '3'::double precision NOT NULL,
    migration_urgency double precision DEFAULT '3'::double precision NOT NULL,
    compliance_requirements double precision DEFAULT '3'::double precision NOT NULL,
    cost_sensitivity double precision DEFAULT '3'::double precision NOT NULL,
    risk_tolerance double precision DEFAULT '3'::double precision NOT NULL,
    innovation_priority double precision DEFAULT '3'::double precision NOT NULL,
    application_type character varying(20) DEFAULT 'custom'::character varying,
    parameter_source character varying(50) DEFAULT 'initial'::character varying,
    confidence_level double precision DEFAULT '1'::double precision,
    created_by character varying(100),
    updated_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    parameter_notes text,
    validation_status character varying(20) DEFAULT 'valid'::character varying
);


ALTER TABLE migration.sixr_analysis_parameters OWNER TO postgres;

--
-- Name: sixr_decisions; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.sixr_decisions (
    id uuid NOT NULL,
    assessment_flow_id uuid NOT NULL,
    application_id uuid NOT NULL,
    application_name character varying(255) NOT NULL,
    overall_strategy character varying(20) NOT NULL,
    confidence_score double precision,
    rationale text,
    architecture_exceptions jsonb NOT NULL,
    tech_debt_score double precision,
    risk_factors jsonb NOT NULL,
    move_group_hints jsonb NOT NULL,
    estimated_effort_hours integer,
    estimated_cost numeric(12,2),
    user_modifications jsonb,
    modified_by character varying(100),
    modified_at timestamp with time zone,
    app_on_page_data jsonb,
    decision_factors jsonb,
    ready_for_planning boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT valid_confidence_score CHECK (((confidence_score >= (0)::double precision) AND (confidence_score <= (1)::double precision))),
    CONSTRAINT valid_overall_strategy CHECK (((overall_strategy)::text = ANY ((ARRAY['rewrite'::character varying, 'rearchitect'::character varying, 'refactor'::character varying, 'replatform'::character varying, 'rehost'::character varying, 'repurchase'::character varying, 'retire'::character varying, 'retain'::character varying])::text[])))
);


ALTER TABLE migration.sixr_decisions OWNER TO postgres;

--
-- Name: sixr_iterations; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.sixr_iterations (
    id uuid NOT NULL,
    analysis_id uuid NOT NULL,
    iteration_number integer NOT NULL,
    iteration_name character varying(255),
    iteration_reason text,
    stakeholder_feedback text,
    parameter_changes json,
    question_responses json,
    recommendation_data json,
    confidence_score double precision,
    analysis_duration double precision,
    agent_insights json,
    status character varying(20) DEFAULT 'pending'::character varying,
    error_details json,
    created_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);


ALTER TABLE migration.sixr_iterations OWNER TO postgres;

--
-- Name: sixr_parameters; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.sixr_parameters (
    id uuid NOT NULL,
    parameter_key character varying(255) NOT NULL,
    value json NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.sixr_parameters OWNER TO postgres;

--
-- Name: sixr_question_responses; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.sixr_question_responses (
    id uuid NOT NULL,
    analysis_id uuid NOT NULL,
    iteration_number integer NOT NULL,
    question_id character varying(100) NOT NULL,
    response_value json,
    response_text text,
    confidence double precision DEFAULT '1'::double precision,
    source character varying(50) DEFAULT 'user'::character varying,
    response_time double precision,
    validation_status character varying(20) DEFAULT 'pending'::character varying,
    validation_errors json,
    created_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.sixr_question_responses OWNER TO postgres;

--
-- Name: sixr_questions; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.sixr_questions (
    id uuid NOT NULL,
    question_id character varying(100) NOT NULL,
    question_text text NOT NULL,
    question_type character varying(50) NOT NULL,
    category character varying(100) NOT NULL,
    priority integer DEFAULT 1,
    required boolean DEFAULT false,
    active boolean DEFAULT true,
    options json,
    validation_rules json,
    help_text text,
    depends_on character varying(100),
    show_conditions json,
    skip_conditions json,
    created_by character varying(100),
    updated_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    version character varying(20) DEFAULT '1.0'::character varying,
    parent_question_id character varying(100)
);


ALTER TABLE migration.sixr_questions OWNER TO postgres;

--
-- Name: sixr_recommendations; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.sixr_recommendations (
    id uuid NOT NULL,
    analysis_id uuid NOT NULL,
    iteration_number integer DEFAULT 1,
    recommended_strategy character varying(50) NOT NULL,
    confidence_score double precision NOT NULL,
    strategy_scores json,
    key_factors json,
    assumptions json,
    next_steps json,
    estimated_effort character varying(50),
    estimated_timeline character varying(100),
    estimated_cost_impact character varying(50),
    risk_factors json,
    business_benefits json,
    technical_benefits json,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    created_by character varying(100)
);


ALTER TABLE migration.sixr_recommendations OWNER TO postgres;

--
-- Name: soft_deleted_items; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.soft_deleted_items (
    id uuid NOT NULL,
    item_type character varying(30) NOT NULL,
    item_id uuid NOT NULL,
    item_name character varying(255),
    client_account_id uuid,
    engagement_id uuid,
    deleted_by uuid NOT NULL,
    deleted_at timestamp with time zone DEFAULT now(),
    delete_reason text,
    reviewed_by uuid,
    reviewed_at timestamp with time zone,
    review_decision character varying(20),
    review_notes text,
    purged_at timestamp with time zone,
    purged_by uuid,
    status character varying(20) DEFAULT 'pending_review'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.soft_deleted_items OWNER TO postgres;

--
-- Name: tags; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.tags (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    name character varying(100) NOT NULL,
    category character varying(50) NOT NULL,
    description text,
    reference_embedding text,
    confidence_threshold double precision DEFAULT '0.7'::double precision,
    is_active boolean DEFAULT true,
    usage_count integer DEFAULT 0,
    last_used timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.tags OWNER TO postgres;

--
-- Name: tech_debt_analysis; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.tech_debt_analysis (
    id uuid NOT NULL,
    assessment_flow_id uuid NOT NULL,
    application_id uuid NOT NULL,
    component_id uuid,
    debt_category character varying(100) NOT NULL,
    severity character varying(20) NOT NULL,
    description text NOT NULL,
    remediation_effort_hours integer,
    impact_on_migration text,
    tech_debt_score double precision,
    detected_by_agent character varying(100),
    agent_confidence double precision,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT valid_agent_confidence CHECK (((agent_confidence >= (0)::double precision) AND (agent_confidence <= (1)::double precision))),
    CONSTRAINT valid_severity CHECK (((severity)::text = ANY ((ARRAY['critical'::character varying, 'high'::character varying, 'medium'::character varying, 'low'::character varying])::text[])))
);


ALTER TABLE migration.tech_debt_analysis OWNER TO postgres;

--
-- Name: user_account_associations; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.user_account_associations (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    role character varying(50) DEFAULT 'member'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid
);


ALTER TABLE migration.user_account_associations OWNER TO postgres;

--
-- Name: user_active_flows; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.user_active_flows (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    flow_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    activated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_current boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE migration.user_active_flows OWNER TO postgres;

--
-- Name: user_profiles; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.user_profiles (
    user_id uuid NOT NULL,
    status character varying(20) DEFAULT 'PENDING_APPROVAL'::character varying NOT NULL,
    approval_requested_at timestamp with time zone DEFAULT now(),
    approved_at timestamp with time zone,
    approved_by uuid,
    registration_reason text,
    organization character varying(255),
    role_description character varying(255),
    requested_access_level character varying(20) DEFAULT 'READ_ONLY'::character varying,
    phone_number character varying(20),
    manager_email character varying(255),
    linkedin_profile character varying(255),
    last_login_at timestamp with time zone,
    login_count integer DEFAULT 0,
    failed_login_attempts integer DEFAULT 0,
    last_failed_login timestamp with time zone,
    notification_preferences json DEFAULT '{"email_notifications": true, "system_alerts": true, "learning_updates": false, "weekly_reports": true}'::json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE migration.user_profiles OWNER TO postgres;

--
-- Name: user_roles; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.user_roles (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    role_type character varying(50) NOT NULL,
    role_name character varying(100) NOT NULL,
    description text,
    permissions json DEFAULT '{"can_create_clients": false, "can_manage_engagements": false, "can_import_data": true, "can_export_data": true, "can_view_analytics": true, "can_manage_users": false, "can_configure_agents": false, "can_access_admin_console": false}'::json,
    scope_type character varying(20) DEFAULT 'global'::character varying,
    scope_client_id uuid,
    scope_engagement_id uuid,
    is_active boolean DEFAULT true,
    assigned_at timestamp with time zone DEFAULT now(),
    assigned_by uuid,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE migration.user_roles OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255),
    first_name character varying(100),
    last_name character varying(100),
    is_active boolean DEFAULT true,
    is_verified boolean DEFAULT false,
    default_client_id uuid,
    default_engagement_id uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_login timestamp with time zone
);


ALTER TABLE migration.users OWNER TO postgres;

--
-- Name: wave_plans; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.wave_plans (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    migration_id uuid NOT NULL,
    wave_number integer NOT NULL,
    wave_name character varying(255),
    description text,
    planned_start_date timestamp with time zone,
    planned_end_date timestamp with time zone,
    actual_start_date timestamp with time zone,
    actual_end_date timestamp with time zone,
    total_assets integer DEFAULT 0,
    completed_assets integer DEFAULT 0,
    estimated_effort_hours integer,
    estimated_cost double precision,
    prerequisites json,
    dependencies json,
    constraints json,
    overall_risk_level character varying(20),
    complexity_score double precision,
    success_criteria json,
    status character varying(50) DEFAULT 'planned'::character varying,
    progress_percentage double precision DEFAULT '0'::double precision,
    ai_recommendations json,
    optimization_score double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE migration.wave_plans OWNER TO postgres;

--
-- Name: workflow_progress; Type: TABLE; Schema: migration; Owner: postgres
--

CREATE TABLE migration.workflow_progress (
    id uuid NOT NULL,
    asset_id uuid NOT NULL,
    stage character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    notes text,
    started_at timestamp with time zone,
    completed_at timestamp with time zone
);


ALTER TABLE migration.workflow_progress OWNER TO postgres;

--
-- Name: migration_logs id; Type: DEFAULT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.migration_logs ALTER COLUMN id SET DEFAULT nextval('migration.migration_logs_id_seq'::regclass);


--
-- Name: user_account_associations _user_client_account_uc; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_account_associations
    ADD CONSTRAINT _user_client_account_uc UNIQUE (user_id, client_account_id);


--
-- Name: access_audit_log access_audit_log_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.access_audit_log
    ADD CONSTRAINT access_audit_log_pkey PRIMARY KEY (id);


--
-- Name: agent_discovered_patterns agent_discovered_patterns_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.agent_discovered_patterns
    ADD CONSTRAINT agent_discovered_patterns_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: application_architecture_overrides application_architecture_overrides_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.application_architecture_overrides
    ADD CONSTRAINT application_architecture_overrides_pkey PRIMARY KEY (id);


--
-- Name: application_components application_components_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.application_components
    ADD CONSTRAINT application_components_pkey PRIMARY KEY (id);


--
-- Name: assessment_flows assessment_flows_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessment_flows
    ADD CONSTRAINT assessment_flows_pkey PRIMARY KEY (id);


--
-- Name: assessment_learning_feedback assessment_learning_feedback_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessment_learning_feedback
    ADD CONSTRAINT assessment_learning_feedback_pkey PRIMARY KEY (id);


--
-- Name: assessments assessments_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessments
    ADD CONSTRAINT assessments_pkey PRIMARY KEY (id);


--
-- Name: asset_dependencies asset_dependencies_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_dependencies
    ADD CONSTRAINT asset_dependencies_pkey PRIMARY KEY (id);


--
-- Name: asset_embeddings asset_embeddings_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_embeddings
    ADD CONSTRAINT asset_embeddings_pkey PRIMARY KEY (id);


--
-- Name: asset_tags asset_tags_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_tags
    ADD CONSTRAINT asset_tags_pkey PRIMARY KEY (id);


--
-- Name: assets assets_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assets
    ADD CONSTRAINT assets_pkey PRIMARY KEY (id);


--
-- Name: client_access client_access_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.client_access
    ADD CONSTRAINT client_access_pkey PRIMARY KEY (id);


--
-- Name: client_accounts client_accounts_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.client_accounts
    ADD CONSTRAINT client_accounts_pkey PRIMARY KEY (id);


--
-- Name: client_accounts client_accounts_slug_key; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.client_accounts
    ADD CONSTRAINT client_accounts_slug_key UNIQUE (slug);


--
-- Name: cmdb_sixr_analyses cmdb_sixr_analyses_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.cmdb_sixr_analyses
    ADD CONSTRAINT cmdb_sixr_analyses_pkey PRIMARY KEY (id);


--
-- Name: component_treatments component_treatments_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.component_treatments
    ADD CONSTRAINT component_treatments_pkey PRIMARY KEY (id);


--
-- Name: crewai_flow_state_extensions crewai_flow_state_extensions_flow_id_key; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.crewai_flow_state_extensions
    ADD CONSTRAINT crewai_flow_state_extensions_flow_id_key UNIQUE (flow_id);


--
-- Name: crewai_flow_state_extensions crewai_flow_state_extensions_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.crewai_flow_state_extensions
    ADD CONSTRAINT crewai_flow_state_extensions_pkey PRIMARY KEY (id);


--
-- Name: custom_target_fields custom_target_fields_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.custom_target_fields
    ADD CONSTRAINT custom_target_fields_pkey PRIMARY KEY (id);


--
-- Name: data_import_sessions data_import_sessions_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.data_import_sessions
    ADD CONSTRAINT data_import_sessions_pkey PRIMARY KEY (id);


--
-- Name: data_imports data_imports_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.data_imports
    ADD CONSTRAINT data_imports_pkey PRIMARY KEY (id);


--
-- Name: discovery_flows discovery_flows_flow_id_key; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.discovery_flows
    ADD CONSTRAINT discovery_flows_flow_id_key UNIQUE (flow_id);


--
-- Name: discovery_flows discovery_flows_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.discovery_flows
    ADD CONSTRAINT discovery_flows_pkey PRIMARY KEY (id);


--
-- Name: engagement_access engagement_access_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagement_access
    ADD CONSTRAINT engagement_access_pkey PRIMARY KEY (id);


--
-- Name: engagement_architecture_standards engagement_architecture_standards_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagement_architecture_standards
    ADD CONSTRAINT engagement_architecture_standards_pkey PRIMARY KEY (id);


--
-- Name: engagements engagements_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagements
    ADD CONSTRAINT engagements_pkey PRIMARY KEY (id);


--
-- Name: enhanced_access_audit_log enhanced_access_audit_log_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.enhanced_access_audit_log
    ADD CONSTRAINT enhanced_access_audit_log_pkey PRIMARY KEY (id);


--
-- Name: enhanced_user_profiles enhanced_user_profiles_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_pkey PRIMARY KEY (user_id);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- Name: feedback_summaries feedback_summaries_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.feedback_summaries
    ADD CONSTRAINT feedback_summaries_pkey PRIMARY KEY (id);


--
-- Name: flow_deletion_audit flow_deletion_audit_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.flow_deletion_audit
    ADD CONSTRAINT flow_deletion_audit_pkey PRIMARY KEY (id);


--
-- Name: import_field_mappings import_field_mappings_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.import_field_mappings
    ADD CONSTRAINT import_field_mappings_pkey PRIMARY KEY (id);


--
-- Name: import_processing_steps import_processing_steps_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.import_processing_steps
    ADD CONSTRAINT import_processing_steps_pkey PRIMARY KEY (id);


--
-- Name: llm_model_pricing llm_model_pricing_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.llm_model_pricing
    ADD CONSTRAINT llm_model_pricing_pkey PRIMARY KEY (id);


--
-- Name: llm_usage_logs llm_usage_logs_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.llm_usage_logs
    ADD CONSTRAINT llm_usage_logs_pkey PRIMARY KEY (id);


--
-- Name: llm_usage_summary llm_usage_summary_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.llm_usage_summary
    ADD CONSTRAINT llm_usage_summary_pkey PRIMARY KEY (id);


--
-- Name: migration_logs migration_logs_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.migration_logs
    ADD CONSTRAINT migration_logs_pkey PRIMARY KEY (id);


--
-- Name: migration_waves migration_waves_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.migration_waves
    ADD CONSTRAINT migration_waves_pkey PRIMARY KEY (id);


--
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (id);


--
-- Name: raw_import_records raw_import_records_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.raw_import_records
    ADD CONSTRAINT raw_import_records_pkey PRIMARY KEY (id);


--
-- Name: role_change_approvals role_change_approvals_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.role_change_approvals
    ADD CONSTRAINT role_change_approvals_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- Name: security_audit_logs security_audit_logs_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.security_audit_logs
    ADD CONSTRAINT security_audit_logs_pkey PRIMARY KEY (id);


--
-- Name: sixr_analyses sixr_analyses_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_analyses
    ADD CONSTRAINT sixr_analyses_pkey PRIMARY KEY (id);


--
-- Name: sixr_analysis_parameters sixr_analysis_parameters_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_analysis_parameters
    ADD CONSTRAINT sixr_analysis_parameters_pkey PRIMARY KEY (id);


--
-- Name: sixr_decisions sixr_decisions_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_decisions
    ADD CONSTRAINT sixr_decisions_pkey PRIMARY KEY (id);


--
-- Name: sixr_iterations sixr_iterations_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_iterations
    ADD CONSTRAINT sixr_iterations_pkey PRIMARY KEY (id);


--
-- Name: sixr_parameters sixr_parameters_parameter_key_key; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_parameters
    ADD CONSTRAINT sixr_parameters_parameter_key_key UNIQUE (parameter_key);


--
-- Name: sixr_parameters sixr_parameters_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_parameters
    ADD CONSTRAINT sixr_parameters_pkey PRIMARY KEY (id);


--
-- Name: sixr_question_responses sixr_question_responses_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_question_responses
    ADD CONSTRAINT sixr_question_responses_pkey PRIMARY KEY (id);


--
-- Name: sixr_questions sixr_questions_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_questions
    ADD CONSTRAINT sixr_questions_pkey PRIMARY KEY (id);


--
-- Name: sixr_questions sixr_questions_question_id_key; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_questions
    ADD CONSTRAINT sixr_questions_question_id_key UNIQUE (question_id);


--
-- Name: sixr_recommendations sixr_recommendations_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_recommendations
    ADD CONSTRAINT sixr_recommendations_pkey PRIMARY KEY (id);


--
-- Name: soft_deleted_items soft_deleted_items_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_pkey PRIMARY KEY (id);


--
-- Name: tags tags_name_key; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.tags
    ADD CONSTRAINT tags_name_key UNIQUE (name);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: tech_debt_analysis tech_debt_analysis_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.tech_debt_analysis
    ADD CONSTRAINT tech_debt_analysis_pkey PRIMARY KEY (id);


--
-- Name: application_components unique_app_component; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.application_components
    ADD CONSTRAINT unique_app_component UNIQUE (assessment_flow_id, application_id, component_name);


--
-- Name: sixr_decisions unique_app_decision; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_decisions
    ADD CONSTRAINT unique_app_decision UNIQUE (assessment_flow_id, application_id);


--
-- Name: component_treatments unique_component_treatment; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.component_treatments
    ADD CONSTRAINT unique_component_treatment UNIQUE (assessment_flow_id, component_id);


--
-- Name: engagement_architecture_standards unique_engagement_requirement; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagement_architecture_standards
    ADD CONSTRAINT unique_engagement_requirement UNIQUE (engagement_id, requirement_type);


--
-- Name: llm_model_pricing uq_model_pricing_version_date; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.llm_model_pricing
    ADD CONSTRAINT uq_model_pricing_version_date UNIQUE (provider, model_name, model_version, effective_from);


--
-- Name: llm_usage_summary uq_usage_summary_period_context; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.llm_usage_summary
    ADD CONSTRAINT uq_usage_summary_period_context UNIQUE (period_type, period_start, client_account_id, engagement_id, user_id, llm_provider, model_name, page_context, feature_context);


--
-- Name: user_active_flows uq_user_active_flows_user_flow; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_active_flows
    ADD CONSTRAINT uq_user_active_flows_user_flow UNIQUE (user_id, flow_id);


--
-- Name: user_account_associations user_account_associations_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_account_associations
    ADD CONSTRAINT user_account_associations_pkey PRIMARY KEY (id);


--
-- Name: user_active_flows user_active_flows_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_active_flows
    ADD CONSTRAINT user_active_flows_pkey PRIMARY KEY (id);


--
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (user_id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: wave_plans wave_plans_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.wave_plans
    ADD CONSTRAINT wave_plans_pkey PRIMARY KEY (id);


--
-- Name: workflow_progress workflow_progress_pkey; Type: CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.workflow_progress
    ADD CONSTRAINT workflow_progress_pkey PRIMARY KEY (id);


--
-- Name: idx_app_components; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_app_components ON migration.application_components USING btree (application_id);


--
-- Name: idx_assessment_flows_client; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_assessment_flows_client ON migration.assessment_flows USING btree (client_account_id, engagement_id);


--
-- Name: idx_assessment_flows_pause_points_gin; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_assessment_flows_pause_points_gin ON migration.assessment_flows USING gin (pause_points);


--
-- Name: idx_assessment_flows_phase; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_assessment_flows_phase ON migration.assessment_flows USING btree (current_phase, next_phase);


--
-- Name: idx_assessment_flows_selected_apps_gin; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_assessment_flows_selected_apps_gin ON migration.assessment_flows USING gin (selected_application_ids);


--
-- Name: idx_assessment_flows_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_assessment_flows_status ON migration.assessment_flows USING btree (status);


--
-- Name: idx_assessment_flows_user_inputs_gin; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_assessment_flows_user_inputs_gin ON migration.assessment_flows USING gin (user_inputs);


--
-- Name: idx_component_dependencies_gin; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_component_dependencies_gin ON migration.application_components USING gin (dependencies);


--
-- Name: idx_component_tech_stack_gin; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_component_tech_stack_gin ON migration.application_components USING gin (technology_stack);


--
-- Name: idx_component_treatments; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_component_treatments ON migration.component_treatments USING btree (application_id, recommended_strategy);


--
-- Name: idx_crewai_flow_state_client_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_crewai_flow_state_client_status ON migration.crewai_flow_state_extensions USING btree (client_account_id, flow_status);


--
-- Name: idx_crewai_flow_state_created_desc; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_crewai_flow_state_created_desc ON migration.crewai_flow_state_extensions USING btree (created_at DESC);


--
-- Name: idx_crewai_flow_state_flow_type_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_crewai_flow_state_flow_type_status ON migration.crewai_flow_state_extensions USING btree (flow_type, flow_status);


--
-- Name: idx_eng_arch_standards; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_eng_arch_standards ON migration.engagement_architecture_standards USING btree (engagement_id);


--
-- Name: idx_llm_usage_client_account; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_llm_usage_client_account ON migration.llm_usage_logs USING btree (client_account_id);


--
-- Name: idx_llm_usage_cost_analysis; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_llm_usage_cost_analysis ON migration.llm_usage_logs USING btree (client_account_id, llm_provider, model_name, created_at);


--
-- Name: idx_llm_usage_created_at; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_llm_usage_created_at ON migration.llm_usage_logs USING btree (created_at);


--
-- Name: idx_llm_usage_engagement; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_llm_usage_engagement ON migration.llm_usage_logs USING btree (engagement_id);


--
-- Name: idx_llm_usage_feature_context; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_llm_usage_feature_context ON migration.llm_usage_logs USING btree (feature_context);


--
-- Name: idx_llm_usage_page_context; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_llm_usage_page_context ON migration.llm_usage_logs USING btree (page_context);


--
-- Name: idx_llm_usage_provider_model; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_llm_usage_provider_model ON migration.llm_usage_logs USING btree (llm_provider, model_name);


--
-- Name: idx_llm_usage_reporting; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_llm_usage_reporting ON migration.llm_usage_logs USING btree (client_account_id, created_at, success);


--
-- Name: idx_llm_usage_success; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_llm_usage_success ON migration.llm_usage_logs USING btree (success);


--
-- Name: idx_llm_usage_user; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_llm_usage_user ON migration.llm_usage_logs USING btree (user_id);


--
-- Name: idx_model_pricing_active; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_model_pricing_active ON migration.llm_model_pricing USING btree (is_active, effective_from, effective_to);


--
-- Name: idx_model_pricing_provider_model; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_model_pricing_provider_model ON migration.llm_model_pricing USING btree (provider, model_name);


--
-- Name: idx_sixr_app_on_page_gin; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_sixr_app_on_page_gin ON migration.sixr_decisions USING gin (app_on_page_data);


--
-- Name: idx_sixr_decisions_app; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_sixr_decisions_app ON migration.sixr_decisions USING btree (application_id);


--
-- Name: idx_sixr_ready_planning; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_sixr_ready_planning ON migration.sixr_decisions USING btree (ready_for_planning);


--
-- Name: idx_tech_debt_component; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_tech_debt_component ON migration.tech_debt_analysis USING btree (component_id);


--
-- Name: idx_tech_debt_severity; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_tech_debt_severity ON migration.tech_debt_analysis USING btree (severity);


--
-- Name: idx_usage_summary_client; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_usage_summary_client ON migration.llm_usage_summary USING btree (client_account_id, period_start);


--
-- Name: idx_usage_summary_model; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_usage_summary_model ON migration.llm_usage_summary USING btree (llm_provider, model_name, period_start);


--
-- Name: idx_usage_summary_period; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_usage_summary_period ON migration.llm_usage_summary USING btree (period_type, period_start, period_end);


--
-- Name: idx_user_active_flows_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_user_active_flows_engagement_id ON migration.user_active_flows USING btree (engagement_id);


--
-- Name: idx_user_active_flows_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_user_active_flows_flow_id ON migration.user_active_flows USING btree (flow_id);


--
-- Name: idx_user_active_flows_is_current; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_user_active_flows_is_current ON migration.user_active_flows USING btree (is_current);


--
-- Name: idx_user_active_flows_user_engagement; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_user_active_flows_user_engagement ON migration.user_active_flows USING btree (user_id, engagement_id);


--
-- Name: idx_user_active_flows_user_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX idx_user_active_flows_user_id ON migration.user_active_flows USING btree (user_id);


--
-- Name: ix_access_audit_log_action_type; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_access_audit_log_action_type ON migration.access_audit_log USING btree (action_type);


--
-- Name: ix_access_audit_log_created_at; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_access_audit_log_created_at ON migration.access_audit_log USING btree (created_at);


--
-- Name: ix_access_audit_log_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_access_audit_log_id ON migration.access_audit_log USING btree (id);


--
-- Name: ix_access_audit_log_user_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_access_audit_log_user_id ON migration.access_audit_log USING btree (user_id);


--
-- Name: ix_agent_patterns_client_account; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_agent_patterns_client_account ON migration.agent_discovered_patterns USING btree (client_account_id);


--
-- Name: ix_agent_patterns_confidence; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_agent_patterns_confidence ON migration.agent_discovered_patterns USING btree (confidence_score);


--
-- Name: ix_agent_patterns_discovery; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_agent_patterns_discovery ON migration.agent_discovered_patterns USING btree (discovered_by_agent, created_at);


--
-- Name: ix_agent_patterns_engagement; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_agent_patterns_engagement ON migration.agent_discovered_patterns USING btree (engagement_id);


--
-- Name: ix_agent_patterns_type; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_agent_patterns_type ON migration.agent_discovered_patterns USING btree (pattern_type);


--
-- Name: ix_application_architecture_overrides_application_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_application_architecture_overrides_application_id ON migration.application_architecture_overrides USING btree (application_id);


--
-- Name: ix_application_architecture_overrides_assessment_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_application_architecture_overrides_assessment_flow_id ON migration.application_architecture_overrides USING btree (assessment_flow_id);


--
-- Name: ix_application_components_application_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_application_components_application_id ON migration.application_components USING btree (application_id);


--
-- Name: ix_application_components_assessment_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_application_components_assessment_flow_id ON migration.application_components USING btree (assessment_flow_id);


--
-- Name: ix_assessment_flows_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assessment_flows_client_account_id ON migration.assessment_flows USING btree (client_account_id);


--
-- Name: ix_assessment_flows_current_phase; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assessment_flows_current_phase ON migration.assessment_flows USING btree (current_phase);


--
-- Name: ix_assessment_flows_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assessment_flows_engagement_id ON migration.assessment_flows USING btree (engagement_id);


--
-- Name: ix_assessment_flows_next_phase; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assessment_flows_next_phase ON migration.assessment_flows USING btree (next_phase);


--
-- Name: ix_assessment_flows_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assessment_flows_status ON migration.assessment_flows USING btree (status);


--
-- Name: ix_assessment_learning_feedback_assessment_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assessment_learning_feedback_assessment_flow_id ON migration.assessment_learning_feedback USING btree (assessment_flow_id);


--
-- Name: ix_assessment_learning_feedback_decision_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assessment_learning_feedback_decision_id ON migration.assessment_learning_feedback USING btree (decision_id);


--
-- Name: ix_assessments_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assessments_client_account_id ON migration.assessments USING btree (client_account_id);


--
-- Name: ix_assessments_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assessments_engagement_id ON migration.assessments USING btree (engagement_id);


--
-- Name: ix_assessments_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assessments_id ON migration.assessments USING btree (id);


--
-- Name: ix_asset_embeddings_asset_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_asset_embeddings_asset_id ON migration.asset_embeddings USING btree (asset_id);


--
-- Name: ix_asset_embeddings_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_asset_embeddings_client_account_id ON migration.asset_embeddings USING btree (client_account_id);


--
-- Name: ix_asset_embeddings_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_asset_embeddings_engagement_id ON migration.asset_embeddings USING btree (engagement_id);


--
-- Name: ix_asset_embeddings_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_asset_embeddings_id ON migration.asset_embeddings USING btree (id);


--
-- Name: ix_asset_tags_asset_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_asset_tags_asset_id ON migration.asset_tags USING btree (asset_id);


--
-- Name: ix_asset_tags_tag_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_asset_tags_tag_id ON migration.asset_tags USING btree (tag_id);


--
-- Name: ix_assets_assessment_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_assessment_flow_id ON migration.assets USING btree (assessment_flow_id);


--
-- Name: ix_assets_asset_type; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_asset_type ON migration.assets USING btree (asset_type);


--
-- Name: ix_assets_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_client_account_id ON migration.assets USING btree (client_account_id);


--
-- Name: ix_assets_current_phase; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_current_phase ON migration.assets USING btree (current_phase);


--
-- Name: ix_assets_discovery_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_discovery_flow_id ON migration.assets USING btree (discovery_flow_id);


--
-- Name: ix_assets_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_engagement_id ON migration.assets USING btree (engagement_id);


--
-- Name: ix_assets_environment; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_environment ON migration.assets USING btree (environment);


--
-- Name: ix_assets_execution_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_execution_flow_id ON migration.assets USING btree (execution_flow_id);


--
-- Name: ix_assets_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_flow_id ON migration.assets USING btree (flow_id);


--
-- Name: ix_assets_hostname; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_hostname ON migration.assets USING btree (hostname);


--
-- Name: ix_assets_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_id ON migration.assets USING btree (id);


--
-- Name: ix_assets_mapping_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_mapping_status ON migration.assets USING btree (mapping_status);


--
-- Name: ix_assets_master_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_master_flow_id ON migration.assets USING btree (master_flow_id);


--
-- Name: ix_assets_migration_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_migration_status ON migration.assets USING btree (migration_status);


--
-- Name: ix_assets_name; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_name ON migration.assets USING btree (name);


--
-- Name: ix_assets_planning_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_planning_flow_id ON migration.assets USING btree (planning_flow_id);


--
-- Name: ix_assets_source_phase; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_source_phase ON migration.assets USING btree (source_phase);


--
-- Name: ix_assets_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_assets_status ON migration.assets USING btree (status);


--
-- Name: ix_client_access_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_client_access_client_account_id ON migration.client_access USING btree (client_account_id);


--
-- Name: ix_client_access_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_client_access_id ON migration.client_access USING btree (id);


--
-- Name: ix_client_access_is_active; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_client_access_is_active ON migration.client_access USING btree (is_active);


--
-- Name: ix_client_access_user_profile_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_client_access_user_profile_id ON migration.client_access USING btree (user_profile_id);


--
-- Name: ix_client_accounts_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_client_accounts_id ON migration.client_accounts USING btree (id);


--
-- Name: ix_client_accounts_is_active; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_client_accounts_is_active ON migration.client_accounts USING btree (is_active);


--
-- Name: ix_client_accounts_slug; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_client_accounts_slug ON migration.client_accounts USING btree (slug);


--
-- Name: ix_cmdb_sixr_analyses_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_cmdb_sixr_analyses_client_account_id ON migration.cmdb_sixr_analyses USING btree (client_account_id);


--
-- Name: ix_cmdb_sixr_analyses_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_cmdb_sixr_analyses_engagement_id ON migration.cmdb_sixr_analyses USING btree (engagement_id);


--
-- Name: ix_cmdb_sixr_analyses_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_cmdb_sixr_analyses_id ON migration.cmdb_sixr_analyses USING btree (id);


--
-- Name: ix_component_treatments_application_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_component_treatments_application_id ON migration.component_treatments USING btree (application_id);


--
-- Name: ix_component_treatments_assessment_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_component_treatments_assessment_flow_id ON migration.component_treatments USING btree (assessment_flow_id);


--
-- Name: ix_component_treatments_recommended_strategy; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_component_treatments_recommended_strategy ON migration.component_treatments USING btree (recommended_strategy);


--
-- Name: ix_crewai_flow_state_extensions_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_crewai_flow_state_extensions_client_account_id ON migration.crewai_flow_state_extensions USING btree (client_account_id);


--
-- Name: ix_crewai_flow_state_extensions_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_crewai_flow_state_extensions_engagement_id ON migration.crewai_flow_state_extensions USING btree (engagement_id);


--
-- Name: ix_crewai_flow_state_extensions_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_crewai_flow_state_extensions_flow_id ON migration.crewai_flow_state_extensions USING btree (flow_id);


--
-- Name: ix_data_import_sessions_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_data_import_sessions_client_account_id ON migration.data_import_sessions USING btree (client_account_id);


--
-- Name: ix_data_import_sessions_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_data_import_sessions_engagement_id ON migration.data_import_sessions USING btree (engagement_id);


--
-- Name: ix_data_import_sessions_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_data_import_sessions_id ON migration.data_import_sessions USING btree (id);


--
-- Name: ix_data_import_sessions_is_default; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_data_import_sessions_is_default ON migration.data_import_sessions USING btree (is_default);


--
-- Name: ix_data_import_sessions_session_name; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_data_import_sessions_session_name ON migration.data_import_sessions USING btree (session_name);


--
-- Name: ix_data_import_sessions_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_data_import_sessions_status ON migration.data_import_sessions USING btree (status);


--
-- Name: ix_data_imports_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_data_imports_client_account_id ON migration.data_imports USING btree (client_account_id);


--
-- Name: ix_data_imports_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_data_imports_engagement_id ON migration.data_imports USING btree (engagement_id);


--
-- Name: ix_data_imports_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_data_imports_id ON migration.data_imports USING btree (id);


--
-- Name: ix_discovery_flows_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_discovery_flows_client_account_id ON migration.discovery_flows USING btree (client_account_id);


--
-- Name: ix_discovery_flows_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_discovery_flows_engagement_id ON migration.discovery_flows USING btree (engagement_id);


--
-- Name: ix_discovery_flows_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_discovery_flows_flow_id ON migration.discovery_flows USING btree (flow_id);


--
-- Name: ix_discovery_flows_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_discovery_flows_id ON migration.discovery_flows USING btree (id);


--
-- Name: ix_discovery_flows_master_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_discovery_flows_master_flow_id ON migration.discovery_flows USING btree (master_flow_id);


--
-- Name: ix_discovery_flows_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_discovery_flows_status ON migration.discovery_flows USING btree (status);


--
-- Name: ix_engagement_access_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_engagement_access_engagement_id ON migration.engagement_access USING btree (engagement_id);


--
-- Name: ix_engagement_access_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_engagement_access_id ON migration.engagement_access USING btree (id);


--
-- Name: ix_engagement_access_is_active; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_engagement_access_is_active ON migration.engagement_access USING btree (is_active);


--
-- Name: ix_engagement_access_user_profile_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_engagement_access_user_profile_id ON migration.engagement_access USING btree (user_profile_id);


--
-- Name: ix_engagement_architecture_standards_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_engagement_architecture_standards_engagement_id ON migration.engagement_architecture_standards USING btree (engagement_id);


--
-- Name: ix_engagements_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_engagements_client_account_id ON migration.engagements USING btree (client_account_id);


--
-- Name: ix_engagements_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_engagements_id ON migration.engagements USING btree (id);


--
-- Name: ix_engagements_is_active; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_engagements_is_active ON migration.engagements USING btree (is_active);


--
-- Name: ix_engagements_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_engagements_status ON migration.engagements USING btree (status);


--
-- Name: ix_enhanced_access_audit_log_action_type; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_enhanced_access_audit_log_action_type ON migration.enhanced_access_audit_log USING btree (action_type);


--
-- Name: ix_enhanced_access_audit_log_created_at; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_enhanced_access_audit_log_created_at ON migration.enhanced_access_audit_log USING btree (created_at);


--
-- Name: ix_enhanced_access_audit_log_user_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_enhanced_access_audit_log_user_id ON migration.enhanced_access_audit_log USING btree (user_id);


--
-- Name: ix_enhanced_user_profiles_data_scope; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_enhanced_user_profiles_data_scope ON migration.enhanced_user_profiles USING btree (data_scope);


--
-- Name: ix_enhanced_user_profiles_is_deleted; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_enhanced_user_profiles_is_deleted ON migration.enhanced_user_profiles USING btree (is_deleted);


--
-- Name: ix_enhanced_user_profiles_role_level; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_enhanced_user_profiles_role_level ON migration.enhanced_user_profiles USING btree (role_level);


--
-- Name: ix_enhanced_user_profiles_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_enhanced_user_profiles_status ON migration.enhanced_user_profiles USING btree (status);


--
-- Name: ix_feedback_feedback_type; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_feedback_feedback_type ON migration.feedback USING btree (feedback_type);


--
-- Name: ix_feedback_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_feedback_id ON migration.feedback USING btree (id);


--
-- Name: ix_feedback_page; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_feedback_page ON migration.feedback USING btree (page);


--
-- Name: ix_feedback_summaries_feedback_type; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_feedback_summaries_feedback_type ON migration.feedback_summaries USING btree (feedback_type);


--
-- Name: ix_feedback_summaries_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_feedback_summaries_id ON migration.feedback_summaries USING btree (id);


--
-- Name: ix_feedback_summaries_page; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_feedback_summaries_page ON migration.feedback_summaries USING btree (page);


--
-- Name: ix_flow_deletion_audit_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_flow_deletion_audit_client_account_id ON migration.flow_deletion_audit USING btree (client_account_id);


--
-- Name: ix_flow_deletion_audit_deleted_at; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_flow_deletion_audit_deleted_at ON migration.flow_deletion_audit USING btree (deleted_at);


--
-- Name: ix_flow_deletion_audit_deletion_type; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_flow_deletion_audit_deletion_type ON migration.flow_deletion_audit USING btree (deletion_type);


--
-- Name: ix_flow_deletion_audit_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_flow_deletion_audit_engagement_id ON migration.flow_deletion_audit USING btree (engagement_id);


--
-- Name: ix_flow_deletion_audit_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_flow_deletion_audit_flow_id ON migration.flow_deletion_audit USING btree (flow_id);


--
-- Name: ix_import_field_mappings_data_import_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_import_field_mappings_data_import_id ON migration.import_field_mappings USING btree (data_import_id);


--
-- Name: ix_import_field_mappings_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_import_field_mappings_id ON migration.import_field_mappings USING btree (id);


--
-- Name: ix_migration_logs_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_migration_logs_id ON migration.migration_logs USING btree (id);


--
-- Name: ix_migration_waves_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_migration_waves_client_account_id ON migration.migration_waves USING btree (client_account_id);


--
-- Name: ix_migration_waves_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_migration_waves_engagement_id ON migration.migration_waves USING btree (engagement_id);


--
-- Name: ix_migration_waves_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_migration_waves_id ON migration.migration_waves USING btree (id);


--
-- Name: ix_migration_waves_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_migration_waves_status ON migration.migration_waves USING btree (status);


--
-- Name: ix_migration_waves_wave_number; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_migration_waves_wave_number ON migration.migration_waves USING btree (wave_number);


--
-- Name: ix_migrations_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_migrations_id ON migration.migrations USING btree (id);


--
-- Name: ix_migrations_name; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_migrations_name ON migration.migrations USING btree (name);


--
-- Name: ix_raw_import_records_data_import_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_raw_import_records_data_import_id ON migration.raw_import_records USING btree (data_import_id);


--
-- Name: ix_raw_import_records_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_raw_import_records_id ON migration.raw_import_records USING btree (id);


--
-- Name: ix_role_change_approvals_requested_by; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_role_change_approvals_requested_by ON migration.role_change_approvals USING btree (requested_by);


--
-- Name: ix_role_change_approvals_target_user_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_role_change_approvals_target_user_id ON migration.role_change_approvals USING btree (target_user_id);


--
-- Name: ix_role_permissions_role_level; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_role_permissions_role_level ON migration.role_permissions USING btree (role_level);


--
-- Name: ix_security_audit_logs_actor_user_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_security_audit_logs_actor_user_id ON migration.security_audit_logs USING btree (actor_user_id);


--
-- Name: ix_security_audit_logs_created_at; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_security_audit_logs_created_at ON migration.security_audit_logs USING btree (created_at);


--
-- Name: ix_security_audit_logs_event_category; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_security_audit_logs_event_category ON migration.security_audit_logs USING btree (event_category);


--
-- Name: ix_security_audit_logs_event_type; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_security_audit_logs_event_type ON migration.security_audit_logs USING btree (event_type);


--
-- Name: ix_security_audit_logs_is_suspicious; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_security_audit_logs_is_suspicious ON migration.security_audit_logs USING btree (is_suspicious);


--
-- Name: ix_security_audit_logs_requires_review; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_security_audit_logs_requires_review ON migration.security_audit_logs USING btree (requires_review);


--
-- Name: ix_security_audit_logs_target_user_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_security_audit_logs_target_user_id ON migration.security_audit_logs USING btree (target_user_id);


--
-- Name: ix_sixr_analyses_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_analyses_client_account_id ON migration.sixr_analyses USING btree (client_account_id);


--
-- Name: ix_sixr_analyses_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_analyses_engagement_id ON migration.sixr_analyses USING btree (engagement_id);


--
-- Name: ix_sixr_analyses_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_analyses_id ON migration.sixr_analyses USING btree (id);


--
-- Name: ix_sixr_analyses_name; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_analyses_name ON migration.sixr_analyses USING btree (name);


--
-- Name: ix_sixr_analysis_parameters_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_analysis_parameters_id ON migration.sixr_analysis_parameters USING btree (id);


--
-- Name: ix_sixr_decisions_application_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_decisions_application_id ON migration.sixr_decisions USING btree (application_id);


--
-- Name: ix_sixr_decisions_assessment_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_decisions_assessment_flow_id ON migration.sixr_decisions USING btree (assessment_flow_id);


--
-- Name: ix_sixr_decisions_overall_strategy; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_decisions_overall_strategy ON migration.sixr_decisions USING btree (overall_strategy);


--
-- Name: ix_sixr_decisions_ready_for_planning; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_decisions_ready_for_planning ON migration.sixr_decisions USING btree (ready_for_planning);


--
-- Name: ix_sixr_iterations_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_iterations_id ON migration.sixr_iterations USING btree (id);


--
-- Name: ix_sixr_parameters_parameter_key; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_parameters_parameter_key ON migration.sixr_parameters USING btree (parameter_key);


--
-- Name: ix_sixr_question_responses_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_question_responses_id ON migration.sixr_question_responses USING btree (id);


--
-- Name: ix_sixr_questions_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_questions_id ON migration.sixr_questions USING btree (id);


--
-- Name: ix_sixr_questions_question_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_sixr_questions_question_id ON migration.sixr_questions USING btree (question_id);


--
-- Name: ix_soft_deleted_items_item_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_soft_deleted_items_item_id ON migration.soft_deleted_items USING btree (item_id);


--
-- Name: ix_soft_deleted_items_item_type; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_soft_deleted_items_item_type ON migration.soft_deleted_items USING btree (item_type);


--
-- Name: ix_soft_deleted_items_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_soft_deleted_items_status ON migration.soft_deleted_items USING btree (status);


--
-- Name: ix_tags_category; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_tags_category ON migration.tags USING btree (category);


--
-- Name: ix_tags_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_tags_client_account_id ON migration.tags USING btree (client_account_id);


--
-- Name: ix_tags_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_tags_id ON migration.tags USING btree (id);


--
-- Name: ix_tags_is_active; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_tags_is_active ON migration.tags USING btree (is_active);


--
-- Name: ix_tags_name; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_tags_name ON migration.tags USING btree (name);


--
-- Name: ix_tech_debt_analysis_application_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_tech_debt_analysis_application_id ON migration.tech_debt_analysis USING btree (application_id);


--
-- Name: ix_tech_debt_analysis_assessment_flow_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_tech_debt_analysis_assessment_flow_id ON migration.tech_debt_analysis USING btree (assessment_flow_id);


--
-- Name: ix_tech_debt_analysis_severity; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_tech_debt_analysis_severity ON migration.tech_debt_analysis USING btree (severity);


--
-- Name: ix_user_account_associations_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_user_account_associations_client_account_id ON migration.user_account_associations USING btree (client_account_id);


--
-- Name: ix_user_account_associations_user_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_user_account_associations_user_id ON migration.user_account_associations USING btree (user_id);


--
-- Name: ix_user_profiles_status; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_user_profiles_status ON migration.user_profiles USING btree (status);


--
-- Name: ix_user_roles_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_user_roles_id ON migration.user_roles USING btree (id);


--
-- Name: ix_user_roles_is_active; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_user_roles_is_active ON migration.user_roles USING btree (is_active);


--
-- Name: ix_user_roles_user_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_user_roles_user_id ON migration.user_roles USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_users_email ON migration.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_users_id ON migration.users USING btree (id);


--
-- Name: ix_users_is_active; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_users_is_active ON migration.users USING btree (is_active);


--
-- Name: ix_wave_plans_client_account_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_wave_plans_client_account_id ON migration.wave_plans USING btree (client_account_id);


--
-- Name: ix_wave_plans_engagement_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_wave_plans_engagement_id ON migration.wave_plans USING btree (engagement_id);


--
-- Name: ix_wave_plans_id; Type: INDEX; Schema: migration; Owner: postgres
--

CREATE INDEX ix_wave_plans_id ON migration.wave_plans USING btree (id);


--
-- Name: access_audit_log access_audit_log_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.access_audit_log
    ADD CONSTRAINT access_audit_log_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id);


--
-- Name: access_audit_log access_audit_log_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.access_audit_log
    ADD CONSTRAINT access_audit_log_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id);


--
-- Name: access_audit_log access_audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.access_audit_log
    ADD CONSTRAINT access_audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES migration.users(id);


--
-- Name: application_architecture_overrides application_architecture_overrides_assessment_flow_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.application_architecture_overrides
    ADD CONSTRAINT application_architecture_overrides_assessment_flow_id_fkey FOREIGN KEY (assessment_flow_id) REFERENCES migration.assessment_flows(id) ON DELETE CASCADE;


--
-- Name: application_architecture_overrides application_architecture_overrides_standard_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.application_architecture_overrides
    ADD CONSTRAINT application_architecture_overrides_standard_id_fkey FOREIGN KEY (standard_id) REFERENCES migration.engagement_architecture_standards(id) ON DELETE SET NULL;


--
-- Name: application_components application_components_assessment_flow_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.application_components
    ADD CONSTRAINT application_components_assessment_flow_id_fkey FOREIGN KEY (assessment_flow_id) REFERENCES migration.assessment_flows(id) ON DELETE CASCADE;


--
-- Name: assessment_flows assessment_flows_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessment_flows
    ADD CONSTRAINT assessment_flows_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: assessment_flows assessment_flows_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessment_flows
    ADD CONSTRAINT assessment_flows_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: assessment_learning_feedback assessment_learning_feedback_assessment_flow_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessment_learning_feedback
    ADD CONSTRAINT assessment_learning_feedback_assessment_flow_id_fkey FOREIGN KEY (assessment_flow_id) REFERENCES migration.assessment_flows(id) ON DELETE CASCADE;


--
-- Name: assessment_learning_feedback assessment_learning_feedback_decision_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessment_learning_feedback
    ADD CONSTRAINT assessment_learning_feedback_decision_id_fkey FOREIGN KEY (decision_id) REFERENCES migration.sixr_decisions(id) ON DELETE CASCADE;


--
-- Name: assessments assessments_asset_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessments
    ADD CONSTRAINT assessments_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES migration.assets(id);


--
-- Name: assessments assessments_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessments
    ADD CONSTRAINT assessments_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: assessments assessments_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessments
    ADD CONSTRAINT assessments_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: assessments assessments_migration_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assessments
    ADD CONSTRAINT assessments_migration_id_fkey FOREIGN KEY (migration_id) REFERENCES migration.migrations(id);


--
-- Name: asset_dependencies asset_dependencies_asset_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_dependencies
    ADD CONSTRAINT asset_dependencies_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES migration.assets(id) ON DELETE CASCADE;


--
-- Name: asset_dependencies asset_dependencies_depends_on_asset_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_dependencies
    ADD CONSTRAINT asset_dependencies_depends_on_asset_id_fkey FOREIGN KEY (depends_on_asset_id) REFERENCES migration.assets(id) ON DELETE CASCADE;


--
-- Name: asset_embeddings asset_embeddings_asset_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_embeddings
    ADD CONSTRAINT asset_embeddings_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES migration.assets(id) ON DELETE CASCADE;


--
-- Name: asset_embeddings asset_embeddings_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_embeddings
    ADD CONSTRAINT asset_embeddings_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: asset_embeddings asset_embeddings_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_embeddings
    ADD CONSTRAINT asset_embeddings_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: asset_tags asset_tags_asset_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_tags
    ADD CONSTRAINT asset_tags_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES migration.assets(id) ON DELETE CASCADE;


--
-- Name: asset_tags asset_tags_assigned_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_tags
    ADD CONSTRAINT asset_tags_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES migration.users(id);


--
-- Name: asset_tags asset_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_tags
    ADD CONSTRAINT asset_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES migration.tags(id) ON DELETE CASCADE;


--
-- Name: asset_tags asset_tags_validated_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.asset_tags
    ADD CONSTRAINT asset_tags_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES migration.users(id);


--
-- Name: assets assets_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assets
    ADD CONSTRAINT assets_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: assets assets_created_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assets
    ADD CONSTRAINT assets_created_by_fkey FOREIGN KEY (created_by) REFERENCES migration.users(id);


--
-- Name: assets assets_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assets
    ADD CONSTRAINT assets_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: assets assets_flow_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assets
    ADD CONSTRAINT assets_flow_id_fkey FOREIGN KEY (flow_id) REFERENCES migration.discovery_flows(flow_id) ON DELETE CASCADE;


--
-- Name: assets assets_imported_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assets
    ADD CONSTRAINT assets_imported_by_fkey FOREIGN KEY (imported_by) REFERENCES migration.users(id);


--
-- Name: assets assets_migration_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assets
    ADD CONSTRAINT assets_migration_id_fkey FOREIGN KEY (migration_id) REFERENCES migration.migrations(id);


--
-- Name: assets assets_updated_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.assets
    ADD CONSTRAINT assets_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES migration.users(id);


--
-- Name: client_access client_access_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.client_access
    ADD CONSTRAINT client_access_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: client_access client_access_granted_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.client_access
    ADD CONSTRAINT client_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES migration.users(id);


--
-- Name: client_access client_access_user_profile_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.client_access
    ADD CONSTRAINT client_access_user_profile_id_fkey FOREIGN KEY (user_profile_id) REFERENCES migration.user_profiles(user_id) ON DELETE CASCADE;


--
-- Name: cmdb_sixr_analyses cmdb_sixr_analyses_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.cmdb_sixr_analyses
    ADD CONSTRAINT cmdb_sixr_analyses_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: cmdb_sixr_analyses cmdb_sixr_analyses_created_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.cmdb_sixr_analyses
    ADD CONSTRAINT cmdb_sixr_analyses_created_by_fkey FOREIGN KEY (created_by) REFERENCES migration.users(id);


--
-- Name: cmdb_sixr_analyses cmdb_sixr_analyses_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.cmdb_sixr_analyses
    ADD CONSTRAINT cmdb_sixr_analyses_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: component_treatments component_treatments_assessment_flow_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.component_treatments
    ADD CONSTRAINT component_treatments_assessment_flow_id_fkey FOREIGN KEY (assessment_flow_id) REFERENCES migration.assessment_flows(id) ON DELETE CASCADE;


--
-- Name: component_treatments component_treatments_component_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.component_treatments
    ADD CONSTRAINT component_treatments_component_id_fkey FOREIGN KEY (component_id) REFERENCES migration.application_components(id) ON DELETE CASCADE;


--
-- Name: custom_target_fields custom_target_fields_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.custom_target_fields
    ADD CONSTRAINT custom_target_fields_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id);


--
-- Name: custom_target_fields custom_target_fields_created_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.custom_target_fields
    ADD CONSTRAINT custom_target_fields_created_by_fkey FOREIGN KEY (created_by) REFERENCES migration.users(id);


--
-- Name: data_import_sessions data_import_sessions_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.data_import_sessions
    ADD CONSTRAINT data_import_sessions_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: data_import_sessions data_import_sessions_created_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.data_import_sessions
    ADD CONSTRAINT data_import_sessions_created_by_fkey FOREIGN KEY (created_by) REFERENCES migration.users(id);


--
-- Name: data_import_sessions data_import_sessions_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.data_import_sessions
    ADD CONSTRAINT data_import_sessions_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: data_import_sessions data_import_sessions_parent_session_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.data_import_sessions
    ADD CONSTRAINT data_import_sessions_parent_session_id_fkey FOREIGN KEY (parent_session_id) REFERENCES migration.data_import_sessions(id) ON DELETE SET NULL;


--
-- Name: data_imports data_imports_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.data_imports
    ADD CONSTRAINT data_imports_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: data_imports data_imports_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.data_imports
    ADD CONSTRAINT data_imports_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: data_imports data_imports_imported_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.data_imports
    ADD CONSTRAINT data_imports_imported_by_fkey FOREIGN KEY (imported_by) REFERENCES migration.users(id);


--
-- Name: data_imports data_imports_master_flow_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.data_imports
    ADD CONSTRAINT data_imports_master_flow_id_fkey FOREIGN KEY (master_flow_id) REFERENCES migration.crewai_flow_state_extensions(id) ON DELETE CASCADE;


--
-- Name: engagement_access engagement_access_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagement_access
    ADD CONSTRAINT engagement_access_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: engagement_access engagement_access_granted_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagement_access
    ADD CONSTRAINT engagement_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES migration.users(id);


--
-- Name: engagement_access engagement_access_user_profile_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagement_access
    ADD CONSTRAINT engagement_access_user_profile_id_fkey FOREIGN KEY (user_profile_id) REFERENCES migration.user_profiles(user_id) ON DELETE CASCADE;


--
-- Name: engagement_architecture_standards engagement_architecture_standards_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagement_architecture_standards
    ADD CONSTRAINT engagement_architecture_standards_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: engagements engagements_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagements
    ADD CONSTRAINT engagements_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: engagements engagements_created_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagements
    ADD CONSTRAINT engagements_created_by_fkey FOREIGN KEY (created_by) REFERENCES migration.users(id);


--
-- Name: engagements engagements_engagement_lead_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.engagements
    ADD CONSTRAINT engagements_engagement_lead_id_fkey FOREIGN KEY (engagement_lead_id) REFERENCES migration.users(id);


--
-- Name: enhanced_access_audit_log enhanced_access_audit_log_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.enhanced_access_audit_log
    ADD CONSTRAINT enhanced_access_audit_log_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id);


--
-- Name: enhanced_access_audit_log enhanced_access_audit_log_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.enhanced_access_audit_log
    ADD CONSTRAINT enhanced_access_audit_log_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id);


--
-- Name: enhanced_access_audit_log enhanced_access_audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.enhanced_access_audit_log
    ADD CONSTRAINT enhanced_access_audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES migration.users(id);


--
-- Name: enhanced_user_profiles enhanced_user_profiles_approved_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES migration.users(id);


--
-- Name: enhanced_user_profiles enhanced_user_profiles_deleted_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES migration.users(id);


--
-- Name: enhanced_user_profiles enhanced_user_profiles_scope_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_scope_client_account_id_fkey FOREIGN KEY (scope_client_account_id) REFERENCES migration.client_accounts(id);


--
-- Name: enhanced_user_profiles enhanced_user_profiles_scope_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_scope_engagement_id_fkey FOREIGN KEY (scope_engagement_id) REFERENCES migration.engagements(id);


--
-- Name: enhanced_user_profiles enhanced_user_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES migration.users(id) ON DELETE CASCADE;


--
-- Name: feedback feedback_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.feedback
    ADD CONSTRAINT feedback_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: feedback feedback_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.feedback
    ADD CONSTRAINT feedback_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: feedback_summaries feedback_summaries_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.feedback_summaries
    ADD CONSTRAINT feedback_summaries_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: feedback_summaries feedback_summaries_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.feedback_summaries
    ADD CONSTRAINT feedback_summaries_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: crewai_flow_state_extensions fk_crewai_flow_state_parent; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.crewai_flow_state_extensions
    ADD CONSTRAINT fk_crewai_flow_state_parent FOREIGN KEY (parent_flow_id) REFERENCES migration.crewai_flow_state_extensions(flow_id) ON DELETE SET NULL;


--
-- Name: discovery_flows fk_discovery_flows_data_import_id; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.discovery_flows
    ADD CONSTRAINT fk_discovery_flows_data_import_id FOREIGN KEY (data_import_id) REFERENCES migration.data_imports(id);


--
-- Name: user_active_flows fk_user_active_flows_engagement; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_active_flows
    ADD CONSTRAINT fk_user_active_flows_engagement FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: user_active_flows fk_user_active_flows_user; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_active_flows
    ADD CONSTRAINT fk_user_active_flows_user FOREIGN KEY (user_id) REFERENCES migration.users(id) ON DELETE CASCADE;


--
-- Name: users fk_users_default_client_id; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.users
    ADD CONSTRAINT fk_users_default_client_id FOREIGN KEY (default_client_id) REFERENCES migration.client_accounts(id);


--
-- Name: users fk_users_default_engagement_id; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.users
    ADD CONSTRAINT fk_users_default_engagement_id FOREIGN KEY (default_engagement_id) REFERENCES migration.engagements(id);


--
-- Name: import_field_mappings import_field_mappings_data_import_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.import_field_mappings
    ADD CONSTRAINT import_field_mappings_data_import_id_fkey FOREIGN KEY (data_import_id) REFERENCES migration.data_imports(id) ON DELETE CASCADE;


--
-- Name: import_field_mappings import_field_mappings_master_flow_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.import_field_mappings
    ADD CONSTRAINT import_field_mappings_master_flow_id_fkey FOREIGN KEY (master_flow_id) REFERENCES migration.crewai_flow_state_extensions(id);


--
-- Name: import_processing_steps import_processing_steps_data_import_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.import_processing_steps
    ADD CONSTRAINT import_processing_steps_data_import_id_fkey FOREIGN KEY (data_import_id) REFERENCES migration.data_imports(id) ON DELETE CASCADE;


--
-- Name: llm_usage_logs llm_usage_logs_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.llm_usage_logs
    ADD CONSTRAINT llm_usage_logs_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id);


--
-- Name: llm_usage_logs llm_usage_logs_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.llm_usage_logs
    ADD CONSTRAINT llm_usage_logs_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id);


--
-- Name: llm_usage_summary llm_usage_summary_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.llm_usage_summary
    ADD CONSTRAINT llm_usage_summary_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id);


--
-- Name: llm_usage_summary llm_usage_summary_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.llm_usage_summary
    ADD CONSTRAINT llm_usage_summary_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id);


--
-- Name: migration_logs migration_logs_migration_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.migration_logs
    ADD CONSTRAINT migration_logs_migration_id_fkey FOREIGN KEY (migration_id) REFERENCES migration.migrations(id);


--
-- Name: migration_waves migration_waves_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.migration_waves
    ADD CONSTRAINT migration_waves_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: migration_waves migration_waves_created_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.migration_waves
    ADD CONSTRAINT migration_waves_created_by_fkey FOREIGN KEY (created_by) REFERENCES migration.users(id);


--
-- Name: migration_waves migration_waves_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.migration_waves
    ADD CONSTRAINT migration_waves_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: raw_import_records raw_import_records_asset_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.raw_import_records
    ADD CONSTRAINT raw_import_records_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES migration.assets(id);


--
-- Name: raw_import_records raw_import_records_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.raw_import_records
    ADD CONSTRAINT raw_import_records_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id);


--
-- Name: raw_import_records raw_import_records_data_import_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.raw_import_records
    ADD CONSTRAINT raw_import_records_data_import_id_fkey FOREIGN KEY (data_import_id) REFERENCES migration.data_imports(id) ON DELETE CASCADE;


--
-- Name: raw_import_records raw_import_records_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.raw_import_records
    ADD CONSTRAINT raw_import_records_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id);


--
-- Name: raw_import_records raw_import_records_master_flow_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.raw_import_records
    ADD CONSTRAINT raw_import_records_master_flow_id_fkey FOREIGN KEY (master_flow_id) REFERENCES migration.crewai_flow_state_extensions(id);


--
-- Name: sixr_analyses sixr_analyses_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_analyses
    ADD CONSTRAINT sixr_analyses_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: sixr_analyses sixr_analyses_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_analyses
    ADD CONSTRAINT sixr_analyses_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: sixr_analyses sixr_analyses_migration_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_analyses
    ADD CONSTRAINT sixr_analyses_migration_id_fkey FOREIGN KEY (migration_id) REFERENCES migration.migrations(id);


--
-- Name: sixr_analysis_parameters sixr_analysis_parameters_analysis_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_analysis_parameters
    ADD CONSTRAINT sixr_analysis_parameters_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES migration.sixr_analyses(id);


--
-- Name: sixr_decisions sixr_decisions_assessment_flow_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_decisions
    ADD CONSTRAINT sixr_decisions_assessment_flow_id_fkey FOREIGN KEY (assessment_flow_id) REFERENCES migration.assessment_flows(id) ON DELETE CASCADE;


--
-- Name: sixr_iterations sixr_iterations_analysis_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_iterations
    ADD CONSTRAINT sixr_iterations_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES migration.sixr_analyses(id);


--
-- Name: sixr_question_responses sixr_question_responses_analysis_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_question_responses
    ADD CONSTRAINT sixr_question_responses_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES migration.sixr_analyses(id);


--
-- Name: sixr_question_responses sixr_question_responses_question_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_question_responses
    ADD CONSTRAINT sixr_question_responses_question_id_fkey FOREIGN KEY (question_id) REFERENCES migration.sixr_questions(question_id);


--
-- Name: sixr_recommendations sixr_recommendations_analysis_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.sixr_recommendations
    ADD CONSTRAINT sixr_recommendations_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES migration.sixr_analyses(id);


--
-- Name: soft_deleted_items soft_deleted_items_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id);


--
-- Name: soft_deleted_items soft_deleted_items_deleted_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES migration.users(id);


--
-- Name: soft_deleted_items soft_deleted_items_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id);


--
-- Name: soft_deleted_items soft_deleted_items_purged_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_purged_by_fkey FOREIGN KEY (purged_by) REFERENCES migration.users(id);


--
-- Name: soft_deleted_items soft_deleted_items_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES migration.users(id);


--
-- Name: tags tags_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.tags
    ADD CONSTRAINT tags_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: tech_debt_analysis tech_debt_analysis_assessment_flow_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.tech_debt_analysis
    ADD CONSTRAINT tech_debt_analysis_assessment_flow_id_fkey FOREIGN KEY (assessment_flow_id) REFERENCES migration.assessment_flows(id) ON DELETE CASCADE;


--
-- Name: tech_debt_analysis tech_debt_analysis_component_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.tech_debt_analysis
    ADD CONSTRAINT tech_debt_analysis_component_id_fkey FOREIGN KEY (component_id) REFERENCES migration.application_components(id) ON DELETE SET NULL;


--
-- Name: user_account_associations user_account_associations_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_account_associations
    ADD CONSTRAINT user_account_associations_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: user_account_associations user_account_associations_created_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_account_associations
    ADD CONSTRAINT user_account_associations_created_by_fkey FOREIGN KEY (created_by) REFERENCES migration.users(id);


--
-- Name: user_account_associations user_account_associations_user_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_account_associations
    ADD CONSTRAINT user_account_associations_user_id_fkey FOREIGN KEY (user_id) REFERENCES migration.users(id) ON DELETE CASCADE;


--
-- Name: user_profiles user_profiles_approved_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_profiles
    ADD CONSTRAINT user_profiles_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES migration.users(id);


--
-- Name: user_profiles user_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_profiles
    ADD CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES migration.users(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_assigned_by_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_roles
    ADD CONSTRAINT user_roles_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES migration.users(id);


--
-- Name: user_roles user_roles_scope_client_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_roles
    ADD CONSTRAINT user_roles_scope_client_id_fkey FOREIGN KEY (scope_client_id) REFERENCES migration.client_accounts(id);


--
-- Name: user_roles user_roles_scope_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_roles
    ADD CONSTRAINT user_roles_scope_engagement_id_fkey FOREIGN KEY (scope_engagement_id) REFERENCES migration.engagements(id);


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES migration.users(id) ON DELETE CASCADE;


--
-- Name: wave_plans wave_plans_client_account_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.wave_plans
    ADD CONSTRAINT wave_plans_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES migration.client_accounts(id) ON DELETE CASCADE;


--
-- Name: wave_plans wave_plans_engagement_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.wave_plans
    ADD CONSTRAINT wave_plans_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES migration.engagements(id) ON DELETE CASCADE;


--
-- Name: wave_plans wave_plans_migration_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.wave_plans
    ADD CONSTRAINT wave_plans_migration_id_fkey FOREIGN KEY (migration_id) REFERENCES migration.migrations(id);


--
-- Name: workflow_progress workflow_progress_asset_id_fkey; Type: FK CONSTRAINT; Schema: migration; Owner: postgres
--

ALTER TABLE ONLY migration.workflow_progress
    ADD CONSTRAINT workflow_progress_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES migration.assets(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

