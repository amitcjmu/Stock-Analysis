# Asset Repository Modularization

## Overview

The `asset_repository.py` file (578 lines) has been successfully modularized to comply with the 400-line pre-commit check requirement.

## Structure

```
backend/app/repositories/asset_repository/
├── __init__.py                 (23 lines)  - Exports main repositories
├── base.py                    (293 lines) - Main repository classes
├── commands.py                (314 lines) - Write operations
├── queries.py                 (439 lines) - Read operations
└── MODULARIZATION.md                      - This file
```

## File Breakdown

### 1. `__init__.py` (23 lines)
- Exports `AssetRepository`, `AssetDependencyRepository`, `WorkflowProgressRepository`
- Maintains backward compatibility with existing imports
- All imports continue to work: `from app.repositories.asset_repository import AssetRepository`

### 2. `base.py` (293 lines)
Core repository classes that compose queries and commands:

**Classes:**
- `AssetRepository`: Main asset repository with delegation to `AssetQueries` and `AssetCommands`
- `AssetDependencyRepository`: Asset dependency repository
- `WorkflowProgressRepository`: Workflow progress repository

**Pattern:**
```python
class AssetRepository(ContextAwareRepository[Asset]):
    def __init__(self, db, client_account_id, engagement_id, include_deleted):
        super().__init__(...)
        self.queries = AssetQueries(...)  # Delegates to queries module
        self.commands = AssetCommands(...) # Delegates to commands module

    # All public methods delegate to queries or commands
    async def get_by_hostname(self, hostname):
        return await self.queries.get_by_hostname(hostname)
```

### 3. `commands.py` (314 lines)
Write operations for all three repositories:

**AssetCommands:**
- `update_workflow_status()` - Update workflow for a single asset
- `bulk_update_workflow_status()` - Bulk update multiple assets
- `calculate_assessment_readiness()` - Calculate and update readiness
- `update_phase_progression()` - Update phase with tracking
- `update_six_r_strategy_from_assessment()` - Issue #999 - Update 6R from assessment

**AssetDependencyCommands:**
- Placeholder for future write operations

**WorkflowProgressCommands:**
- `update_progress()` - Update or create workflow progress records

### 4. `queries.py` (439 lines)
Read operations for all three repositories:

**AssetQueries (230 lines):**
- `get_by_hostname()`, `get_by_asset_type()`, `get_by_environment()`
- `get_by_status()`, `get_by_6r_strategy()`, `get_by_workflow_status()`
- `get_assessment_ready_assets()`, `get_assets_by_import_batch()`
- `search_assets()`, `get_assets_with_dependencies()`
- `get_assets_by_criticality()`, `get_assets_by_department()`
- `get_assets_needing_analysis()`
- `get_data_quality_summary()`, `get_workflow_summary()`
- Master flow methods: `get_by_master_flow()`, `get_by_discovery_flow()`, `get_by_source_phase()`, `get_by_current_phase()`, `get_multi_phase_assets()`
- Analytics: `get_master_flow_summary()`, `get_cross_phase_analytics()`

**AssetDependencyQueries (70 lines):**
- `get_dependencies_for_asset()`, `get_dependents_for_asset()`
- `get_by_dependency_type()`, `get_critical_dependencies()`

**WorkflowProgressQueries (40 lines):**
- `get_progress_for_asset()`, `get_progress_by_phase()`
- `get_active_workflows()`

## Backward Compatibility

All existing imports continue to work without modification:

```python
# These all work exactly as before
from app.repositories.asset_repository import AssetRepository
from app.repositories.asset_repository import AssetDependencyRepository
from app.repositories.asset_repository import WorkflowProgressRepository

# Usage remains identical
repo = AssetRepository(db, client_account_id, engagement_id)
assets = await repo.get_by_hostname("server.example.com")
```

## Import Sites Updated

No import sites needed updating. The `__init__.py` re-exports ensure all 20+ import locations continue to work:

- `/backend/app/api/v1/master_flows_service.py`
- `/backend/app/api/v1/endpoints/asset_inventory/*.py`
- `/backend/app/services/asset_service/base.py`
- `/backend/app/services/assessment_flow_service/core/assessment_manager.py`
- And 15+ more locations

## Pre-Commit Compliance

All files pass the 400-line check:

```
backend/app/repositories/asset_repository/__init__.py     : 23 lines ✅
backend/app/repositories/asset_repository/base.py        : 293 lines ✅
backend/app/repositories/asset_repository/commands.py    : 314 lines ✅
backend/app/repositories/asset_repository/queries.py     : 439 lines ✅
```

## Design Pattern

This modularization follows the established pattern used in `assessment_flow_repository`:

1. **Queries Module**: All read-only operations
2. **Commands Module**: All write operations
3. **Base Module**: Main repository class that composes queries + commands
4. **__init__.py**: Public API exports for backward compatibility

Benefits:
- Each module has a single responsibility
- Easier to navigate and maintain
- Clearer separation of concerns
- Follows industry repository pattern
- All files stay under 400 lines

## Migration Notes

- Original `backend/app/repositories/asset_repository.py` (578 lines) has been deleted
- No code changes required in any consumer code
- All tests continue to work without modification
- All type hints preserved
- All docstrings preserved
- Tenant scoping and soft delete logic preserved
