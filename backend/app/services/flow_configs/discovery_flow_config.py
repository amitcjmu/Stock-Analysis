"""
Discovery Flow Configuration - Compact Version
MFO-039: Create Discovery flow configuration

Comprehensive asset discovery and inventory flow configuration
with all 6 phases and associated validators/handlers.
"""

from app.services.flow_type_registry import FlowCapabilities, FlowTypeConfig

# Import phase constants from separate file to reduce file size
from app.services.flow_configs.discovery_phase_constants import ALL_PHASES

# Import the UnifiedDiscoveryFlow class for crew_class registration
from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow

# Import the DiscoveryChildFlowService for child flow operations
from app.services.child_flow_services import DiscoveryChildFlowService


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

    discovery_config = FlowTypeConfig(
        name="discovery",
        display_name="Discovery Flow",
        description="Comprehensive asset discovery and inventory flow for migration assessment",
        version="2.0.0",
        phases=ALL_PHASES,  # Import from constants file
        capabilities=FlowCapabilities(
            supports_parallel_execution=True,
            supports_phase_rollback=True,
            supports_incremental_execution=True,
            supports_checkpointing=True,
            supports_failure_recovery=True,
            supports_real_time_monitoring=True,
            supports_dynamic_scaling=True,
        ),
        metadata={
            "max_parallel_phases": 3,
            "estimated_total_duration_minutes": 60,
            "resource_requirements": {
                "cpu": "moderate",
                "memory": "high",
                "storage": "moderate",
                "network": "low",
            },
            "required_integrations": ["crewai", "database"],
            "optional_integrations": ["external_apis", "file_systems"],
            "validation_config": {
                "strict_phase_validation": True,
                "allow_phase_skipping": False,
                "require_all_outputs": False,
                "validate_input_schemas": True,
                "enforce_dependencies": True,
            },
            "ui_config": {
                "show_phase_progress": True,
                "allow_manual_intervention": True,
                "display_real_time_logs": True,
                "enable_phase_restart": True,
                "supports_templates": True,
            },
        },
        crew_class=UnifiedDiscoveryFlow,
        # CC FIX: Comment out crew factory to use persistent agents instead
        # crew_factory=create_discovery_crew,  # Deprecated - now uses persistent agents
        child_flow_service=DiscoveryChildFlowService,
        tags=["discovery", "data_import", "inventory", "assessment_prerequisite"],
    )

    return discovery_config
