"""
Discovery Flow Configuration
MFO-039: Create Discovery flow configuration

Comprehensive asset discovery and inventory flow configuration
with all 6 phases and associated validators/handlers.
"""

from typing import Dict, Any, List
from dataclasses import field

from app.services.flow_type_registry import (
    FlowTypeConfig, 
    PhaseConfig, 
    FlowCapabilities,
    RetryConfig
)


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
        max_delay_seconds=30.0
    )
    
    # Phase 1: Data Import
    data_import_phase = PhaseConfig(
        name="data_import",
        display_name="Data Import",
        description="Import and validate data from various sources",
        required_inputs=["raw_data", "import_config"],
        optional_inputs=["validation_rules", "source_metadata"],
        validators=["required_fields", "data_format", "schema_validation"],
        pre_handlers=["data_import_preparation"],
        post_handlers=["data_import_validation"],
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1800,  # 30 minutes
        metadata={
            "supports_bulk_import": True,
            "supported_formats": ["csv", "json", "xml", "excel"],
            "max_file_size_mb": 500
        }
    )
    
    # Phase 2: Field Mapping
    field_mapping_phase = PhaseConfig(
        name="field_mapping",
        display_name="Field Mapping",
        description="Map imported fields to standard schema",
        required_inputs=["imported_data", "mapping_rules"],
        optional_inputs=["custom_mappings", "transformation_rules"],
        validators=["field_mapping_validation", "mapping_completeness"],
        pre_handlers=["field_analysis"],
        post_handlers=["mapping_verification"],
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1200,  # 20 minutes
        metadata={
            "auto_mapping_enabled": True,
            "ai_assisted_mapping": True
        }
    )
    
    # Phase 3: Data Cleansing
    data_cleansing_phase = PhaseConfig(
        name="data_cleansing",
        display_name="Data Cleansing",
        description="Clean and normalize data",
        required_inputs=["mapped_data", "cleansing_rules"],
        optional_inputs=["quality_thresholds", "normalization_rules"],
        validators=["data_quality", "cleansing_validation"],
        pre_handlers=["quality_assessment"],
        post_handlers=["cleansing_report_generation"],
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1500,  # 25 minutes
        metadata={
            "duplicate_detection": True,
            "anomaly_detection": True,
            "data_enrichment": True
        }
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
            "ci_cmdb_integration": True
        }
    )
    
    # Phase 5: Asset Inventory
    asset_inventory_phase = PhaseConfig(
        name="asset_inventory",
        display_name="Asset Inventory",
        description="Build comprehensive asset inventory",
        required_inputs=["assets", "inventory_config"],
        optional_inputs=["grouping_rules", "hierarchy_rules"],
        validators=["inventory_validation", "completeness_check"],
        pre_handlers=["inventory_preparation"],
        post_handlers=["inventory_optimization"],
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1800,  # 30 minutes
        metadata={
            "categorization": True,
            "tagging": True,
            "cost_allocation": True
        }
    )
    
    # Phase 6: Dependency Analysis (Optional)
    dependency_analysis_phase = PhaseConfig(
        name="dependency_analysis",
        display_name="Dependency Analysis",
        description="Analyze asset dependencies and relationships",
        required_inputs=["inventory", "dependency_rules"],
        optional_inputs=["discovery_depth", "relationship_types"],
        validators=["dependency_validation", "circular_dependency_check"],
        pre_handlers=["dependency_discovery"],
        post_handlers=["dependency_visualization"],
        can_pause=True,
        can_skip=True,  # Optional phase
        retry_config=default_retry,
        timeout_seconds=2100,  # 35 minutes
        metadata={
            "auto_discovery": True,
            "impact_analysis": True,
            "visualization_enabled": True
        }
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
        required_permissions=["discovery.read", "discovery.write", "discovery.execute"]
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
            dependency_analysis_phase
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
            "auto_remediation": True
        },
        initialization_handler="discovery_initialization",
        finalization_handler="discovery_finalization",
        error_handler="discovery_error_handler",
        metadata={
            "category": "data_ingestion",
            "complexity": "high",
            "estimated_duration_minutes": 180,
            "required_agents": ["data_import_agent", "mapping_agent", "cleansing_agent"],
            "supports_templates": True
        },
        tags=["discovery", "data_import", "inventory", "assessment_prerequisite"]
    )
    
    return discovery_config