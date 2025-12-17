"""
Collection Flow Configuration
ADCS: Automated Data Collection and Synthesis Flow Configuration

Comprehensive data collection flow configuration for automated platform discovery,
multi-tiered collection strategies, gap analysis, and manual collection.
"""

from app.services.flow_type_registry import (
    FlowCapabilities,
    FlowTypeConfig,
)

# Import phase configurations from modular files
from .collection_phases import (
    get_asset_selection_phase,
    get_auto_enrichment_phase,  # NEW: Phase 2 - Enrichment timing fix
    get_gap_analysis_phase,
    get_questionnaire_generation_phase,
    get_manual_collection_phase,
    get_synthesis_phase,
)

# Per ADR-025: Use child_flow_service pattern (no crew_class)
# REMOVED - CollectionFlow was removed
try:
    from app.services.child_flow_services import CollectionChildFlowService
except ImportError:
    CollectionChildFlowService = None


def get_collection_flow_config() -> FlowTypeConfig:
    """
    Get the Collection flow configuration with all phases

    Phases:
    1. Asset Selection - Detect platforms and select assets for collection
    2. Gap Analysis - Analyze missing data and quality issues
    3. Questionnaire Generation - Generate questionnaires for missing data
    4. Manual Collection - Collect data through questionnaires and manual processes
    5. Synthesis - Synthesize and validate all collected data
    """

    # Get all phase configurations from modular files
    asset_selection_phase = get_asset_selection_phase()
    auto_enrichment_phase = (
        get_auto_enrichment_phase()
    )  # NEW: Phase 2 - Run BEFORE gap analysis
    gap_analysis_phase = get_gap_analysis_phase()
    questionnaire_generation_phase = get_questionnaire_generation_phase()
    manual_collection_phase = get_manual_collection_phase()
    synthesis_phase = get_synthesis_phase()

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
        description=(
            "Automated Data Collection and Synthesis (ADCS) flow for comprehensive "
            "data gathering across multiple platforms and tiers"
        ),
        version="2.1.0",  # Incremented for Phase 2 enrichment timing fix
        phases=[
            asset_selection_phase,
            auto_enrichment_phase,  # NEW: Phase 2 - Enrichment BEFORE gap analysis
            gap_analysis_phase,
            questionnaire_generation_phase,
            manual_collection_phase,
            synthesis_phase,
        ],
        child_flow_service=(
            CollectionChildFlowService if CollectionChildFlowService else None
        ),  # Per ADR-025: Single execution path (REMOVED - CollectionFlow was removed)
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
            # Assessment Readiness Requirements - configurable question IDs
            # Updated per Qodo review to decouple logic from code
            "assessment_readiness_requirements": {
                "business_criticality_questions": [
                    "business_criticality",
                    "business_criticality_score",
                ],
                "environment_questions": [
                    "environment",
                    "deployment_environment",
                    "hosting_environment",
                    "architecture_pattern",  # Proxy: indicates deployment sophistication
                    "availability_requirements",  # Proxy: indicates environment needs
                ],
            },
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
