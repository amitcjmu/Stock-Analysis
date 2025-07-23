"""
Collection Flow Configuration
ADCS: Automated Data Collection and Synthesis Flow Configuration

Comprehensive data collection flow configuration for automated platform discovery,
multi-tiered collection strategies, gap analysis, and manual collection.
"""

from app.services.flow_type_registry import (FlowCapabilities, FlowTypeConfig,
                                             PhaseConfig, RetryConfig)


def get_collection_flow_config() -> FlowTypeConfig:
    """
    Get the Collection flow configuration with all 5 phases

    Phases:
    1. Platform Detection - Detect and identify target platforms
    2. Automated Collection - Automated data collection using adapters
    3. Gap Analysis - Analyze missing data and quality issues
    4. Manual Collection - Collect data through questionnaires and manual processes
    5. Synthesis - Synthesize and validate all collected data
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    # Phase 1: Platform Detection
    platform_detection_phase = PhaseConfig(
        name="platform_detection",
        display_name="Platform Detection",
        description="Detect and identify target platforms for data collection using intelligent agents",
        required_inputs=["environment_config", "automation_tier"],
        optional_inputs=["credentials", "discovery_scope", "platform_hints"],
        validators=["platform_validation", "credential_validation"],
        pre_handlers=["collection_initialization"],
        post_handlers=["platform_inventory_creation"],
        crew_config={
            "crew_type": "platform_detection_crew",
            "crew_factory": "create_platform_detection_crew",
            "input_mapping": {
                "infrastructure_data": "state.environment_config",
                "context": {
                    "platform_info": "state.platform_info",
                    "credentials_available": "credentials",
                    "automation_preferences": "state.automation_preferences",
                    "automation_tier": "automation_tier",
                    "discovery_scope": "discovery_scope",
                },
            },
            "output_mapping": {
                "detected_platforms": "crew_results.platforms",
                "adapter_recommendations": "crew_results.recommended_adapters",
                "platform_metadata": "crew_results.platform_metadata",
                "tier_assignments": "crew_results.tier_assignments",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 180,  # Conservative 3 minutes
                "temperature": 0.1,  # Very conservative for accuracy
                "max_iterations": 1,
                "allow_delegation": True,  # Enable agent collaboration
                "enable_memory": False,  # Conservative mode
                "enable_caching": True,  # Performance optimization
                "enable_parallel": False,  # Sequential for accuracy
                "conservative_mode": True,
            },
            "llm_config": {
                "temperature": 0.1,  # Conservative settings
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"],
            },
            "validation_mapping": {
                "required_fields": [
                    "platforms",
                    "recommended_adapters",
                    "tier_assignments",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "platforms_count": {"min": 1},
                    "adapter_coverage": {"min": 0.8},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_platform_detection": True,
                "prioritize_automation_tiers": True,
                "generate_adapter_mappings": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=900,  # 15 minutes
        metadata={
            "supports_auto_discovery": True,
            "platform_types": ["cloud", "on-premise", "hybrid", "saas"],
            "ai_powered_detection": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )

    # Phase 2: Automated Collection
    automated_collection_phase = PhaseConfig(
        name="automated_collection",
        display_name="Automated Collection",
        description="Collect data automatically using platform-specific adapters and intelligent orchestration",
        required_inputs=["detected_platforms", "adapter_configs"],
        optional_inputs=["collection_filters", "priority_resources", "rate_limits"],
        validators=["collection_validation", "data_quality_validation"],
        pre_handlers=["adapter_preparation"],
        post_handlers=["collection_data_normalization"],
        crew_config={
            "crew_type": "automated_collection_crew",
            "crew_factory": "create_automated_collection_crew",
            "input_mapping": {
                "platforms": "state.detected_platforms",
                "adapter_configs": "adapter_configs",
                "context": {
                    "automation_tier": "state.automation_tier",
                    "tier_assignments": "state.tier_assignments",
                    "collection_filters": "collection_filters",
                    "priority_resources": "priority_resources",
                    "rate_limits": "rate_limits",
                },
            },
            "output_mapping": {
                "collected_data": "crew_results.collected_data",
                "collection_metrics": "crew_results.metrics",
                "quality_scores": "crew_results.quality_scores",
                "collection_gaps": "crew_results.identified_gaps",
                "adapter_results": "crew_results.adapter_results",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 300,  # 5 minutes base
                "temperature": 0.1,  # Very conservative
                "max_iterations": 1,
                "allow_delegation": True,  # Enable adapter delegation
                "enable_memory": False,  # Conservative mode
                "enable_caching": True,  # Performance optimization
                "enable_parallel": True,  # Parallel adapter execution
                "conservative_mode": True,
            },
            "llm_config": {
                "temperature": 0.1,  # Conservative settings
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"],
            },
            "validation_mapping": {
                "required_fields": [
                    "collected_data",
                    "quality_scores",
                    "adapter_results",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "collection_success_rate": {"min": 0.7},
                    "data_quality_score": {"min": 0.6},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "batch_size": 100,
                "parallel_adapters": 5,
                "rate_limiting": True,
                "adaptive_collection": True,
                "quality_based_routing": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=RetryConfig(
            max_attempts=5,  # More retries for collection
            initial_delay_seconds=5.0,
            backoff_multiplier=2.0,
            max_delay_seconds=60.0,
        ),
        timeout_seconds=3600,  # 60 minutes
        metadata={
            "supports_incremental_collection": True,
            "adapter_based_collection": True,
            "ai_orchestrated_collection": True,
            "quality_thresholds": {
                "tier_1": 0.95,
                "tier_2": 0.85,
                "tier_3": 0.75,
                "tier_4": 0.60,
            },
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )

    # Phase 3: Gap Analysis
    gap_analysis_phase = PhaseConfig(
        name="gap_analysis",
        display_name="Gap Analysis",
        description="Analyze collected data for gaps and quality issues using intelligent gap detection",
        required_inputs=["collected_data", "sixr_requirements"],
        optional_inputs=[
            "custom_requirements",
            "priority_fields",
            "quality_thresholds",
        ],
        validators=["gap_validation", "sixr_impact_validation"],
        pre_handlers=["gap_analysis_preparation"],
        post_handlers=["gap_prioritization"],
        crew_config={
            "crew_type": "gap_analysis_crew",
            "crew_factory": "create_gap_analysis_crew",
            "input_mapping": {
                "collected_data": "state.collected_data",
                "requirements": {
                    "sixr_requirements": "sixr_requirements",
                    "custom_requirements": "custom_requirements",
                    "priority_fields": "priority_fields",
                    "quality_thresholds": "quality_thresholds",
                },
                "context": {
                    "automation_tier": "state.automation_tier",
                    "quality_scores": "state.quality_scores",
                    "collection_metrics": "state.collection_metrics",
                },
            },
            "output_mapping": {
                "identified_gaps": "crew_results.data_gaps",
                "gap_categories": "crew_results.gap_categories",
                "sixr_impact": "crew_results.sixr_impact_analysis",
                "resolution_recommendations": "crew_results.recommendations",
                "gap_severity_scores": "crew_results.severity_scores",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 180,  # Conservative 3 minutes
                "temperature": 0.1,  # Very conservative
                "max_iterations": 1,
                "allow_delegation": True,  # Enable agent collaboration
                "enable_memory": False,  # Conservative mode
                "enable_caching": True,  # Performance optimization
                "enable_parallel": False,  # Sequential for accuracy
                "conservative_mode": True,
            },
            "llm_config": {
                "temperature": 0.1,  # Conservative settings
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"],
            },
            "validation_mapping": {
                "required_fields": [
                    "data_gaps",
                    "sixr_impact_analysis",
                    "gap_categories",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "gap_analysis_complete": True,
                    "sixr_coverage": {"min": 0.8},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_gap_detection": True,
                "sixr_alignment_mode": "strict",
                "prioritize_critical_gaps": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1200,  # 20 minutes
        metadata={
            "ai_powered_gap_detection": True,
            "sixr_aligned": True,
            "gap_categories": [
                "missing_data",
                "incomplete_data",
                "quality_issues",
                "validation_errors",
            ],
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )

    # Phase 4: Manual Collection
    manual_collection_phase = PhaseConfig(
        name="manual_collection",
        display_name="Manual Collection",
        description="Collect missing data through intelligent questionnaire generation and response processing",
        required_inputs=["identified_gaps", "questionnaire_templates"],
        optional_inputs=[
            "respondent_assignments",
            "collection_deadlines",
            "response_format",
        ],
        validators=["response_validation", "completeness_validation"],
        pre_handlers=["questionnaire_generation"],
        post_handlers=["response_processing"],
        crew_config={
            "crew_type": "manual_collection_crew",
            "crew_factory": "create_manual_collection_crew",
            "input_mapping": {
                "gaps": {
                    "data_gaps": "state.identified_gaps",
                    "gap_categories": "state.gap_categories",
                    "severity_scores": "state.gap_severity_scores",
                },
                "templates": "questionnaire_templates",
                "context": {
                    "existing_data": "state.collected_data",
                    "respondent_assignments": "respondent_assignments",
                    "collection_deadlines": "collection_deadlines",
                    "response_format": "response_format",
                    "sixr_impact": "state.sixr_impact",
                },
            },
            "output_mapping": {
                "questionnaire_responses": "crew_results.responses",
                "validation_results": "crew_results.validation",
                "confidence_scores": "crew_results.confidence",
                "remaining_gaps": "crew_results.unresolved_gaps",
                "response_quality": "crew_results.response_quality",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 300,  # 5 minutes base
                "temperature": 0.1,  # Very conservative
                "max_iterations": 2,  # Allow follow-up questions
                "allow_delegation": True,  # Enable agent collaboration
                "enable_memory": False,  # Conservative mode
                "enable_caching": True,  # Performance optimization
                "enable_parallel": False,  # Sequential for accuracy
                "conservative_mode": True,
            },
            "llm_config": {
                "temperature": 0.1,  # Conservative settings
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"],
            },
            "validation_mapping": {
                "required_fields": [
                    "responses",
                    "validation",
                    "confidence",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "response_rate": {"min": 0.8},
                    "validation_pass_rate": {"min": 0.9},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_intelligent_questionnaires": True,
                "adaptive_questioning": True,
                "response_validation": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=True,  # Can skip if no gaps
        retry_config=default_retry,
        timeout_seconds=7200,  # 2 hours (allows for human response time)
        metadata={
            "supports_async_collection": True,
            "questionnaire_types": [
                "technical",
                "business",
                "compliance",
                "operational",
            ],
            "ai_powered_questionnaires": True,
            "intelligent_validation": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )

    # Phase 5: Synthesis
    synthesis_phase = PhaseConfig(
        name="synthesis",
        display_name="Data Synthesis",
        description="Synthesize and validate all collected data for completeness and quality using intelligent synthesis",
        required_inputs=["all_collected_data", "validation_rules"],
        optional_inputs=[
            "synthesis_preferences",
            "output_format",
            "export_requirements",
        ],
        validators=["final_validation", "sixr_readiness_validation"],
        pre_handlers=["synthesis_preparation"],
        post_handlers=["collection_finalization"],
        crew_config={
            "crew_type": "data_synthesis_crew",
            "crew_factory": "create_data_synthesis_crew",
            "input_mapping": {
                "data_sources": {
                    "automated_data": "state.automated_collection_data",
                    "manual_data": "state.manual_collection_data",
                    "gap_resolutions": "state.questionnaire_responses",
                },
                "validation_rules": "validation_rules",
                "context": {
                    "automation_tier": "state.automation_tier",
                    "quality_scores": "state.quality_scores",
                    "collection_metrics": "state.collection_metrics",
                    "synthesis_preferences": "synthesis_preferences",
                    "output_format": "output_format",
                },
            },
            "output_mapping": {
                "synthesized_data": "crew_results.final_data",
                "quality_report": "crew_results.quality_report",
                "sixr_readiness": "crew_results.sixr_readiness_score",
                "collection_summary": "crew_results.summary",
                "data_lineage": "crew_results.data_lineage",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 240,  # 4 minutes base
                "temperature": 0.1,  # Very conservative
                "max_iterations": 1,
                "allow_delegation": True,  # Enable agent collaboration
                "enable_memory": False,  # Conservative mode
                "enable_caching": True,  # Performance optimization
                "enable_parallel": False,  # Sequential for accuracy
                "conservative_mode": True,
            },
            "llm_config": {
                "temperature": 0.1,  # Conservative settings
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"],
            },
            "validation_mapping": {
                "required_fields": [
                    "final_data",
                    "quality_report",
                    "sixr_readiness_score",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "data_completeness": {"min": 0.85},
                    "quality_score": {"min": 0.8},
                    "sixr_readiness_score": {"min": 0.75},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_data_synthesis": True,
                "quality_assurance": True,
                "sixr_alignment_validation": True,
                "data_lineage_tracking": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1500,  # 25 minutes
        metadata={
            "generates_quality_report": True,
            "sixr_alignment_check": True,
            "output_formats": ["json", "excel", "pdf"],
            "ai_powered_synthesis": True,
            "data_lineage_enabled": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )

    # Define flow capabilities
    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_branching=True,  # For conditional gap analysis
        supports_iterations=True,
        max_iterations=3,
        supports_scheduling=True,
        supports_parallel_phases=True,  # For parallel adapter execution
        supports_checkpointing=True,
        required_permissions=[
            "collection.read",
            "collection.write",
            "collection.execute",
            "adapter.execute",
        ],
    )

    # Create the flow configuration
    collection_config = FlowTypeConfig(
        name="collection",
        display_name="Data Collection Flow",
        description="Automated Data Collection and Synthesis (ADCS) flow for comprehensive data gathering across multiple platforms and tiers",
        version="2.0.0",
        phases=[
            platform_detection_phase,
            automated_collection_phase,
            gap_analysis_phase,
            manual_collection_phase,
            synthesis_phase,
        ],
        capabilities=capabilities,
        default_configuration={
            "automation_tier": "tier_2",  # Default to Tier 2
            "quality_threshold": 0.8,
            "enable_parallel_collection": True,
            "max_collection_attempts": 3,
            "gap_analysis_depth": "comprehensive",
            "sixr_alignment_mode": "strict",
            "agent_collaboration": True,
            "use_intelligent_routing": True,
            "enable_adaptive_collection": True,
            "confidence_threshold": 0.85,
        },
        initialization_handler="collection_initialization",
        finalization_handler="collection_finalization",
        error_handler="collection_error_handler",
        metadata={
            "category": "data_collection",
            "complexity": "high",
            "estimated_duration_minutes": 180,
            "required_agents": [
                "platform_detection_agent",
                "tier_assessment_agent",
                "collection_orchestrator_agent",
                "gap_detection_agent",
                "questionnaire_agent",
                "synthesis_agent",
            ],
            "output_formats": ["json", "excel", "pdf", "dashboard"],
            "prerequisite_flows": ["discovery"],
            "integration_points": ["discovery_flow", "assessment_flow"],
            "compliance_frameworks": ["SOC2", "ISO27001", "GDPR"],
            "performance_sla": {
                "tier_1": "4_hours",
                "tier_2": "8_hours",
                "tier_3": "24_hours",
                "tier_4": "48_hours",
            },
            "supported_integrations": [
                "aws_adapter",
                "azure_adapter",
                "gcp_adapter",
                "vmware_adapter",
                "kubernetes_adapter",
                "servicenow_adapter",
                "jira_adapter",
            ],
            "custom_capabilities": {
                "multi_tier_automation": True,
                "adaptive_collection": True,
                "quality_based_routing": True,
                "sixr_optimization": True,
                "ai_powered_orchestration": True,
            },
        },
        tags=[
            "collection",
            "automation",
            "adcs",
            "multi-tier",
            "data-quality",
            "ai-powered",
        ],
    )

    return collection_config
