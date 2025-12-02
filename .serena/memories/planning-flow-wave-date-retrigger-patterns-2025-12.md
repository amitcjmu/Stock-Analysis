# Planning Flow Wave Date & Retrigger Patterns - December 2025

## Session Context
PR #1186 - Fix wave start dates and add retrigger capability (Issue #865)

## Key Patterns

### 1. Wave Start Date Configuration
**Problem**: Wave planning used `datetime.now()` instead of user-provided migration start date
**Solution**: Pass `migration_start_date` through config chain

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

### 2. Retrigger Endpoint Pattern
**Problem**: Users needed to regenerate wave plans with updated configuration
**Solution**: POST endpoint that updates config and re-executes wave planning

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

    # Launch background task
    schedule_wave_planning_task(planning_flow_id, context, updated_config)
```

### 3. Shared Utils Modularization
**Problem**: Duplicate UUID parsing code across initialize.py and retrigger.py
**Solution**: Extract to shared_utils.py module

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
    planning_flow_id: Optional[str] = None,
) -> tuple[UUID, ...]:
    """Parse tenant UUIDs with consistent error handling."""
    client_uuid = parse_uuid(client_account_id, "client_account_id")
    engagement_uuid = parse_uuid(engagement_id, "engagement_id")
    if planning_flow_id:
        return parse_uuid(planning_flow_id, "planning_flow_id"), client_uuid, engagement_uuid
    return client_uuid, engagement_uuid

def schedule_wave_planning_task(
    planning_flow_id: UUID,
    context: RequestContext,
    planning_config: Dict[str, Any],
) -> None:
    """Schedule background wave planning with proper lifecycle management."""
    asyncio.create_task(_run_wave_planning_background(...))
```

### 4. Flake8 C901 Complexity Reduction
**Problem**: Pre-commit blocking on C901 complexity > 10
**Solution**: Extract helper functions to reduce cyclomatic complexity

```python
# ❌ WRONG - All logic in endpoint (complexity 16)
@router.post("/initialize")
async def initialize_planning_flow(...):
    try:
        try:
            client_uuid = UUID(client_account_id) if isinstance(...) else ...
        except ValueError:
            raise HTTPException(...)
        try:
            app_uuids = [UUID(app_id) for app_id in ...]
        except ValueError:
            raise HTTPException(...)
        # ... more nested logic

# ✅ CORRECT - Extract to helpers (complexity < 10)
def _parse_tenant_uuids(...) -> tuple[UUID, UUID]:
    """Parse and validate tenant UUIDs from context."""
    ...  # Raises HTTPException on error

def _parse_application_uuids(application_ids: List[str]) -> List[UUID]:
    """Parse and validate application UUIDs."""
    ...  # Raises HTTPException on error

@router.post("/initialize")
async def initialize_planning_flow(...):
    client_uuid, engagement_uuid = _parse_tenant_uuids(...)
    app_uuids = _parse_application_uuids(request.selected_application_ids)
    # ... cleaner main flow
```

### 5. File Length Modularization (400 line limit)
**Problem**: update.py exceeded 400 line limit after adding retrigger
**Solution**: Split into separate modules with shared imports

```
# Before: update.py (520 lines) ❌
backend/app/api/v1/master_flows/planning/
├── update.py  # Contains both update and retrigger

# After: Modularized ✅
backend/app/api/v1/master_flows/planning/
├── __init__.py      # Include all routers
├── update.py        # 321 lines - update_wave_plan only
├── retrigger.py     # 250 lines - retrigger endpoint
└── shared_utils.py  # Common UUID parsing functions

# __init__.py updates:
from .update import router as update_router
from .retrigger import router as retrigger_router
router.include_router(update_router)
router.include_router(retrigger_router)
```

## Testing Patterns

### Playwright API Testing for Wave Dates
```typescript
// Verify wave dates use migration_start_date
const response = await page.request.post('/api/v1/master-flows/planning/retrigger/...',{
    headers: {
        'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
        'X-Engagement-ID': '22222222-2222-2222-2222-222222222222'
    },
    data: { migration_start_date: "2025-03-01" }
});

// Poll status until complete
const status = await page.request.get('/api/v1/master-flows/planning/status/...');
const data = status.json();
// Verify wave dates start from 2025-03-01, not current date
expect(data.wave_plan_data.waves[0].start_date).toContain('2025-03-01');
```

## Files Modified
- `backend/app/api/v1/master_flows/planning/initialize.py` - Add migration_start_date field
- `backend/app/api/v1/master_flows/planning/update.py` - Slim down, remove retrigger
- `backend/app/api/v1/master_flows/planning/retrigger.py` - New endpoint module
- `backend/app/api/v1/master_flows/planning/shared_utils.py` - UUID parsing utilities
- `backend/app/services/planning/wave_planning_service/wave_logic.py` - Use config start date
- `backend/app/services/crewai_flows/tasks/planning_tasks.py` - Include start date in prompt
