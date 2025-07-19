"""
Collection Flow Configuration
ADCS: Automated Data Collection and Synthesis Flow Configuration

Comprehensive data collection flow configuration for automated platform discovery,
multi-tiered collection strategies, gap analysis, and manual collection.
"""

from typing import Dict, Any, List
from dataclasses import field

from app.services.flow_type_registry import (
    FlowTypeConfig, 
    PhaseConfig, 
    FlowCapabilities,
    RetryConfig
)


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
        max_delay_seconds=30.0
    )
    
    # Phase 1: Platform Detection
    platform_detection_phase = PhaseConfig(
        name="platform_detection",
        display_name="Platform Detection",
        description="Detect and identify target platforms for data collection",
        required_inputs=["environment_config", "automation_tier"],
        optional_inputs=["credentials", "discovery_scope"],
        validators=["platform_validation", "credential_validation"],
        pre_handlers=["collection_initialization"],
        post_handlers=["platform_inventory_creation"],
        crew_config={
            "crew_type": "platform_detection_crew",
            "crew_factory": "create_platform_detection_crew",
            "input_mapping": {
                "environment_config": "environment_config",
                "automation_tier": "automation_tier",
                "discovery_scope": "metadata.discovery_scope"
            },
            "output_mapping": {
                "detected_platforms": "crew_results.platforms",
                "adapter_recommendations": "crew_results.recommended_adapters",
                "platform_metadata": "crew_results.platform_metadata"
            },
            "execution_config": {
                "timeout_seconds": 120,
                "max_iterations": 1,
                "allow_delegation": False,
                "enable_memory": True
            },
            "validation_mapping": {
                "required_fields": ["platforms", "recommended_adapters"],
                "success_criteria": {
                    "platforms_count": {"min": 1}
                }
            }
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=600,  # 10 minutes
        metadata={
            "supports_auto_discovery": True,
            "platform_types": ["cloud", "on-premise", "hybrid", "saas"],
            "ai_assisted_detection": True
        }
    )
    
    # Phase 2: Automated Collection
    automated_collection_phase = PhaseConfig(
        name="automated_collection",
        display_name="Automated Collection",
        description="Collect data automatically using platform-specific adapters",
        required_inputs=["detected_platforms", "adapter_configs"],
        optional_inputs=["collection_filters", "priority_resources"],
        validators=["collection_validation", "data_quality_validation"],
        pre_handlers=["adapter_preparation"],
        post_handlers=["collection_data_normalization"],
        crew_config={
            "crew_type": "automated_collection_crew",
            "crew_factory": "create_automated_collection_crew",
            "input_mapping": {
                "platforms": "state.detected_platforms",
                "adapter_configs": "state.adapter_configs",
                "automation_tier": "state.automation_tier"
            },
            "output_mapping": {
                "collected_data": "crew_results.collected_data",
                "collection_metrics": "crew_results.metrics",
                "quality_scores": "crew_results.quality_scores",
                "collection_gaps": "crew_results.identified_gaps"
            },
            "execution_config": {
                "timeout_seconds": 300,  # 5 minutes per platform
                "max_iterations": 1,
                "allow_delegation": True,  # Delegate to multiple adapters
                "enable_memory": True,
                "enable_parallel": True   # Parallel collection
            },
            "validation_mapping": {
                "required_fields": ["collected_data", "quality_scores"],
                "success_criteria": {
                    "collection_success_rate": {"min": 0.7},
                    "data_quality_score": {"min": 0.6}
                }
            },
            "performance_config": {
                "batch_size": 100,
                "parallel_adapters": 5,
                "rate_limiting": True
            }
        },
        can_pause=True,
        can_skip=False,
        retry_config=RetryConfig(
            max_attempts=5,  # More retries for collection
            initial_delay_seconds=5.0,
            backoff_multiplier=2.0,
            max_delay_seconds=60.0
        ),
        timeout_seconds=3600,  # 60 minutes
        metadata={
            "supports_incremental_collection": True,
            "adapter_based_collection": True,
            "quality_thresholds": {
                "tier_1": 0.95,
                "tier_2": 0.85,
                "tier_3": 0.75,
                "tier_4": 0.60
            }
        }
    )
    
    # Phase 3: Gap Analysis
    gap_analysis_phase = PhaseConfig(
        name="gap_analysis",
        display_name="Gap Analysis",
        description="Analyze collected data for gaps and quality issues",
        required_inputs=["collected_data", "sixr_requirements"],
        optional_inputs=["custom_requirements", "priority_fields"],
        validators=["gap_validation", "sixr_impact_validation"],
        pre_handlers=["gap_analysis_preparation"],
        post_handlers=["gap_prioritization"],
        crew_config={
            "crew_type": "gap_analysis_crew",
            "crew_factory": "create_gap_analysis_crew",
            "input_mapping": {
                "collected_data": "state.collected_data",
                "sixr_requirements": "sixr_requirements",
                "automation_tier": "state.automation_tier"
            },
            "output_mapping": {
                "identified_gaps": "crew_results.data_gaps",
                "gap_categories": "crew_results.gap_categories",
                "sixr_impact": "crew_results.sixr_impact_analysis",
                "resolution_recommendations": "crew_results.recommendations"
            },
            "execution_config": {
                "timeout_seconds": 180,
                "max_iterations": 1,
                "allow_delegation": False,
                "enable_memory": True
            },
            "validation_mapping": {
                "required_fields": ["data_gaps", "sixr_impact_analysis"],
                "success_criteria": {
                    "gap_analysis_complete": True
                }
            }
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=900,  # 15 minutes
        metadata={
            "ai_gap_detection": True,
            "sixr_aligned": True,
            "gap_categories": ["missing_data", "incomplete_data", "quality_issues", "validation_errors"]
        }
    )
    
    # Phase 4: Manual Collection
    manual_collection_phase = PhaseConfig(
        name="manual_collection",
        display_name="Manual Collection",
        description="Collect missing data through questionnaires and manual processes",
        required_inputs=["identified_gaps", "questionnaire_templates"],
        optional_inputs=["respondent_assignments", "collection_deadlines"],
        validators=["response_validation", "completeness_validation"],
        pre_handlers=["questionnaire_generation"],
        post_handlers=["response_processing"],
        crew_config={
            "crew_type": "manual_collection_crew",
            "crew_factory": "create_manual_collection_crew",
            "input_mapping": {
                "data_gaps": "state.identified_gaps",
                "templates": "questionnaire_templates",
                "existing_data": "state.collected_data"
            },
            "output_mapping": {
                "questionnaire_responses": "crew_results.responses",
                "validation_results": "crew_results.validation",
                "confidence_scores": "crew_results.confidence",
                "remaining_gaps": "crew_results.unresolved_gaps"
            },
            "execution_config": {
                "timeout_seconds": 300,
                "max_iterations": 2,  # Allow follow-up questions
                "allow_delegation": False,
                "enable_memory": True
            },
            "validation_mapping": {
                "required_fields": ["responses", "validation"],
                "success_criteria": {
                    "response_rate": {"min": 0.8},
                    "validation_pass_rate": {"min": 0.9}
                }
            }
        },
        can_pause=True,
        can_skip=True,  # Can skip if no gaps
        retry_config=default_retry,
        timeout_seconds=7200,  # 2 hours (allows for human response time)
        metadata={
            "supports_async_collection": True,
            "questionnaire_types": ["technical", "business", "compliance", "operational"],
            "ai_assisted_validation": True
        }
    )
    
    # Phase 5: Synthesis
    synthesis_phase = PhaseConfig(
        name="synthesis",
        display_name="Data Synthesis",
        description="Synthesize and validate all collected data for completeness and quality",
        required_inputs=["all_collected_data", "validation_rules"],
        optional_inputs=["synthesis_preferences", "output_format"],
        validators=["final_validation", "sixr_readiness_validation"],
        pre_handlers=["synthesis_preparation"],
        post_handlers=["collection_finalization"],
        crew_config={
            "crew_type": "data_synthesis_crew",
            "crew_factory": "create_data_synthesis_crew",
            "input_mapping": {
                "automated_data": "state.automated_collection_data",
                "manual_data": "state.manual_collection_data",
                "validation_rules": "validation_rules",
                "automation_tier": "state.automation_tier"
            },
            "output_mapping": {
                "synthesized_data": "crew_results.final_data",
                "quality_report": "crew_results.quality_report",
                "sixr_readiness": "crew_results.sixr_readiness_score",
                "collection_summary": "crew_results.summary"
            },
            "execution_config": {
                "timeout_seconds": 240,
                "max_iterations": 1,
                "allow_delegation": False,
                "enable_memory": True
            },
            "validation_mapping": {
                "required_fields": ["final_data", "quality_report", "sixr_readiness_score"],
                "success_criteria": {
                    "data_completeness": {"min": 0.85},
                    "quality_score": {"min": 0.8},
                    "sixr_readiness_score": {"min": 0.75}
                }
            }
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1200,  # 20 minutes
        metadata={
            "generates_quality_report": True,
            "sixr_alignment_check": True,
            "output_formats": ["json", "excel", "pdf"]
        }
    )
    
    # Flow capabilities
    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_checkpointing=True,
        supports_branching=True,
        supports_parallel_phases=True,  # For parallel adapter execution
        supports_iterations=True,
        max_iterations=3  # For retry logic
    )
    
    # Create and return flow configuration
    return FlowTypeConfig(
        name="collection",
        display_name="Data Collection Flow", 
        description="Automated Data Collection and Synthesis (ADCS) flow for comprehensive data gathering across multiple platforms and tiers",
        version="1.0.0",
        phases=[
            platform_detection_phase,
            automated_collection_phase,
            gap_analysis_phase,
            manual_collection_phase,
            synthesis_phase
        ],
        capabilities=capabilities,
        initialization_handler="collection_initialization",
        finalization_handler="collection_finalization",
        error_handler="collection_error_handler",
        default_configuration={
            "automation_tier": "tier_2",  # Default to Tier 2
            "quality_threshold": 0.8,
            "enable_parallel_collection": True,
            "max_collection_attempts": 3,
            "gap_analysis_depth": "comprehensive",
            "sixr_alignment_mode": "strict"
        },
        metadata={
            "flow_category": "data_collection",
            "integration_points": ["discovery_flow", "assessment_flow"],
            "compliance_frameworks": ["SOC2", "ISO27001", "GDPR"],
            "performance_sla": {
                "tier_1": "4_hours",
                "tier_2": "8_hours", 
                "tier_3": "24_hours",
                "tier_4": "48_hours"
            },
            "supported_integrations": [
                "aws_adapter",
                "azure_adapter", 
                "gcp_adapter",
                "vmware_adapter",
                "kubernetes_adapter",
                "servicenow_adapter",
                "jira_adapter"
            ],
            "custom_capabilities": {
                "multi_tier_automation": True,
                "adaptive_collection": True,
                "quality_based_routing": True,
                "sixr_optimization": True
            },
            "rollback_handler": "collection_rollback_handler",
            "checkpoint_handler": "collection_checkpoint_handler",
            "dependencies": ["discovery"],
            "prerequisites": {
                "required_data": ["client_account", "engagement", "environment_config"],
                "required_permissions": ["read:platforms", "write:collection_data", "execute:adapters"],
                "required_services": ["adapter_registry", "quality_analyzer", "gap_detector"]
            }
        },
        tags=["collection", "automation", "adcs", "multi-tier", "data-quality"]
    )