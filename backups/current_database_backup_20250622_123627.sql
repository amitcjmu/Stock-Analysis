--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8 (Debian 16.8-1.pgdg120+1)
-- Dumped by pg_dump version 17.4

-- Started on 2025-06-22 12:36:27 EDT

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 922 (class 1247 OID 16512)
-- Name: analysisstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.analysisstatus AS ENUM (
    'PENDING',
    'IN_PROGRESS',
    'COMPLETED',
    'FAILED',
    'REQUIRES_INPUT'
);


--
-- TOC entry 916 (class 1247 OID 16488)
-- Name: assessmentstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.assessmentstatus AS ENUM (
    'PENDING',
    'IN_PROGRESS',
    'COMPLETED',
    'REVIEWED',
    'APPROVED',
    'REJECTED'
);


--
-- TOC entry 913 (class 1247 OID 16472)
-- Name: assessmenttype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.assessmenttype AS ENUM (
    'SIX_R_ANALYSIS',
    'RISK_ASSESSMENT',
    'COST_ANALYSIS',
    'TECHNICAL_ASSESSMENT',
    'BUSINESS_IMPACT',
    'SECURITY_ASSESSMENT',
    'COMPLIANCE_REVIEW'
);


--
-- TOC entry 907 (class 1247 OID 16442)
-- Name: assetstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.assetstatus AS ENUM (
    'DISCOVERED',
    'ASSESSED',
    'PLANNED',
    'MIGRATING',
    'MIGRATED',
    'FAILED',
    'EXCLUDED'
);


--
-- TOC entry 904 (class 1247 OID 16420)
-- Name: assettype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.assettype AS ENUM (
    'SERVER',
    'DATABASE',
    'APPLICATION',
    'NETWORK',
    'STORAGE',
    'CONTAINER',
    'VIRTUAL_MACHINE',
    'LOAD_BALANCER',
    'SECURITY_GROUP',
    'OTHER'
);


--
-- TOC entry 901 (class 1247 OID 16402)
-- Name: migrationphase; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.migrationphase AS ENUM (
    'DISCOVERY',
    'ASSESS',
    'PLAN',
    'EXECUTE',
    'MODERNIZE',
    'FINOPS',
    'OBSERVABILITY',
    'DECOMMISSION'
);


--
-- TOC entry 898 (class 1247 OID 16390)
-- Name: migrationstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.migrationstatus AS ENUM (
    'PLANNING',
    'IN_PROGRESS',
    'COMPLETED',
    'PAUSED',
    'CANCELLED'
);


--
-- TOC entry 925 (class 1247 OID 16524)
-- Name: questiontype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.questiontype AS ENUM (
    'TEXT',
    'SELECT',
    'MULTISELECT',
    'FILE_UPLOAD',
    'BOOLEAN',
    'NUMERIC'
);


--
-- TOC entry 919 (class 1247 OID 16502)
-- Name: risklevel; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.risklevel AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);


--
-- TOC entry 910 (class 1247 OID 16458)
-- Name: sixrstrategy; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sixrstrategy AS ENUM (
    'REHOST',
    'REPLATFORM',
    'REFACTOR',
    'REARCHITECT',
    'RETIRE',
    'RETAIN'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 262 (class 1259 OID 17281)
-- Name: access_audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.access_audit_log (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    action_type character varying(50) NOT NULL,
    resource_type character varying(50),
    resource_id character varying(255),
    client_account_id uuid,
    engagement_id uuid,
    session_id uuid,
    result character varying(20) NOT NULL,
    reason text,
    ip_address character varying(45),
    user_agent text,
    details json,
    created_at timestamp with time zone DEFAULT now()
);


--
-- TOC entry 232 (class 1259 OID 16691)
-- Name: assessments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.assessments (
    id integer NOT NULL,
    migration_id integer NOT NULL,
    asset_id uuid,
    assessment_type public.assessmenttype NOT NULL,
    status public.assessmentstatus,
    title character varying(255) NOT NULL,
    description text,
    overall_score double precision,
    risk_level public.risklevel,
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


--
-- TOC entry 231 (class 1259 OID 16690)
-- Name: assessments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.assessments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4036 (class 0 OID 0)
-- Dependencies: 231
-- Name: assessments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.assessments_id_seq OWNED BY public.assessments.id;


--
-- TOC entry 230 (class 1259 OID 16670)
-- Name: asset_dependencies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.asset_dependencies (
    id integer NOT NULL,
    source_asset_id uuid NOT NULL,
    target_asset_id uuid NOT NULL,
    dependency_type character varying(50),
    description text,
    criticality character varying(20),
    discovered_at timestamp with time zone DEFAULT now(),
    discovery_method character varying(50),
    confidence_level double precision
);


--
-- TOC entry 229 (class 1259 OID 16669)
-- Name: asset_dependencies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.asset_dependencies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4037 (class 0 OID 0)
-- Dependencies: 229
-- Name: asset_dependencies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.asset_dependencies_id_seq OWNED BY public.asset_dependencies.id;


--
-- TOC entry 273 (class 1259 OID 26292)
-- Name: asset_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.asset_embeddings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    asset_id uuid NOT NULL,
    embedding text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- TOC entry 251 (class 1259 OID 17046)
-- Name: asset_tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.asset_tags (
    id uuid NOT NULL,
    cmdb_asset_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    confidence_score double precision,
    assigned_method character varying(50),
    assigned_by uuid,
    is_validated boolean,
    validated_by uuid,
    validated_at timestamp with time zone,
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 224 (class 1259 OID 16602)
-- Name: assets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.assets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    migration_id integer NOT NULL,
    name character varying(255) NOT NULL,
    asset_type public.assettype NOT NULL,
    description text,
    hostname character varying(255),
    ip_address character varying(45),
    fqdn character varying(255),
    asset_id character varying(100),
    environment character varying(50),
    datacenter character varying(100),
    rack_location character varying(50),
    availability_zone character varying(50),
    operating_system character varying(100),
    os_version character varying(50),
    cpu_cores integer,
    memory_gb double precision,
    storage_gb double precision,
    network_interfaces json,
    status public.assetstatus,
    six_r_strategy public.sixrstrategy,
    migration_priority integer,
    migration_complexity character varying(20),
    migration_wave integer,
    dependencies json,
    dependents json,
    discovered_at timestamp with time zone DEFAULT now(),
    last_scanned timestamp with time zone,
    discovery_method character varying(50),
    discovery_source character varying(100),
    risk_score double precision,
    business_criticality character varying(20),
    compliance_requirements json,
    current_monthly_cost double precision,
    estimated_cloud_cost double precision,
    cost_optimization_potential double precision,
    performance_metrics json,
    security_findings json,
    compatibility_issues json,
    ai_recommendations json,
    confidence_score double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 223 (class 1259 OID 16601)
-- Name: assets_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.assets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4038 (class 0 OID 0)
-- Dependencies: 223
-- Name: assets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.assets_id_seq OWNED BY public.assets.id;


--
-- TOC entry 263 (class 1259 OID 17313)
-- Name: client_access; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.client_access (
    id uuid NOT NULL,
    user_profile_id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    access_level character varying(20) NOT NULL,
    permissions json,
    restricted_environments json,
    restricted_data_types json,
    granted_at timestamp with time zone DEFAULT now(),
    granted_by uuid NOT NULL,
    expires_at timestamp with time zone,
    is_active boolean,
    last_accessed_at timestamp with time zone,
    access_count integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 228 (class 1259 OID 16652)
-- Name: client_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.client_accounts (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    industry character varying(100),
    company_size character varying(50),
    subscription_tier character varying(50),
    billing_contact_email character varying(255),
    settings json,
    branding json,
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    is_active boolean,
    headquarters_location character varying(255),
    primary_contact_name character varying(255),
    primary_contact_email character varying(255),
    primary_contact_phone character varying(50),
    business_objectives json,
    it_guidelines json,
    decision_criteria json,
    agent_preferences json
);


--
-- TOC entry 250 (class 1259 OID 17018)
-- Name: cmdb_asset_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cmdb_asset_embeddings (
    id uuid NOT NULL,
    cmdb_asset_id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    embedding text,
    source_text text,
    embedding_model character varying(100),
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 244 (class 1259 OID 16852)
-- Name: cmdb_assets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cmdb_assets (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    hostname character varying(255),
    asset_type public.assettype NOT NULL,
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
    department character varying(100),
    application_name character varying(255),
    technology_stack character varying(255),
    criticality character varying(20),
    status public.assetstatus,
    six_r_strategy public.sixrstrategy,
    migration_priority integer,
    migration_complexity character varying(20),
    migration_wave integer,
    sixr_ready character varying(50),
    dependencies json,
    related_assets json,
    discovery_method character varying(50),
    discovery_source character varying(100),
    discovery_timestamp timestamp with time zone,
    cpu_utilization_percent double precision,
    memory_utilization_percent double precision,
    disk_iops double precision,
    network_throughput_mbps double precision,
    current_monthly_cost double precision,
    estimated_cloud_cost double precision,
    imported_by uuid,
    imported_at timestamp with time zone,
    source_filename character varying(255),
    raw_data json,
    field_mappings_used json,
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    updated_by uuid
);


--
-- TOC entry 245 (class 1259 OID 16894)
-- Name: cmdb_sixr_analyses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cmdb_sixr_analyses (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    analysis_name character varying(255) NOT NULL,
    description text,
    status character varying(50),
    total_assets integer,
    rehost_count integer,
    replatform_count integer,
    refactor_count integer,
    rearchitect_count integer,
    retire_count integer,
    retain_count integer,
    total_current_cost double precision,
    total_estimated_cost double precision,
    potential_savings double precision,
    analysis_results json,
    recommendations json,
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid
);


--
-- TOC entry 243 (class 1259 OID 16832)
-- Name: custom_target_fields; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.custom_target_fields (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    field_name character varying(255) NOT NULL,
    field_type character varying(50) NOT NULL,
    description text,
    is_required boolean,
    is_searchable boolean,
    is_critical boolean,
    created_by uuid NOT NULL,
    usage_count integer,
    success_rate double precision,
    validation_schema json,
    default_value text,
    allowed_values json,
    common_source_patterns json,
    sample_values json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    last_used_at timestamp with time zone
);


--
-- TOC entry 259 (class 1259 OID 17198)
-- Name: data_import_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_import_sessions (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    session_name character varying(255) NOT NULL,
    session_display_name character varying(255),
    description text,
    session_type character varying(50) NOT NULL,
    auto_created boolean NOT NULL,
    source_filename character varying(255),
    status character varying(20) NOT NULL,
    progress_percentage integer,
    total_imports integer,
    total_assets_processed integer,
    total_records_imported integer,
    data_quality_score integer,
    session_config json,
    business_context json,
    agent_insights json,
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    last_activity_at timestamp with time zone DEFAULT now(),
    created_by uuid NOT NULL,
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 247 (class 1259 OID 16951)
-- Name: data_imports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_imports (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    import_name character varying(255) NOT NULL,
    import_type character varying(50) NOT NULL,
    description text,
    source_filename character varying(255) NOT NULL,
    file_size_bytes integer,
    file_type character varying(100),
    file_hash character varying(64),
    status character varying(20) NOT NULL,
    progress_percentage double precision,
    total_records integer,
    processed_records integer,
    failed_records integer,
    import_config json,
    imported_by uuid NOT NULL,
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 255 (class 1259 OID 17127)
-- Name: data_quality_issues; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_quality_issues (
    id uuid NOT NULL,
    data_import_id uuid NOT NULL,
    raw_record_id uuid,
    issue_type character varying(50) NOT NULL,
    field_name character varying(255),
    current_value text,
    suggested_value text,
    severity character varying(20),
    confidence_score double precision,
    reasoning text,
    status character varying(20),
    resolution_method character varying(50),
    resolved_by uuid,
    resolution_notes text,
    detected_at timestamp with time zone DEFAULT now(),
    resolved_at timestamp with time zone
);


--
-- TOC entry 264 (class 1259 OID 17341)
-- Name: engagement_access; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.engagement_access (
    id uuid NOT NULL,
    user_profile_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    access_level character varying(20) NOT NULL,
    engagement_role character varying(100),
    permissions json,
    restricted_sessions json,
    allowed_session_types json,
    granted_at timestamp with time zone DEFAULT now(),
    granted_by uuid NOT NULL,
    expires_at timestamp with time zone,
    is_active boolean,
    last_accessed_at timestamp with time zone,
    access_count integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 241 (class 1259 OID 16780)
-- Name: engagements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.engagements (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    engagement_type character varying(50),
    status character varying(50),
    priority character varying(20),
    start_date timestamp with time zone,
    target_completion_date timestamp with time zone,
    actual_completion_date timestamp with time zone,
    engagement_lead_id uuid,
    client_contact_name character varying(255),
    client_contact_email character varying(255),
    settings json,
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    is_active boolean,
    migration_scope json,
    team_preferences json
);


--
-- TOC entry 271 (class 1259 OID 17517)
-- Name: enhanced_access_audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.enhanced_access_audit_log (
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
    details json,
    user_role_level character varying(30),
    user_data_scope character varying(20),
    created_at timestamp with time zone DEFAULT now()
);


--
-- TOC entry 268 (class 1259 OID 17435)
-- Name: enhanced_user_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.enhanced_user_profiles (
    user_id uuid NOT NULL,
    status character varying(20) NOT NULL,
    role_level character varying(30) NOT NULL,
    data_scope character varying(20) NOT NULL,
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
    login_count integer,
    failed_login_attempts integer,
    is_deleted boolean,
    deleted_at timestamp with time zone,
    deleted_by uuid,
    delete_reason text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 248 (class 1259 OID 16976)
-- Name: feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback (
    id uuid NOT NULL,
    feedback_type character varying(50) NOT NULL,
    page character varying(255),
    rating integer,
    comment text,
    category character varying(50),
    breadcrumb character varying(500),
    filename character varying(255),
    original_analysis json,
    user_corrections json,
    asset_type_override character varying(100),
    status character varying(20),
    processed boolean,
    user_agent character varying(500),
    user_timestamp character varying(50),
    client_ip character varying(45),
    client_account_id uuid,
    engagement_id uuid,
    learning_patterns_extracted json,
    confidence_impact double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    processed_at timestamp with time zone
);


--
-- TOC entry 249 (class 1259 OID 16997)
-- Name: feedback_summaries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_summaries (
    id uuid NOT NULL,
    feedback_type character varying(50) NOT NULL,
    page character varying(255),
    time_period character varying(20),
    total_feedback integer,
    average_rating double precision,
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


--
-- TOC entry 254 (class 1259 OID 17108)
-- Name: import_field_mappings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.import_field_mappings (
    id uuid NOT NULL,
    data_import_id uuid NOT NULL,
    source_field character varying(255) NOT NULL,
    target_field character varying(255) NOT NULL,
    mapping_type character varying(50) NOT NULL,
    confidence_score double precision,
    is_user_defined boolean,
    is_validated boolean,
    validation_method character varying(50),
    status character varying(20),
    user_feedback text,
    original_ai_suggestion character varying(255),
    correction_reason text,
    transformation_logic json,
    validation_rules json,
    sample_values json,
    suggested_by character varying(50),
    validated_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    validated_at timestamp with time zone
);


--
-- TOC entry 253 (class 1259 OID 17094)
-- Name: import_processing_steps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.import_processing_steps (
    id uuid NOT NULL,
    data_import_id uuid NOT NULL,
    step_name character varying(100) NOT NULL,
    step_order integer NOT NULL,
    status character varying(20) NOT NULL,
    description text,
    input_data json,
    output_data json,
    error_details json,
    records_processed integer,
    duration_seconds double precision,
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);


--
-- TOC entry 266 (class 1259 OID 17398)
-- Name: llm_model_pricing; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_model_pricing (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    provider character varying(100) NOT NULL,
    model_name character varying(255) NOT NULL,
    model_version character varying(100),
    input_cost_per_1k_tokens numeric(10,6) NOT NULL,
    output_cost_per_1k_tokens numeric(10,6) NOT NULL,
    currency character varying(10) NOT NULL,
    effective_from timestamp with time zone NOT NULL,
    effective_to timestamp with time zone,
    is_active boolean NOT NULL,
    source character varying(255),
    notes text
);


--
-- TOC entry 265 (class 1259 OID 17369)
-- Name: llm_usage_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_usage_logs (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    client_account_id uuid,
    engagement_id uuid,
    user_id integer,
    username character varying(255),
    session_id character varying(255),
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
    cost_currency character varying(10) NOT NULL,
    response_time_ms integer,
    success boolean NOT NULL,
    error_type character varying(255),
    error_message text,
    request_data jsonb,
    response_data jsonb,
    additional_metadata jsonb,
    ip_address character varying(45),
    user_agent character varying(500)
);


--
-- TOC entry 267 (class 1259 OID 17411)
-- Name: llm_usage_summary; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_usage_summary (
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
    total_requests integer NOT NULL,
    successful_requests integer NOT NULL,
    failed_requests integer NOT NULL,
    total_input_tokens bigint NOT NULL,
    total_output_tokens bigint NOT NULL,
    total_tokens bigint NOT NULL,
    total_cost numeric(12,6) NOT NULL,
    avg_response_time_ms integer,
    min_response_time_ms integer,
    max_response_time_ms integer
);


--
-- TOC entry 256 (class 1259 OID 17151)
-- Name: mapping_learning_patterns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mapping_learning_patterns (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    source_field_pattern character varying(255) NOT NULL,
    content_pattern json,
    target_field character varying(255) NOT NULL,
    pattern_confidence double precision,
    success_count integer,
    failure_count integer,
    learned_from_mapping_id uuid,
    user_feedback text,
    matching_rules json,
    transformation_hints json,
    quality_checks json,
    times_applied integer,
    last_applied_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 222 (class 1259 OID 16586)
-- Name: migration_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.migration_logs (
    id integer NOT NULL,
    migration_id integer NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    level character varying(20),
    message text NOT NULL,
    details json,
    phase public.migrationphase,
    user_id character varying(100),
    action character varying(100)
);


--
-- TOC entry 221 (class 1259 OID 16585)
-- Name: migration_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.migration_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4039 (class 0 OID 0)
-- Dependencies: 221
-- Name: migration_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.migration_logs_id_seq OWNED BY public.migration_logs.id;


--
-- TOC entry 246 (class 1259 OID 16922)
-- Name: migration_waves; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.migration_waves (
    id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    engagement_id uuid NOT NULL,
    wave_number integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    status character varying(50),
    planned_start_date timestamp with time zone,
    planned_end_date timestamp with time zone,
    actual_start_date timestamp with time zone,
    actual_end_date timestamp with time zone,
    total_assets integer,
    completed_assets integer,
    failed_assets integer,
    estimated_cost double precision,
    actual_cost double precision,
    estimated_effort_hours double precision,
    actual_effort_hours double precision,
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid
);


--
-- TOC entry 216 (class 1259 OID 16538)
-- Name: migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.migrations (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    status public.migrationstatus,
    current_phase public.migrationphase,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    start_date timestamp with time zone,
    target_completion_date timestamp with time zone,
    actual_completion_date timestamp with time zone,
    source_environment character varying(100),
    target_environment character varying(100),
    migration_strategy character varying(50),
    progress_percentage integer,
    total_assets integer,
    migrated_assets integer,
    ai_recommendations json,
    risk_assessment json,
    cost_estimates json,
    settings json
);


--
-- TOC entry 215 (class 1259 OID 16537)
-- Name: migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.migrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4040 (class 0 OID 0)
-- Dependencies: 215
-- Name: migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.migrations_id_seq OWNED BY public.migrations.id;


--
-- TOC entry 252 (class 1259 OID 17075)
-- Name: raw_import_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.raw_import_records (
    id uuid NOT NULL,
    data_import_id uuid NOT NULL,
    row_number integer NOT NULL,
    record_id character varying(255),
    raw_data json NOT NULL,
    processed_data json,
    validation_errors json,
    processing_notes text,
    is_processed boolean,
    is_valid boolean,
    cmdb_asset_id uuid,
    created_at timestamp with time zone DEFAULT now(),
    processed_at timestamp with time zone
);


--
-- TOC entry 269 (class 1259 OID 17473)
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_permissions (
    id uuid NOT NULL,
    role_level character varying(30) NOT NULL,
    can_manage_platform_settings boolean,
    can_manage_all_clients boolean,
    can_manage_all_users boolean,
    can_purge_deleted_data boolean,
    can_view_system_logs boolean,
    can_create_clients boolean,
    can_modify_client_settings boolean,
    can_manage_client_users boolean,
    can_delete_client_data boolean,
    can_create_engagements boolean,
    can_modify_engagement_settings boolean,
    can_manage_engagement_users boolean,
    can_delete_engagement_data boolean,
    can_import_data boolean,
    can_export_data boolean,
    can_view_analytics boolean,
    can_modify_data boolean,
    can_configure_agents boolean,
    can_view_agent_insights boolean,
    can_approve_agent_decisions boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 227 (class 1259 OID 16636)
-- Name: sixr_analyses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sixr_analyses (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    migration_id integer,
    name character varying(255) NOT NULL,
    description text,
    status public.analysisstatus NOT NULL,
    priority integer,
    application_ids json,
    application_data json,
    current_iteration integer,
    progress_percentage double precision,
    estimated_completion timestamp with time zone,
    final_recommendation public.sixrstrategy,
    confidence_score double precision,
    created_by character varying(100),
    updated_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    analysis_config json
);


--
-- TOC entry 272 (class 1259 OID 26259)
-- Name: sixr_analysis_parameters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sixr_analysis_parameters (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    analysis_id uuid NOT NULL,
    iteration_number integer NOT NULL,
    business_value double precision NOT NULL,
    technical_complexity double precision NOT NULL,
    migration_urgency double precision NOT NULL,
    compliance_requirements double precision NOT NULL,
    cost_sensitivity double precision NOT NULL,
    risk_tolerance double precision NOT NULL,
    innovation_priority double precision NOT NULL,
    application_type character varying(20),
    parameter_source character varying(50),
    confidence_level double precision,
    created_by character varying(100),
    updated_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    parameter_notes text,
    validation_status character varying(20)
);


--
-- TOC entry 236 (class 1259 OID 16729)
-- Name: sixr_iterations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sixr_iterations (
    id integer NOT NULL,
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
    status character varying(20),
    error_details json,
    created_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);


--
-- TOC entry 235 (class 1259 OID 16728)
-- Name: sixr_iterations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sixr_iterations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4041 (class 0 OID 0)
-- Dependencies: 235
-- Name: sixr_iterations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sixr_iterations_id_seq OWNED BY public.sixr_iterations.id;


--
-- TOC entry 234 (class 1259 OID 16713)
-- Name: sixr_parameters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sixr_parameters (
    id integer NOT NULL,
    analysis_id uuid NOT NULL,
    iteration_number integer NOT NULL,
    business_value double precision NOT NULL,
    technical_complexity double precision NOT NULL,
    migration_urgency double precision NOT NULL,
    compliance_requirements double precision NOT NULL,
    cost_sensitivity double precision NOT NULL,
    risk_tolerance double precision NOT NULL,
    innovation_priority double precision NOT NULL,
    application_type character varying(20),
    parameter_source character varying(50),
    confidence_level double precision,
    created_by character varying(100),
    updated_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    parameter_notes text,
    validation_status character varying(20)
);


--
-- TOC entry 233 (class 1259 OID 16712)
-- Name: sixr_parameters_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sixr_parameters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4042 (class 0 OID 0)
-- Dependencies: 233
-- Name: sixr_parameters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sixr_parameters_id_seq OWNED BY public.sixr_parameters.id;


--
-- TOC entry 240 (class 1259 OID 16760)
-- Name: sixr_question_responses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sixr_question_responses (
    id integer NOT NULL,
    analysis_id uuid NOT NULL,
    iteration_number integer NOT NULL,
    question_id character varying(100) NOT NULL,
    response_value json,
    response_text text,
    confidence double precision,
    source character varying(50),
    response_time double precision,
    validation_status character varying(20),
    validation_errors json,
    created_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 239 (class 1259 OID 16759)
-- Name: sixr_question_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sixr_question_responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4043 (class 0 OID 0)
-- Dependencies: 239
-- Name: sixr_question_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sixr_question_responses_id_seq OWNED BY public.sixr_question_responses.id;


--
-- TOC entry 218 (class 1259 OID 16550)
-- Name: sixr_questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sixr_questions (
    id integer NOT NULL,
    question_id character varying(100) NOT NULL,
    question_text text NOT NULL,
    question_type public.questiontype NOT NULL,
    category character varying(100) NOT NULL,
    priority integer,
    required boolean,
    active boolean,
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
    version character varying(20),
    parent_question_id character varying(100)
);


--
-- TOC entry 217 (class 1259 OID 16549)
-- Name: sixr_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sixr_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4044 (class 0 OID 0)
-- Dependencies: 217
-- Name: sixr_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sixr_questions_id_seq OWNED BY public.sixr_questions.id;


--
-- TOC entry 238 (class 1259 OID 16745)
-- Name: sixr_recommendations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sixr_recommendations (
    id integer NOT NULL,
    analysis_id uuid NOT NULL,
    iteration_number integer,
    recommended_strategy public.sixrstrategy NOT NULL,
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
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by character varying(100)
);


--
-- TOC entry 237 (class 1259 OID 16744)
-- Name: sixr_recommendations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sixr_recommendations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4045 (class 0 OID 0)
-- Dependencies: 237
-- Name: sixr_recommendations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sixr_recommendations_id_seq OWNED BY public.sixr_recommendations.id;


--
-- TOC entry 270 (class 1259 OID 17480)
-- Name: soft_deleted_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.soft_deleted_items (
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
    status character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 220 (class 1259 OID 16573)
-- Name: tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tags (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    category character varying(50) NOT NULL,
    description text,
    reference_embedding text,
    confidence_threshold double precision,
    is_active boolean,
    usage_count integer,
    last_used timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 242 (class 1259 OID 16808)
-- Name: user_account_associations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_account_associations (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    client_account_id uuid NOT NULL,
    role character varying(50) NOT NULL,
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid
);


--
-- TOC entry 260 (class 1259 OID 17229)
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_profiles (
    user_id uuid NOT NULL,
    status character varying(20) NOT NULL,
    approval_requested_at timestamp with time zone DEFAULT now(),
    approved_at timestamp with time zone,
    approved_by uuid,
    registration_reason text,
    organization character varying(255),
    role_description character varying(255),
    requested_access_level character varying(20),
    phone_number character varying(20),
    manager_email character varying(255),
    linkedin_profile character varying(255),
    last_login_at timestamp with time zone,
    login_count integer,
    failed_login_attempts integer,
    last_failed_login timestamp with time zone,
    notification_preferences json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 261 (class 1259 OID 17249)
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_roles (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    role_type character varying(50) NOT NULL,
    role_name character varying(100) NOT NULL,
    description text,
    permissions json,
    scope_type character varying(20),
    scope_client_id uuid,
    scope_engagement_id uuid,
    is_active boolean,
    assigned_at timestamp with time zone DEFAULT now(),
    assigned_by uuid NOT NULL,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 219 (class 1259 OID 16561)
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255),
    first_name character varying(100),
    last_name character varying(100),
    is_active boolean,
    is_verified boolean,
    is_mock boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    last_login timestamp with time zone
);


--
-- TOC entry 226 (class 1259 OID 16620)
-- Name: wave_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wave_plans (
    id integer NOT NULL,
    migration_id integer NOT NULL,
    wave_number integer NOT NULL,
    wave_name character varying(255),
    description text,
    planned_start_date timestamp with time zone,
    planned_end_date timestamp with time zone,
    actual_start_date timestamp with time zone,
    actual_end_date timestamp with time zone,
    total_assets integer,
    completed_assets integer,
    estimated_effort_hours integer,
    estimated_cost double precision,
    prerequisites json,
    dependencies json,
    constraints json,
    overall_risk_level public.risklevel,
    complexity_score double precision,
    success_criteria json,
    status character varying(50),
    progress_percentage double precision,
    ai_recommendations json,
    optimization_score double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 225 (class 1259 OID 16619)
-- Name: wave_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.wave_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4046 (class 0 OID 0)
-- Dependencies: 225
-- Name: wave_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.wave_plans_id_seq OWNED BY public.wave_plans.id;


--
-- TOC entry 258 (class 1259 OID 17174)
-- Name: workflow_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_progress (
    id integer NOT NULL,
    asset_id uuid NOT NULL,
    phase character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    progress_percentage double precision,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    notes text,
    errors json,
    client_account_id uuid,
    engagement_id uuid,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- TOC entry 257 (class 1259 OID 17173)
-- Name: workflow_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.workflow_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4047 (class 0 OID 0)
-- Dependencies: 257
-- Name: workflow_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.workflow_progress_id_seq OWNED BY public.workflow_progress.id;


--
-- TOC entry 3446 (class 2604 OID 16694)
-- Name: assessments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessments ALTER COLUMN id SET DEFAULT nextval('public.assessments_id_seq'::regclass);


--
-- TOC entry 3444 (class 2604 OID 16673)
-- Name: asset_dependencies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_dependencies ALTER COLUMN id SET DEFAULT nextval('public.asset_dependencies_id_seq'::regclass);


--
-- TOC entry 3434 (class 2604 OID 16589)
-- Name: migration_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.migration_logs ALTER COLUMN id SET DEFAULT nextval('public.migration_logs_id_seq'::regclass);


--
-- TOC entry 3428 (class 2604 OID 16541)
-- Name: migrations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.migrations ALTER COLUMN id SET DEFAULT nextval('public.migrations_id_seq'::regclass);


--
-- TOC entry 3451 (class 2604 OID 16732)
-- Name: sixr_iterations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_iterations ALTER COLUMN id SET DEFAULT nextval('public.sixr_iterations_id_seq'::regclass);


--
-- TOC entry 3449 (class 2604 OID 16716)
-- Name: sixr_parameters id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_parameters ALTER COLUMN id SET DEFAULT nextval('public.sixr_parameters_id_seq'::regclass);


--
-- TOC entry 3454 (class 2604 OID 16763)
-- Name: sixr_question_responses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_question_responses ALTER COLUMN id SET DEFAULT nextval('public.sixr_question_responses_id_seq'::regclass);


--
-- TOC entry 3430 (class 2604 OID 16553)
-- Name: sixr_questions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_questions ALTER COLUMN id SET DEFAULT nextval('public.sixr_questions_id_seq'::regclass);


--
-- TOC entry 3453 (class 2604 OID 16748)
-- Name: sixr_recommendations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_recommendations ALTER COLUMN id SET DEFAULT nextval('public.sixr_recommendations_id_seq'::regclass);


--
-- TOC entry 3439 (class 2604 OID 16623)
-- Name: wave_plans id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wave_plans ALTER COLUMN id SET DEFAULT nextval('public.wave_plans_id_seq'::regclass);


--
-- TOC entry 3473 (class 2604 OID 17177)
-- Name: workflow_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_progress ALTER COLUMN id SET DEFAULT nextval('public.workflow_progress_id_seq'::regclass);


--
-- TOC entry 4019 (class 0 OID 17281)
-- Dependencies: 262
-- Data for Name: access_audit_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.access_audit_log (id, user_id, action_type, resource_type, resource_id, client_account_id, engagement_id, session_id, result, reason, ip_address, user_agent, details, created_at) FROM stdin;
\.


--
-- TOC entry 3989 (class 0 OID 16691)
-- Dependencies: 232
-- Data for Name: assessments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.assessments (id, migration_id, asset_id, assessment_type, status, title, description, overall_score, risk_level, confidence_level, recommended_strategy, alternative_strategies, strategy_rationale, current_cost, estimated_migration_cost, estimated_target_cost, cost_savings_potential, roi_months, identified_risks, risk_mitigation, blockers, dependencies_impact, technical_complexity, compatibility_score, modernization_opportunities, performance_impact, business_criticality, downtime_requirements, user_impact, compliance_considerations, ai_insights, ai_confidence, ai_model_version, estimated_effort_hours, estimated_duration_days, recommended_wave, prerequisites, assessor, assessment_date, review_date, approval_date, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3987 (class 0 OID 16670)
-- Dependencies: 230
-- Data for Name: asset_dependencies; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.asset_dependencies (id, source_asset_id, target_asset_id, dependency_type, description, criticality, discovered_at, discovery_method, confidence_level) FROM stdin;
\.


--
-- TOC entry 4030 (class 0 OID 26292)
-- Dependencies: 273
-- Data for Name: asset_embeddings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.asset_embeddings (id, asset_id, embedding, metadata, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4008 (class 0 OID 17046)
-- Dependencies: 251
-- Data for Name: asset_tags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.asset_tags (id, cmdb_asset_id, tag_id, confidence_score, assigned_method, assigned_by, is_validated, validated_by, validated_at, is_mock, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3981 (class 0 OID 16602)
-- Dependencies: 224
-- Data for Name: assets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.assets (id, migration_id, name, asset_type, description, hostname, ip_address, fqdn, asset_id, environment, datacenter, rack_location, availability_zone, operating_system, os_version, cpu_cores, memory_gb, storage_gb, network_interfaces, status, six_r_strategy, migration_priority, migration_complexity, migration_wave, dependencies, dependents, discovered_at, last_scanned, discovery_method, discovery_source, risk_score, business_criticality, compliance_requirements, current_monthly_cost, estimated_cloud_cost, cost_optimization_potential, performance_metrics, security_findings, compatibility_issues, ai_recommendations, confidence_score, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4020 (class 0 OID 17313)
-- Dependencies: 263
-- Data for Name: client_access; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.client_access (id, user_profile_id, client_account_id, access_level, permissions, restricted_environments, restricted_data_types, granted_at, granted_by, expires_at, is_active, last_accessed_at, access_count, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3985 (class 0 OID 16652)
-- Dependencies: 228
-- Data for Name: client_accounts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.client_accounts (id, name, slug, description, industry, company_size, subscription_tier, billing_contact_email, settings, branding, is_mock, created_at, updated_at, created_by, is_active, headquarters_location, primary_contact_name, primary_contact_email, primary_contact_phone, business_objectives, it_guidelines, decision_criteria, agent_preferences) FROM stdin;
\.


--
-- TOC entry 4007 (class 0 OID 17018)
-- Dependencies: 250
-- Data for Name: cmdb_asset_embeddings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cmdb_asset_embeddings (id, cmdb_asset_id, client_account_id, engagement_id, embedding, source_text, embedding_model, is_mock, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4001 (class 0 OID 16852)
-- Dependencies: 244
-- Data for Name: cmdb_assets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cmdb_assets (id, client_account_id, engagement_id, name, hostname, asset_type, description, ip_address, fqdn, mac_address, environment, location, datacenter, rack_location, availability_zone, operating_system, os_version, cpu_cores, memory_gb, storage_gb, business_owner, department, application_name, technology_stack, criticality, status, six_r_strategy, migration_priority, migration_complexity, migration_wave, sixr_ready, dependencies, related_assets, discovery_method, discovery_source, discovery_timestamp, cpu_utilization_percent, memory_utilization_percent, disk_iops, network_throughput_mbps, current_monthly_cost, estimated_cloud_cost, imported_by, imported_at, source_filename, raw_data, field_mappings_used, is_mock, created_at, updated_at, created_by, updated_by) FROM stdin;
\.


--
-- TOC entry 4002 (class 0 OID 16894)
-- Dependencies: 245
-- Data for Name: cmdb_sixr_analyses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cmdb_sixr_analyses (id, client_account_id, engagement_id, analysis_name, description, status, total_assets, rehost_count, replatform_count, refactor_count, rearchitect_count, retire_count, retain_count, total_current_cost, total_estimated_cost, potential_savings, analysis_results, recommendations, is_mock, created_at, updated_at, created_by) FROM stdin;
\.


--
-- TOC entry 4000 (class 0 OID 16832)
-- Dependencies: 243
-- Data for Name: custom_target_fields; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.custom_target_fields (id, client_account_id, field_name, field_type, description, is_required, is_searchable, is_critical, created_by, usage_count, success_rate, validation_schema, default_value, allowed_values, common_source_patterns, sample_values, created_at, updated_at, last_used_at) FROM stdin;
\.


--
-- TOC entry 4016 (class 0 OID 17198)
-- Dependencies: 259
-- Data for Name: data_import_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.data_import_sessions (id, client_account_id, engagement_id, session_name, session_display_name, description, session_type, auto_created, source_filename, status, progress_percentage, total_imports, total_assets_processed, total_records_imported, data_quality_score, session_config, business_context, agent_insights, started_at, completed_at, last_activity_at, created_by, is_mock, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4004 (class 0 OID 16951)
-- Dependencies: 247
-- Data for Name: data_imports; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.data_imports (id, client_account_id, engagement_id, import_name, import_type, description, source_filename, file_size_bytes, file_type, file_hash, status, progress_percentage, total_records, processed_records, failed_records, import_config, imported_by, started_at, completed_at, is_mock, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4012 (class 0 OID 17127)
-- Dependencies: 255
-- Data for Name: data_quality_issues; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.data_quality_issues (id, data_import_id, raw_record_id, issue_type, field_name, current_value, suggested_value, severity, confidence_score, reasoning, status, resolution_method, resolved_by, resolution_notes, detected_at, resolved_at) FROM stdin;
\.


--
-- TOC entry 4021 (class 0 OID 17341)
-- Dependencies: 264
-- Data for Name: engagement_access; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.engagement_access (id, user_profile_id, engagement_id, access_level, engagement_role, permissions, restricted_sessions, allowed_session_types, granted_at, granted_by, expires_at, is_active, last_accessed_at, access_count, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3998 (class 0 OID 16780)
-- Dependencies: 241
-- Data for Name: engagements; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.engagements (id, client_account_id, name, slug, description, engagement_type, status, priority, start_date, target_completion_date, actual_completion_date, engagement_lead_id, client_contact_name, client_contact_email, settings, is_mock, created_at, updated_at, created_by, is_active, migration_scope, team_preferences) FROM stdin;
\.


--
-- TOC entry 4028 (class 0 OID 17517)
-- Dependencies: 271
-- Data for Name: enhanced_access_audit_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.enhanced_access_audit_log (id, user_id, action_type, resource_type, resource_id, client_account_id, engagement_id, result, reason, ip_address, user_agent, details, user_role_level, user_data_scope, created_at) FROM stdin;
\.


--
-- TOC entry 4025 (class 0 OID 17435)
-- Dependencies: 268
-- Data for Name: enhanced_user_profiles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.enhanced_user_profiles (user_id, status, role_level, data_scope, scope_client_account_id, scope_engagement_id, registration_reason, organization, role_description, phone_number, manager_email, approval_requested_at, approved_at, approved_by, last_login_at, login_count, failed_login_attempts, is_deleted, deleted_at, deleted_by, delete_reason, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4005 (class 0 OID 16976)
-- Dependencies: 248
-- Data for Name: feedback; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback (id, feedback_type, page, rating, comment, category, breadcrumb, filename, original_analysis, user_corrections, asset_type_override, status, processed, user_agent, user_timestamp, client_ip, client_account_id, engagement_id, learning_patterns_extracted, confidence_impact, created_at, updated_at, processed_at) FROM stdin;
ae0a40aa-d779-4f8f-b7b4-71a69fa04bdd	page_feedback	Asset Inventory	4	Testing feedback on Vercel	ui	Discovery > Asset Inventory	\N	\N	\N	\N	new	f	\N	2025-05-31T15:42:25.086Z	\N	\N	\N	\N	0	2025-05-31 15:42:25.476067+00	\N	\N
\.


--
-- TOC entry 4006 (class 0 OID 16997)
-- Dependencies: 249
-- Data for Name: feedback_summaries; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feedback_summaries (id, feedback_type, page, time_period, total_feedback, average_rating, status_counts, rating_distribution, category_counts, feedback_trend, rating_trend, client_account_id, engagement_id, last_calculated, calculation_duration_ms) FROM stdin;
\.


--
-- TOC entry 4011 (class 0 OID 17108)
-- Dependencies: 254
-- Data for Name: import_field_mappings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.import_field_mappings (id, data_import_id, source_field, target_field, mapping_type, confidence_score, is_user_defined, is_validated, validation_method, status, user_feedback, original_ai_suggestion, correction_reason, transformation_logic, validation_rules, sample_values, suggested_by, validated_by, created_at, validated_at) FROM stdin;
\.


--
-- TOC entry 4010 (class 0 OID 17094)
-- Dependencies: 253
-- Data for Name: import_processing_steps; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.import_processing_steps (id, data_import_id, step_name, step_order, status, description, input_data, output_data, error_details, records_processed, duration_seconds, started_at, completed_at) FROM stdin;
\.


--
-- TOC entry 4023 (class 0 OID 17398)
-- Dependencies: 266
-- Data for Name: llm_model_pricing; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.llm_model_pricing (id, created_at, updated_at, provider, model_name, model_version, input_cost_per_1k_tokens, output_cost_per_1k_tokens, currency, effective_from, effective_to, is_active, source, notes) FROM stdin;
\.


--
-- TOC entry 4022 (class 0 OID 17369)
-- Dependencies: 265
-- Data for Name: llm_usage_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.llm_usage_logs (id, created_at, updated_at, client_account_id, engagement_id, user_id, username, session_id, request_id, endpoint, page_context, feature_context, llm_provider, model_name, model_version, input_tokens, output_tokens, total_tokens, input_cost, output_cost, total_cost, cost_currency, response_time_ms, success, error_type, error_message, request_data, response_data, additional_metadata, ip_address, user_agent) FROM stdin;
\.


--
-- TOC entry 4024 (class 0 OID 17411)
-- Dependencies: 267
-- Data for Name: llm_usage_summary; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.llm_usage_summary (id, created_at, updated_at, period_type, period_start, period_end, client_account_id, engagement_id, user_id, llm_provider, model_name, page_context, feature_context, total_requests, successful_requests, failed_requests, total_input_tokens, total_output_tokens, total_tokens, total_cost, avg_response_time_ms, min_response_time_ms, max_response_time_ms) FROM stdin;
\.


--
-- TOC entry 4013 (class 0 OID 17151)
-- Dependencies: 256
-- Data for Name: mapping_learning_patterns; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.mapping_learning_patterns (id, client_account_id, source_field_pattern, content_pattern, target_field, pattern_confidence, success_count, failure_count, learned_from_mapping_id, user_feedback, matching_rules, transformation_hints, quality_checks, times_applied, last_applied_at, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3979 (class 0 OID 16586)
-- Dependencies: 222
-- Data for Name: migration_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.migration_logs (id, migration_id, "timestamp", level, message, details, phase, user_id, action) FROM stdin;
\.


--
-- TOC entry 4003 (class 0 OID 16922)
-- Dependencies: 246
-- Data for Name: migration_waves; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.migration_waves (id, client_account_id, engagement_id, wave_number, name, description, status, planned_start_date, planned_end_date, actual_start_date, actual_end_date, total_assets, completed_assets, failed_assets, estimated_cost, actual_cost, estimated_effort_hours, actual_effort_hours, is_mock, created_at, updated_at, created_by) FROM stdin;
\.


--
-- TOC entry 3973 (class 0 OID 16538)
-- Dependencies: 216
-- Data for Name: migrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.migrations (id, name, description, status, current_phase, created_at, updated_at, start_date, target_completion_date, actual_completion_date, source_environment, target_environment, migration_strategy, progress_percentage, total_assets, migrated_assets, ai_recommendations, risk_assessment, cost_estimates, settings) FROM stdin;
\.


--
-- TOC entry 4009 (class 0 OID 17075)
-- Dependencies: 252
-- Data for Name: raw_import_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.raw_import_records (id, data_import_id, row_number, record_id, raw_data, processed_data, validation_errors, processing_notes, is_processed, is_valid, cmdb_asset_id, created_at, processed_at) FROM stdin;
\.


--
-- TOC entry 4026 (class 0 OID 17473)
-- Dependencies: 269
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_permissions (id, role_level, can_manage_platform_settings, can_manage_all_clients, can_manage_all_users, can_purge_deleted_data, can_view_system_logs, can_create_clients, can_modify_client_settings, can_manage_client_users, can_delete_client_data, can_create_engagements, can_modify_engagement_settings, can_manage_engagement_users, can_delete_engagement_data, can_import_data, can_export_data, can_view_analytics, can_modify_data, can_configure_agents, can_view_agent_insights, can_approve_agent_decisions, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3984 (class 0 OID 16636)
-- Dependencies: 227
-- Data for Name: sixr_analyses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sixr_analyses (id, migration_id, name, description, status, priority, application_ids, application_data, current_iteration, progress_percentage, estimated_completion, final_recommendation, confidence_score, created_by, updated_by, created_at, updated_at, analysis_config) FROM stdin;
\.


--
-- TOC entry 4029 (class 0 OID 26259)
-- Dependencies: 272
-- Data for Name: sixr_analysis_parameters; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sixr_analysis_parameters (id, analysis_id, iteration_number, business_value, technical_complexity, migration_urgency, compliance_requirements, cost_sensitivity, risk_tolerance, innovation_priority, application_type, parameter_source, confidence_level, created_by, updated_by, created_at, updated_at, parameter_notes, validation_status) FROM stdin;
\.


--
-- TOC entry 3993 (class 0 OID 16729)
-- Dependencies: 236
-- Data for Name: sixr_iterations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sixr_iterations (id, analysis_id, iteration_number, iteration_name, iteration_reason, stakeholder_feedback, parameter_changes, question_responses, recommendation_data, confidence_score, analysis_duration, agent_insights, status, error_details, created_by, created_at, completed_at) FROM stdin;
\.


--
-- TOC entry 3991 (class 0 OID 16713)
-- Dependencies: 234
-- Data for Name: sixr_parameters; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sixr_parameters (id, analysis_id, iteration_number, business_value, technical_complexity, migration_urgency, compliance_requirements, cost_sensitivity, risk_tolerance, innovation_priority, application_type, parameter_source, confidence_level, created_by, updated_by, created_at, updated_at, parameter_notes, validation_status) FROM stdin;
\.


--
-- TOC entry 3997 (class 0 OID 16760)
-- Dependencies: 240
-- Data for Name: sixr_question_responses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sixr_question_responses (id, analysis_id, iteration_number, question_id, response_value, response_text, confidence, source, response_time, validation_status, validation_errors, created_by, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3975 (class 0 OID 16550)
-- Dependencies: 218
-- Data for Name: sixr_questions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sixr_questions (id, question_id, question_text, question_type, category, priority, required, active, options, validation_rules, help_text, depends_on, show_conditions, skip_conditions, created_by, updated_by, created_at, updated_at, version, parent_question_id) FROM stdin;
\.


--
-- TOC entry 3995 (class 0 OID 16745)
-- Dependencies: 238
-- Data for Name: sixr_recommendations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sixr_recommendations (id, analysis_id, iteration_number, recommended_strategy, confidence_score, strategy_scores, key_factors, assumptions, next_steps, estimated_effort, estimated_timeline, estimated_cost_impact, risk_factors, business_benefits, technical_benefits, created_at, updated_at, created_by) FROM stdin;
\.


--
-- TOC entry 4027 (class 0 OID 17480)
-- Dependencies: 270
-- Data for Name: soft_deleted_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.soft_deleted_items (id, item_type, item_id, item_name, client_account_id, engagement_id, deleted_by, deleted_at, delete_reason, reviewed_by, reviewed_at, review_decision, review_notes, purged_at, purged_by, status, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3977 (class 0 OID 16573)
-- Dependencies: 220
-- Data for Name: tags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tags (id, name, category, description, reference_embedding, confidence_threshold, is_active, usage_count, last_used, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3999 (class 0 OID 16808)
-- Dependencies: 242
-- Data for Name: user_account_associations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_account_associations (id, user_id, client_account_id, role, is_mock, created_at, updated_at, created_by) FROM stdin;
\.


--
-- TOC entry 4017 (class 0 OID 17229)
-- Dependencies: 260
-- Data for Name: user_profiles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_profiles (user_id, status, approval_requested_at, approved_at, approved_by, registration_reason, organization, role_description, requested_access_level, phone_number, manager_email, linkedin_profile, last_login_at, login_count, failed_login_attempts, last_failed_login, notification_preferences, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4018 (class 0 OID 17249)
-- Dependencies: 261
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_roles (id, user_id, role_type, role_name, description, permissions, scope_type, scope_client_id, scope_engagement_id, is_active, assigned_at, assigned_by, expires_at, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3976 (class 0 OID 16561)
-- Dependencies: 219
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, email, password_hash, first_name, last_name, is_active, is_verified, is_mock, created_at, updated_at, last_login) FROM stdin;
\.


--
-- TOC entry 3983 (class 0 OID 16620)
-- Dependencies: 226
-- Data for Name: wave_plans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.wave_plans (id, migration_id, wave_number, wave_name, description, planned_start_date, planned_end_date, actual_start_date, actual_end_date, total_assets, completed_assets, estimated_effort_hours, estimated_cost, prerequisites, dependencies, constraints, overall_risk_level, complexity_score, success_criteria, status, progress_percentage, ai_recommendations, optimization_score, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4015 (class 0 OID 17174)
-- Dependencies: 258
-- Data for Name: workflow_progress; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.workflow_progress (id, asset_id, phase, status, progress_percentage, started_at, completed_at, notes, errors, client_account_id, engagement_id, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4048 (class 0 OID 0)
-- Dependencies: 231
-- Name: assessments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.assessments_id_seq', 1, false);


--
-- TOC entry 4049 (class 0 OID 0)
-- Dependencies: 229
-- Name: asset_dependencies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.asset_dependencies_id_seq', 1, false);


--
-- TOC entry 4050 (class 0 OID 0)
-- Dependencies: 223
-- Name: assets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.assets_id_seq', 1, false);


--
-- TOC entry 4051 (class 0 OID 0)
-- Dependencies: 221
-- Name: migration_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.migration_logs_id_seq', 1, false);


--
-- TOC entry 4052 (class 0 OID 0)
-- Dependencies: 215
-- Name: migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.migrations_id_seq', 1, false);


--
-- TOC entry 4053 (class 0 OID 0)
-- Dependencies: 235
-- Name: sixr_iterations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sixr_iterations_id_seq', 1, false);


--
-- TOC entry 4054 (class 0 OID 0)
-- Dependencies: 233
-- Name: sixr_parameters_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sixr_parameters_id_seq', 1, false);


--
-- TOC entry 4055 (class 0 OID 0)
-- Dependencies: 239
-- Name: sixr_question_responses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sixr_question_responses_id_seq', 1, false);


--
-- TOC entry 4056 (class 0 OID 0)
-- Dependencies: 217
-- Name: sixr_questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sixr_questions_id_seq', 1, false);


--
-- TOC entry 4057 (class 0 OID 0)
-- Dependencies: 237
-- Name: sixr_recommendations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sixr_recommendations_id_seq', 1, false);


--
-- TOC entry 4058 (class 0 OID 0)
-- Dependencies: 225
-- Name: wave_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.wave_plans_id_seq', 1, false);


--
-- TOC entry 4059 (class 0 OID 0)
-- Dependencies: 257
-- Name: workflow_progress_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.workflow_progress_id_seq', 1, false);


--
-- TOC entry 3665 (class 2606 OID 17288)
-- Name: access_audit_log access_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_audit_log
    ADD CONSTRAINT access_audit_log_pkey PRIMARY KEY (id);


--
-- TOC entry 3547 (class 2606 OID 16700)
-- Name: assessments assessments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_pkey PRIMARY KEY (id);


--
-- TOC entry 3544 (class 2606 OID 16678)
-- Name: asset_dependencies asset_dependencies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_dependencies
    ADD CONSTRAINT asset_dependencies_pkey PRIMARY KEY (id);


--
-- TOC entry 3729 (class 2606 OID 26301)
-- Name: asset_embeddings asset_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_embeddings
    ADD CONSTRAINT asset_embeddings_pkey PRIMARY KEY (id);


--
-- TOC entry 3624 (class 2606 OID 17051)
-- Name: asset_tags asset_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_tags
    ADD CONSTRAINT asset_tags_pkey PRIMARY KEY (id);


--
-- TOC entry 3527 (class 2606 OID 26346)
-- Name: assets assets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_pkey PRIMARY KEY (id);


--
-- TOC entry 3671 (class 2606 OID 17321)
-- Name: client_access client_access_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_access
    ADD CONSTRAINT client_access_pkey PRIMARY KEY (id);


--
-- TOC entry 3538 (class 2606 OID 16659)
-- Name: client_accounts client_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_accounts
    ADD CONSTRAINT client_accounts_pkey PRIMARY KEY (id);


--
-- TOC entry 3617 (class 2606 OID 17025)
-- Name: cmdb_asset_embeddings cmdb_asset_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_asset_embeddings
    ADD CONSTRAINT cmdb_asset_embeddings_pkey PRIMARY KEY (id);


--
-- TOC entry 3578 (class 2606 OID 16859)
-- Name: cmdb_assets cmdb_assets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_assets
    ADD CONSTRAINT cmdb_assets_pkey PRIMARY KEY (id);


--
-- TOC entry 3589 (class 2606 OID 16901)
-- Name: cmdb_sixr_analyses cmdb_sixr_analyses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_sixr_analyses
    ADD CONSTRAINT cmdb_sixr_analyses_pkey PRIMARY KEY (id);


--
-- TOC entry 3574 (class 2606 OID 16839)
-- Name: custom_target_fields custom_target_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.custom_target_fields
    ADD CONSTRAINT custom_target_fields_pkey PRIMARY KEY (id);


--
-- TOC entry 3649 (class 2606 OID 17207)
-- Name: data_import_sessions data_import_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_import_sessions
    ADD CONSTRAINT data_import_sessions_pkey PRIMARY KEY (id);


--
-- TOC entry 3604 (class 2606 OID 16959)
-- Name: data_imports data_imports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_imports
    ADD CONSTRAINT data_imports_pkey PRIMARY KEY (id);


--
-- TOC entry 3638 (class 2606 OID 17134)
-- Name: data_quality_issues data_quality_issues_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_issues
    ADD CONSTRAINT data_quality_issues_pkey PRIMARY KEY (id);


--
-- TOC entry 3677 (class 2606 OID 17349)
-- Name: engagement_access engagement_access_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.engagement_access
    ADD CONSTRAINT engagement_access_pkey PRIMARY KEY (id);


--
-- TOC entry 3562 (class 2606 OID 16787)
-- Name: engagements engagements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.engagements
    ADD CONSTRAINT engagements_pkey PRIMARY KEY (id);


--
-- TOC entry 3722 (class 2606 OID 17524)
-- Name: enhanced_access_audit_log enhanced_access_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enhanced_access_audit_log
    ADD CONSTRAINT enhanced_access_audit_log_pkey PRIMARY KEY (id);


--
-- TOC entry 3708 (class 2606 OID 17443)
-- Name: enhanced_user_profiles enhanced_user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_pkey PRIMARY KEY (user_id);


--
-- TOC entry 3607 (class 2606 OID 16983)
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- TOC entry 3612 (class 2606 OID 17004)
-- Name: feedback_summaries feedback_summaries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_summaries
    ADD CONSTRAINT feedback_summaries_pkey PRIMARY KEY (id);


--
-- TOC entry 3635 (class 2606 OID 17115)
-- Name: import_field_mappings import_field_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_field_mappings
    ADD CONSTRAINT import_field_mappings_pkey PRIMARY KEY (id);


--
-- TOC entry 3632 (class 2606 OID 17101)
-- Name: import_processing_steps import_processing_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_processing_steps
    ADD CONSTRAINT import_processing_steps_pkey PRIMARY KEY (id);


--
-- TOC entry 3697 (class 2606 OID 17406)
-- Name: llm_model_pricing llm_model_pricing_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_model_pricing
    ADD CONSTRAINT llm_model_pricing_pkey PRIMARY KEY (id);


--
-- TOC entry 3693 (class 2606 OID 17377)
-- Name: llm_usage_logs llm_usage_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_logs
    ADD CONSTRAINT llm_usage_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 3704 (class 2606 OID 17419)
-- Name: llm_usage_summary llm_usage_summary_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_summary
    ADD CONSTRAINT llm_usage_summary_pkey PRIMARY KEY (id);


--
-- TOC entry 3644 (class 2606 OID 17158)
-- Name: mapping_learning_patterns mapping_learning_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mapping_learning_patterns
    ADD CONSTRAINT mapping_learning_patterns_pkey PRIMARY KEY (id);


--
-- TOC entry 3525 (class 2606 OID 16594)
-- Name: migration_logs migration_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.migration_logs
    ADD CONSTRAINT migration_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 3602 (class 2606 OID 16929)
-- Name: migration_waves migration_waves_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.migration_waves
    ADD CONSTRAINT migration_waves_pkey PRIMARY KEY (id);


--
-- TOC entry 3506 (class 2606 OID 16546)
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (id);


--
-- TOC entry 3630 (class 2606 OID 17082)
-- Name: raw_import_records raw_import_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.raw_import_records
    ADD CONSTRAINT raw_import_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3715 (class 2606 OID 17478)
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3536 (class 2606 OID 26186)
-- Name: sixr_analyses sixr_analyses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_analyses
    ADD CONSTRAINT sixr_analyses_pkey PRIMARY KEY (id);


--
-- TOC entry 3727 (class 2606 OID 26267)
-- Name: sixr_analysis_parameters sixr_analysis_parameters_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_analysis_parameters
    ADD CONSTRAINT sixr_analysis_parameters_pkey PRIMARY KEY (id);


--
-- TOC entry 3554 (class 2606 OID 16737)
-- Name: sixr_iterations sixr_iterations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_iterations
    ADD CONSTRAINT sixr_iterations_pkey PRIMARY KEY (id);


--
-- TOC entry 3551 (class 2606 OID 16721)
-- Name: sixr_parameters sixr_parameters_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_parameters
    ADD CONSTRAINT sixr_parameters_pkey PRIMARY KEY (id);


--
-- TOC entry 3560 (class 2606 OID 16768)
-- Name: sixr_question_responses sixr_question_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_question_responses
    ADD CONSTRAINT sixr_question_responses_pkey PRIMARY KEY (id);


--
-- TOC entry 3510 (class 2606 OID 16558)
-- Name: sixr_questions sixr_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_questions
    ADD CONSTRAINT sixr_questions_pkey PRIMARY KEY (id);


--
-- TOC entry 3557 (class 2606 OID 16752)
-- Name: sixr_recommendations sixr_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_recommendations
    ADD CONSTRAINT sixr_recommendations_pkey PRIMARY KEY (id);


--
-- TOC entry 3720 (class 2606 OID 17488)
-- Name: soft_deleted_items soft_deleted_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_pkey PRIMARY KEY (id);


--
-- TOC entry 3522 (class 2606 OID 16580)
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- TOC entry 3699 (class 2606 OID 17408)
-- Name: llm_model_pricing uq_model_pricing_version_date; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_model_pricing
    ADD CONSTRAINT uq_model_pricing_version_date UNIQUE (provider, model_name, model_version, effective_from);


--
-- TOC entry 3706 (class 2606 OID 17421)
-- Name: llm_usage_summary uq_usage_summary_period_context; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_summary
    ADD CONSTRAINT uq_usage_summary_period_context UNIQUE (period_type, period_start, client_account_id, engagement_id, user_id, llm_provider, model_name, page_context, feature_context);


--
-- TOC entry 3572 (class 2606 OID 16813)
-- Name: user_account_associations user_account_associations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_associations
    ADD CONSTRAINT user_account_associations_pkey PRIMARY KEY (id);


--
-- TOC entry 3658 (class 2606 OID 17237)
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (user_id);


--
-- TOC entry 3663 (class 2606 OID 17257)
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- TOC entry 3516 (class 2606 OID 16568)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 3532 (class 2606 OID 16628)
-- Name: wave_plans wave_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wave_plans
    ADD CONSTRAINT wave_plans_pkey PRIMARY KEY (id);


--
-- TOC entry 3647 (class 2606 OID 17181)
-- Name: workflow_progress workflow_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_progress
    ADD CONSTRAINT workflow_progress_pkey PRIMARY KEY (id);


--
-- TOC entry 3730 (class 1259 OID 26336)
-- Name: idx_asset_embeddings_asset_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_asset_embeddings_asset_id ON public.asset_embeddings USING btree (asset_id);


--
-- TOC entry 3682 (class 1259 OID 17388)
-- Name: idx_llm_usage_client_account; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_llm_usage_client_account ON public.llm_usage_logs USING btree (client_account_id);


--
-- TOC entry 3683 (class 1259 OID 17396)
-- Name: idx_llm_usage_cost_analysis; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_llm_usage_cost_analysis ON public.llm_usage_logs USING btree (client_account_id, llm_provider, model_name, created_at);


--
-- TOC entry 3684 (class 1259 OID 17397)
-- Name: idx_llm_usage_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_llm_usage_created_at ON public.llm_usage_logs USING btree (created_at);


--
-- TOC entry 3685 (class 1259 OID 17393)
-- Name: idx_llm_usage_engagement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_llm_usage_engagement ON public.llm_usage_logs USING btree (engagement_id);


--
-- TOC entry 3686 (class 1259 OID 17389)
-- Name: idx_llm_usage_feature_context; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_llm_usage_feature_context ON public.llm_usage_logs USING btree (feature_context);


--
-- TOC entry 3687 (class 1259 OID 17394)
-- Name: idx_llm_usage_page_context; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_llm_usage_page_context ON public.llm_usage_logs USING btree (page_context);


--
-- TOC entry 3688 (class 1259 OID 17390)
-- Name: idx_llm_usage_provider_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_llm_usage_provider_model ON public.llm_usage_logs USING btree (llm_provider, model_name);


--
-- TOC entry 3689 (class 1259 OID 17395)
-- Name: idx_llm_usage_reporting; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_llm_usage_reporting ON public.llm_usage_logs USING btree (client_account_id, created_at, success);


--
-- TOC entry 3690 (class 1259 OID 17392)
-- Name: idx_llm_usage_success; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_llm_usage_success ON public.llm_usage_logs USING btree (success);


--
-- TOC entry 3691 (class 1259 OID 17391)
-- Name: idx_llm_usage_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_llm_usage_user ON public.llm_usage_logs USING btree (user_id);


--
-- TOC entry 3694 (class 1259 OID 17410)
-- Name: idx_model_pricing_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_pricing_active ON public.llm_model_pricing USING btree (is_active, effective_from, effective_to);


--
-- TOC entry 3695 (class 1259 OID 17409)
-- Name: idx_model_pricing_provider_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_pricing_provider_model ON public.llm_model_pricing USING btree (provider, model_name);


--
-- TOC entry 3700 (class 1259 OID 17433)
-- Name: idx_usage_summary_client; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usage_summary_client ON public.llm_usage_summary USING btree (client_account_id, period_start);


--
-- TOC entry 3701 (class 1259 OID 17434)
-- Name: idx_usage_summary_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usage_summary_model ON public.llm_usage_summary USING btree (llm_provider, model_name, period_start);


--
-- TOC entry 3702 (class 1259 OID 17432)
-- Name: idx_usage_summary_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usage_summary_period ON public.llm_usage_summary USING btree (period_type, period_start, period_end);


--
-- TOC entry 3666 (class 1259 OID 17311)
-- Name: ix_access_audit_log_action_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_access_audit_log_action_type ON public.access_audit_log USING btree (action_type);


--
-- TOC entry 3667 (class 1259 OID 17309)
-- Name: ix_access_audit_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_access_audit_log_created_at ON public.access_audit_log USING btree (created_at);


--
-- TOC entry 3668 (class 1259 OID 17310)
-- Name: ix_access_audit_log_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_access_audit_log_id ON public.access_audit_log USING btree (id);


--
-- TOC entry 3669 (class 1259 OID 17312)
-- Name: ix_access_audit_log_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_access_audit_log_user_id ON public.access_audit_log USING btree (user_id);


--
-- TOC entry 3548 (class 1259 OID 16711)
-- Name: ix_assessments_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_assessments_id ON public.assessments USING btree (id);


--
-- TOC entry 3545 (class 1259 OID 16689)
-- Name: ix_asset_dependencies_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_asset_dependencies_id ON public.asset_dependencies USING btree (id);


--
-- TOC entry 3625 (class 1259 OID 17073)
-- Name: ix_asset_tags_cmdb_asset_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_asset_tags_cmdb_asset_id ON public.asset_tags USING btree (cmdb_asset_id);


--
-- TOC entry 3626 (class 1259 OID 17074)
-- Name: ix_asset_tags_is_mock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_asset_tags_is_mock ON public.asset_tags USING btree (is_mock);


--
-- TOC entry 3627 (class 1259 OID 17072)
-- Name: ix_asset_tags_tag_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_asset_tags_tag_id ON public.asset_tags USING btree (tag_id);


--
-- TOC entry 3528 (class 1259 OID 26347)
-- Name: ix_assets_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_assets_id ON public.assets USING btree (id);


--
-- TOC entry 3529 (class 1259 OID 16617)
-- Name: ix_assets_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_assets_name ON public.assets USING btree (name);


--
-- TOC entry 3672 (class 1259 OID 17337)
-- Name: ix_client_access_client_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_access_client_account_id ON public.client_access USING btree (client_account_id);


--
-- TOC entry 3673 (class 1259 OID 17339)
-- Name: ix_client_access_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_access_id ON public.client_access USING btree (id);


--
-- TOC entry 3674 (class 1259 OID 17338)
-- Name: ix_client_access_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_access_is_active ON public.client_access USING btree (is_active);


--
-- TOC entry 3675 (class 1259 OID 17340)
-- Name: ix_client_access_user_profile_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_access_user_profile_id ON public.client_access USING btree (user_profile_id);


--
-- TOC entry 3539 (class 1259 OID 16668)
-- Name: ix_client_accounts_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_accounts_id ON public.client_accounts USING btree (id);


--
-- TOC entry 3540 (class 1259 OID 16667)
-- Name: ix_client_accounts_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_accounts_is_active ON public.client_accounts USING btree (is_active);


--
-- TOC entry 3541 (class 1259 OID 16665)
-- Name: ix_client_accounts_is_mock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_accounts_is_mock ON public.client_accounts USING btree (is_mock);


--
-- TOC entry 3542 (class 1259 OID 16666)
-- Name: ix_client_accounts_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_client_accounts_slug ON public.client_accounts USING btree (slug);


--
-- TOC entry 3618 (class 1259 OID 17043)
-- Name: ix_cmdb_asset_embeddings_client_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_asset_embeddings_client_account_id ON public.cmdb_asset_embeddings USING btree (client_account_id);


--
-- TOC entry 3619 (class 1259 OID 17042)
-- Name: ix_cmdb_asset_embeddings_cmdb_asset_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_asset_embeddings_cmdb_asset_id ON public.cmdb_asset_embeddings USING btree (cmdb_asset_id);


--
-- TOC entry 3620 (class 1259 OID 17044)
-- Name: ix_cmdb_asset_embeddings_engagement_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_asset_embeddings_engagement_id ON public.cmdb_asset_embeddings USING btree (engagement_id);


--
-- TOC entry 3621 (class 1259 OID 17045)
-- Name: ix_cmdb_asset_embeddings_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_asset_embeddings_id ON public.cmdb_asset_embeddings USING btree (id);


--
-- TOC entry 3622 (class 1259 OID 17041)
-- Name: ix_cmdb_asset_embeddings_is_mock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_asset_embeddings_is_mock ON public.cmdb_asset_embeddings USING btree (is_mock);


--
-- TOC entry 3579 (class 1259 OID 16891)
-- Name: ix_cmdb_assets_asset_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_assets_asset_type ON public.cmdb_assets USING btree (asset_type);


--
-- TOC entry 3580 (class 1259 OID 16885)
-- Name: ix_cmdb_assets_client_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_assets_client_account_id ON public.cmdb_assets USING btree (client_account_id);


--
-- TOC entry 3581 (class 1259 OID 16886)
-- Name: ix_cmdb_assets_engagement_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_assets_engagement_id ON public.cmdb_assets USING btree (engagement_id);


--
-- TOC entry 3582 (class 1259 OID 16888)
-- Name: ix_cmdb_assets_environment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_assets_environment ON public.cmdb_assets USING btree (environment);


--
-- TOC entry 3583 (class 1259 OID 16892)
-- Name: ix_cmdb_assets_hostname; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_assets_hostname ON public.cmdb_assets USING btree (hostname);


--
-- TOC entry 3584 (class 1259 OID 16890)
-- Name: ix_cmdb_assets_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_assets_id ON public.cmdb_assets USING btree (id);


--
-- TOC entry 3585 (class 1259 OID 16887)
-- Name: ix_cmdb_assets_is_mock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_assets_is_mock ON public.cmdb_assets USING btree (is_mock);


--
-- TOC entry 3586 (class 1259 OID 16893)
-- Name: ix_cmdb_assets_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_assets_name ON public.cmdb_assets USING btree (name);


--
-- TOC entry 3587 (class 1259 OID 16889)
-- Name: ix_cmdb_assets_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_assets_status ON public.cmdb_assets USING btree (status);


--
-- TOC entry 3590 (class 1259 OID 16917)
-- Name: ix_cmdb_sixr_analyses_client_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_sixr_analyses_client_account_id ON public.cmdb_sixr_analyses USING btree (client_account_id);


--
-- TOC entry 3591 (class 1259 OID 16918)
-- Name: ix_cmdb_sixr_analyses_engagement_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_sixr_analyses_engagement_id ON public.cmdb_sixr_analyses USING btree (engagement_id);


--
-- TOC entry 3592 (class 1259 OID 16920)
-- Name: ix_cmdb_sixr_analyses_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_sixr_analyses_id ON public.cmdb_sixr_analyses USING btree (id);


--
-- TOC entry 3593 (class 1259 OID 16921)
-- Name: ix_cmdb_sixr_analyses_is_mock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_sixr_analyses_is_mock ON public.cmdb_sixr_analyses USING btree (is_mock);


--
-- TOC entry 3594 (class 1259 OID 16919)
-- Name: ix_cmdb_sixr_analyses_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cmdb_sixr_analyses_status ON public.cmdb_sixr_analyses USING btree (status);


--
-- TOC entry 3575 (class 1259 OID 16850)
-- Name: ix_custom_target_fields_field_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_custom_target_fields_field_name ON public.custom_target_fields USING btree (field_name);


--
-- TOC entry 3576 (class 1259 OID 16851)
-- Name: ix_custom_target_fields_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_custom_target_fields_id ON public.custom_target_fields USING btree (id);


--
-- TOC entry 3650 (class 1259 OID 17223)
-- Name: ix_data_import_sessions_client_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_import_sessions_client_account_id ON public.data_import_sessions USING btree (client_account_id);


--
-- TOC entry 3651 (class 1259 OID 17225)
-- Name: ix_data_import_sessions_engagement_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_import_sessions_engagement_id ON public.data_import_sessions USING btree (engagement_id);


--
-- TOC entry 3652 (class 1259 OID 17224)
-- Name: ix_data_import_sessions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_import_sessions_id ON public.data_import_sessions USING btree (id);


--
-- TOC entry 3653 (class 1259 OID 17228)
-- Name: ix_data_import_sessions_is_mock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_import_sessions_is_mock ON public.data_import_sessions USING btree (is_mock);


--
-- TOC entry 3654 (class 1259 OID 17227)
-- Name: ix_data_import_sessions_session_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_import_sessions_session_name ON public.data_import_sessions USING btree (session_name);


--
-- TOC entry 3655 (class 1259 OID 17226)
-- Name: ix_data_import_sessions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_import_sessions_status ON public.data_import_sessions USING btree (status);


--
-- TOC entry 3605 (class 1259 OID 16975)
-- Name: ix_data_imports_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_imports_id ON public.data_imports USING btree (id);


--
-- TOC entry 3639 (class 1259 OID 17150)
-- Name: ix_data_quality_issues_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_quality_issues_id ON public.data_quality_issues USING btree (id);


--
-- TOC entry 3678 (class 1259 OID 17368)
-- Name: ix_engagement_access_engagement_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_engagement_access_engagement_id ON public.engagement_access USING btree (engagement_id);


--
-- TOC entry 3679 (class 1259 OID 17366)
-- Name: ix_engagement_access_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_engagement_access_id ON public.engagement_access USING btree (id);


--
-- TOC entry 3680 (class 1259 OID 17367)
-- Name: ix_engagement_access_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_engagement_access_is_active ON public.engagement_access USING btree (is_active);


--
-- TOC entry 3681 (class 1259 OID 17365)
-- Name: ix_engagement_access_user_profile_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_engagement_access_user_profile_id ON public.engagement_access USING btree (user_profile_id);


--
-- TOC entry 3563 (class 1259 OID 16804)
-- Name: ix_engagements_client_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_engagements_client_account_id ON public.engagements USING btree (client_account_id);


--
-- TOC entry 3564 (class 1259 OID 16803)
-- Name: ix_engagements_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_engagements_id ON public.engagements USING btree (id);


--
-- TOC entry 3565 (class 1259 OID 16807)
-- Name: ix_engagements_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_engagements_is_active ON public.engagements USING btree (is_active);


--
-- TOC entry 3566 (class 1259 OID 16806)
-- Name: ix_engagements_is_mock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_engagements_is_mock ON public.engagements USING btree (is_mock);


--
-- TOC entry 3567 (class 1259 OID 16805)
-- Name: ix_engagements_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_engagements_status ON public.engagements USING btree (status);


--
-- TOC entry 3723 (class 1259 OID 17542)
-- Name: ix_enhanced_access_audit_log_action_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_enhanced_access_audit_log_action_type ON public.enhanced_access_audit_log USING btree (action_type);


--
-- TOC entry 3724 (class 1259 OID 17541)
-- Name: ix_enhanced_access_audit_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_enhanced_access_audit_log_created_at ON public.enhanced_access_audit_log USING btree (created_at);


--
-- TOC entry 3725 (class 1259 OID 17540)
-- Name: ix_enhanced_access_audit_log_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_enhanced_access_audit_log_user_id ON public.enhanced_access_audit_log USING btree (user_id);


--
-- TOC entry 3709 (class 1259 OID 17470)
-- Name: ix_enhanced_user_profiles_data_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_enhanced_user_profiles_data_scope ON public.enhanced_user_profiles USING btree (data_scope);


--
-- TOC entry 3710 (class 1259 OID 17472)
-- Name: ix_enhanced_user_profiles_is_deleted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_enhanced_user_profiles_is_deleted ON public.enhanced_user_profiles USING btree (is_deleted);


--
-- TOC entry 3711 (class 1259 OID 17469)
-- Name: ix_enhanced_user_profiles_role_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_enhanced_user_profiles_role_level ON public.enhanced_user_profiles USING btree (role_level);


--
-- TOC entry 3712 (class 1259 OID 17471)
-- Name: ix_enhanced_user_profiles_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_enhanced_user_profiles_status ON public.enhanced_user_profiles USING btree (status);


--
-- TOC entry 3608 (class 1259 OID 16994)
-- Name: ix_feedback_feedback_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feedback_feedback_type ON public.feedback USING btree (feedback_type);


--
-- TOC entry 3609 (class 1259 OID 16995)
-- Name: ix_feedback_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feedback_id ON public.feedback USING btree (id);


--
-- TOC entry 3610 (class 1259 OID 16996)
-- Name: ix_feedback_page; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feedback_page ON public.feedback USING btree (page);


--
-- TOC entry 3613 (class 1259 OID 17016)
-- Name: ix_feedback_summaries_feedback_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feedback_summaries_feedback_type ON public.feedback_summaries USING btree (feedback_type);


--
-- TOC entry 3614 (class 1259 OID 17017)
-- Name: ix_feedback_summaries_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feedback_summaries_id ON public.feedback_summaries USING btree (id);


--
-- TOC entry 3615 (class 1259 OID 17015)
-- Name: ix_feedback_summaries_page; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feedback_summaries_page ON public.feedback_summaries USING btree (page);


--
-- TOC entry 3636 (class 1259 OID 17126)
-- Name: ix_import_field_mappings_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_field_mappings_id ON public.import_field_mappings USING btree (id);


--
-- TOC entry 3633 (class 1259 OID 17107)
-- Name: ix_import_processing_steps_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_processing_steps_id ON public.import_processing_steps USING btree (id);


--
-- TOC entry 3640 (class 1259 OID 17170)
-- Name: ix_mapping_learning_patterns_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mapping_learning_patterns_id ON public.mapping_learning_patterns USING btree (id);


--
-- TOC entry 3641 (class 1259 OID 17169)
-- Name: ix_mapping_learning_patterns_source_field_pattern; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mapping_learning_patterns_source_field_pattern ON public.mapping_learning_patterns USING btree (source_field_pattern);


--
-- TOC entry 3642 (class 1259 OID 17171)
-- Name: ix_mapping_learning_patterns_target_field; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mapping_learning_patterns_target_field ON public.mapping_learning_patterns USING btree (target_field);


--
-- TOC entry 3523 (class 1259 OID 16600)
-- Name: ix_migration_logs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_migration_logs_id ON public.migration_logs USING btree (id);


--
-- TOC entry 3595 (class 1259 OID 16950)
-- Name: ix_migration_waves_client_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_migration_waves_client_account_id ON public.migration_waves USING btree (client_account_id);


--
-- TOC entry 3596 (class 1259 OID 16948)
-- Name: ix_migration_waves_engagement_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_migration_waves_engagement_id ON public.migration_waves USING btree (engagement_id);


--
-- TOC entry 3597 (class 1259 OID 16947)
-- Name: ix_migration_waves_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_migration_waves_id ON public.migration_waves USING btree (id);


--
-- TOC entry 3598 (class 1259 OID 16949)
-- Name: ix_migration_waves_is_mock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_migration_waves_is_mock ON public.migration_waves USING btree (is_mock);


--
-- TOC entry 3599 (class 1259 OID 16946)
-- Name: ix_migration_waves_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_migration_waves_status ON public.migration_waves USING btree (status);


--
-- TOC entry 3600 (class 1259 OID 16945)
-- Name: ix_migration_waves_wave_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_migration_waves_wave_number ON public.migration_waves USING btree (wave_number);


--
-- TOC entry 3503 (class 1259 OID 16547)
-- Name: ix_migrations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_migrations_id ON public.migrations USING btree (id);


--
-- TOC entry 3504 (class 1259 OID 16548)
-- Name: ix_migrations_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_migrations_name ON public.migrations USING btree (name);


--
-- TOC entry 3628 (class 1259 OID 17093)
-- Name: ix_raw_import_records_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_raw_import_records_id ON public.raw_import_records USING btree (id);


--
-- TOC entry 3713 (class 1259 OID 17479)
-- Name: ix_role_permissions_role_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_role_permissions_role_level ON public.role_permissions USING btree (role_level);


--
-- TOC entry 3533 (class 1259 OID 26187)
-- Name: ix_sixr_analyses_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sixr_analyses_id ON public.sixr_analyses USING btree (id);


--
-- TOC entry 3534 (class 1259 OID 16650)
-- Name: ix_sixr_analyses_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sixr_analyses_name ON public.sixr_analyses USING btree (name);


--
-- TOC entry 3552 (class 1259 OID 16743)
-- Name: ix_sixr_iterations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sixr_iterations_id ON public.sixr_iterations USING btree (id);


--
-- TOC entry 3549 (class 1259 OID 16727)
-- Name: ix_sixr_parameters_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sixr_parameters_id ON public.sixr_parameters USING btree (id);


--
-- TOC entry 3558 (class 1259 OID 16779)
-- Name: ix_sixr_question_responses_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sixr_question_responses_id ON public.sixr_question_responses USING btree (id);


--
-- TOC entry 3507 (class 1259 OID 16560)
-- Name: ix_sixr_questions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sixr_questions_id ON public.sixr_questions USING btree (id);


--
-- TOC entry 3508 (class 1259 OID 16559)
-- Name: ix_sixr_questions_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_sixr_questions_question_id ON public.sixr_questions USING btree (question_id);


--
-- TOC entry 3555 (class 1259 OID 16758)
-- Name: ix_sixr_recommendations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sixr_recommendations_id ON public.sixr_recommendations USING btree (id);


--
-- TOC entry 3716 (class 1259 OID 17515)
-- Name: ix_soft_deleted_items_item_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_soft_deleted_items_item_id ON public.soft_deleted_items USING btree (item_id);


--
-- TOC entry 3717 (class 1259 OID 17514)
-- Name: ix_soft_deleted_items_item_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_soft_deleted_items_item_type ON public.soft_deleted_items USING btree (item_type);


--
-- TOC entry 3718 (class 1259 OID 17516)
-- Name: ix_soft_deleted_items_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_soft_deleted_items_status ON public.soft_deleted_items USING btree (status);


--
-- TOC entry 3517 (class 1259 OID 16581)
-- Name: ix_tags_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tags_category ON public.tags USING btree (category);


--
-- TOC entry 3518 (class 1259 OID 16584)
-- Name: ix_tags_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tags_id ON public.tags USING btree (id);


--
-- TOC entry 3519 (class 1259 OID 16582)
-- Name: ix_tags_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tags_is_active ON public.tags USING btree (is_active);


--
-- TOC entry 3520 (class 1259 OID 16583)
-- Name: ix_tags_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_tags_name ON public.tags USING btree (name);


--
-- TOC entry 3568 (class 1259 OID 16831)
-- Name: ix_user_account_associations_client_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_account_associations_client_account_id ON public.user_account_associations USING btree (client_account_id);


--
-- TOC entry 3569 (class 1259 OID 16830)
-- Name: ix_user_account_associations_is_mock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_account_associations_is_mock ON public.user_account_associations USING btree (is_mock);


--
-- TOC entry 3570 (class 1259 OID 16829)
-- Name: ix_user_account_associations_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_account_associations_user_id ON public.user_account_associations USING btree (user_id);


--
-- TOC entry 3656 (class 1259 OID 17248)
-- Name: ix_user_profiles_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_profiles_status ON public.user_profiles USING btree (status);


--
-- TOC entry 3659 (class 1259 OID 17280)
-- Name: ix_user_roles_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_roles_id ON public.user_roles USING btree (id);


--
-- TOC entry 3660 (class 1259 OID 17279)
-- Name: ix_user_roles_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_roles_is_active ON public.user_roles USING btree (is_active);


--
-- TOC entry 3661 (class 1259 OID 17278)
-- Name: ix_user_roles_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_roles_user_id ON public.user_roles USING btree (user_id);


--
-- TOC entry 3511 (class 1259 OID 16572)
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- TOC entry 3512 (class 1259 OID 16569)
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- TOC entry 3513 (class 1259 OID 16570)
-- Name: ix_users_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_is_active ON public.users USING btree (is_active);


--
-- TOC entry 3514 (class 1259 OID 16571)
-- Name: ix_users_is_mock; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_is_mock ON public.users USING btree (is_mock);


--
-- TOC entry 3530 (class 1259 OID 16634)
-- Name: ix_wave_plans_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wave_plans_id ON public.wave_plans USING btree (id);


--
-- TOC entry 3645 (class 1259 OID 17197)
-- Name: ix_workflow_progress_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_workflow_progress_id ON public.workflow_progress USING btree (id);


--
-- TOC entry 3800 (class 2606 OID 17294)
-- Name: access_audit_log access_audit_log_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_audit_log
    ADD CONSTRAINT access_audit_log_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id);


--
-- TOC entry 3801 (class 2606 OID 17299)
-- Name: access_audit_log access_audit_log_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_audit_log
    ADD CONSTRAINT access_audit_log_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id);


--
-- TOC entry 3802 (class 2606 OID 17304)
-- Name: access_audit_log access_audit_log_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_audit_log
    ADD CONSTRAINT access_audit_log_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.data_import_sessions(id);


--
-- TOC entry 3803 (class 2606 OID 17289)
-- Name: access_audit_log access_audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_audit_log
    ADD CONSTRAINT access_audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3738 (class 2606 OID 26367)
-- Name: assessments assessments_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- TOC entry 3739 (class 2606 OID 16701)
-- Name: assessments assessments_migration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_migration_id_fkey FOREIGN KEY (migration_id) REFERENCES public.migrations(id);


--
-- TOC entry 3736 (class 2606 OID 26357)
-- Name: asset_dependencies asset_dependencies_source_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_dependencies
    ADD CONSTRAINT asset_dependencies_source_asset_id_fkey FOREIGN KEY (source_asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- TOC entry 3737 (class 2606 OID 26362)
-- Name: asset_dependencies asset_dependencies_target_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_dependencies
    ADD CONSTRAINT asset_dependencies_target_asset_id_fkey FOREIGN KEY (target_asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- TOC entry 3828 (class 2606 OID 26377)
-- Name: asset_embeddings asset_embeddings_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_embeddings
    ADD CONSTRAINT asset_embeddings_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- TOC entry 3774 (class 2606 OID 17062)
-- Name: asset_tags asset_tags_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_tags
    ADD CONSTRAINT asset_tags_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- TOC entry 3775 (class 2606 OID 17052)
-- Name: asset_tags asset_tags_cmdb_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_tags
    ADD CONSTRAINT asset_tags_cmdb_asset_id_fkey FOREIGN KEY (cmdb_asset_id) REFERENCES public.cmdb_assets(id) ON DELETE CASCADE;


--
-- TOC entry 3776 (class 2606 OID 17057)
-- Name: asset_tags asset_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_tags
    ADD CONSTRAINT asset_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- TOC entry 3777 (class 2606 OID 17067)
-- Name: asset_tags asset_tags_validated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_tags
    ADD CONSTRAINT asset_tags_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES public.users(id);


--
-- TOC entry 3732 (class 2606 OID 16612)
-- Name: assets assets_migration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_migration_id_fkey FOREIGN KEY (migration_id) REFERENCES public.migrations(id);


--
-- TOC entry 3804 (class 2606 OID 17327)
-- Name: client_access client_access_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_access
    ADD CONSTRAINT client_access_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3805 (class 2606 OID 17332)
-- Name: client_access client_access_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_access
    ADD CONSTRAINT client_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id);


--
-- TOC entry 3806 (class 2606 OID 17322)
-- Name: client_access client_access_user_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_access
    ADD CONSTRAINT client_access_user_profile_id_fkey FOREIGN KEY (user_profile_id) REFERENCES public.user_profiles(user_id) ON DELETE CASCADE;


--
-- TOC entry 3735 (class 2606 OID 16660)
-- Name: client_accounts client_accounts_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_accounts
    ADD CONSTRAINT client_accounts_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3771 (class 2606 OID 17031)
-- Name: cmdb_asset_embeddings cmdb_asset_embeddings_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_asset_embeddings
    ADD CONSTRAINT cmdb_asset_embeddings_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3772 (class 2606 OID 17026)
-- Name: cmdb_asset_embeddings cmdb_asset_embeddings_cmdb_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_asset_embeddings
    ADD CONSTRAINT cmdb_asset_embeddings_cmdb_asset_id_fkey FOREIGN KEY (cmdb_asset_id) REFERENCES public.cmdb_assets(id) ON DELETE CASCADE;


--
-- TOC entry 3773 (class 2606 OID 17036)
-- Name: cmdb_asset_embeddings cmdb_asset_embeddings_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_asset_embeddings
    ADD CONSTRAINT cmdb_asset_embeddings_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id) ON DELETE CASCADE;


--
-- TOC entry 3753 (class 2606 OID 16860)
-- Name: cmdb_assets cmdb_assets_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_assets
    ADD CONSTRAINT cmdb_assets_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3754 (class 2606 OID 16875)
-- Name: cmdb_assets cmdb_assets_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_assets
    ADD CONSTRAINT cmdb_assets_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3755 (class 2606 OID 16865)
-- Name: cmdb_assets cmdb_assets_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_assets
    ADD CONSTRAINT cmdb_assets_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id) ON DELETE CASCADE;


--
-- TOC entry 3756 (class 2606 OID 16870)
-- Name: cmdb_assets cmdb_assets_imported_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_assets
    ADD CONSTRAINT cmdb_assets_imported_by_fkey FOREIGN KEY (imported_by) REFERENCES public.users(id);


--
-- TOC entry 3757 (class 2606 OID 16880)
-- Name: cmdb_assets cmdb_assets_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_assets
    ADD CONSTRAINT cmdb_assets_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- TOC entry 3758 (class 2606 OID 16902)
-- Name: cmdb_sixr_analyses cmdb_sixr_analyses_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_sixr_analyses
    ADD CONSTRAINT cmdb_sixr_analyses_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3759 (class 2606 OID 16912)
-- Name: cmdb_sixr_analyses cmdb_sixr_analyses_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_sixr_analyses
    ADD CONSTRAINT cmdb_sixr_analyses_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3760 (class 2606 OID 16907)
-- Name: cmdb_sixr_analyses cmdb_sixr_analyses_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_sixr_analyses
    ADD CONSTRAINT cmdb_sixr_analyses_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id) ON DELETE CASCADE;


--
-- TOC entry 3751 (class 2606 OID 16840)
-- Name: custom_target_fields custom_target_fields_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.custom_target_fields
    ADD CONSTRAINT custom_target_fields_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3752 (class 2606 OID 16845)
-- Name: custom_target_fields custom_target_fields_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.custom_target_fields
    ADD CONSTRAINT custom_target_fields_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3791 (class 2606 OID 17208)
-- Name: data_import_sessions data_import_sessions_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_import_sessions
    ADD CONSTRAINT data_import_sessions_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3792 (class 2606 OID 17218)
-- Name: data_import_sessions data_import_sessions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_import_sessions
    ADD CONSTRAINT data_import_sessions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3793 (class 2606 OID 17213)
-- Name: data_import_sessions data_import_sessions_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_import_sessions
    ADD CONSTRAINT data_import_sessions_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id) ON DELETE CASCADE;


--
-- TOC entry 3764 (class 2606 OID 16960)
-- Name: data_imports data_imports_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_imports
    ADD CONSTRAINT data_imports_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3765 (class 2606 OID 16965)
-- Name: data_imports data_imports_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_imports
    ADD CONSTRAINT data_imports_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id) ON DELETE CASCADE;


--
-- TOC entry 3766 (class 2606 OID 16970)
-- Name: data_imports data_imports_imported_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_imports
    ADD CONSTRAINT data_imports_imported_by_fkey FOREIGN KEY (imported_by) REFERENCES public.users(id);


--
-- TOC entry 3783 (class 2606 OID 17135)
-- Name: data_quality_issues data_quality_issues_data_import_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_issues
    ADD CONSTRAINT data_quality_issues_data_import_id_fkey FOREIGN KEY (data_import_id) REFERENCES public.data_imports(id) ON DELETE CASCADE;


--
-- TOC entry 3784 (class 2606 OID 17140)
-- Name: data_quality_issues data_quality_issues_raw_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_issues
    ADD CONSTRAINT data_quality_issues_raw_record_id_fkey FOREIGN KEY (raw_record_id) REFERENCES public.raw_import_records(id);


--
-- TOC entry 3785 (class 2606 OID 17145)
-- Name: data_quality_issues data_quality_issues_resolved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_issues
    ADD CONSTRAINT data_quality_issues_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES public.users(id);


--
-- TOC entry 3807 (class 2606 OID 17355)
-- Name: engagement_access engagement_access_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.engagement_access
    ADD CONSTRAINT engagement_access_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id) ON DELETE CASCADE;


--
-- TOC entry 3808 (class 2606 OID 17360)
-- Name: engagement_access engagement_access_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.engagement_access
    ADD CONSTRAINT engagement_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id);


--
-- TOC entry 3809 (class 2606 OID 17350)
-- Name: engagement_access engagement_access_user_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.engagement_access
    ADD CONSTRAINT engagement_access_user_profile_id_fkey FOREIGN KEY (user_profile_id) REFERENCES public.user_profiles(user_id) ON DELETE CASCADE;


--
-- TOC entry 3745 (class 2606 OID 16788)
-- Name: engagements engagements_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.engagements
    ADD CONSTRAINT engagements_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3746 (class 2606 OID 16798)
-- Name: engagements engagements_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.engagements
    ADD CONSTRAINT engagements_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3747 (class 2606 OID 16793)
-- Name: engagements engagements_engagement_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.engagements
    ADD CONSTRAINT engagements_engagement_lead_id_fkey FOREIGN KEY (engagement_lead_id) REFERENCES public.users(id);


--
-- TOC entry 3824 (class 2606 OID 17530)
-- Name: enhanced_access_audit_log enhanced_access_audit_log_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enhanced_access_audit_log
    ADD CONSTRAINT enhanced_access_audit_log_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id);


--
-- TOC entry 3825 (class 2606 OID 17535)
-- Name: enhanced_access_audit_log enhanced_access_audit_log_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enhanced_access_audit_log
    ADD CONSTRAINT enhanced_access_audit_log_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id);


--
-- TOC entry 3826 (class 2606 OID 17525)
-- Name: enhanced_access_audit_log enhanced_access_audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enhanced_access_audit_log
    ADD CONSTRAINT enhanced_access_audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3814 (class 2606 OID 17459)
-- Name: enhanced_user_profiles enhanced_user_profiles_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 3815 (class 2606 OID 17464)
-- Name: enhanced_user_profiles enhanced_user_profiles_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.users(id);


--
-- TOC entry 3816 (class 2606 OID 17449)
-- Name: enhanced_user_profiles enhanced_user_profiles_scope_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_scope_client_account_id_fkey FOREIGN KEY (scope_client_account_id) REFERENCES public.client_accounts(id);


--
-- TOC entry 3817 (class 2606 OID 17454)
-- Name: enhanced_user_profiles enhanced_user_profiles_scope_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_scope_engagement_id_fkey FOREIGN KEY (scope_engagement_id) REFERENCES public.engagements(id);


--
-- TOC entry 3818 (class 2606 OID 17444)
-- Name: enhanced_user_profiles enhanced_user_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enhanced_user_profiles
    ADD CONSTRAINT enhanced_user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3767 (class 2606 OID 16984)
-- Name: feedback feedback_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3768 (class 2606 OID 16989)
-- Name: feedback feedback_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id) ON DELETE CASCADE;


--
-- TOC entry 3769 (class 2606 OID 17005)
-- Name: feedback_summaries feedback_summaries_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_summaries
    ADD CONSTRAINT feedback_summaries_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3770 (class 2606 OID 17010)
-- Name: feedback_summaries feedback_summaries_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_summaries
    ADD CONSTRAINT feedback_summaries_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id) ON DELETE CASCADE;


--
-- TOC entry 3781 (class 2606 OID 17116)
-- Name: import_field_mappings import_field_mappings_data_import_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_field_mappings
    ADD CONSTRAINT import_field_mappings_data_import_id_fkey FOREIGN KEY (data_import_id) REFERENCES public.data_imports(id) ON DELETE CASCADE;


--
-- TOC entry 3782 (class 2606 OID 17121)
-- Name: import_field_mappings import_field_mappings_validated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_field_mappings
    ADD CONSTRAINT import_field_mappings_validated_by_fkey FOREIGN KEY (validated_by) REFERENCES public.users(id);


--
-- TOC entry 3780 (class 2606 OID 17102)
-- Name: import_processing_steps import_processing_steps_data_import_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_processing_steps
    ADD CONSTRAINT import_processing_steps_data_import_id_fkey FOREIGN KEY (data_import_id) REFERENCES public.data_imports(id) ON DELETE CASCADE;


--
-- TOC entry 3810 (class 2606 OID 17378)
-- Name: llm_usage_logs llm_usage_logs_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_logs
    ADD CONSTRAINT llm_usage_logs_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id);


--
-- TOC entry 3811 (class 2606 OID 17383)
-- Name: llm_usage_logs llm_usage_logs_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_logs
    ADD CONSTRAINT llm_usage_logs_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id);


--
-- TOC entry 3812 (class 2606 OID 17422)
-- Name: llm_usage_summary llm_usage_summary_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_summary
    ADD CONSTRAINT llm_usage_summary_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id);


--
-- TOC entry 3813 (class 2606 OID 17427)
-- Name: llm_usage_summary llm_usage_summary_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_summary
    ADD CONSTRAINT llm_usage_summary_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id);


--
-- TOC entry 3786 (class 2606 OID 17159)
-- Name: mapping_learning_patterns mapping_learning_patterns_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mapping_learning_patterns
    ADD CONSTRAINT mapping_learning_patterns_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3787 (class 2606 OID 17164)
-- Name: mapping_learning_patterns mapping_learning_patterns_learned_from_mapping_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mapping_learning_patterns
    ADD CONSTRAINT mapping_learning_patterns_learned_from_mapping_id_fkey FOREIGN KEY (learned_from_mapping_id) REFERENCES public.import_field_mappings(id);


--
-- TOC entry 3731 (class 2606 OID 16595)
-- Name: migration_logs migration_logs_migration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.migration_logs
    ADD CONSTRAINT migration_logs_migration_id_fkey FOREIGN KEY (migration_id) REFERENCES public.migrations(id);


--
-- TOC entry 3761 (class 2606 OID 16930)
-- Name: migration_waves migration_waves_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.migration_waves
    ADD CONSTRAINT migration_waves_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3762 (class 2606 OID 16940)
-- Name: migration_waves migration_waves_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.migration_waves
    ADD CONSTRAINT migration_waves_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3763 (class 2606 OID 16935)
-- Name: migration_waves migration_waves_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.migration_waves
    ADD CONSTRAINT migration_waves_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id) ON DELETE CASCADE;


--
-- TOC entry 3778 (class 2606 OID 17088)
-- Name: raw_import_records raw_import_records_cmdb_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.raw_import_records
    ADD CONSTRAINT raw_import_records_cmdb_asset_id_fkey FOREIGN KEY (cmdb_asset_id) REFERENCES public.cmdb_assets(id);


--
-- TOC entry 3779 (class 2606 OID 17083)
-- Name: raw_import_records raw_import_records_data_import_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.raw_import_records
    ADD CONSTRAINT raw_import_records_data_import_id_fkey FOREIGN KEY (data_import_id) REFERENCES public.data_imports(id) ON DELETE CASCADE;


--
-- TOC entry 3734 (class 2606 OID 16645)
-- Name: sixr_analyses sixr_analyses_migration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_analyses
    ADD CONSTRAINT sixr_analyses_migration_id_fkey FOREIGN KEY (migration_id) REFERENCES public.migrations(id);


--
-- TOC entry 3827 (class 2606 OID 26268)
-- Name: sixr_analysis_parameters sixr_analysis_parameters_analysis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_analysis_parameters
    ADD CONSTRAINT sixr_analysis_parameters_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.sixr_analyses(id);


--
-- TOC entry 3741 (class 2606 OID 26225)
-- Name: sixr_iterations sixr_iterations_analysis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_iterations
    ADD CONSTRAINT sixr_iterations_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.sixr_analyses(id);


--
-- TOC entry 3740 (class 2606 OID 26230)
-- Name: sixr_parameters sixr_parameters_analysis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_parameters
    ADD CONSTRAINT sixr_parameters_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.sixr_analyses(id);


--
-- TOC entry 3743 (class 2606 OID 26235)
-- Name: sixr_question_responses sixr_question_responses_analysis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_question_responses
    ADD CONSTRAINT sixr_question_responses_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.sixr_analyses(id);


--
-- TOC entry 3744 (class 2606 OID 16774)
-- Name: sixr_question_responses sixr_question_responses_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_question_responses
    ADD CONSTRAINT sixr_question_responses_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.sixr_questions(question_id);


--
-- TOC entry 3742 (class 2606 OID 26240)
-- Name: sixr_recommendations sixr_recommendations_analysis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sixr_recommendations
    ADD CONSTRAINT sixr_recommendations_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.sixr_analyses(id);


--
-- TOC entry 3819 (class 2606 OID 17489)
-- Name: soft_deleted_items soft_deleted_items_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id);


--
-- TOC entry 3820 (class 2606 OID 17499)
-- Name: soft_deleted_items soft_deleted_items_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.users(id);


--
-- TOC entry 3821 (class 2606 OID 17494)
-- Name: soft_deleted_items soft_deleted_items_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id);


--
-- TOC entry 3822 (class 2606 OID 17509)
-- Name: soft_deleted_items soft_deleted_items_purged_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_purged_by_fkey FOREIGN KEY (purged_by) REFERENCES public.users(id);


--
-- TOC entry 3823 (class 2606 OID 17504)
-- Name: soft_deleted_items soft_deleted_items_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.soft_deleted_items
    ADD CONSTRAINT soft_deleted_items_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(id);


--
-- TOC entry 3748 (class 2606 OID 16819)
-- Name: user_account_associations user_account_associations_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_associations
    ADD CONSTRAINT user_account_associations_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3749 (class 2606 OID 16824)
-- Name: user_account_associations user_account_associations_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_associations
    ADD CONSTRAINT user_account_associations_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3750 (class 2606 OID 16814)
-- Name: user_account_associations user_account_associations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account_associations
    ADD CONSTRAINT user_account_associations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3794 (class 2606 OID 17243)
-- Name: user_profiles user_profiles_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 3795 (class 2606 OID 17238)
-- Name: user_profiles user_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3796 (class 2606 OID 17273)
-- Name: user_roles user_roles_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- TOC entry 3797 (class 2606 OID 17263)
-- Name: user_roles user_roles_scope_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_scope_client_id_fkey FOREIGN KEY (scope_client_id) REFERENCES public.client_accounts(id);


--
-- TOC entry 3798 (class 2606 OID 17268)
-- Name: user_roles user_roles_scope_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_scope_engagement_id_fkey FOREIGN KEY (scope_engagement_id) REFERENCES public.engagements(id);


--
-- TOC entry 3799 (class 2606 OID 17258)
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3733 (class 2606 OID 16629)
-- Name: wave_plans wave_plans_migration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wave_plans
    ADD CONSTRAINT wave_plans_migration_id_fkey FOREIGN KEY (migration_id) REFERENCES public.migrations(id);


--
-- TOC entry 3788 (class 2606 OID 26372)
-- Name: workflow_progress workflow_progress_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_progress
    ADD CONSTRAINT workflow_progress_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- TOC entry 3789 (class 2606 OID 17187)
-- Name: workflow_progress workflow_progress_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_progress
    ADD CONSTRAINT workflow_progress_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id);


--
-- TOC entry 3790 (class 2606 OID 17192)
-- Name: workflow_progress workflow_progress_engagement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_progress
    ADD CONSTRAINT workflow_progress_engagement_id_fkey FOREIGN KEY (engagement_id) REFERENCES public.engagements(id);


-- Completed on 2025-06-22 12:36:31 EDT

--
-- PostgreSQL database dump complete
--
