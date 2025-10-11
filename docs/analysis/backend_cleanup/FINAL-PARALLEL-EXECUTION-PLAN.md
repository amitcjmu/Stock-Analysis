# FINAL: Parallel CC Agent Execution Plan
**Backend Cleanup & Migration**

**Date**: 2025-10-10
**Based on**: Dependency graph analysis + GPT5 consolidated plan (003)
**Execution Model**: Parallel CC agents with dependency tracking

---

## 🎯 Executive Summary

**Approach**: Two parallel workstreams that can be executed simultaneously by CC agents:
- **Workstream A (Archive)**: Move safe files to archive/ (1-2 days)
- **Workstream B (Migrate)**: Decouple old patterns and modernize (3-4 weeks)

**Total Timeline**: 4 weeks with parallel execution
**Agent Requirements**: 3-4 CC agents working concurrently

---

## ✅ Final Classification (Corrected from 003)

### KEEP (actively used - DO NOT TOUCH)
```
✅ backend/app/services/crewai_flows/crews/persistent_field_mapping.py (166 importers)
✅ backend/app/services/crewai_flows/crews/field_mapping_crew.py (168 importers)
✅ backend/app/services/crewai_flows/crews/simple_field_mapper.py (CRITICAL fallback)
✅ backend/app/services/crewai_flows/crews/dependency_analysis_crew/ (172 importers)
✅ backend/app/services/crewai_flows/crews/technical_debt_crew.py (165 importers)
✅ backend/app/services/crewai_flows/crews/tech_debt_analysis_crew/ (171 importers)
✅ backend/app/services/crewai_flows/crews/component_analysis_crew/
✅ backend/app/services/crewai_flows/crews/architecture_standards_crew/
✅ backend/app/services/crewai_flows/crews/sixr_strategy_crew/
✅ backend/app/services/crewai_flows/crews/app_server_dependency_crew/
✅ backend/app/services/crewai_flows/crews/app_app_dependency_crew.py
✅ backend/app/services/crewai_flows/crews/asset_intelligence_crew.py
✅ backend/app/services/crewai_flows/crews/data_import_validation_crew.py
✅ backend/app/services/crewai_flows/crews/optimized_crew_base.py
✅ backend/app/services/crewai_flows/crews/crew_config.py
✅ backend/app/services/crewai_flows/config/crew_factory/factory.py (209 importers)
✅ backend/app/services/crews/base_crew.py (398 importers)
✅ backend/app/services/crewai_flows/crews/inventory_building_crew_original/ (160 importers - keep for now)
```

### MIGRATE (decouple, then archive later)

**CORRECTED from 003 based on dependency analysis:**

```python
# Files with mixed patterns (OLD + NEW) - need refactoring
🔄 backend/app/services/crewai_flows/crews/persistent_field_mapping.py (has both Crew() AND TenantScopedAgentPool)
🔄 backend/app/services/crewai_flows/crews/inventory_building_crew_original/crew.py (mixed patterns)
🔄 backend/app/services/field_mapping_executor/agent_executor.py (mixed patterns)
🔄 backend/app/services/flow_configs/discovery_flow_config.py (crew_class usage)

# crew_class usage (needs migration to child_flow_service)
🔄 backend/app/services/flow_configs/discovery_flow_config.py
🔄 backend/app/services/sixr_engine_modular.py
🔄 backend/app/services/master_flow_orchestrator/operations/flow_creation_operations.py
🔄 backend/app/services/master_flow_orchestrator/operations/flow_lifecycle/state_operations.py
🔄 backend/app/services/flow_type_registry.py
```

### ARCHIVE (safe now - 20 files)

**CORRECTED from 003:**

```bash
# Unmounted endpoints (6 files)
🗑️ backend/app/api/v1/endpoints/demo.py
🗑️ backend/app/api/v1/endpoints/data_cleansing.py.bak
🗑️ backend/app/api/v1/endpoints/flow_processing.py.backup
🗑️ backend/app/api/v1/discovery/dependency_endpoints.py
🗑️ backend/app/api/v1/discovery/chat_interface.py
🗑️ backend/app/api/v1/discovery/app_server_mappings.py

# Legacy superseded crews (5 files) - CORRECTED
🗑️ backend/app/services/crewai_flows/crews/inventory_building_crew_legacy.py
🗑️ backend/app/services/crewai_flows/crews/collection/manual_collection_crew.py
🗑️ backend/app/services/crewai_flows/crews/collection/data_synthesis_crew.py
🗑️ backend/app/services/crewai_flows/crews/field_mapping_crew_fast.py
🗑️ backend/app/services/crewai_flows/crews/agentic_asset_enrichment_crew.py  # CORRECTED: No active imports
# 🗑️ backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/  # CORRECTED: Add to archive list (only self-referential)

# Example agents (9 files) - move to docs/examples/
🗑️ backend/app/services/agents/*_crewai.py → docs/examples/agent_patterns/
```

**Key Corrections from 003:**
1. ✅ `agentic_asset_enrichment_crew.py` → ARCHIVE (no active imports found)
2. ✅ `optimized_field_mapping_crew/` → ARCHIVE (only self-referential)
3. ✅ `inventory_building_crew_original/` → KEEP (160 importers - migrate later)

---

## 🚀 Workstream A: Archive (Parallel Execution)

**Agent**: `general-purpose` or manual file operations
**Duration**: 1-2 days
**Dependencies**: None (can start immediately)

### Task A1: Archive Unmounted Endpoints
```bash
# Create archive structure
mkdir -p backend/archive/2025-10/endpoints_legacy

# Move files
mv backend/app/api/v1/endpoints/demo.py \
   backend/archive/2025-10/endpoints_legacy/demo.py
mv backend/app/api/v1/endpoints/data_cleansing.py.bak \
   backend/archive/2025-10/endpoints_legacy/data_cleansing.py.bak
mv backend/app/api/v1/endpoints/flow_processing.py.backup \
   backend/archive/2025-10/endpoints_legacy/flow_processing.py.backup

# Legacy discovery endpoints
mv backend/app/api/v1/discovery/dependency_endpoints.py \
   backend/archive/2025-10/endpoints_legacy/dependency_endpoints.py
mv backend/app/api/v1/discovery/chat_interface.py \
   backend/archive/2025-10/endpoints_legacy/chat_interface.py
mv backend/app/api/v1/discovery/app_server_mappings.py \
   backend/archive/2025-10/endpoints_legacy/app_server_mappings.py

# Create README
cat > backend/archive/2025-10/endpoints_legacy/README.md << 'EOF'
# Archived Legacy Endpoints

Archived: 2025-10-10
Reason: Unmounted from router_registry.py

## Files
- demo.py - Demo endpoint (never registered)
- data_cleansing.py.bak - Backup file
- flow_processing.py.backup - Backup file
- dependency_endpoints.py - Legacy discovery endpoint
- chat_interface.py - Legacy discovery endpoint
- app_server_mappings.py - Legacy discovery endpoint

## Verification
Checked router_registry.py - none of these are registered.
EOF
```

### Task A2: Archive Legacy Crews
```bash
# Create archive structure
mkdir -p backend/archive/2025-10/crews_legacy

# Move files
mv backend/app/services/crewai_flows/crews/inventory_building_crew_legacy.py \
   backend/archive/2025-10/crews_legacy/inventory_building_crew_legacy.py
mv backend/app/services/crewai_flows/crews/collection/manual_collection_crew.py \
   backend/archive/2025-10/crews_legacy/manual_collection_crew.py
mv backend/app/services/crewai_flows/crews/collection/data_synthesis_crew.py \
   backend/archive/2025-10/crews_legacy/data_synthesis_crew.py
mv backend/app/services/crewai_flows/crews/field_mapping_crew_fast.py \
   backend/archive/2025-10/crews_legacy/field_mapping_crew_fast.py
mv backend/app/services/crewai_flows/crews/agentic_asset_enrichment_crew.py \
   backend/archive/2025-10/crews_legacy/agentic_asset_enrichment_crew.py
mv backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/ \
   backend/archive/2025-10/crews_legacy/optimized_field_mapping_crew/

# Create README
cat > backend/archive/2025-10/crews_legacy/README.md << 'EOF'
# Archived Legacy Crews

Archived: 2025-10-10
Reason: Superseded by persistent agent pattern or service layer

## Files
- inventory_building_crew_legacy.py - Superseded by persistent agents
- manual_collection_crew.py - Superseded by validation_service.py
- data_synthesis_crew.py - Not imported
- field_mapping_crew_fast.py - Superseded by persistent_field_mapping.py
- agentic_asset_enrichment_crew.py - No active imports
- optimized_field_mapping_crew/ - Only self-referential imports

## Verification
Dependency analysis showed no active imports outside self-references.
EOF
```

### Task A3: Move Example Agents to Docs
```bash
# Create examples structure
mkdir -p docs/examples/agent_patterns

# Move all example agents
for agent in backend/app/services/agents/*_crewai.py; do
    basename=$(basename "$agent" .py)
    mv "$agent" "docs/examples/agent_patterns/${basename}_example.py"
done

# Create README
cat > docs/examples/agent_patterns/README.md << 'EOF'
# Agent Pattern Examples (ADR-024)

These are example agent implementations demonstrating ADR-024 patterns.
They are NOT used in production - see TenantScopedAgentPool for actual usage.

## Files (9 examples)
- validation_workflow_agent_crewai_example.py
- tier_recommendation_agent_crewai_example.py
- progress_tracking_agent_crewai_example.py
- data_validation_agent_crewai_example.py
- data_cleansing_agent_crewai_example.py
- critical_attribute_assessor_crewai_example.py
- credential_validation_agent_crewai_example.py
- collection_orchestrator_agent_crewai_example.py
- asset_inventory_agent_crewai_example.py

## Usage
Study these for pattern reference, but use TenantScopedAgentPool in production.
EOF

# Remove from services/__init__.py if present
# (This needs manual verification)
```

### Task A4: Add Pre-commit Guards
```bash
# Create guard script
cat > backend/scripts/check_legacy_imports.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
FAILED=0

echo "🔍 Checking for legacy import patterns..."

# Check for imports from archive
if git diff --cached -U0 -- '*.py' | grep -E "^\+.*(from|import)\s+(backend\.archive|app\.archive)" 2>/dev/null; then
  echo "❌ Import from archive detected in staged changes"
  FAILED=1
fi

# Check for direct Crew() instantiation
if git diff --cached -U0 -- '*.py' | grep -E "^\+.*\bCrew\s*\(" 2>/dev/null; then
  echo "❌ Direct Crew() instantiation detected. Use TenantScopedAgentPool instead."
  FAILED=1
fi

# Check for new crew_class usage
if git diff --cached -U0 -- '*.py' | grep -E "^\+.*crew_class\s*=" 2>/dev/null; then
  echo "❌ crew_class assignment detected. Use child_flow_service instead."
  FAILED=1
fi

if [ $FAILED -eq 0 ]; then
  echo "✅ No legacy patterns detected"
fi

exit $FAILED
SCRIPT

chmod +x backend/scripts/check_legacy_imports.sh

# Add to .pre-commit-config.yaml
# (Requires manual edit)
```

**Acceptance Criteria for Workstream A:**
- [ ] 20 files moved to archive/
- [ ] 9 example agents moved to docs/examples/
- [ ] READMEs created in archive directories
- [ ] Pre-commit guard script created and enabled
- [ ] All tests still pass
- [ ] No imports from archived files remain

---

## 🔄 Workstream B: Migrate (Parallel Phases)

**Agents**: `python-crewai-fastapi-expert` (primary), `sre-precommit-enforcer` (verification)
**Duration**: 3-4 weeks
**Dependencies**: Sequential phases, but parallel tasks within phases

### Phase B1: Create Persistent Agent Wrappers (Week 1)

**Tasks can run in PARALLEL** - assign to multiple agents

#### Task B1.1: Field Mapping Wrapper
**Agent**: `python-crewai-fastapi-expert`

```python
# Create: backend/app/services/persistent_agents/field_mapping_persistent.py

from typing import Any, Dict
from app.core.context import RequestContext
from app.services.service_registry import ServiceRegistry
from app.services.persistent_agents import TenantScopedAgentPool

async def get_persistent_field_mapper(
    context: RequestContext,
    service_registry: ServiceRegistry
) -> Any:
    """
    Get or create persistent field mapping agent.

    Replaces: app.services.crewai_flows.crews.field_mapping_crew.create_field_mapping_crew

    Returns: Persistent agent configured for field mapping
    """
    return await TenantScopedAgentPool.get_agent(
        context=context,
        agent_type="field_mapping",
        service_registry=service_registry
    )

async def execute_field_mapping(
    context: RequestContext,
    service_registry: ServiceRegistry,
    raw_data: list,
    **kwargs
) -> Dict[str, Any]:
    """Execute field mapping using persistent agent"""
    agent = await get_persistent_field_mapper(context, service_registry)
    return await agent.process(raw_data, **kwargs)
```

#### Task B1.2: Dependency Analysis Wrapper
**Agent**: `python-crewai-fastapi-expert`

```python
# Create: backend/app/services/persistent_agents/dependency_analysis_persistent.py

async def get_persistent_dependency_analyzer(
    context: RequestContext,
    service_registry: ServiceRegistry
) -> Any:
    """
    Get or create persistent dependency analysis agent.

    Replaces: app.services.crewai_flows.crews.dependency_analysis_crew
    """
    return await TenantScopedAgentPool.get_agent(
        context=context,
        agent_type="dependency_analysis",
        service_registry=service_registry
    )
```

#### Task B1.3: Technical Debt Wrapper
**Agent**: `python-crewai-fastapi-expert`

```python
# Create: backend/app/services/persistent_agents/technical_debt_persistent.py

async def get_persistent_tech_debt_analyzer(
    context: RequestContext,
    service_registry: ServiceRegistry
) -> Any:
    """
    Get or create persistent technical debt analysis agent.

    Replaces: app.services.crewai_flows.crews.technical_debt_crew
    """
    return await TenantScopedAgentPool.get_agent(
        context=context,
        agent_type="tech_debt_analysis",
        service_registry=service_registry
    )
```

#### Task B1.4: Data Import Validation Wrapper
**Agent**: `python-crewai-fastapi-expert`

```python
# Create: backend/app/services/persistent_agents/data_import_validation_persistent.py

async def get_persistent_data_import_validator(
    context: RequestContext,
    service_registry: ServiceRegistry
) -> Any:
    """
    Get or create persistent data import validation agent.

    Replaces: app.services.crewai_flows.crews.data_import_validation_crew
    """
    return await TenantScopedAgentPool.get_agent(
        context=context,
        agent_type="data_import_validation",
        service_registry=service_registry
    )
```

**Verification**: All 4 wrappers created, tests pass

---

### Phase B2: Update Importers (Week 2)

**Tasks can run in PARALLEL** - assign to multiple agents
**Pattern**: Replace old imports with new persistent wrappers

#### Task B2.1: Update unified_flow_crew_manager.py
**Agent**: `python-crewai-fastapi-expert`

```python
# File: backend/app/services/crewai_flows/handlers/unified_flow_crew_manager.py

# OLD (lines 67-82)
try:
    from app.services.crewai_flows.crews.persistent_field_mapping import (
        create_persistent_field_mapper,
    )
    field_mapping_factory = create_persistent_field_mapper
except ImportError:
    from app.services.crewai_flows.crews.field_mapping_crew import (
        create_field_mapping_crew,
    )
    field_mapping_factory = create_field_mapping_crew

# NEW
from app.services.persistent_agents.field_mapping_persistent import (
    get_persistent_field_mapper
)
field_mapping_factory = get_persistent_field_mapper
```

#### Task B2.2: Update field_mapping.py phase executor
**Agent**: `python-crewai-fastapi-expert`

```python
# File: backend/app/services/crewai_flows/handlers/crew_execution/field_mapping.py

# OLD (lines 62-78)
from app.services.crewai_flows.crews.field_mapping_crew import (
    create_field_mapping_crew,
)
crew = create_field_mapping_crew(crewai_service, state.raw_data)

# NEW
from app.services.persistent_agents.field_mapping_persistent import (
    execute_field_mapping
)
result = await execute_field_mapping(
    context=self.context,
    service_registry=self.service_registry,
    raw_data=state.raw_data
)
```

#### Task B2.3: Update collection_readiness_service.py
**Agent**: `python-crewai-fastapi-expert`

```python
# File: backend/app/services/collection_readiness_service.py

# Find all crew imports and replace with persistent agent calls
# OLD
from app.services.crewai_flows.crews.field_mapping_crew import create_field_mapping_crew

# NEW
from app.services.persistent_agents.field_mapping_persistent import get_persistent_field_mapper
```

#### Task B2.4: Update other importers (batched)
**Agent**: `python-crewai-fastapi-expert`

Find remaining importers:
```bash
grep -r "from app.services.crewai_flows.crews" --include="*.py" \
    backend/app/services backend/app/api \
    | grep -v "backend/app/services/crewai_flows/crews" \
    | cut -d: -f1 | sort -u
```

Update each file to use persistent wrappers.

**Verification**:
```bash
# Should return 0
grep -r "from app.services.crewai_flows.crews.field_mapping_crew" \
    --include="*.py" backend/app/services backend/app/api | wc -l
```

---

### Phase B3: crew_class Migration (Week 3)

**Tasks MUST run SEQUENTIALLY** (dependencies between them)

#### Task B3.1: Add initialize_flow() to ChildFlowServices
**Agent**: `python-crewai-fastapi-expert`

```python
# File: backend/app/services/child_flow_services/base.py

class BaseChildFlowService:
    """Base class for child flow services"""

    async def initialize_flow(
        self,
        flow_id: str,
        initial_state: Dict[str, Any],
        configuration: Dict[str, Any],
        context: RequestContext
    ) -> Dict[str, Any]:
        """
        Initialize a new flow instance.

        Replaces crew_class instantiation in MFO.
        """
        # Default implementation
        return {
            "flow_id": flow_id,
            "status": "initialized",
            "configuration": configuration,
            "state": initial_state
        }
```

```python
# File: backend/app/services/child_flow_services/discovery.py

class DiscoveryChildFlowService(BaseChildFlowService):
    """Discovery flow child service"""

    async def initialize_flow(
        self,
        flow_id: str,
        initial_state: Dict[str, Any],
        configuration: Dict[str, Any],
        context: RequestContext
    ) -> Dict[str, Any]:
        """Initialize discovery flow"""
        # Discovery-specific initialization
        logger.info(f"Initializing discovery flow {flow_id}")

        # Create child flow record
        child_flow = await self.repository.create_discovery_flow(
            flow_id=flow_id,
            configuration=configuration,
            initial_state=initial_state
        )

        return {
            "flow_id": flow_id,
            "child_flow_id": child_flow.id,
            "status": "initialized",
            "message": "Discovery flow initialized successfully"
        }
```

#### Task B3.2: Update flow_creation_operations.py
**Agent**: `python-crewai-fastapi-expert`
**Depends on**: Task B3.1

```python
# File: backend/app/services/master_flow_orchestrator/operations/flow_creation_operations.py

# OLD (lines 348-381)
if can_instantiate:
    try:
        flow_instance = flow_config.crew_class(
            flow_id=flow_id,
            initial_state=flow_data.get("flow_persistence_data", {}),
            configuration=flow_data.get("flow_configuration", {}),
            context=self.context,
        )
        if hasattr(flow_instance, "initialize"):
            initialization_result = await flow_instance.initialize()
    except TypeError as e:
        logger.warning(f"Crew class instantiation fallback for {flow_type}: {e}")
        flow_instance = {...}

# NEW
if flow_config.child_flow_service:
    # Use child service for initialization (modern pattern)
    initialization_result = await flow_config.child_flow_service.initialize_flow(
        flow_id=flow_id,
        initial_state=flow_data.get("flow_persistence_data", {}),
        configuration=flow_data.get("flow_configuration", {}),
        context=self.context
    )
    flow_instance = initialization_result
    logger.info(f"✅ Flow initialized via child_flow_service for {flow_id}")
elif flow_config.crew_class:
    # Deprecated: crew_class fallback (remove after migration)
    logger.warning(f"⚠️ Using deprecated crew_class for {flow_type} - migrate to child_flow_service")
    try:
        flow_instance = flow_config.crew_class(...)
    except TypeError as e:
        logger.error(f"crew_class instantiation failed for {flow_type}: {e}")
        flow_instance = {...}
else:
    raise ValueError(f"Flow type {flow_type} must have child_flow_service configured")
```

#### Task B3.3: Update flow_type_registry.py
**Agent**: `python-crewai-fastapi-expert`
**Depends on**: Task B3.2

```python
# File: backend/app/services/flow_type_registry.py

@dataclass
class FlowTypeConfig:
    """Flow type configuration"""
    name: str
    display_name: str
    description: str
    version: str
    phases: List[PhaseConfig]
    capabilities: FlowCapabilities
    metadata: Dict[str, Any]

    # NEW: Required field
    child_flow_service: Any  # Required for execution and initialization

    # DEPRECATED: Optional for backward compatibility only
    crew_class: Optional[Any] = None  # Deprecated - use child_flow_service

    def __post_init__(self):
        """Validate required fields"""
        if not self.child_flow_service:
            if self.crew_class:
                logger.warning(
                    f"⚠️ Flow {self.name} uses deprecated crew_class. "
                    f"Migrate to child_flow_service."
                )
            else:
                raise ValueError(
                    f"Flow {self.name} must have child_flow_service configured"
                )
```

#### Task B3.4: Remove crew_class from configs
**Agent**: `python-crewai-fastapi-expert`
**Depends on**: Task B3.3

```python
# File: backend/app/services/flow_configs/discovery_flow_config.py

def get_discovery_flow_config() -> FlowTypeConfig:
    discovery_config = FlowTypeConfig(
        name="discovery",
        # ... other fields ...

        # REMOVED: crew_class=UnifiedDiscoveryFlow,  # Deprecated per ADR-025
        child_flow_service=DiscoveryChildFlowService,  # NEW: Handles both init and exec

        tags=["discovery", "data_import", "inventory"],
    )
    return discovery_config
```

```python
# File: backend/app/services/sixr_engine_modular.py

# Replace any crew_class usage with child_flow_service calls
# (Specific changes depend on current implementation)
```

**Verification**:
```bash
# Should return 0
grep -r "crew_class\s*=" --include="*.py" backend/app/services/flow_configs/ | wc -l
```

---

### Phase B4: Testing & Cleanup (Week 4)

**Tasks can run in PARALLEL**

#### Task B4.1: Run Full Test Suite
**Agent**: `qa-playwright-tester` (for E2E), `sre-precommit-enforcer` (for unit)

```bash
# Unit tests
cd backend
pytest tests/unit/ -v --tb=short

# Integration tests
pytest tests/integration/ -v --tb=short

# E2E tests (Docker)
npm run test:e2e:journey
```

#### Task B4.2: Verify No Crew() in Production Paths
**Agent**: `sre-precommit-enforcer`

```bash
# Should return 0 or only test files
grep -r "Crew\(" --include="*.py" backend/app/services/ backend/app/api/ | grep -v test | wc -l

# Check for crew imports
grep -r "from crewai import Crew" --include="*.py" backend/app/ | grep -v test | wc -l
```

#### Task B4.3: Performance Validation
**Agent**: `general-purpose`

```bash
# Compare response times before/after migration
docker logs migration_backend 2>&1 | grep "duration\|timing" | tail -100

# Check for persistent agent usage
docker logs migration_backend 2>&1 | grep "TenantScopedAgentPool" | wc -l
```

#### Task B4.4: Documentation Updates
**Agent**: `docs-curator`

Update these docs:
1. ADR-025 - Mark crew_class as fully deprecated
2. architectural_patterns.md - Update agent initialization patterns
3. coding-agent-guide.md - Add persistent agent examples
4. This cleanup plan - Mark as COMPLETED

---

## 🤖 CC Agent Assignment Matrix

| Task | Agent Type | Duration | Dependencies | Can Parallelize |
|------|------------|----------|--------------|-----------------|
| **Workstream A (Archive)** |
| A1: Archive endpoints | `general-purpose` | 1h | None | Yes |
| A2: Archive crews | `general-purpose` | 1h | None | Yes |
| A3: Move example agents | `general-purpose` | 30min | None | Yes |
| A4: Pre-commit guards | `sre-precommit-enforcer` | 1h | None | Yes |
| **Phase B1 (Wrappers)** |
| B1.1: Field mapping wrapper | `python-crewai-fastapi-expert` | 2h | None | Yes |
| B1.2: Dependency wrapper | `python-crewai-fastapi-expert` | 2h | None | Yes |
| B1.3: Tech debt wrapper | `python-crewai-fastapi-expert` | 2h | None | Yes |
| B1.4: Data import wrapper | `python-crewai-fastapi-expert` | 2h | None | Yes |
| **Phase B2 (Update Importers)** |
| B2.1: Update crew_manager | `python-crewai-fastapi-expert` | 2h | B1.* | Yes |
| B2.2: Update phase executor | `python-crewai-fastapi-expert` | 2h | B1.* | Yes |
| B2.3: Update readiness service | `python-crewai-fastapi-expert` | 2h | B1.* | Yes |
| B2.4: Update other importers | `python-crewai-fastapi-expert` | 4h | B1.* | Yes |
| **Phase B3 (crew_class Migration)** |
| B3.1: Add initialize_flow() | `python-crewai-fastapi-expert` | 4h | None | No (sequential) |
| B3.2: Update flow_creation | `python-crewai-fastapi-expert` | 4h | B3.1 | No (sequential) |
| B3.3: Update registry | `python-crewai-fastapi-expert` | 2h | B3.2 | No (sequential) |
| B3.4: Remove crew_class | `python-crewai-fastapi-expert` | 2h | B3.3 | No (sequential) |
| **Phase B4 (Testing)** |
| B4.1: Run tests | `sre-precommit-enforcer` | 2h | B3.* | Yes |
| B4.2: Verify no Crew() | `sre-precommit-enforcer` | 30min | B3.* | Yes |
| B4.3: Performance check | `general-purpose` | 1h | B3.* | Yes |
| B4.4: Update docs | `docs-curator` | 2h | B3.* | Yes |

---

## 🎯 Parallel Execution Strategy

### Week 1: Kickoff (Parallel)
```bash
# Launch all Workstream A tasks in parallel
cc-agent general-purpose "Execute Task A1: Archive endpoints"
cc-agent general-purpose "Execute Task A2: Archive crews"
cc-agent general-purpose "Execute Task A3: Move example agents"
cc-agent sre-precommit-enforcer "Execute Task A4: Add pre-commit guards"

# Launch all Phase B1 tasks in parallel
cc-agent python-crewai-fastapi-expert "Execute Task B1.1: Create field_mapping_persistent.py"
cc-agent python-crewai-fastapi-expert "Execute Task B1.2: Create dependency_analysis_persistent.py"
cc-agent python-crewai-fastapi-expert "Execute Task B1.3: Create technical_debt_persistent.py"
cc-agent python-crewai-fastapi-expert "Execute Task B1.4: Create data_import_validation_persistent.py"
```

### Week 2: Import Updates (Parallel after B1 completes)
```bash
# Wait for B1.* completion, then launch B2 in parallel
cc-agent python-crewai-fastapi-expert "Execute Task B2.1: Update unified_flow_crew_manager.py"
cc-agent python-crewai-fastapi-expert "Execute Task B2.2: Update field_mapping.py executor"
cc-agent python-crewai-fastapi-expert "Execute Task B2.3: Update collection_readiness_service.py"
cc-agent python-crewai-fastapi-expert "Execute Task B2.4: Update remaining importers"
```

### Week 3: crew_class Migration (Sequential)
```bash
# MUST run sequentially due to dependencies
cc-agent python-crewai-fastapi-expert "Execute Task B3.1: Add initialize_flow()" && \
cc-agent python-crewai-fastapi-expert "Execute Task B3.2: Update flow_creation_operations.py" && \
cc-agent python-crewai-fastapi-expert "Execute Task B3.3: Update flow_type_registry.py" && \
cc-agent python-crewai-fastapi-expert "Execute Task B3.4: Remove crew_class from configs"
```

### Week 4: Validation (Parallel)
```bash
# Launch all B4 tasks in parallel
cc-agent sre-precommit-enforcer "Execute Task B4.1: Run full test suite"
cc-agent sre-precommit-enforcer "Execute Task B4.2: Verify no Crew() in production"
cc-agent general-purpose "Execute Task B4.3: Performance validation"
cc-agent docs-curator "Execute Task B4.4: Update documentation"
```

---

## ✅ Acceptance Criteria

### Workstream A (Archive)
- [ ] 6 unmounted endpoints moved to `archive/2025-10/endpoints_legacy/`
- [ ] 6 legacy crews moved to `archive/2025-10/crews_legacy/`
- [ ] 9 example agents moved to `docs/examples/agent_patterns/`
- [ ] READMEs created in each archive directory
- [ ] Pre-commit guard script created and enabled
- [ ] No imports from archived files remain in active code
- [ ] All tests pass after archival

### Workstream B (Migrate)
- [ ] 4 persistent agent wrappers created in `services/persistent_agents/`
- [ ] All importers updated to use persistent wrappers
- [ ] `initialize_flow()` method added to all ChildFlowServices
- [ ] `flow_creation_operations.py` uses `child_flow_service.initialize_flow()`
- [ ] `crew_class` removed from all flow configs
- [ ] 0 direct `Crew()` instantiations in production code
- [ ] 0 imports from `app.services.crewai_flows.crews.*` outside crews/ directory
- [ ] All tests pass (unit, integration, E2E)
- [ ] Performance maintained or improved
- [ ] Documentation updated

### Overall Success
- [ ] Dependency graph shows 0 circular dependencies
- [ ] Pre-commit guards prevent new violations
- [ ] Docker logs show only `TenantScopedAgentPool` usage (no Crew())
- [ ] All flows initialize and execute via `child_flow_service`
- [ ] No production incidents during or after migration

---

## 🛡️ Rollback Strategy

If any phase fails:

```bash
# 1. Identify the failed task
echo "Failed at: Task B2.3"

# 2. Git revert the changes
git log --oneline --since="1 week ago" | grep "Task B2.3"
git revert <commit-hash>

# 3. Rebuild containers
docker-compose -f config/docker/docker-compose.yml build --no-cache backend

# 4. Restart services
docker-compose -f config/docker/docker-compose.yml up -d

# 5. Verify rollback
docker logs migration_backend --tail=100
pytest tests/integration/ -v
```

---

## 📊 Progress Tracking

Create a tracking issue in GitHub with this checklist:

```markdown
## Backend Cleanup & Migration Progress

### Workstream A: Archive
- [ ] Task A1: Archive endpoints (Agent: @general-purpose)
- [ ] Task A2: Archive crews (Agent: @general-purpose)
- [ ] Task A3: Move example agents (Agent: @general-purpose)
- [ ] Task A4: Pre-commit guards (Agent: @sre-precommit-enforcer)

### Phase B1: Wrappers (Week 1)
- [ ] Task B1.1: Field mapping wrapper (Agent: @python-crewai-fastapi-expert)
- [ ] Task B1.2: Dependency wrapper (Agent: @python-crewai-fastapi-expert)
- [ ] Task B1.3: Tech debt wrapper (Agent: @python-crewai-fastapi-expert)
- [ ] Task B1.4: Data import wrapper (Agent: @python-crewai-fastapi-expert)

### Phase B2: Update Importers (Week 2)
- [ ] Task B2.1: Update crew_manager (Agent: @python-crewai-fastapi-expert)
- [ ] Task B2.2: Update phase executor (Agent: @python-crewai-fastapi-expert)
- [ ] Task B2.3: Update readiness service (Agent: @python-crewai-fastapi-expert)
- [ ] Task B2.4: Update other importers (Agent: @python-crewai-fastapi-expert)

### Phase B3: crew_class Migration (Week 3) - SEQUENTIAL
- [ ] Task B3.1: Add initialize_flow() (Agent: @python-crewai-fastapi-expert)
- [ ] Task B3.2: Update flow_creation (Agent: @python-crewai-fastapi-expert)
- [ ] Task B3.3: Update registry (Agent: @python-crewai-fastapi-expert)
- [ ] Task B3.4: Remove crew_class (Agent: @python-crewai-fastapi-expert)

### Phase B4: Validation (Week 4)
- [ ] Task B4.1: Run tests (Agent: @sre-precommit-enforcer)
- [ ] Task B4.2: Verify no Crew() (Agent: @sre-precommit-enforcer)
- [ ] Task B4.3: Performance check (Agent: @general-purpose)
- [ ] Task B4.4: Update docs (Agent: @docs-curator)

### Final Checklist
- [ ] All acceptance criteria met
- [ ] No production incidents
- [ ] Documentation updated
- [ ] Migration marked COMPLETE
```

---

**READY FOR PARALLEL EXECUTION**

This plan can be executed by CC agents starting with Workstream A and Phase B1 in parallel.

**Estimated completion**: 4 weeks with 3-4 agents working concurrently.