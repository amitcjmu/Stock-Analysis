"""
Discovery Flow Configuration
Per ADR-027: FlowTypeConfig as universal pattern

Comprehensive asset discovery and inventory flow configuration.
Version 3.0.0 reduces scope to 5 phases (removed dependency_analysis
and tech_debt_assessment which moved to Assessment flow).
"""

from app.services.flow_type_registry import (
    FlowCapabilities,
    FlowTypeConfig,
)
from app.services.child_flow_services import DiscoveryChildFlowService
from .discovery_phases import (
    get_asset_inventory_phase,
    get_data_cleansing_phase,
    get_data_import_phase,
    get_data_validation_phase,
    get_field_mapping_phase,
)


def get_discovery_flow_config() -> FlowTypeConfig:
    """
    Get Discovery flow configuration

    Per ADR-027: Discovery focuses on data acquisition and normalization.
    Dependency analysis and tech debt moved to Assessment flow.

    Phases:
    1. Data Import - Import CMDB data
    2. Data Validation - Validate imported data
    3. Field Mapping - Map source fields to target schema
    4. Data Cleansing - Clean and normalize data
    5. Asset Inventory - Create asset records
    """

    # Define flow capabilities
    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_branching=False,
        supports_iterations=True,
        max_iterations=3,
        supports_scheduling=True,
        supports_parallel_phases=False,
        supports_checkpointing=True,
        required_permissions=[
            "discovery.read",
            "discovery.write",
            "discovery.execute",
        ],
    )

    # Create flow configuration
    return FlowTypeConfig(
        name="discovery",
        display_name="Discovery Flow",
        description=(
            "Data discovery flow for importing, validating, mapping, "
            "and creating asset inventory from CMDB exports"
        ),
        version="3.0.0",  # Major version for phase scope change
        phases=[
            get_data_import_phase(),
            get_data_validation_phase(),
            get_field_mapping_phase(),
            get_data_cleansing_phase(),
            get_asset_inventory_phase(),
        ],
        child_flow_service=DiscoveryChildFlowService,  # Per ADR-025
        capabilities=capabilities,
        default_configuration={
            "auto_validate": True,
            "quality_threshold": 0.8,
            "enable_smart_mapping": True,
            "create_assets_incrementally": True,
            "agent_collaboration": True,
            "confidence_threshold": 0.85,
        },
        initialization_handler="discovery_initialization",
        finalization_handler="discovery_finalization",
        error_handler="discovery_error_handler",
        metadata={
            "category": "data_acquisition",
            "complexity": "medium",
            "estimated_duration_minutes": 60,
            "required_agents": [
                "data_import_agent",
                "validation_agent",
                "mapping_agent",
                "cleansing_agent",
                "inventory_agent",
            ],
            "output_formats": ["json", "excel", "dashboard"],
            "prerequisite_flows": [],
            "next_flows": ["collection", "assessment"],
            "phase_scope_change": {
                "version": "3.0.0",
                "removed_phases": ["dependency_analysis", "tech_debt_assessment"],
                "reason": "Moved to Assessment flow per ADR-027",
                "backward_compatibility": "Database flags retained for legacy data",
            },
        },
        tags=[
            "discovery",
            "data_import",
            "asset_inventory",
            "cmdb",
        ],
    )
