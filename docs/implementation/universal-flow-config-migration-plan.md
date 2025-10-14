# Universal FlowTypeConfig Migration - Implementation Plan

**ADR**: 027-universal-flow-type-config-pattern.md
**Estimated Duration**: 5 days
**Risk Level**: Medium (mitigated with feature flags)

---

## Overview

Migrate all flows to use FlowTypeConfig pattern and consolidate scattered phase definitions into a single authoritative source. Move dependency_analysis and tech_debt_assessment from Discovery to Assessment flow.

---

## Pre-Migration Checklist

- [ ] ADR-027 approved by stakeholders
- [ ] All existing tests passing
- [ ] Feature flag system ready
- [ ] Rollback plan documented
- [ ] Monitoring/alerting configured

---

## Phase 1: Create Discovery FlowTypeConfig (Day 1)

### 1.1 Create Discovery Phase Configs

**File**: `backend/app/services/flow_configs/discovery_phases/__init__.py`

```python
"""Discovery flow phase configurations"""
from .data_import_phase import get_data_import_phase
from .data_validation_phase import get_data_validation_phase
from .field_mapping_phase import get_field_mapping_phase
from .data_cleansing_phase import get_data_cleansing_phase
from .asset_inventory_phase import get_asset_inventory_phase

__all__ = [
    'get_data_import_phase',
    'get_data_validation_phase',
    'get_field_mapping_phase',
    'get_data_cleansing_phase',
    'get_asset_inventory_phase',
]
```

**Create individual phase files** (example: `data_import_phase.py`):

```python
from app.services.flow_type_registry import PhaseConfig, RetryConfig

def get_data_import_phase() -> PhaseConfig:
    """Data Import and Validation Phase"""
    return PhaseConfig(
        name="data_import",
        display_name="Data Import & Validation",
        description="Import CMDB data and validate format/quality",

        # Inputs
        required_inputs=["file_upload"],
        optional_inputs=["import_options"],

        # Validation
        validators=[
            "file_format_validation",
            "data_quality_check",
            "schema_validation"
        ],

        # Handlers
        pre_handlers=["create_import_record", "initialize_storage"],
        post_handlers=[
            "persist_completion_flag",
            "notify_completion",
            "prepare_next_phase"
        ],

        # CrewAI Integration
        crew_config={
            "crew_type": "data_import_validation",
            "crew_factory": "create_data_import_validation_crew",
            "input_mapping": {
                "file_data": "state.file_upload",
                "import_options": "state.import_options",
            },
            "output_mapping": {
                "import_results": "crew_results.validation_results",
                "data_quality_score": "crew_results.quality_score",
            },
            "execution_config": {
                "timeout_seconds": 300,
                "temperature": 0.1,
                "enable_memory": False,  # Per ADR-024
            },
        },

        # Execution Control
        can_pause=True,
        can_skip=False,
        retry_config=RetryConfig(
            max_attempts=3,
            initial_delay_seconds=5.0,
            backoff_multiplier=2.0,
            max_delay_seconds=60.0,
        ),
        timeout_seconds=1800,  # 30 minutes

        # UI Metadata
        metadata={
            "ui_route": "/discovery/cmdb-import",
            "estimated_duration_minutes": 10,
            "icon": "upload",
            "help_text": "Upload your CMDB export file",
            "success_criteria": [
                "File format valid",
                "No critical data quality issues",
                "At least 1 asset imported"
            ],
        },
    )
```

**Repeat for**:
- `data_validation_phase.py`
- `field_mapping_phase.py`
- `data_cleansing_phase.py`
- `asset_inventory_phase.py`

### 1.2 Create Main Discovery Config

**File**: `backend/app/services/flow_configs/discovery_flow_config.py`

```python
"""
Discovery Flow Configuration
Per ADR-027: FlowTypeConfig as universal pattern
"""

from app.services.flow_type_registry import (
    FlowCapabilities,
    FlowTypeConfig,
)
from app.services.child_flow_services import DiscoveryChildFlowService
from .discovery_phases import (
    get_data_import_phase,
    get_data_validation_phase,
    get_field_mapping_phase,
    get_data_cleansing_phase,
    get_asset_inventory_phase,
)


def get_discovery_flow_config() -> FlowTypeConfig:
    """
    Get Discovery flow configuration

    Per ADR-027: Discovery focuses on data acquisition and normalization.
    Dependency analysis and tech debt moved to Assessment flow.

    Phases:
    1. Initialization - Setup flow context
    2. Data Import - Import CMDB data
    3. Data Validation - Validate imported data
    4. Field Mapping - Map source fields to target schema
    5. Data Cleansing - Clean and normalize data
    6. Asset Inventory - Create asset records
    7. Finalization - Complete flow and prepare for Assessment
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
                "backward_compatibility": "Database flags retained for legacy data"
            },
        },
        tags=[
            "discovery",
            "data_import",
            "asset_inventory",
            "cmdb",
        ],
    )
```

### 1.3 Register Discovery Config

**Note**: We use the helper functions from `flow_type_registry_helpers.py` which wrap the registry singleton.

**File**: `backend/app/app_setup/lifecycle.py` (or `main.py`)

Add startup initialization:

```python
from app.services.flow_type_registry_helpers import initialize_default_flow_configs

# In startup event handler
@app.on_event("startup")
async def startup_event():
    # ... other startup tasks
    
    # Initialize flow type configurations
    initialize_default_flow_configs()
    logger.info("✅ Flow type configurations initialized")
```

The `initialize_default_flow_configs()` function (from `flow_type_registry_helpers.py`) registers all flow configs:

```python
def initialize_default_flow_configs() -> None:
    """
    Initialize default flow configurations
    Called at application startup to register all flow types.
    MUST be called before any flow operations.
    """
    from app.services.flow_configs.discovery_flow_config import get_discovery_flow_config
    from app.services.flow_configs.collection_flow_config import get_collection_flow_config
    from app.services.flow_configs.assessment_flow_config import get_assessment_flow_config

    if not is_flow_registered("discovery"):
        register_flow_config(get_discovery_flow_config())
    if not is_flow_registered("collection"):
        register_flow_config(get_collection_flow_config())
    if not is_flow_registered("assessment"):
        register_flow_config(get_assessment_flow_config())

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Initialized {len(flow_type_registry.list_flow_types())} flow type(s)")
```

**Deliverables**:
- [x] 5 phase config files created
- [x] Main discovery_flow_config.py created
- [x] Registered with FlowTypeRegistry
- [x] Unit tests for config validation

---

## Phase 2: Create Phase Alias System (Day 1)

### 2.1 Centralized Alias Mapping

**File**: `backend/app/services/flow_configs/phase_aliases.py`

```python
"""
Phase name alias system for backward compatibility
Per ADR-027: Support legacy phase names from frontend/database
"""

from typing import Dict, Optional

# Aliases by flow type
PHASE_ALIASES: Dict[str, Dict[str, str]] = {
    "discovery": {
        # Frontend legacy names
        "attribute_mapping": "field_mapping",
        "inventory": "asset_inventory",
        "dependencies": "dependency_analysis",  # Now redirects to Assessment
        "tech_debt": "tech_debt_assessment",    # Now redirects to Assessment

        # Database legacy names
        "data_import_validation": "data_import",
        "data_cleaning": "data_cleansing",
        "assets": "asset_inventory",

        # Special cases
        "initialization": "data_import",  # Legacy start phase
    },
    "collection": {
        "platform_detection": "asset_selection",  # Deprecated
        "automated_collection": "asset_selection",  # Deprecated
        "finalization": "synthesis",
    },
    "assessment": {
        "architecture_minimums": "readiness_assessment",
        "component_sixr_strategies": "risk_assessment",
        "app_on_page_generation": "recommendation_generation",

        # Migrated from Discovery
        "dependencies": "dependency_analysis",
        "tech_debt": "tech_debt_assessment",
    },
}


def normalize_phase_name(flow_type: str, phase: str) -> str:
    """
    Normalize phase name from any variant to canonical name

    Args:
        flow_type: Flow type (discovery, collection, assessment)
        phase: Phase name (any variant)

    Returns:
        Canonical phase name

    Raises:
        ValueError: If phase invalid even after normalization
    """
    # Check if already canonical
    from app.services.flow_type_registry import get_flow_config

    try:
        config = get_flow_config(flow_type)
        canonical_names = [p.name for p in config.phases]

        if phase in canonical_names:
            return phase

        # Check aliases
        aliases = PHASE_ALIASES.get(flow_type, {})
        if phase in aliases:
            normalized = aliases[phase]

            # If alias points to phase in different flow, raise clear error
            if normalized not in canonical_names:
                raise ValueError(
                    f"Phase '{phase}' was moved from {flow_type} to another flow. "
                    f"Please use the correct flow type."
                )

            return normalized

        # Unknown phase
        raise ValueError(
            f"Unknown phase '{phase}' for flow type '{flow_type}'. "
            f"Valid phases: {canonical_names}"
        )
    except Exception as e:
        raise ValueError(f"Error normalizing phase: {e}")


def get_phase_flow_type(phase: str) -> Optional[str]:
    """
    Determine which flow type a phase belongs to

    Useful for migrated phases (dependency_analysis, tech_debt_assessment)
    that may come from legacy discovery code but now belong to assessment.

    Returns:
        Flow type string or None if phase not found
    """
    from app.services.flow_type_registry_helpers import get_all_flow_configs

    for config in get_all_flow_configs():
        phase_names = [p.name for p in config.phases]
        if phase in phase_names:
            return config.name

        # Check aliases
        aliases = PHASE_ALIASES.get(config.name, {})
        for alias, canonical in aliases.items():
            if alias == phase and canonical in phase_names:
                return config.name

    return None
```

### 2.2 Update Consumers

**File**: `backend/app/services/discovery/flow_execution_service.py`

```python
# BEFORE (lines 42-58):
phase_mapping = {
    "field_mapping_suggestions": "field_mapping",
    "data_cleaning": "data_cleansing",
    "assets": "asset_inventory",
}

# AFTER:
from app.services.flow_configs.phase_aliases import normalize_phase_name

# Replace all ad-hoc normalization with:
normalized_phase = normalize_phase_name("discovery", current_phase)
```

**Note**: The `normalize_phase_name()` function internally uses `get_flow_config()` from helpers.

**Deliverables**:
- [x] phase_aliases.py created
- [x] All ad-hoc phase mappings removed
- [x] Consumers updated to use normalize_phase_name
- [x] Tests for alias resolution

---

## Phase 3: Update Assessment Flow (Day 2)

### 3.1 Add Migrated Phases to Assessment

**File**: `backend/app/services/flow_configs/assessment_phases/dependency_analysis_phase.py`

```python
def get_dependency_analysis_phase() -> PhaseConfig:
    """
    Dependency Analysis Phase
    Migrated from Discovery flow per ADR-027
    """
    return PhaseConfig(
        name="dependency_analysis",
        display_name="Dependency Analysis",
        description="Analyze dependencies and relationships between assets",
        required_inputs=["asset_inventory"],
        crew_config={
            "crew_type": "dependency_analysis",
            # ... crew configuration
        },
        metadata={
            "migration_note": "Moved from Discovery flow in v3.0.0",
            "estimated_duration_minutes": 20,
        },
        # ... other config
    )
```

**File**: `backend/app/services/flow_configs/assessment_phases/tech_debt_assessment_phase.py`

```python
def get_tech_debt_assessment_phase() -> PhaseConfig:
    """
    Tech Debt Assessment Phase
    Migrated from Discovery flow per ADR-027
    """
    return PhaseConfig(
        name="tech_debt_assessment",
        display_name="Technical Debt Assessment",
        description="Assess technical debt across asset inventory",
        required_inputs=["asset_inventory", "dependency_map"],
        crew_config={
            "crew_type": "tech_debt_assessment",
            # ... crew configuration
        },
        metadata={
            "migration_note": "Moved from Discovery flow in v3.0.0",
            "estimated_duration_minutes": 30,
        },
        # ... other config
    )
```

### 3.2 Update Assessment Config

**File**: `backend/app/services/flow_configs/assessment_flow_config.py`

```python
from .assessment_phases import (
    # ... existing
    get_dependency_analysis_phase,  # NEW
    get_tech_debt_assessment_phase,  # NEW
)

def get_assessment_flow_config() -> FlowTypeConfig:
    return FlowTypeConfig(
        name="assessment",
        version="3.0.0",  # Major version for new phases
        phases=[
            readiness_assessment_phase,
            complexity_analysis_phase,
            get_dependency_analysis_phase(),  # NEW
            get_tech_debt_assessment_phase(),  # NEW
            risk_assessment_phase,
            recommendation_generation_phase,
        ],
        metadata={
            "phase_scope_change": {
                "version": "3.0.0",
                "added_phases": ["dependency_analysis", "tech_debt_assessment"],
                "reason": "Migrated from Discovery per ADR-027",
                "prerequisite_note": "Requires completed Discovery flow"
            },
        },
        # ... rest of config
    )
```

**Deliverables**:
- [x] dependency_analysis_phase.py created
- [x] tech_debt_assessment_phase.py created
- [x] Assessment config updated
- [x] Tests for new assessment phases

---

## Phase 4: Remove Scattered Phase Definitions (Day 2-3)

### 4.1 Files to Update/Remove

| File | Action | Replacement |
|------|--------|-------------|
| `flow_constants/flow_states.py` | Deprecate PHASE_SEQUENCES + migrate progress calc | `get_flow_config()` |
| `flow_constants/flow_configuration.py` | Deprecate DEFAULT_FLOW_CONFIGS | Use FlowTypeConfig |
| `discovery/flow_config.py` | Remove PHASE_ORDER | Use FlowTypeConfig |
| `discovery_phase_constants.py` | **DELETE** | Duplicate |
| `simple_flow_router.py` | Update PHASE_PROGRESSION | Query FlowTypeConfig |
| `route_decision.py` | Update ROUTE_MAPPING | Query FlowTypeConfig |
| `transition_utils.py` | Remove hardcoded phases | Query FlowTypeConfig |
| `unified_discovery_flow/flow_config.py` | Remove PHASE_ORDER | Query FlowTypeConfig |
| `unified_discovery_flow/phase_controller.py` | Remove phase_sequence | Query FlowTypeConfig |
| `collection_phase_runner.py` | Remove legacy phases | Query FlowTypeConfig |
| `data_import/import_validator.py` | Update legacy phase names | Query FlowTypeConfig |

### 4.2 Update flow_states.py

**File**: `backend/app/utils/flow_constants/flow_states.py`

```python
import warnings
from typing import Dict, List, Optional
from enum import Enum

# Import helper functions
from app.services.flow_type_registry_helpers import get_flow_config

# Keep enums for type safety
class FlowPhase(str, Enum):
    """Phase name enums (for type safety only)"""
    INITIALIZATION = "initialization"
    DATA_IMPORT = "data_import"
    # ... all phases


# Deprecation warning for PHASE_SEQUENCES
def _warn_phase_sequences_deprecated():
    """Issue deprecation warning for PHASE_SEQUENCES usage"""
    warnings.warn(
        "PHASE_SEQUENCES is deprecated. Use get_flow_config() instead. "
        "Will be removed in v4.0.0. See ADR-027 for migration guide.",
        DeprecationWarning,
        stacklevel=3
    )


# Keep for backward compatibility only - DO NOT USE
PHASE_SEQUENCES: Dict[FlowType, List[FlowPhase]] = {
    # Kept for backward compatibility only
    # DO NOT USE for new code
}


def get_next_phase(flow_type: FlowType, current_phase: FlowPhase) -> Optional[FlowPhase]:
    """
    Get next phase from FlowTypeConfig
    
    .. deprecated:: 3.0.0
        PHASE_SEQUENCES is no longer authoritative.
        Use FlowTypeConfig instead via get_flow_config().
        Will be removed in v4.0.0
    """
    warnings.warn(
        "get_next_phase() with PHASE_SEQUENCES is deprecated. "
        "Use FlowTypeConfig instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    config = get_flow_config(flow_type.value)
    phases = [p.name for p in config.phases]
    
    try:
        current_idx = phases.index(current_phase.value)
        if current_idx < len(phases) - 1:
            return FlowPhase(phases[current_idx + 1])
    except (ValueError, IndexError):
        pass
    
    return None


def calculate_progress_percentage(flow_type: str, current_phase: str) -> float:
    """
    Calculate progress percentage based on FlowTypeConfig
    
    Migrated from hardcoded PHASE_SEQUENCES to config-driven approach.
    
    Args:
        flow_type: Flow type (discovery, collection, assessment)
        current_phase: Current phase name
        
    Returns:
        Progress percentage (0.0 to 100.0)
    """
    config = get_flow_config(flow_type)
    phases = [p.name for p in config.phases]
    
    if current_phase not in phases:
        return 0.0
    
    current_idx = phases.index(current_phase)
    return (current_idx + 1) / len(phases) * 100.0
```

### 4.3 Deprecate flow_configuration.py

**File**: `backend/app/utils/flow_constants/flow_configuration.py`

This file contains a duplicate configuration system (`DEFAULT_FLOW_CONFIGS`) that conflicts with FlowTypeConfig.

```python
import warnings

# Issue deprecation warning at module import
warnings.warn(
    "flow_configuration.py and DEFAULT_FLOW_CONFIGS are deprecated. "
    "Use FlowTypeConfig pattern instead via get_flow_config(). "
    "This module will be removed in v4.0.0. See ADR-027.",
    DeprecationWarning,
    stacklevel=2
)

# Keep existing code for backward compatibility but mark as deprecated in docstrings
"""
.. deprecated:: 3.0.0
    This module is deprecated. Use FlowTypeConfig pattern instead.
    See backend/app/services/flow_configs/ for new implementations.
    Will be removed in v4.0.0
"""

# ... existing DEFAULT_FLOW_CONFIGS code retained for legacy support
```

### 4.5 Update Route Decision Tool

**File**: `backend/app/services/agents/flow_processing/tools/route_decision.py`

```python
# BEFORE (lines 25-48):
ROUTE_MAPPING = {
    'discovery': {
        'data_import': '/discovery/cmdb-import',
        # ... hardcoded routes
    }
}

# AFTER:
from app.services.flow_type_registry_helpers import get_flow_config

def get_route_for_phase(flow_type: str, phase: str) -> str:
    """Get UI route from FlowTypeConfig metadata"""
    config = get_flow_config(flow_type)
    
    for phase_config in config.phases:
        if phase_config.name == phase:
            return phase_config.metadata.get('ui_route', f'/{flow_type}')
    
    return f'/{flow_type}'
```

### 4.6 Update Transition Utils

**File**: `backend/app/services/flow_orchestration/transition_utils.py`

```python
# BEFORE (lines 394-436):
discovery_phases = [
    "initialization",
    "data_import",
    # ... hardcoded list
]

# AFTER:
from app.services.flow_type_registry_helpers import get_flow_config

def get_flow_phases(flow_type: str) -> List[str]:
    """Get phases from FlowTypeConfig"""
    config = get_flow_config(flow_type)
    return [p.name for p in config.phases]
```

**Deliverables**:
- [x] flow_states.py deprecation warnings added (using warnings.warn())
- [x] flow_configuration.py marked deprecated
- [x] calculate_progress_percentage() migrated to config-driven
- [x] discovery_phase_constants.py deleted
- [x] All hardcoded phase lists removed
- [x] All consumers updated to use helper functions
- [x] Tests updated

---

## Phase 5: Update DiscoveryChildFlowService (Day 3)

### 5.1 Enhance Child Flow Service

**File**: `backend/app/services/child_flow_services/discovery.py`

```python
class DiscoveryChildFlowService(BaseChildFlowService):
    """
    Discovery flow child service
    Per ADR-027: Uses FlowTypeConfig for phase execution
    """

    async def initialize_flow(self, state: DiscoveryFlowState) -> DiscoveryFlowState:
        """Initialize discovery flow using FlowTypeConfig"""
        from app.services.flow_type_registry_helpers import get_flow_config
        
        config = get_flow_config("discovery")

        # Validate prerequisites
        for phase_config in config.phases:
            for validator_name in phase_config.validators:
                validator = self._get_validator(validator_name)
                await validator(state)

        return state

    async def execute_phase(
        self,
        state: DiscoveryFlowState,
        phase: str
    ) -> DiscoveryFlowState:
        """
        Execute a single phase using FlowTypeConfig

        Implements:
        - Pre-handlers
        - Crew execution
        - Post-handlers
        - Retry logic
        - Timeout management
        """
        from app.services.flow_type_registry_helpers import get_flow_config
        
        config = get_flow_config("discovery")
        phase_config = self._get_phase_config(config, phase)

        # Pre-handlers
        for handler_name in phase_config.pre_handlers:
            handler = self._get_handler(handler_name)
            state = await handler(state)

        # Execute crew with retry
        result = await self._execute_with_retry(
            phase_config,
            state,
            retry_config=phase_config.retry_config
        )

        # Post-handlers
        for handler_name in phase_config.post_handlers:
            handler = self._get_handler(handler_name)
            state = await handler(state, result)

        return state

    async def _execute_with_retry(
        self,
        phase_config: PhaseConfig,
        state: DiscoveryFlowState,
        retry_config: RetryConfig
    ) -> Any:
        """Execute phase with automatic retry"""
        for attempt in range(retry_config.max_attempts):
            try:
                # Execute crew
                crew = self._create_crew(phase_config.crew_config)
                result = await crew.execute(state)

                # Validate result
                if self._validate_result(result, phase_config):
                    return result

            except Exception as e:
                if attempt == retry_config.max_attempts - 1:
                    raise

                delay = retry_config.calculate_delay(attempt)
                await asyncio.sleep(delay)

        raise RuntimeError(f"Phase {phase_config.name} failed after {retry_config.max_attempts} attempts")
```

**Deliverables**:
- [x] DiscoveryChildFlowService enhanced
- [x] Phase execution uses FlowTypeConfig
- [x] Pre/post handlers implemented
- [x] Retry logic implemented
- [x] Tests for enhanced service

---

## Phase 6: Create API Endpoint (Day 3)

### 6.1 Phase Metadata Endpoint

**File**: `backend/app/api/v1/endpoints/flow_metadata.py`

```python
"""
Flow metadata endpoints
Provides authoritative phase information for frontend
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from app.services.flow_type_registry_helpers import get_flow_config, get_all_flow_configs
from app.services.flow_configs.phase_aliases import normalize_phase_name

router = APIRouter(prefix="/api/v1/flow-metadata", tags=["flow-metadata"])


@router.get("/phases")
async def get_all_flow_phases() -> Dict[str, Any]:
    """
    Get authoritative phase sequences for all flow types

    Frontend SHOULD use this endpoint instead of hardcoding phases.
    Ensures backend/frontend stay synchronized.

    Returns:
        {
            "discovery": {
                "phases": ["data_import", "field_mapping", ...],
                "phase_details": [{...}, {...}]
            },
            ...
        }
    """
    result = {}

    for config in get_all_flow_configs():
        phases = []
        phase_details = []

        for phase_config in config.phases:
            phases.append(phase_config.name)
            phase_details.append({
                "name": phase_config.name,
                "display_name": phase_config.display_name,
                "description": phase_config.description,
                "order": phases.index(phase_config.name),
                "estimated_duration_minutes": phase_config.metadata.get("estimated_duration_minutes"),
                "can_pause": phase_config.can_pause,
                "can_skip": phase_config.can_skip,
                "ui_route": phase_config.metadata.get("ui_route"),
                "icon": phase_config.metadata.get("icon"),
                "help_text": phase_config.metadata.get("help_text"),
            })

        result[config.name] = {
            "flow_type": config.name,
            "display_name": config.display_name,
            "version": config.version,
            "phases": phases,
            "phase_details": phase_details,
            "phase_count": len(phases),
            "estimated_total_duration_minutes": sum(
                p.get("estimated_duration_minutes", 0) for p in phase_details
            ),
        }

    return result


@router.get("/phases/{flow_type}")
async def get_flow_type_phases(flow_type: str) -> Dict[str, Any]:
    """
    Get phases for specific flow type

    Args:
        flow_type: Flow type (discovery, collection, assessment, etc.)

    Returns:
        Phase information for the flow type

    Raises:
        404: If flow type not found
    """
    try:
        config = get_flow_config(flow_type)

        phases = []
        phase_details = []

        for phase_config in config.phases:
            phases.append(phase_config.name)
            phase_details.append({
                "name": phase_config.name,
                "display_name": phase_config.display_name,
                "description": phase_config.description,
                "order": len(phases) - 1,
                "estimated_duration_minutes": phase_config.metadata.get("estimated_duration_minutes"),
                "can_pause": phase_config.can_pause,
                "can_skip": phase_config.can_skip,
                "ui_route": phase_config.metadata.get("ui_route"),
            })

        return {
            "flow_type": config.name,
            "display_name": config.display_name,
            "version": config.version,
            "phases": phases,
            "phase_details": phase_details,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/phases/normalize")
async def normalize_phase(
    flow_type: str,
    phase: str
) -> Dict[str, str]:
    """
    Normalize a phase name from any variant to canonical name

    Useful for legacy frontend code that uses old phase names.

    Args:
        flow_type: Flow type
        phase: Phase name (any variant)

    Returns:
        {"canonical_phase": "field_mapping"}

    Raises:
        400: If phase invalid
    """
    try:
        canonical = normalize_phase_name(flow_type, phase)
        return {
            "flow_type": flow_type,
            "input_phase": phase,
            "canonical_phase": canonical,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 6.2 Register Router

**File**: `backend/app/api/v1/router_registry.py`

```python
from app.api.v1.endpoints import flow_metadata

# Register flow metadata routes
app.include_router(flow_metadata.router)
```

**Deliverables**:
- [x] flow_metadata.py created
- [x] GET /api/v1/flow-metadata/phases endpoint
- [x] GET /api/v1/flow-metadata/phases/{flow_type} endpoint
- [x] POST /api/v1/flow-metadata/phases/normalize endpoint
- [x] OpenAPI documentation
- [x] Tests for all endpoints

---

## Phase 7: Update Frontend (Day 4)

### 7.1 Create useFlowPhases Hook

**File**: `src/hooks/useFlowPhases.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/lib/api';

export interface PhaseDetail {
  name: string;
  display_name: string;
  description: string;
  order: number;
  estimated_duration_minutes: number;
  can_pause: boolean;
  can_skip: boolean;
  ui_route: string;
  icon?: string;
  help_text?: string;
}

export interface FlowPhases {
  flow_type: string;
  display_name: string;
  version: string;
  phases: string[];
  phase_details: PhaseDetail[];
  phase_count: number;
}

/**
 * Fetch authoritative phase sequence from backend
 *
 * Replaces hardcoded PHASE_SEQUENCES in flowRoutes.ts
 */
export function useFlowPhases(flowType: string) {
  return useQuery<FlowPhases>(
    ['flow-phases', flowType],
    async () => {
      const response = await apiCall(`/api/v1/flow-metadata/phases/${flowType}`);
      return response as FlowPhases;
    },
    {
      staleTime: 30 * 60 * 1000, // 30 minutes (phases rarely change)
      cacheTime: 60 * 60 * 1000, // 1 hour
    }
  );
}

/**
 * Fetch all flow phases
 */
export function useAllFlowPhases() {
  return useQuery<Record<string, FlowPhases>>(
    ['flow-phases-all'],
    async () => {
      const response = await apiCall('/api/v1/flow-metadata/phases');
      return response as Record<string, FlowPhases>;
    },
    {
      staleTime: 30 * 60 * 1000,
      cacheTime: 60 * 60 * 1000,
    }
  );
}
```

### 7.2 Update Frontend Phase Files

**Files to Update**:

1. `src/config/flowRoutes.ts` - Main phase sequences
2. `src/config/discoveryRoutes.ts` - Discovery phase routes
3. `src/utils/secureNavigation.ts` - Phase validation constants

### 7.2.1 Update flowRoutes.ts

**File**: `src/config/flowRoutes.ts`

```typescript
// BEFORE (lines 258-291):
export const PHASE_SEQUENCES: Record<FlowType, string[]> = {
  discovery: [
    "data_import",
    "attribute_mapping",  // ← Wrong name
    // ...
  ],
  // ... hardcoded sequences
};

// AFTER:
/**
 * @deprecated Use useFlowPhases hook instead
 *
 * This constant is kept for backward compatibility only.
 * New code should fetch phases from API using useFlowPhases.
 *
 * Will be removed in v4.0.0
 */
export const PHASE_SEQUENCES_LEGACY: Record<FlowType, string[]> = {
  // ... keep for legacy code during migration
};

// New function that queries API
export async function getPhaseSequence(flowType: FlowType): Promise<string[]> {
  const response = await fetch(`/api/v1/flow-metadata/phases/${flowType}`);
  const data = await response.json();
  return data.phases;
}
```

### 7.2.2 Update discoveryRoutes.ts

**File**: `src/config/discoveryRoutes.ts`

```typescript
// BEFORE:
export const DISCOVERY_PHASE_ROUTES = {
  data_import: '/discovery/cmdb-import',
  attribute_mapping: '/discovery/field-mapping',  // Wrong phase name
  // ... hardcoded routes
};

// AFTER:
/**
 * @deprecated Use useFlowPhases hook to get routes from phase metadata
 * 
 * Phase routes are now provided by the backend API via FlowTypeConfig.
 * This constant kept for backward compatibility only.
 */
export const DISCOVERY_PHASE_ROUTES_LEGACY = {
  // ... keep for legacy code
};

// Use API-driven routes instead
export async function getPhaseRoute(flowType: string, phase: string): Promise<string> {
  const response = await fetch(`/api/v1/flow-metadata/phases/${flowType}`);
  const data = await response.json();
  const phaseDetail = data.phase_details.find((p: any) => p.name === phase);
  return phaseDetail?.ui_route || `/${flowType}`;
}
```

### 7.2.3 Update secureNavigation.ts

**File**: `src/utils/secureNavigation.ts`

```typescript
// BEFORE:
const DISCOVERY_PHASES = [
  'data_import',
  'attribute_mapping',  // Wrong name
  'data_cleansing',
  // ... hardcoded list
];

// AFTER:
/**
 * @deprecated Use useFlowPhases hook to validate phases
 * 
 * Phase validation should use the authoritative backend API.
 * This constant kept for backward compatibility only.
 */
const DISCOVERY_PHASES_LEGACY = [
  // ... keep for legacy code
];

// Use API-driven validation
export async function isValidPhase(flowType: string, phase: string): Promise<boolean> {
  const response = await fetch(`/api/v1/flow-metadata/phases/${flowType}`);
  const data = await response.json();
  return data.phases.includes(phase);
}
```

### 7.3 Optional: Add Serializer Hook for Phase Normalization

**File**: `backend/app/api/v1/serializers/flow_serializer.py` (new)

This optional enhancement normalizes `current_phase` at the response boundary to ensure consistent phase names.

```python
"""
Flow response serializers
Optional: Normalize phase names at API boundary
"""

from typing import Dict, Any
from app.services.flow_configs.phase_aliases import normalize_phase_name

def normalize_flow_response(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize flow response data
    
    Ensures current_phase uses canonical names even if
    database contains legacy phase names.
    
    Args:
        flow_data: Raw flow data from database
        
    Returns:
        Flow data with normalized phase names
    """
    if "current_phase" in flow_data and "flow_type" in flow_data:
        try:
            flow_data["current_phase"] = normalize_phase_name(
                flow_data["flow_type"],
                flow_data["current_phase"]
            )
        except ValueError:
            # Phase invalid, leave as-is and let validation catch it
            pass
    
    return flow_data
```

**Apply in API endpoints**:

```python
# Example: backend/app/api/v1/endpoints/flow_processing/queries.py
from app.api.v1.serializers.flow_serializer import normalize_flow_response

async def process_flow_continuation(...):
    # ... existing code ...
    
    flow_data = flow_status_result.get("flow", {})
    
    # Normalize phase names before using
    flow_data = normalize_flow_response(flow_data)
    
    current_phase = flow_data.get("current_phase", "data_import")
    # ... rest of code
```

**Benefits**:
- Frontend always receives canonical phase names
- Legacy data automatically normalized
- Reduces phase name confusion at API boundary
- Optional enhancement, not required for migration

### 7.4 Update Components

**Files to Update**:
- `src/pages/discovery/**/*.tsx` - Replace hardcoded phase checks with API
- `src/components/collection/progress/*.tsx` - Use useFlowPhases
- `src/pages/assessment/**/*.tsx` - Use useFlowPhases

**Example Update**:
```typescript
// BEFORE:
const validPhases = ['data_import', 'attribute_mapping', 'data_cleansing'];

// AFTER:
const { data: phases } = useFlowPhases('discovery');
const validPhases = phases?.phases || [];
```

**Deliverables**:
- [x] useFlowPhases hook created
- [x] flowRoutes.ts marked deprecated
- [x] discoveryRoutes.ts updated to use API
- [x] secureNavigation.ts updated to use API
- [x] Optional: Serializer hook for phase normalization
- [x] All components updated to use hook
- [x] Legacy constants kept for gradual migration
- [x] Tests for new hook

---

## Phase 8: Database Migration (Day 4)

### 8.1 Add Deprecation Comments

**File**: `backend/alembic/versions/XXXX_add_phase_deprecation_comments.py`

```python
"""Add deprecation comments for migrated phases

Revision ID: XXXX
Revises: YYYY
Create Date: 2025-01-XX

"""
from alembic import op


def upgrade():
    # Add comments to deprecated fields
    op.execute("""
        COMMENT ON COLUMN migration.discovery_flows.dependency_analysis_completed IS
        'DEPRECATED: This phase moved to Assessment flow in v3.0.0. '
        'Kept for backward compatibility with legacy data. '
        'See ADR-027 for details.'
    """)

    op.execute("""
        COMMENT ON COLUMN migration.discovery_flows.tech_debt_assessment_completed IS
        'DEPRECATED: This phase moved to Assessment flow in v3.0.0. '
        'Kept for backward compatibility with legacy data. '
        'See ADR-027 for details.'
    """)


def downgrade():
    # Remove comments
    op.execute("COMMENT ON COLUMN migration.discovery_flows.dependency_analysis_completed IS NULL")
    op.execute("COMMENT ON COLUMN migration.discovery_flows.tech_debt_assessment_completed IS NULL")
```

**Deliverables**:
- [x] Migration created
- [x] Tested in development
- [x] Applied to staging
- [x] Documentation updated

---

## Phase 9: Feature Flag Implementation (Day 5)

### 9.1 Add Feature Flag

**File**: `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # Feature flags
    USE_FLOW_TYPE_CONFIG: bool = True  # Default ON for new pattern

    # Rollback capability
    LEGACY_PHASE_SEQUENCES_ENABLED: bool = False  # Emergency rollback
```

### 9.2 Conditional Execution

**File**: `backend/app/services/discovery/flow_execution_service.py`

```python
from app.core.config import settings
from app.services.flow_type_registry_helpers import get_flow_config

def get_discovery_phases() -> List[str]:
    """Get discovery phases based on feature flag"""
    
    if settings.USE_FLOW_TYPE_CONFIG:
        # New pattern (default)
        config = get_flow_config("discovery")
        return [p.name for p in config.phases]
    else:
        # Legacy fallback (emergency only)
        from app.utils.flow_constants.flow_states import PHASE_SEQUENCES, FlowType
        return [p.value for p in PHASE_SEQUENCES[FlowType.DISCOVERY]]
```

**Deliverables**:
- [x] Feature flags added
- [x] Conditional execution paths
- [x] Rollback tested
- [x] Monitoring configured

---

## Phase 10: Testing & Validation (Day 5)

### 10.1 Test Checklist

**Unit Tests**:
- [ ] All PhaseConfig objects validate successfully
- [ ] Phase alias normalization works correctly
- [ ] FlowTypeConfig query functions work
- [ ] Deprecated code paths show warnings

**Integration Tests**:
- [ ] Discovery flow executes with new config
- [ ] Phase transitions work correctly
- [ ] Retry logic functions as expected
- [ ] Timeout handling works

**E2E Tests**:
- [ ] Full discovery flow completes successfully
- [ ] Assessment receives correct input from Discovery
- [ ] Frontend displays correct phase information
- [ ] Legacy phase names still work (via aliases)

**Migration Tests**:
- [ ] Flows in progress continue without issues
- [ ] Completed flows display correctly
- [ ] Database flags backward compatible

### 10.2 Performance Testing

- [ ] Phase metadata endpoint responds < 100ms
- [ ] Frontend phase queries cached properly
- [ ] No N+1 query issues
- [ ] Memory usage acceptable

### 10.3 Rollback Testing

- [ ] Feature flag rollback works
- [ ] No data loss on rollback
- [ ] Flows can be resumed after rollback

**Deliverables**:
- [x] All tests passing
- [x] Performance benchmarks met
- [x] Rollback verified
- [x] Production readiness approved

---

## Rollback Plan

### Immediate Rollback (< 1 hour)

```bash
# Set feature flag to disable new pattern
export USE_FLOW_TYPE_CONFIG=false
export LEGACY_PHASE_SEQUENCES_ENABLED=true

# Restart services
docker-compose restart backend
```

### Full Rollback (< 4 hours)

1. Revert database migration
2. Revert backend code to previous commit
3. Revert frontend code to previous commit
4. Deploy previous version

**No data loss** - All database schema changes are additive only.

---

## Success Criteria

- [ ] All flows use FlowTypeConfig pattern
- [ ] Zero hardcoded phase sequences in codebase
- [ ] Frontend fetches phases from API
- [ ] All tests passing (100% coverage on new code)
- [ ] Performance metrics met
- [ ] Production deployment successful
- [ ] No customer-facing issues
- [ ] Documentation updated
- [ ] Team trained on new pattern

---

## Post-Migration Cleanup (Week 2)

After 1 week of stable production:

1. Remove feature flags (make new pattern permanent)
2. Delete deprecated code paths
3. Remove PHASE_SEQUENCES from flow_states.py
4. Remove legacy frontend PHASE_SEQUENCES
5. Update all documentation
6. Announce deprecation removals

---

## Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Phase transition breaks | Medium | High | Feature flags, comprehensive testing |
| Performance degradation | Low | Medium | Caching, load testing |
| Frontend/backend desync | Low | High | API contract, version checks |
| Data loss | Very Low | Critical | Additive-only migrations, backups |
| Customer impact | Low | Critical | Staged rollout, monitoring |

---

## Communication Plan

**Before Migration**:
- [ ] Stakeholder briefing
- [ ] Team training session
- [ ] Documentation published
- [ ] Timeline communicated

**During Migration**:
- [ ] Daily standup updates
- [ ] Real-time issue tracking
- [ ] Slack channel for questions

**After Migration**:
- [ ] Retrospective meeting
- [ ] Lessons learned documented
- [ ] Success metrics shared

---

## References

- ADR-027: Universal FlowTypeConfig Pattern
- ADR-025: Child Flow Service Pattern
- ADR-024: CrewAI Memory Configuration
- [FlowTypeConfig API Documentation]
- [Collection Flow Implementation] (reference example)
- [Assessment Flow Implementation] (reference example)
