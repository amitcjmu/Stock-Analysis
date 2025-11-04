# Deduplication Pattern: Handling Legitimate Duplicate Assets

**Date**: January 2025  
**Context**: Canada Life import with 150+ server cluster conflicts  
**Issue**: #910

## Problem

The current deduplication modal assumes all conflicts are data errors requiring resolution via keep/replace/merge. This breaks legitimate use cases where multiple similar assets should exist with shared dependencies.

**Real-World Example**:
- Multiple servers tied to one application
- Differ only by serial number/UUID/hostname
- ALL should exist as separate assets
- Share dependency to parent application

## Current Architecture Gap

### Asset Conflict Resolution (AssetConflictModal.tsx)
Offers only 3 actions:
1. `keep_existing` - Discard new asset
2. `replace_with_new` - Replace existing asset
3. `merge` - Field-by-field selection

**Missing**: "Create Both" option

### Workflow Limitation
```
Asset Inventory Phase → Deduplication Check → BLOCKS creation
                                              ❌ Forces choice of one asset
                                              ❌ Loses legitimate duplicates

Dependency Analysis Phase → Runs AFTER inventory
                         → Cannot tag dependencies during conflict resolution
```

## Solution Architecture (Issue #910)

### Add 4th Resolution Action: `create_both_with_dependency`

**Frontend Flow**:
```typescript
User selects "Create Both (link to parent application)"
  ↓
DependencySelector component appears
  ↓ User picks parent application (searchable dropdown)
  ↓ User picks dependency type (hosting/infrastructure/server)
  ↓
AssetConflictModal submits to backend
```

**Backend Flow**:
```python
AssetConflictService.resolve_conflicts()
  ↓
For "create_both_with_dependency" action:
  1. Create new asset (don't update existing)
  2. Create dependency: Parent → Existing Asset
  3. Create dependency: Parent → New Asset
  ↓
Return created_assets + created_dependencies UUIDs
```

### Key Files to Create

**Frontend**:
- `src/components/discovery/DependencySelector.tsx` - Searchable parent asset picker
- `src/types/assetConflict.ts` - Add `create_both_with_dependency` type
- `src/components/discovery/AssetConflictModal.tsx` - Add 4th radio button

**Backend**:
- `backend/app/api/v1/endpoints/asset_conflict.py` - New endpoint
- `backend/app/schemas/asset_conflict.py` - New Pydantic schemas
- `backend/app/services/asset_conflict_service.py` - New service layer
- `backend/app/services/dependency_analysis_service.py` - Add `create_dependency()` method

### Data Model

```python
class DependencySelection(BaseModel):
    parent_asset_id: UUID        # Application to link to
    parent_asset_name: str       # For display
    dependency_type: Literal["hosting", "infrastructure", "server"]
    confidence_score: float = 1.0  # Manual = 1.0, AI-detected < 1.0

class AssetConflictResolutionRequest(BaseModel):
    conflict_id: str
    resolution_action: Literal[
        "keep_existing", 
        "replace_with_new", 
        "merge", 
        "create_both_with_dependency"  # NEW
    ]
    merge_field_selections: Optional[dict[str, str]] = None
    dependency_selection: Optional[DependencySelection] = None  # NEW
```

## Benefits

1. **No Data Loss**: Preserves all server cluster assets
2. **Atomic Operations**: Assets + dependencies created together
3. **User Control**: User decides legitimacy of duplicates
4. **Audit Trail**: Manual dependencies marked with confidence_score = 1.0
5. **Bulk Support**: Can apply to all 150 conflicts at once

## Alternative Solutions Considered

### Option 2: Bypass Deduplication Flag
- Add `allow_duplicates` checkbox in Field Mapping phase
- Skip deduplication entirely for those imports
- **Rejected**: Loses safety check, could import bad data

### Option 3: Post-Import Dependency Tagging
- Let duplicates through, tag dependencies later
- Detect server clusters in Dependency Analysis phase
- **Rejected**: Requires two-phase user workflow, worse UX

## Implementation Sequence

1. Backend schemas (`asset_conflict.py`)
2. Backend service layer (`asset_conflict_service.py`)
3. Backend endpoint (`/api/v1/asset-conflicts/resolve`)
4. Frontend types (`assetConflict.ts`)
5. Frontend component (`DependencySelector.tsx`)
6. Frontend modal updates (`AssetConflictModal.tsx`)
7. E2E test (create 3 servers → 1 application)

## Related Patterns

- **Idempotency Pattern**: Conflict detection matches DB constraints (see `duplicate-asset-bug-fix-2025-01.md`)
- **Dependency Analysis**: CrewAI agent runs AFTER inventory completes (see `dependency_analysis_executor.py`)
- **Asset Service Layer**: Uses repository pattern for multi-tenant scoping (see `asset_service/base.py`)

## Testing Strategy

**E2E Test Scenario**:
```
1. Import CSV with 3 servers: "App-Server-01", "App-Server-02", "App-Server-03"
2. First import succeeds
3. Re-import same CSV → 3 conflicts
4. User selects "Create Both" for all 3
5. User picks parent: "My Application"
6. User picks dependency type: "hosting"
7. Submit resolution
8. Verify: 6 assets total (3 from first import + 3 new)
9. Verify: 6 dependencies (My Application → each server)
10. Verify: Dependencies page shows all 6 with confidence_score = 1.0
```

## References

- Issue #910 - Implementation tracking
- `src/components/discovery/AssetConflictModal.tsx:398-421` - Current resolution options
- `backend/app/services/crewai_flows/handlers/phase_executors/dependency_analysis_executor.py:292-299` - Dependency persistence
- `src/types/assetConflict.ts:92` - ResolutionAction type definition
