# Discovery Flow Patterns Master

**Last Updated**: 2025-11-30
**Version**: 1.0
**Consolidates**: 16 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **Three ID Types**: master_flow_id (API), discovery_flow_id (internal), data_import_id (data)
> 2. **Phase Progression**: Must update BOTH discovery_flows AND crewai_flow_state_extensions tables
> 3. **Asset Type Validation**: Only valid enum values (server, database, application, etc.) - NO "device"
> 4. **Data Import Context**: Always lookup data_import_id through discovery_flows, never assume
> 5. **is_valid Filter**: Don't use as hard filter blocking pipeline - process all records

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Common Patterns](#common-patterns)
4. [Bug Fix Patterns](#bug-fix-patterns)
5. [Anti-Patterns](#anti-patterns)
6. [Code Templates](#code-templates)
7. [Troubleshooting](#troubleshooting)
8. [Related Documentation](#related-documentation)
9. [Consolidated Sources](#consolidated-sources)

---

## Overview

### What This Covers
Discovery Flow is the data import and analysis workflow that processes CSV/CMDB imports through phases: data import → field mapping → data cleansing → asset inventory → dependency analysis.

### When to Reference
- Implementing Discovery Flow endpoints
- Debugging phase progression issues
- Fixing asset creation problems
- Resolving ID confusion between master/child flows
- Understanding data pipeline from CSV to assets

### Key Files in Codebase
- `backend/app/api/v1/endpoints/flow_processing.py`
- `backend/app/services/crewai_flows/unified_discovery_flow/`
- `backend/app/services/crewai_flows/handlers/phase_executors/`
- `backend/app/repositories/discovery_flow_repository/`

---

## Architecture Patterns

### Pattern 1: Three ID Types

**Critical Understanding**: Discovery Flow uses three different IDs.

| ID Type | Storage | Used By | Frontend Access |
|---------|---------|---------|-----------------|
| `master_flow_id` | `crewai_flow_state_extensions.flow_id` | MFO, all APIs | ✅ Always use |
| `discovery_flow_id` | `discovery_flows.id` | Internal linkage | ❌ Never expose |
| `data_import_id` | `discovery_flows.data_import_id` | Data operations | Lookup via flow |

**Lookup Chain**:
```
flow_id (from frontend)
    → discovery_flows.master_flow_id
    → discovery_flows.data_import_id
    → raw_import_records.data_import_id
```

**Correct Pattern**:
```python
# Accept flow_id from frontend
if flow_id:
    discovery = await db.execute(
        select(DiscoveryFlow).where(
            DiscoveryFlow.master_flow_id == flow_id
        )
    )
    discovery_flow = discovery.scalar_one_or_none()

    if discovery_flow and discovery_flow.data_import_id:
        data_import = await db.execute(
            select(DataImport).where(
                DataImport.id == discovery_flow.data_import_id
            )
        )
```

**Source**: Consolidated from `discovery_flow_id_coordination_patterns_2025_09`

---

### Pattern 2: Dual Table State Update

**Critical Rule**: Phase transitions must update BOTH tables.

**Tables**:
- `discovery_flows` - Child flow operational status
- `crewai_flow_state_extensions` - Master flow lifecycle

**Correct Pattern**:
```python
# Update BOTH tables for phase transition
# 1. Update child flow
await db.execute(
    update(DiscoveryFlow)
    .where(DiscoveryFlow.master_flow_id == flow_id)
    .values(
        current_phase=next_phase,
        status="running"
    )
)

# 2. Update master flow
await db.execute(
    update(CrewAIFlowStateExtensions)
    .where(CrewAIFlowStateExtensions.flow_id == flow_id)
    .values(
        flow_status="running",
        current_phase=next_phase
    )
)

await db.commit()
```

**Source**: Consolidated from `bug_430_discovery_flow_complete_fix_2025_09`

---

### Pattern 3: Phase Progression Implementation

**Location**: `backend/app/api/v1/endpoints/flow_processing.py`

**Safe Implementation**:
```python
if next_phase and next_phase != current_phase:
    from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
        FlowPhaseManagementCommands
    )

    phase_mgmt = FlowPhaseManagementCommands(
        db,
        context.client_account_id,
        context.engagement_id
    )

    await phase_mgmt.update_phase_completion(
        flow_id=flow_id,
        phase=next_phase,
        completed=False,  # Don't mark complete prematurely!
        data=None,
        agent_insights=None
    )

    logger.info(f"✅ Advanced from {current_phase} to {next_phase}")
```

**Key Safety Points**:
- `completed=False` prevents corrupting progress flags
- Guard condition avoids redundant writes
- Use repository pattern, not raw SQL

**Source**: Consolidated from `discovery_flow_phase_progression_fix_implementation_2025_11`

---

## Common Patterns

### Pattern 4: Valid Asset Types

**AssetType Enum** (`backend/app/models/asset/enums.py`):
- server, database, application, network, load_balancer
- storage, security_group, virtual_machine, container, other

**Invalid Types** (will cause errors):
- ❌ device → Use "server"
- ❌ infrastructure → Use "other"
- ❌ network_device → Use "network"

**Mapping Corrections**:
```python
ASSET_TYPE_NORMALIZATION = {
    "device": "server",
    "service": "application",
    "cache": "database",
    "external": "other",
    "network_device": "network",
    "infrastructure": "other",
}
```

**Source**: Consolidated from `bug_430_discovery_flow_complete_fix_2025_09`

---

### Pattern 5: Data Cleansing Phase Context

**Problem**: Data cleansing fails without data_import_id in phase state.

**Solution**: Retrieve from discovery_flows table:
```python
async def _prepare_phase_input(self, flow_id: str, phase: str) -> Dict:
    # Try to get from existing state
    data_import_id = state.get("data_import_id")

    # Fallback: retrieve from discovery_flows
    if not data_import_id:
        result = await self.db.execute(
            select(DiscoveryFlow.data_import_id).where(
                DiscoveryFlow.master_flow_id == flow_id
            )
        )
        data_import_id = result.scalar_one_or_none()

    return {
        "flow_id": flow_id,
        "data_import_id": data_import_id,
        # ...
    }
```

**Source**: Consolidated from `bug_430_discovery_flow_complete_fix_2025_09`

---

### Pattern 6: Processing All Records (No is_valid Filter)

**Problem**: Records with `is_valid != True` blocked from pipeline.

**Wrong**:
```python
query = (
    select(RawImportRecord)
    .where(RawImportRecord.data_import_id == data_import_id)
    .where(RawImportRecord.is_valid is True)  # Blocks records!
)
```

**Right**:
```python
query = (
    select(RawImportRecord)
    .where(RawImportRecord.data_import_id == data_import_id)
    # No is_valid filter - validation happens during processing
)
```

**Key Learning**: `is_valid` should not block pipeline. Validate during processing, not at query level.

**Source**: Consolidated from `discovery_flow_asset_creation_fix`

---

## Bug Fix Patterns

### Bug: Flow Stuck in "paused" After Field Mapping Approval

**Date Fixed**: September 2025
**Symptoms**: Flow doesn't advance to data_cleansing after approval

**Root Cause**: Only discovery_flows table updated, not crewai_flow_state_extensions.

**Fix**: Update both tables (see Pattern 2).

**Source**: `bug_430_discovery_flow_complete_fix_2025_09`

---

### Bug: Invalid "device" Asset Type

**Date Fixed**: September 2025
**Symptoms**: Assets created with type "device" (not in enum)

**Root Cause**: Multiple mappings creating invalid types.

**Fix**: Normalize all asset types to valid enum values:
```python
if asset_type == "device":
    asset_type = "server"
```

**Source**: `bug_430_discovery_flow_complete_fix_2025_09`

---

### Bug: CSV Records Not Creating Assets

**Date Fixed**: September 2025
**Symptoms**: Only existing assets shown, new uploads ignored

**Root Cause**: `is_valid` filter blocking records.

**Fix**: Remove `is_valid` filter from query (see Pattern 6).

**Source**: `discovery_flow_asset_creation_fix`

---

### Bug: Phase Not Advancing via Continue Button

**Date Fixed**: November 2025
**Symptoms**: current_phase doesn't update when Continue clicked

**Root Cause**: Missing phase update in flow_processing.py branches.

**Fix**: Add phase update in both fast-path and simple-logic branches:
```python
if next_phase and next_phase != current_phase:
    await phase_mgmt.update_phase_completion(flow_id, next_phase, completed=False)
```

**Source**: `discovery_flow_phase_progression_fix_implementation_2025_11`

---

## Anti-Patterns

### Don't: Use discovery_flow_id in API Responses

**Why it's bad**: Internal ID, not stable for frontend.

**Wrong**:
```python
return {"flow_id": str(discovery_flow.id)}  # Internal ID
```

**Right**:
```python
return {"flow_id": str(discovery_flow.master_flow_id)}  # Master ID
```

---

### Don't: Filter by is_valid at Query Level

**Why it's bad**: Blocks valid data from pipeline.

**Wrong**:
```python
.where(RawImportRecord.is_valid is True)
```

**Right**: Validate during processing, not at query.

---

### Don't: Update Only One Table

**Why it's bad**: State inconsistency between master and child.

**Wrong**:
```python
await db.execute(update(DiscoveryFlow)...)  # Only child
```

**Right**:
```python
await db.execute(update(DiscoveryFlow)...)  # Child
await db.execute(update(CrewAIFlowStateExtensions)...)  # Master
```

---

### Don't: Assume IDs Match

**Why it's bad**: flow_id ≠ data_import_id.

**Wrong**:
```python
data_import_id = flow_id  # Never assume!
```

**Right**: Always lookup via discovery_flows table.

---

## Code Templates

### Template 1: Phase Executor with Context

```python
class DataCleansingExecutor(BasePhaseExecutor):
    async def execute(self, flow_id: str, phase_input: Dict) -> PhaseResult:
        # 1. Get data_import_id (with fallback)
        data_import_id = phase_input.get("data_import_id")
        if not data_import_id:
            result = await self.db.execute(
                select(DiscoveryFlow.data_import_id).where(
                    DiscoveryFlow.master_flow_id == flow_id
                )
            )
            data_import_id = result.scalar_one_or_none()

        if not data_import_id:
            return PhaseResult(success=False, error="No data import found")

        # 2. Query records WITHOUT is_valid filter
        records = await self.db.execute(
            select(RawImportRecord).where(
                RawImportRecord.data_import_id == data_import_id
            )
        )

        # 3. Process and validate during iteration
        for record in records.scalars():
            cleansed = self._cleanse_record(record)
            if self._is_valid(cleansed):
                # ... process
                pass

        return PhaseResult(success=True)
```

---

### Template 2: Dual Table Update

```python
async def update_flow_phase(
    db: AsyncSession,
    flow_id: str,
    next_phase: str,
    status: str = "running"
):
    """Update phase in both child and master tables."""
    # Update child flow
    await db.execute(
        update(DiscoveryFlow)
        .where(DiscoveryFlow.master_flow_id == UUID(flow_id))
        .values(
            current_phase=next_phase,
            status=status,
            updated_at=datetime.now(timezone.utc)
        )
    )

    # Update master flow
    await db.execute(
        update(CrewAIFlowStateExtensions)
        .where(CrewAIFlowStateExtensions.flow_id == UUID(flow_id))
        .values(
            current_phase=next_phase,
            flow_status=status,
            updated_at=datetime.now(timezone.utc)
        )
    )

    await db.commit()
    logger.info(f"✅ Updated flow {flow_id} to phase {next_phase}")
```

---

## Troubleshooting

### Issue: Flow stuck at initialization

**Diagnosis**:
```sql
SELECT flow_id, current_phase, status, data_import_id
FROM migration.discovery_flows
WHERE master_flow_id = 'xxx';
```

**Common Causes**:
1. data_import_id is NULL → Check data upload
2. status is "paused" → Resume flow
3. current_phase is NULL → Initialize properly

---

### Issue: Assets not being created

**Diagnosis**:
```sql
-- Check raw records
SELECT COUNT(*) FROM migration.raw_import_records
WHERE data_import_id = 'xxx';

-- Check cleansed data
SELECT COUNT(cleansed_data) FROM migration.raw_import_records
WHERE data_import_id = 'xxx' AND cleansed_data IS NOT NULL;
```

**Common Causes**:
1. is_valid filter blocking → Remove filter
2. Phase not reaching asset_inventory → Check phase progression
3. Invalid asset_type → Check normalization

---

### Issue: Phase not advancing

**Diagnosis**:
```sql
SELECT
  df.current_phase as child_phase,
  cfse.current_phase as master_phase,
  df.status as child_status,
  cfse.flow_status as master_status
FROM migration.discovery_flows df
JOIN migration.crewai_flow_state_extensions cfse
  ON df.master_flow_id = cfse.flow_id
WHERE df.master_flow_id = 'xxx';
```

**Common Cause**: Only one table updated. Ensure dual-table update.

---

## Related Documentation

| Resource | Location | Purpose |
|----------|----------|---------|
| MFO Pattern | `.serena/memories/mfo_two_table_flow_id_pattern_critical.md` | Two-table architecture |
| Collection Flow | `.serena/memories/collection_flow_patterns_master.md` | Similar flow patterns |
| ADR-012 | `/docs/adr/012-flow-status-phase-separation.md` | Status vs phase |

---

## Consolidated Sources

| Original Memory | Date | Key Contribution |
|-----------------|------|------------------|
| `discovery_flow_phase_progression_fix_implementation_2025_11` | 2025-11 | Safe phase update |
| `discovery_flow_id_coordination_patterns_2025_09` | 2025-09 | Three ID types |
| `discovery_flow_debugging_patterns_2025_09_18` | 2025-09 | Debug patterns |
| `discovery_flow_asset_creation_fix` | 2025-09 | is_valid filter |
| `bug_430_discovery_flow_complete_fix_2025_09` | 2025-09 | Comprehensive fix |
| `discovery_flow_data_display_issues_2025_09` | 2025-09 | Data display |
| `discovery_flow_initialization_fixes_2025_09` | 2025-09 | Initialization |
| `discovery_flow_phase_execution_gap_2025_09` | 2025-09 | Phase execution |
| `discovery_flow_phase_progression_bug_2025_11` | 2025-11 | Bug analysis |
| `discovery_flow_phase_progression_fix_2025_01` | 2025-01 | Phase fix |
| `discovery_flow_unmapped_fields_handling_fix` | 2025-09 | Unmapped fields |
| `e2e_testing_discovery_flow_methodology` | 2025-09 | Testing methodology |
| `network_discovery_integration_analysis_2025_10` | 2025-10 | Network integration |
| `persistent_agent_migration_discovery_flow` | 2025-10 | Agent migration |

**Archive Location**: `.serena/archive/discovery/`

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-30 | Initial consolidation of 16 memories | Claude Code |

---

## Search Keywords

discovery, flow, phase_progression, asset_creation, data_import, field_mapping, data_cleansing, asset_inventory, master_flow_id, dual_table
