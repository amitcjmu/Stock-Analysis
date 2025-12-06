# Planning Flow Patterns Master

**Last Updated**: 2025-12-05
**Version**: 1.0
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **Wave Start Date**: Pass `migration_start_date` through config chain, not `datetime.now()`
> 2. **Retrigger Pattern**: Merge existing config with new values, reset phase status
> 3. **Async Execution**: Use `asyncio.create_task()` for background wave planning
> 4. **C901 Complexity**: Extract UUID parsing helpers to reduce cyclomatic complexity
> 5. **File Length**: Split endpoints >400 lines into separate modules with shared_utils

---

## Table of Contents

1. [Overview](#overview)
2. [Wave Configuration Patterns](#wave-configuration-patterns)
3. [Endpoint Patterns](#endpoint-patterns)
4. [Modularization Patterns](#modularization-patterns)
5. [Anti-Patterns](#anti-patterns)
6. [Code Templates](#code-templates)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What This Covers
Planning Flow handles wave planning for migration execution. Organizes applications into waves based on dependencies, 6R strategies, and resource capacity.

### When to Reference
- Implementing wave planning endpoints
- Adding retrigger/reconfigure functionality
- Fixing wave date calculation issues
- Modularizing planning flow files

### Key Files
- `backend/app/api/v1/master_flows/planning/initialize.py`
- `backend/app/api/v1/master_flows/planning/retrigger.py`
- `backend/app/api/v1/master_flows/planning/shared_utils.py`
- `backend/app/services/planning/wave_planning_service/`

---

## Wave Configuration Patterns

### Pattern 1: Migration Start Date Propagation

**Problem**: Wave planning used `datetime.now()` instead of user-provided migration start date.

**Solution**: Pass `migration_start_date` through config chain:

```python
# Request model with migration_start_date
class InitializePlanningRequest(BaseModel):
    selected_application_ids: List[str] = Field(...)
    migration_start_date: Optional[str] = Field(
        default=None,
        description="Migration start date in ISO format (YYYY-MM-DD).",
    )
    planning_config: Optional[Dict[str, Any]] = Field(default_factory=dict)

# Endpoint passes start date into config
planning_config = request.planning_config or {}
if request.migration_start_date is not None:
    planning_config["migration_start_date"] = request.migration_start_date

# Wave logic uses config start date
migration_start_date_str = config.get("migration_start_date")
if migration_start_date_str:
    start_date = datetime.fromisoformat(migration_start_date_str)
else:
    start_date = datetime.now(timezone.utc)  # Fallback only
```

### Pattern 2: Async Background Execution

**Problem**: Wave planning takes 2+ minutes, causing frontend timeout.

**Solution**: Use `asyncio.create_task()` for background execution:

```python
async def run_wave_planning_background():
    """Background task to execute wave planning asynchronously."""
    from app.core.database import AsyncSessionLocal

    bg_db = None
    try:
        bg_db = AsyncSessionLocal()
        result = await execute_wave_planning_for_flow(
            db=bg_db,
            context=context,
            planning_flow_id=planning_flow_id,
            planning_config=planning_config,
        )
        logger.info(f"[Background] Wave planning completed: {planning_flow_id}")
    except Exception as e:
        logger.error(f"[Background] Wave planning error: {e}")
    finally:
        if bg_db:
            await bg_db.close()

# Launch background task (non-blocking)
asyncio.create_task(run_wave_planning_background())

# Return immediately
return {"status": "in_progress", "message": "Poll status endpoint for completion"}
```

### Pattern 3: Application Data for Agent

**Problem**: Agent received only summary counts, made up "Application 1", "Application 2" names.

**Solution**: Pass actual application list with IDs, names, and 6R strategies:

```python
def _format_applications_for_agent(applications: List[Dict[str, Any]]) -> str:
    """Ultra-compact format: id|name|strategy|complexity|criticality"""
    lines = []
    use_short_id = len(applications) > 20  # Shorten UUIDs for large lists

    for app in applications:
        app_id = app.get("id")
        if not app_id:
            logger.warning(f"Skipping app with missing ID: {app.get('name', 'N/A')}")
            continue

        display_id = app_id[:8] if use_short_id else app_id
        name = app.get("name", f"App_{app_id[:8]}")[:30]
        strategy = (app.get("migration_strategy", "") or app.get("six_r_strategy", "") or "rehost")[:10]

        lines.append(f"{display_id}|{name}|{strategy}")

    return "Format: id|name|strategy\n" + "\n".join(lines)
```

---

## Endpoint Patterns

### Pattern 4: Retrigger Endpoint

**Problem**: Users needed to regenerate wave plans with updated configuration.

**Solution**: POST endpoint that merges config and re-executes:

```python
class RetriggerWavePlanRequest(BaseModel):
    migration_start_date: Optional[str] = Field(default=None)
    max_apps_per_wave: Optional[int] = Field(default=None)
    wave_duration_limit_days: Optional[int] = Field(default=None)

@router.post("/retrigger/{planning_flow_id}")
async def retrigger_wave_planning(...):
    # Merge existing config with new values
    existing_config = planning_flow.planning_config or {}
    updated_config = existing_config.copy()

    if request.migration_start_date is not None:
        updated_config["migration_start_date"] = request.migration_start_date
    if request.max_apps_per_wave is not None:
        updated_config["max_apps_per_wave"] = request.max_apps_per_wave

    # Reset phase status and re-execute
    await repo.update_phase_status(current_phase="wave_planning", phase_status="in_progress")
    schedule_wave_planning_task(planning_flow_id, context, updated_config)
```

---

## Modularization Patterns

### Pattern 5: Shared Utils Module

**Problem**: Duplicate UUID parsing code across initialize.py and retrigger.py.

**Solution**: Extract to shared_utils.py:

```python
# shared_utils.py
def parse_uuid(value: str, field_name: str = "UUID") -> UUID:
    """Parse and validate a single UUID."""
    try:
        return UUID(value) if isinstance(value, str) else value
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}: {e}")

def parse_tenant_uuids(
    client_account_id: str,
    engagement_id: str,
) -> tuple[UUID, UUID]:
    """Parse tenant UUIDs with consistent error handling."""
    return (
        parse_uuid(client_account_id, "client_account_id"),
        parse_uuid(engagement_id, "engagement_id"),
    )
```

### Pattern 6: C901 Complexity Reduction

**Problem**: Pre-commit blocking on C901 complexity > 10.

**Solution**: Extract helper functions:

```python
# Before: complexity 16
@router.post("/initialize")
async def initialize_planning_flow(...):
    try:
        try:
            client_uuid = UUID(client_account_id) if isinstance(...) else ...
        except ValueError:
            raise HTTPException(...)
        # ... more nested logic

# After: complexity < 10
def _parse_tenant_uuids(...) -> tuple[UUID, UUID]:
    """Raises HTTPException on error"""
    ...

@router.post("/initialize")
async def initialize_planning_flow(...):
    client_uuid, engagement_uuid = _parse_tenant_uuids(...)
    # ... cleaner main flow
```

---

## Anti-Patterns

### Don't: Use datetime.now() for Wave Dates

```python
# WRONG
start_date = datetime.now()

# CORRECT
start_date = datetime.fromisoformat(config.get("migration_start_date")) if config.get("migration_start_date") else datetime.now(timezone.utc)
```

### Don't: Block on Long-Running Operations

```python
# WRONG - Causes timeout
result = await execute_wave_planning_for_flow(...)
return result

# CORRECT - Background execution
asyncio.create_task(run_wave_planning_background())
return {"status": "in_progress"}
```

### Don't: Send Summary-Only to Agent

```python
# WRONG - Agent makes up names
app_summary = {"total_applications": 30, "complexity_distribution": {...}}

# CORRECT - Include actual app data
app_list = _format_applications_for_agent(applications)
```

---

## Code Templates

### Template 1: Planning Flow Initialization

```python
@router.post("/initialize")
async def initialize_planning_flow(
    request: InitializePlanningRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    # Parse tenant UUIDs
    client_uuid, engagement_uuid = parse_tenant_uuids(
        context.client_account_id, context.engagement_id
    )

    # Generate flow IDs
    master_flow_id = uuid4()
    planning_flow_id = uuid4()

    # Prepare config with start date
    planning_config = request.planning_config or {}
    if request.migration_start_date:
        planning_config["migration_start_date"] = request.migration_start_date

    # Create flows atomically
    async with db.begin():
        # Create master flow
        # Create child planning flow
        pass

    # Launch background wave planning
    asyncio.create_task(run_wave_planning_background())

    return {"status": "in_progress", "planning_flow_id": str(planning_flow_id)}
```

---

## Troubleshooting

### Issue: Wave dates start from today instead of configured date

**Cause**: `migration_start_date` not propagated through config chain.

**Fix**: Ensure date flows through: Request → Config → Wave Logic.

### Issue: "Application 1", "Application 2" in wave plan

**Cause**: Agent prompt only included summary counts, not actual app data.

**Fix**: Use `_format_applications_for_agent()` to include real IDs and names.

### Issue: Frontend timeout on wave planning

**Cause**: Synchronous execution of 2+ minute operation.

**Fix**: Use `asyncio.create_task()` for background execution, return immediately.

---

## Consolidated Sources

| Original Memory | Date | Key Contribution |
|-----------------|------|------------------|
| `planning-flow-wave-date-retrigger-patterns-2025-12` | 2025-12 | Wave dates, retrigger, modularization |

---

## Search Keywords

planning, wave, migration_start_date, retrigger, async, background, C901, complexity, shared_utils
