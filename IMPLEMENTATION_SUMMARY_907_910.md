# Implementation Summary: Issues #907 and #910

## Overview
This document summarizes the implementation of two enhancement issues:
- **Issue #907**: Asset Creation Preview Modal for User Approval
- **Issue #910**: Add 'Create Both with Shared Dependency' Option to Asset Conflict Resolution

## Completed Work

### Database Changes (Issue #910)
✅ **Migration Created**: `backend/alembic/versions/123_add_confidence_score_to_asset_dependencies.py`
- Added `confidence_score` field to `asset_dependencies` table
- 1.0 = manual/user-created dependencies
- <1.0 = auto-detected dependencies
- Idempotent migration with proper indexing

✅ **Model Updated**: `backend/app/models/asset/relationships.py`
- Added `confidence_score` column to AssetDependency model
- Properly documented with Issue #910 reference

### Backend Services (Issue #910)
✅ **Schemas Created**: `backend/app/schemas/asset_conflict.py`
- `DependencySelection` - Parent asset and dependency type selection
- Updated `AssetConflictResolutionRequest` to support `create_both_with_dependency` action
- Updated `BulkConflictResolutionRequest` with proper tenant isolation
- Updated `ConflictResolutionResponse` with `created_dependencies` field
- Maintained backward compatibility with `AssetConflictDetail`

✅ **Service Created**: `backend/app/services/asset_conflict_service.py`
- Implements all 4 resolution actions:
  - keep_existing
  - replace_with_new
  - merge
  - create_both_with_dependency (NEW)
- Atomic transaction handling
- Multi-tenant isolation
- Proper error handling

✅ **Repository Enhanced**: `backend/app/repositories/dependency_repository.py`
- Added `create_dependency()` method with confidence_score support
- Validates both assets exist
- Handles existing dependencies gracefully
- Extracts client_account_id and engagement_id from source asset

✅ **Endpoint Updated**: `backend/app/api/v1/endpoints/asset_conflicts.py`
- Added handling for `create_both_with_dependency` action in `/resolve-bulk` endpoint
- Creates new asset from conflict data
- Creates two dependencies (Parent → Existing, Parent → New)
- Proper error handling and logging
- Multi-tenant security validation

### Backend Services (Issue #907)
✅ **Endpoint Created**: `backend/app/api/v1/endpoints/asset_preview.py`
- `GET /{flow_id}` - Retrieve asset preview from flow_persistence_data
- `POST /{flow_id}/approve` - Approve assets for creation
- Uses existing JSONB flow_persistence_data column
- Multi-tenant isolation
- Auth required

## Remaining Work

### Backend
1. **Run Migration**:
   ```bash
   cd config/docker && docker-compose up -d
   docker-compose exec migration_backend bash -c "cd backend && alembic upgrade head"
   ```

2. **Register Endpoints**: Update `backend/app/api/v1/router_registry.py`
   ```python
   # Add to imports
   from app.api.v1.endpoints import asset_preview

   # Add to router registration
   api_router.include_router(
       asset_preview.router,
       tags=["asset-preview"],
   )
   ```

3. **Fix Linting Issues**: Run from project root
   ```bash
   python3.11 -m ruff check backend/app --fix
   cd backend && python3.11 -m mypy app/
   ```

### Frontend (Issue #910)

1. **Update Type Definitions**: `src/types/assetConflict.ts`
   ```typescript
   export type ResolutionAction =
     | 'keep_existing'
     | 'replace_with_new'
     | 'merge'
     | 'create_both_with_dependency';  // NEW

   export interface DependencySelection {
     parent_asset_id: string;
     parent_asset_name: string;
     dependency_type: 'hosting' | 'infrastructure' | 'server';
     confidence_score?: number;
   }

   export interface ConflictResolution {
     conflict_id: string;
     resolution_action: ResolutionAction;
     merge_field_selections?: Record<string, 'existing' | 'new'>;
     dependency_selection?: DependencySelection;  // NEW
   }
   ```

2. **Create Component**: `src/components/discovery/DependencySelector.tsx`
   - Searchable dropdown for parent application (filter asset_type === 'application')
   - Radio group for dependency type selection
   - Validation before submission

3. **Update Modal**: `src/components/discovery/AssetConflictResolutionModal.tsx`
   - Add 4th radio button for `create_both_with_dependency`
   - Conditionally render `DependencySelector`
   - Update submission logic to include `dependency_selection`

4. **API Service**: Update conflict resolution API calls
   - Include `dependency_selection` in request payload
   - Handle `created_dependencies` in response

### Frontend (Issue #907)

1. **Create Component**: `src/components/discovery/AssetCreationPreviewModal.tsx`
   - Table view showing all assets to be created
   - Display: name, asset_type, description, os/version
   - Inline editing for critical fields
   - Bulk actions: "Approve All", "Approve Selected", "Reject"
   - Individual asset approval/rejection

2. **Update Pages**:
   - `src/pages/discovery/DataCleansing.tsx` - Add preview step transition
   - `src/pages/discovery/Inventory.tsx` - Show preview modal on load

3. **API Service**: `src/lib/api/assetPreview.ts`
   ```typescript
   export const getAssetPreview = async (flow_id: string) => {
     return apiCall(`/api/v1/asset-preview/${flow_id}`, { method: 'GET' });
   };

   export const approveAssets = async (flow_id: string, asset_ids: string[]) => {
     return apiCall(`/api/v1/asset-preview/${flow_id}/approve`, {
       method: 'POST',
       body: JSON.stringify(asset_ids)
     });
   };
   ```

### Testing

1. **Backend Integration Tests**:
   ```bash
   cd backend
   python -m pytest tests/backend/integration/test_asset_conflicts.py -v
   python -m pytest tests/backend/integration/test_asset_preview.py -v
   ```

2. **E2E Testing with Playwright**:
   Use `/qa-test-flow` command to validate:
   - Conflict resolution with create_both_with_dependency
   - Asset preview and approval workflow
   - Dependency creation and display

3. **Manual Testing**:
   - Import CSV with duplicate assets (e.g., server clusters)
   - Verify "Create Both" option appears in conflict modal
   - Test parent selection and dependency creation
   - Verify dependencies appear with confidence_score = 1.0
   - Test asset preview modal before inventory creation

## Architecture Notes

### Multi-Tenant Isolation
All changes maintain strict multi-tenant isolation:
- All queries include `client_account_id` and `engagement_id`
- Endpoint security validated via `RequestContext`
- Dependencies inherit tenant context from source asset

### Atomic Transactions
- Conflict resolution uses atomic transactions
- Rollback on any error
- Dependency creation happens in same transaction as asset creation

### Field Naming Convention
**CRITICAL**: All new code uses `snake_case` (NOT camelCase)
- Frontend types use `snake_case` to match backend
- API responses use `snake_case` directly
- No field name transformation needed

## Testing Checklist

- [ ] Migration runs successfully
- [ ] Endpoints registered in router
- [ ] Backend linting passes (ruff, mypy)
- [ ] Conflict resolution: keep_existing works
- [ ] Conflict resolution: replace_with_new works
- [ ] Conflict resolution: merge works
- [ ] Conflict resolution: create_both_with_dependency works
- [ ] Dependencies created with confidence_score = 1.0
- [ ] Asset preview returns transformed assets
- [ ] Asset approval persists to database
- [ ] Frontend modal shows 4 radio options
- [ ] Parent asset selector filters applications only
- [ ] Dependency type selection works
- [ ] Asset preview modal displays correctly
- [ ] Inline editing works in preview modal
- [ ] Bulk approve/reject functions correctly

## Deployment Notes

### Database
- Migration must run before deploying backend code
- `confidence_score` field nullable for backward compatibility
- Existing dependencies will have NULL confidence_score

### Backend
- No breaking changes to existing endpoints
- `/asset-conflicts/resolve-bulk` extended with new action
- New `/asset-preview` endpoints added

### Frontend
- Existing conflict resolution flows continue to work
- New "Create Both" option appears automatically
- Asset preview is opt-in via flow configuration

## Known Limitations

1. **Asset Preview Persistence**: Currently uses JSONB flow_persistence_data
   - May need dedicated table for large datasets (>1000 assets)
   - Consider pagination for preview modal

2. **Dependency Validation**: No validation of dependency cycles
   - Consider adding cycle detection for app-app dependencies
   - Warn user if creating circular dependencies

3. **Bulk Operations**: create_both_with_dependency creates 2N dependencies for N conflicts
   - Monitor performance with >100 conflicts
   - Consider batch insertion optimization

## References

- Issue #907: https://github.com/[org]/[repo]/issues/907
- Issue #910: https://github.com/[org]/[repo]/issues/910
- CLAUDE.md: Seven-layer architecture requirements
- ADR-012: Two-table flow pattern
- Migration Pattern: `backend/alembic/versions/092_*.py`
