"""
Discovery Flow Phase Constants

Extracted from discovery_flow_config.py to reduce file length.
Contains phase configurations, retry policies, and related constants.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig

# Define retry configuration for phases
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay_seconds=2.0,
    backoff_multiplier=2.0,
    max_delay_seconds=30.0,
)

# Phase 1: Data Import
DATA_IMPORT_PHASE = PhaseConfig(
    name="data_import",
    display_name="Data Import",
    description="Import and validate data from various sources using AI-powered validation",
    required_inputs=["raw_data", "import_config"],
    optional_inputs=["validation_rules", "source_metadata"],
    outputs=["imported_data", "import_summary", "validation_results"],
    expected_duration_minutes=5,
    retry_config=DEFAULT_RETRY_CONFIG,
    parallel_execution=False,
    dependencies=[],
    success_criteria={"imported_records": ">=1", "validation_passed": True},
    failure_conditions={"critical_errors": ">0", "import_failure_rate": ">50%"},
)

# Phase 2: Field Mapping
FIELD_MAPPING_PHASE = PhaseConfig(
    name="field_mapping",
    display_name="Field Mapping",
    description="Map imported fields to standardized schema using AI field analysis",
    required_inputs=["imported_data", "target_schema"],
    optional_inputs=["existing_mappings", "mapping_rules"],
    outputs=["field_mappings", "mapping_confidence", "unmapped_fields"],
    expected_duration_minutes=8,
    retry_config=DEFAULT_RETRY_CONFIG,
    parallel_execution=False,
    dependencies=["data_import"],
    success_criteria={"mapping_coverage": ">=80%", "confidence_score": ">=70%"},
    failure_conditions={"mapping_coverage": "<50%", "critical_fields_unmapped": True},
)

# Phase 3: Data Cleansing
DATA_CLEANSING_PHASE = PhaseConfig(
    name="data_cleansing",
    display_name="Data Cleansing",
    description="Clean and normalize data using AI-powered data quality assessment",
    required_inputs=["imported_data", "field_mappings"],
    optional_inputs=["cleansing_rules", "reference_data"],
    outputs=["cleaned_data", "quality_metrics", "cleansing_log"],
    expected_duration_minutes=10,
    retry_config=DEFAULT_RETRY_CONFIG,
    parallel_execution=True,
    dependencies=["field_mapping"],
    success_criteria={"data_quality_score": ">=75%", "completeness": ">=85%"},
    failure_conditions={"data_quality_score": "<50%", "critical_data_loss": True},
)

# Phase 4: Asset Creation (New phase between cleansing and inventory)
ASSET_CREATION_PHASE = PhaseConfig(
    name="asset_creation",
    display_name="Asset Creation",
    description="Create asset records in database from cleansed data",
    required_inputs=["cleaned_data", "field_mappings"],
    optional_inputs=["asset_templates", "validation_rules"],
    outputs=["created_assets", "asset_summary", "creation_log"],
    expected_duration_minutes=7,
    retry_config=DEFAULT_RETRY_CONFIG,
    parallel_execution=True,
    dependencies=["data_cleansing"],
    success_criteria={"assets_created": ">=1", "creation_success_rate": ">=90%"},
    failure_conditions={"creation_failure_rate": ">25%", "database_errors": ">5"},
)

# Phase 5: Asset Inventory
ASSET_INVENTORY_PHASE = PhaseConfig(
    name="asset_inventory",
    display_name="Asset Inventory",
    description="Build comprehensive asset inventory with AI-driven classification",
    required_inputs=["created_assets", "cleaned_data"],
    optional_inputs=["classification_rules", "inventory_templates"],
    outputs=["asset_inventory", "classifications", "inventory_metrics"],
    expected_duration_minutes=12,
    retry_config=DEFAULT_RETRY_CONFIG,
    parallel_execution=True,
    dependencies=["asset_creation"],
    success_criteria={
        "inventory_completeness": ">=90%",
        "classification_accuracy": ">=80%",
    },
    failure_conditions={"inventory_errors": ">10%", "classification_failures": ">30%"},
)

# Phase 6: Dependency Analysis
DEPENDENCY_ANALYSIS_PHASE = PhaseConfig(
    name="dependency_analysis",
    display_name="Dependency Analysis",
    description="Analyze and map asset dependencies using graph analysis algorithms",
    required_inputs=["asset_inventory", "cleaned_data"],
    optional_inputs=["dependency_rules", "network_topology"],
    outputs=["dependency_map", "relationship_graph", "analysis_insights"],
    expected_duration_minutes=15,
    retry_config=DEFAULT_RETRY_CONFIG,
    parallel_execution=False,
    dependencies=["asset_inventory"],
    success_criteria={"dependencies_mapped": ">=70%", "graph_completeness": ">=80%"},
    failure_conditions={
        "analysis_errors": ">15%",
        "critical_dependencies_missing": True,
    },
)

# All phases in order
ALL_PHASES = [
    DATA_IMPORT_PHASE,
    FIELD_MAPPING_PHASE,
    DATA_CLEANSING_PHASE,
    ASSET_CREATION_PHASE,
    ASSET_INVENTORY_PHASE,
    DEPENDENCY_ANALYSIS_PHASE,
]

# Phase dependencies mapping
PHASE_DEPENDENCIES = {
    "data_import": [],
    "field_mapping": ["data_import"],
    "data_cleansing": ["field_mapping"],
    "asset_creation": ["data_cleansing"],
    "asset_inventory": ["asset_creation"],
    "dependency_analysis": ["asset_inventory"],
}

# Expected phase sequence
PHASE_SEQUENCE = [
    "data_import",
    "field_mapping",
    "data_cleansing",
    "asset_creation",
    "asset_inventory",
    "dependency_analysis",
]
