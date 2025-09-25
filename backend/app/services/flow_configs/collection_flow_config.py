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
    get_gap_analysis_phase,
    get_questionnaire_generation_phase,
    get_manual_collection_phase,
    get_synthesis_phase,
)

# Conditional import for UnifiedCollectionFlow with graceful fallback
COLLECTION_FLOW_AVAILABLE = False
UnifiedCollectionFlow = None

try:
    from app.services.crewai_flows.unified_collection_flow import UnifiedCollectionFlow

    COLLECTION_FLOW_AVAILABLE = True
except ImportError:
    # Graceful fallback when CrewAI is not available
    COLLECTION_FLOW_AVAILABLE = False
    UnifiedCollectionFlow = None


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
        version="2.0.0",
        phases=[
            asset_selection_phase,
            gap_analysis_phase,
            questionnaire_generation_phase,
            manual_collection_phase,
            synthesis_phase,
        ],
        crew_class=(
            UnifiedCollectionFlow if COLLECTION_FLOW_AVAILABLE else None
        ),  # Conditional crew class registration
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
            "collection_flow_available": COLLECTION_FLOW_AVAILABLE,
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
