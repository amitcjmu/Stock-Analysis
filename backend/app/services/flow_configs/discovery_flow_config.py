"""
Discovery Flow Configuration
MFO-039: Create Discovery flow configuration

Comprehensive asset discovery and inventory flow configuration
with all 6 phases and associated validators/handlers.
"""

from app.services.flow_type_registry import (FlowCapabilities, FlowTypeConfig,
                                             PhaseConfig, RetryConfig)


def get_discovery_flow_config() -> FlowTypeConfig:
    """
    Get the Discovery flow configuration with all 6 phases

    Phases:
    1. Data Import - Import and validate data from various sources
    2. Field Mapping - Map imported fields to standard schema
    3. Data Cleansing - Clean and normalize data
    4. Asset Creation - Create asset records from cleansed data
    5. Asset Inventory - Build comprehensive asset inventory
    6. Dependency Analysis - Analyze asset dependencies
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    # Phase 1: Data Import
    data_import_phase = PhaseConfig(
        name="data_import",
        display_name="Data Import",
        description="Import and validate data from various sources using AI-powered validation",
        required_inputs=["raw_data", "import_config"],
        optional_inputs=["validation_rules", "source_metadata"],
        validators=["required_fields", "data_format", "schema_validation"],
        pre_handlers=["data_import_preparation"],
        post_handlers=["data_import_validation"],
        crew_config={
            "crew_type": "data_import_validation_crew",
            "crew_factory": "create_data_import_validation_crew",
            "input_mapping": {
                "raw_data": "raw_data",
                "metadata": "import_config",
                "validation_rules": "metadata.validation_rules",
            },
            "output_mapping": {
                "validation_result": "crew_results",
                "file_type": "crew_results.file_type",
                "security_status": "crew_results.security_status",
                "recommendations": "crew_results.recommended_agent",
            },
            "execution_config": {
                "timeout_seconds": 180,  # 3 minutes for large datasets
                "max_iterations": 1,
                "allow_delegation": False,
                "enable_memory": False,
            },
            "validation_mapping": {
                "required_fields": [
                    "file_type",
                    "security_status",
                    "asset_inventory_suitable",
                ],
                "success_criteria": {
                    "security_status": ["clean"],
                    "asset_inventory_suitable": True,
                },
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1800,  # 30 minutes
        metadata={
            "supports_bulk_import": True,
            "supported_formats": ["csv", "json", "xml", "excel"],
            "max_file_size_mb": 500,
            "ai_validation_enabled": True,
        },
    )

    # Phase 2: Field Mapping
    field_mapping_phase = PhaseConfig(
        name="field_mapping",
        display_name="Field Mapping",
        description="Map imported fields to standard schema using memory-enhanced AI mapping",
        required_inputs=["imported_data", "mapping_rules"],
        optional_inputs=["custom_mappings", "transformation_rules"],
        validators=["field_mapping_validation", "mapping_completeness"],
        pre_handlers=["field_analysis"],
        post_handlers=["mapping_verification"],
        crew_config={
            "crew_type": "optimized_field_mapping_crew",
            "crew_factory": "create_optimized_field_mapping_crew",
            "input_mapping": {
                "raw_data": "state.raw_data",
                "context": "state.context",
                "learning_context": "engagement_context",
            },
            "output_mapping": {
                "mappings": "crew_results.mappings",
                "confidence_scores": "crew_results.confidence_scores",
                "learning_opportunities": "crew_results.learning_opportunities",
                "memory_patterns_used": "crew_results.memory_patterns_used",
            },
            "execution_config": {
                "timeout_seconds": 180,  # 3 minutes for enhanced processing
                "max_iterations": 1,
                "allow_delegation": False,  # Single expert agent
                "enable_memory": True,  # Key learning feature
                "enable_caching": True,  # Performance optimization
                "enable_parallel": False,  # Sequential for accuracy
            },
            "validation_mapping": {
                "required_fields": ["mappings", "confidence_scores", "success"],
                "success_criteria": {
                    "mappings_count": {"min": 1},
                    "avg_confidence": {"min": 0.6},
                    "success": True,
                },
            },
            "performance_config": {
                "enable_learning": True,
                "store_patterns": True,
                "generate_intelligence_reports": True,
                "confidence_threshold": 0.7,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1200,  # 20 minutes
        metadata={
            "auto_mapping_enabled": True,
            "ai_assisted_mapping": True,
            "memory_enhanced_learning": True,
            "pattern_recognition": True,
        },
    )

    # Phase 3: Data Cleansing
    data_cleansing_phase = PhaseConfig(
        name="data_cleansing",
        display_name="Data Cleansing",
        description="Clean and normalize data with agentic intelligence enrichment",
        required_inputs=["mapped_data", "cleansing_rules"],
        optional_inputs=["quality_thresholds", "normalization_rules"],
        validators=["data_quality", "cleansing_validation"],
        pre_handlers=["quality_assessment"],
        post_handlers=["cleansing_report_generation"],
        crew_config={
            "crew_type": "data_cleansing_crew",
            "crew_factory": "create_data_cleansing_crew",
            "input_mapping": {
                "raw_data": "state.raw_data",
                "field_mappings": "state.field_mappings",
                "cleansing_rules": "cleansing_rules",
                "quality_thresholds": "quality_thresholds",
            },
            "output_mapping": {
                "cleaned_data": "crew_results.cleaned_data",
                "enrichment_summary": "crew_results.enrichment_summary",
                "quality_metrics": "crew_results.quality_metrics",
                "agentic_analysis": "crew_results.agentic_analysis",
            },
            "execution_config": {
                "timeout_seconds": 180,  # 3 minutes for agentic processing
                "max_iterations": 1,
                "allow_delegation": False,
                "enable_memory": True,
                "batch_processing": True,
                "parallel_agents": True,
                "temperature": 0.1,  # Low temperature to prevent hallucinations
                "max_tokens": 2000,  # Conservative token limit
                "conservative_mode": True,  # Enable factual accuracy mode
            },
            "validation_mapping": {
                "required_fields": [
                    "cleaned_data",
                    "quality_metrics",
                    "enrichment_summary",
                ],
                "success_criteria": {
                    "enrichment_success_rate": {"min": 0.8},
                    "quality_score": {"min": 70},
                    "agentic_analysis": True,
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "batch_size": 3,
                "enable_parallel_execution": True,
                "agentic_intelligence": True,
                "factual_accuracy_mode": True,
                "verification_enabled": True,
                "confidence_threshold": 0.8,
            },
            "llm_config": {
                "temperature": 0.1,  # Very conservative for data accuracy
                "top_p": 0.8,  # Reduce randomness
                "frequency_penalty": 0.3,  # Discourage repetition
                "presence_penalty": 0.1,  # Minimal creativity
                "stop_sequences": ["HALLUCINATION", "SPECULATION"],
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1500,  # 25 minutes
        metadata={
            "duplicate_detection": True,
            "anomaly_detection": True,
            "data_enrichment": True,
            "agentic_intelligence": True,
            "business_value_analysis": True,
            "risk_assessment": True,
            "modernization_analysis": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )

    # Phase 4: Asset Creation
    asset_creation_phase = PhaseConfig(
        name="asset_creation",
        display_name="Asset Creation",
        description="Create asset records from cleansed data",
        required_inputs=["cleansed_data", "asset_templates"],
        optional_inputs=["business_rules", "categorization_rules"],
        validators=["asset_validation", "business_rule_validation"],
        pre_handlers=["asset_preparation"],
        post_handlers=["asset_indexing"],
        completion_handler="asset_creation_completion",
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=2400,  # 40 minutes
        metadata={
            "batch_processing": True,
            "relationship_mapping": True,
            "ci_cmdb_integration": True,
        },
    )

    # Phase 5: Asset Inventory
    asset_inventory_phase = PhaseConfig(
        name="asset_inventory",
        display_name="Asset Inventory",
        description="Build comprehensive asset inventory with multi-domain classification and deduplication",
        required_inputs=["assets", "inventory_config"],
        optional_inputs=["grouping_rules", "hierarchy_rules"],
        validators=["inventory_validation", "completeness_check"],
        pre_handlers=["inventory_preparation"],
        post_handlers=["inventory_optimization"],
        crew_config={
            "crew_type": "inventory_building_crew",
            "crew_factory": "create_inventory_building_crew",
            "input_mapping": {
                "cleaned_data": "state.cleaned_data",
                "field_mappings": "state.field_mappings",
                "inventory_config": "inventory_config",
                "context_info": "engagement_context",
            },
            "output_mapping": {
                "asset_inventory": "crew_results.servers + crew_results.applications + crew_results.devices",
                "asset_relationships": "crew_results.relationships",
                "classification_summary": "crew_results.classification_metrics",
                "deduplication_report": "crew_results.deduplication_summary",
            },
            "execution_config": {
                "timeout_seconds": 180,  # 3 minutes for multi-domain processing
                "max_iterations": 1,
                "allow_delegation": False,
                "enable_memory": True,
                "batch_processing": True,
                "parallel_agents": True,
                "temperature": 0.1,  # Conservative to prevent hallucinations
                "max_tokens": 2000,
                "conservative_mode": True,
            },
            "validation_mapping": {
                "required_fields": [
                    "asset_inventory",
                    "asset_relationships",
                    "classification_summary",
                ],
                "success_criteria": {
                    "classification_success_rate": {"min": 0.85},
                    "deduplication_effectiveness": {"min": 0.95},
                    "cross_domain_coverage": True,
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_parallel_execution": True,
                "intelligent_deduplication": True,
                "task_completion_optimization": True,
                "multi_domain_classification": True,
                "confidence_threshold": 0.8,
            },
            "llm_config": {
                "temperature": 0.1,
                "top_p": 0.8,
                "frequency_penalty": 0.3,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "DUPLICATE"],
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1800,  # 30 minutes
        metadata={
            "categorization": True,
            "tagging": True,
            "cost_allocation": True,
            "multi_domain_classification": True,
            "intelligent_deduplication": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )

    # Phase 6: Dependency Analysis (Optional)
    dependency_analysis_phase = PhaseConfig(
        name="dependency_analysis",
        display_name="Dependency Analysis",
        description="Analyze asset dependencies and relationships using comprehensive network and infrastructure analysis",
        required_inputs=["inventory", "dependency_rules"],
        optional_inputs=["discovery_depth", "relationship_types"],
        validators=["dependency_validation", "circular_dependency_check"],
        pre_handlers=["dependency_discovery"],
        post_handlers=["dependency_visualization"],
        crew_config={
            "crew_type": "dependency_analysis_crew",
            "crew_factory": "create_dependency_analysis_crew",
            "input_mapping": {
                "assets_data": "state.asset_inventory",
                "context": {
                    "dependency_rules": "dependency_rules",
                    "discovery_depth": "discovery_depth",
                    "relationship_types": "relationship_types",
                    "engagement_context": "engagement_context",
                },
            },
            "output_mapping": {
                "dependency_analysis": "crew_results.analysis_results",
                "dependency_relationships": "crew_results.summary",
                "migration_sequence": "crew_results.analysis_results[*].migration_sequence",
                "risk_assessment": "crew_results.analysis_results[*].risk_assessment",
                "critical_paths": "crew_results.analysis_results[*].critical_path_analysis",
            },
            "execution_config": {
                "timeout_seconds": 180,  # 3 minutes for dependency analysis
                "max_iterations": 1,
                "allow_delegation": False,  # Single expert crew
                "enable_memory": True,  # Learning from previous analyses
                "enable_caching": True,  # Performance optimization
                "enable_parallel": False,  # Sequential for accuracy
                "temperature": 0.1,  # Conservative for accuracy
                "max_tokens": 2000,  # Conservative token limit
                "conservative_mode": True,  # Enable factual accuracy mode
            },
            "validation_mapping": {
                "required_fields": ["analysis_results", "summary", "metadata"],
                "success_criteria": {
                    "analysis_success": True,
                    "avg_confidence": {"min": 0.7},
                    "assets_analyzed": {"min": 1},
                    "dependency_mapping_complete": True,
                },
            },
            "performance_config": {
                "enable_parallel_execution": False,  # Sequential for dependency accuracy
                "dependency_analysis_depth": "comprehensive",
                "network_topology_analysis": True,
                "infrastructure_assessment": True,
                "migration_planning": True,
                "confidence_threshold": 0.75,
            },
            "llm_config": {
                "temperature": 0.1,  # Very conservative for dependency accuracy
                "top_p": 0.8,  # Reduce randomness
                "frequency_penalty": 0.3,  # Discourage repetition
                "presence_penalty": 0.1,  # Minimal creativity
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"],
            },
        },
        can_pause=True,
        can_skip=True,  # Optional phase
        retry_config=default_retry,
        timeout_seconds=2100,  # 35 minutes
        metadata={
            "auto_discovery": True,
            "impact_analysis": True,
            "visualization_enabled": True,
            "network_analysis": True,
            "infrastructure_analysis": True,
            "migration_planning": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )

    # Define flow capabilities
    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_branching=False,
        supports_iterations=True,
        max_iterations=5,
        supports_scheduling=True,
        supports_parallel_phases=False,
        supports_checkpointing=True,
        required_permissions=["discovery.read", "discovery.write", "discovery.execute"],
    )

    # Create the flow configuration
    discovery_config = FlowTypeConfig(
        name="discovery",
        display_name="Discovery Flow",
        description="Comprehensive asset discovery and inventory flow for migration assessment",
        version="2.0.0",
        phases=[
            data_import_phase,
            field_mapping_phase,
            data_cleansing_phase,
            asset_creation_phase,
            asset_inventory_phase,
            dependency_analysis_phase,
        ],
        capabilities=capabilities,
        default_configuration={
            "enable_real_time_validation": True,
            "auto_retry_failed_phases": True,
            "notification_channels": ["email", "webhook"],
            "agent_collaboration": True,
            "parallel_processing": True,
            "incremental_discovery": True,
            "data_quality_threshold": 0.95,
            "auto_remediation": True,
        },
        initialization_handler="discovery_initialization",
        finalization_handler="discovery_finalization",
        error_handler="discovery_error_handler",
        metadata={
            "category": "data_ingestion",
            "complexity": "high",
            "estimated_duration_minutes": 180,
            "required_agents": [
                "data_import_agent",
                "mapping_agent",
                "cleansing_agent",
            ],
            "supports_templates": True,
        },
        tags=["discovery", "data_import", "inventory", "assessment_prerequisite"],
    )

    return discovery_config
