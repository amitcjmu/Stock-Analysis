### Dependency Mapping → Assessment: Rollback + Refactor Plan

**Status**: PIVOT TO ROLLBACK (2025-10-13)

**Original Goal**: Resolve asset→application mismatch when transitioning from Collection to Assessment.

**Pivot Reason**: Discovered 100% redundancy - `collection_flow_applications` table ALREADY provides all required functionality. Full analysis in `backend/ASSET_RESOLUTION_REDUNDANCY_ANALYSIS.md`.

---

### Context and Problem

- **Observed issue**: Collection passes selected IDs that may be any asset type (e.g., server). Assessment APIs iterate `selected_application_ids` assuming application entities, causing zero results or errors.
- **Root cause**: Missing user-facing workflow to map assets → canonical applications BEFORE assessment begins.
- **Original (incorrect) approach**: Create new `asset_application_mappings` table, new service, new endpoints, new phase.
- **Correct approach**: Reuse existing `collection_flow_applications` table and `ApplicationDeduplicationService`.

---

### Discovery: Existing Infrastructure (ALREADY EXISTS!)

#### Database: `collection_flow_applications` Table

Already has ALL required fields:
```sql
-- backend/app/models/canonical_applications/collection_flow_app.py
CREATE TABLE migration.collection_flow_applications (
    id UUID PRIMARY KEY,
    collection_flow_id UUID NOT NULL,
    asset_id UUID,                      -- ✅ Asset link!
    canonical_application_id UUID,      -- ✅ Application link!
    client_account_id UUID,             -- ✅ Tenant scoping!
    engagement_id UUID,                 -- ✅ Tenant scoping!
    deduplication_method VARCHAR(50),   -- ✅ Mapping method!
    match_confidence FLOAT,             -- ✅ Confidence score!
    -- ... other fields
);
```

**Query for unmapped assets**:
```sql
SELECT cfa.asset_id, a.name, a.asset_type
FROM collection_flow_applications cfa
JOIN assets a ON cfa.asset_id = a.id
WHERE cfa.collection_flow_id = :flow_id
  AND cfa.asset_id IS NOT NULL
  AND cfa.canonical_application_id IS NULL  -- ← Unresolved condition!
  AND cfa.client_account_id = :client_account_id;
```

#### Service: Application Deduplication Service

**Location**: `backend/app/services/application_deduplication/`

**Key Functions** (already production-ready):
- `canonical_operations.create_collection_flow_link()` - Creates/updates canonical mappings
- `matching.py` - Similarity matching (exact, fuzzy, acronym, vector)
- `vector_ops.py` - Embedding-based search
- Multi-tenant isolation built-in
- Confidence scoring, match method tracking

**Example Usage**:
```python
from app.services.application_deduplication import canonical_operations

await canonical_operations.create_collection_flow_link(
    db=db,
    collection_flow_id=flow_id,
    canonical_app=selected_canonical_app,
    variant=None,
    original_name=asset.name,
    client_account_id=client_account_id,
    engagement_id=engagement_id
)
# ✅ Handles tenant scoping, deduplication_method, match_confidence
```

#### Frontend: Production-Ready UI Components

**Location**: `src/components/collection/application-input/`

**Components** (already built and tested):
- `ApplicationDeduplicationManager.tsx` - Full mapping UI
- `ApplicationInputField.tsx` - Smart search with suggestions
- `DuplicateDetectionModal.tsx` - Conflict resolution
- `CanonicalApplicationView.tsx` - Display mapped applications

**Features**:
- ✅ Similarity search with confidence thresholds (0.4-1.0)
- ✅ Green checkmarks for high-confidence auto-suggestions (≥0.95)
- ✅ Yellow warning modal for duplicates (0.8-0.95)
- ✅ Gray suggestions in dropdown (0.6-0.8)
- ✅ Manual application creation
- ✅ Variant management

---

### Decision: Rollback + Refactor

**What to Remove** (redundant code):
1. ❌ Migration 091: `asset_application_mappings` table
2. ❌ `AssetResolutionService` (320 lines)
3. ❌ API endpoints under assessment routes (407 lines)
4. ❌ Frontend page `/assessment/[flowId]/asset-resolution` (400 lines)
5. ❌ ASSET_APPLICATION_RESOLUTION phase from enum

**What to Keep**:
1. ✅ Enum unification work (single canonical source)
2. ✅ Existing `collection_flow_applications` table and service
3. ✅ Existing `ApplicationDeduplicationManager` component

**What to Add** (minimal new code):
1. 2 small Collection API endpoints (GET unmapped, POST link)
2. Assessment apps endpoint adjustment (derive from existing links)
3. Frontend banner wrapper (reuses existing `ApplicationDeduplicationManager`)

---

### Minimal, Correct Design

#### Backend: Two Small Collection Endpoints

**Location**: `backend/app/api/v1/endpoints/collection_post_completion.py` (NEW)

```python
@router.get("/{flow_id}/unmapped-assets")
async def get_unmapped_assets_in_collection(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access)
) -> List[Dict[str, Any]]:
    """Get collection flow applications with assets but no canonical mapping"""
    # Query: asset_id IS NOT NULL AND canonical_application_id IS NULL
    # Return: asset details + original application_name from collection

@router.post("/{flow_id}/link-asset-to-canonical")
async def link_asset_to_canonical_application(
    flow_id: str,
    request: LinkAssetRequest,  # { asset_id, canonical_application_id }
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access)
) -> Dict[str, Any]:
    """Map asset to canonical application using existing deduplication service"""
    # Reuse: canonical_operations.create_collection_flow_link()
    # Updates: canonical_application_id, deduplication_method, match_confidence
```

#### Backend: Assessment Apps Derivation (Adjustment)

**Location**: `backend/app/api/v1/master_flows/master_flows_assessment.py` (MODIFY)

```python
@router.get("/{flow_id}/assessment-applications")
async def get_assessment_applications_via_master(...):
    """Derive applications from collection_flow_applications canonical links"""

    # Query collection_flow_applications where canonical_application_id IS NOT NULL
    stmt = select(CollectionFlowApplication).where(
        CollectionFlowApplication.collection_flow_id == source_collection_flow_id,
        CollectionFlowApplication.canonical_application_id.is_not(None),
        CollectionFlowApplication.client_account_id == client_account_id
    )

    links = await db.execute(stmt)

    if not links:
        # Return structured hint: "pending_resolution"
        return {
            "status": "pending_resolution",
            "unmapped_count": <count of unmapped>,
            "message": "Assets need to be mapped to applications"
        }

    # Otherwise, fetch application details from canonical_applications
    applications = []
    for link in links:
        app = await get_canonical_application_details(link.canonical_application_id)
        applications.append(app)

    return applications
```

#### Frontend: Banner + Wrapper

**Location**: `src/components/assessment/AssetResolutionBanner.tsx` (NEW)

```tsx
export const AssetResolutionBanner: React.FC<{flowId: string}> = ({flowId}) => {
  const { data: unmappedAssets } = useQuery({
    queryKey: ['unmapped-assets', flowId],
    queryFn: () => collectionAPI.getUnmappedAssets(flowId)
  });

  const [showManager, setShowManager] = useState(false);

  if (!unmappedAssets || unmappedAssets.length === 0) return null;

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
      <AlertCircle className="h-5 w-5 text-amber-600" />
      <div className="ml-3">
        <h3 className="text-sm font-medium text-amber-800">
          Asset Resolution Required
        </h3>
        <p className="text-sm text-amber-700 mt-1">
          {unmappedAssets.length} asset(s) need to be mapped to applications before proceeding.
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowManager(true)}
          className="mt-2"
        >
          Resolve Assets
        </Button>
      </div>

      {/* Reuse existing ApplicationDeduplicationManager in modal */}
      {showManager && (
        <ApplicationDeduplicationManager
          collectionFlowId={flowId}
          unmappedAssets={unmappedAssets}
          onComplete={() => {
            setShowManager(false);
            // Refresh assessment applications
          }}
        />
      )}
    </div>
  );
};
```

**Usage**: Add to `AssessmentFlowLayout.tsx` or assessment initialization page.

---

### Data Flow (Corrected)

```
Collection (assets selected)
    ↓
collection_flow_applications created
    - asset_id populated
    - canonical_application_id = NULL (unmapped)
    ↓
User clicks "Continue to Assessment"
    ↓
Assessment checks for unmapped assets
    - Query: WHERE canonical_application_id IS NULL
    - If found: Show banner with "Resolve Assets" button
    ↓
User clicks "Resolve Assets"
    - Modal opens with ApplicationDeduplicationManager
    - Search for canonical application
    - Select from suggestions OR create new
    - Calls: POST /collection/{flow_id}/link-asset-to-canonical
    ↓
canonical_operations.create_collection_flow_link() updates row
    - Sets canonical_application_id
    - Sets deduplication_method (user_manual, fuzzy_match, etc.)
    - Sets match_confidence (0.0-1.0)
    ↓
Banner disappears (no more unmapped assets)
    ↓
Assessment applications endpoint
    - Queries: WHERE canonical_application_id IS NOT NULL
    - Returns: Application details from canonical_applications
    ↓
User proceeds with ARCHITECTURE_MINIMUMS, 6R analysis, etc.
```

---

### Rollback Actions

#### Step 1: Database Rollback

```bash
cd backend
alembic downgrade -1  # Remove migration 091
```

**Verification**:
```sql
\dt migration.asset_application_mappings  -- Should show "Did not find any relation"
```

#### Step 2: Remove Redundant Backend Files

```bash
# Remove new files
rm backend/app/services/assessment_flow_service/core/asset_resolution_service.py
rm backend/app/api/v1/endpoints/assessment_flow/asset_resolution.py
rm backend/alembic/versions/091_add_asset_application_mappings.py

# Revert modified files (keep enum unification, remove phase addition)
# assessment_flow_state.py: Remove ASSET_APPLICATION_RESOLUTION from enum
# assessment_flow_utils.py: Remove from phase sequence and progress map
# assessment_flow_router.py: Remove asset_resolution router import
# api_tags.py: Remove ASSET_RESOLUTION tag
```

#### Step 3: Remove Redundant Frontend Files

```bash
# Remove new page
rm src/pages/assessment/[flowId]/asset-resolution.tsx

# Revert modified files (remove asset_application_resolution phase)
# src/hooks/useAssessmentFlow/types.ts: Remove phase from union type
# src/hooks/useAssessmentFlow/api.ts: Remove 3 asset resolution methods
# src/hooks/useAssessmentFlow/useAssessmentFlow.ts: Remove phase handling
# src/config/flowRoutes.ts: Remove phase route
# src/components/assessment/AssessmentFlowLayout.tsx: Remove phase config
```

#### Step 4: Keep Enum Unification (This Part Is Good)

**DO NOT REVERT**:
- `backend/app/models/assessment_flow_state.py` - Canonical enum (minus new phase)
- `backend/app/models/assessment_flow/enums_and_exceptions.py` - Import fix
- `backend/app/services/crewai_flows/assessment_flow/phase_handlers.py` - FINALIZATION usage
- `backend/app/services/crewai_flows/unified_assessment_flow.py` - Phase method mapping

---

### Refactor Actions (Extend Existing)

#### Backend: Collection API Extension

**New File**: `backend/app/api/v1/endpoints/collection_post_completion.py`

- GET `/{flow_id}/unmapped-assets`
- POST `/{flow_id}/link-asset-to-canonical`

**Modified File**: `backend/app/api/v1/master_flows/master_flows_assessment.py`

- Update `get_assessment_applications_via_master()` to derive from `collection_flow_applications` canonical links
- Return `"pending_resolution"` status if unmapped assets exist

#### Frontend: Banner Component

**New File**: `src/components/assessment/AssetResolutionBanner.tsx`

- Queries unmapped assets
- Shows warning banner if any exist
- Opens `ApplicationDeduplicationManager` in modal
- Refreshes on completion

**Modified File**: `src/components/assessment/AssessmentFlowLayout.tsx`

- Add `<AssetResolutionBanner />` to layout

---

### Testing Strategy

#### Backend Tests

```python
async def test_unmapped_assets_query():
    """Verify query returns assets without canonical mapping"""
    # Create collection_flow_application with asset_id but no canonical_application_id
    # Verify it appears in GET /unmapped-assets
    # Map via POST /link-asset-to-canonical
    # Verify it no longer appears in unmapped list

async def test_assessment_apps_derivation():
    """Verify assessment apps derived from canonical links"""
    # Create collection with mapped assets
    # Call GET /assessment-applications
    # Verify returns canonical application details
    # Create collection with unmapped assets
    # Verify returns "pending_resolution" status
```

#### Frontend Tests

```typescript
test("Asset resolution banner workflow", async ({ page }) => {
  // Navigate to assessment initialization
  // Verify banner shows "X assets need mapping"
  // Click "Resolve Assets"
  // Modal opens with ApplicationDeduplicationManager
  // Select canonical application from suggestions
  // Verify banner disappears
  // Verify assessment applications now available
});
```

---

### Effort Estimate (Rollback + Refactor)

**Rollback** (2-3 hours):
- [ ] Downgrade migration 091
- [ ] Delete redundant files (5 files)
- [ ] Revert modified files (6 files)
- [ ] Remove ASSET_APPLICATION_RESOLUTION phase from enum

**Refactor** (9-11 hours):
- [ ] Backend: 2 collection endpoints (3-4h)
- [ ] Backend: Adjust assessment apps derivation (2-3h)
- [ ] Backend: Tenant scoping validation (1h)
- [ ] Frontend: Asset resolution banner component (2-3h)
- [ ] Frontend: Integration with ApplicationDeduplicationManager (1-2h)

**Testing** (2-3 hours):
- [ ] Backend integration tests
- [ ] Frontend E2E tests

**Total**: 13-17 hours (vs. 1,296 lines of redundant code long-term)

---

### Acceptance Criteria (Refactored)

- ✅ Enum unified (single canonical source in backend)
- ✅ Migration 091 rolled back successfully
- ✅ All redundant code removed (service, endpoints, page)
- ✅ Collection API has 2 new endpoints for unmapped assets
- ✅ Assessment apps derived from `collection_flow_applications` canonical links
- ✅ Banner shows if unmapped assets exist, hides when resolved
- ✅ Existing `ApplicationDeduplicationManager` reused successfully
- ✅ Multi-tenant scoping enforced on all queries
- ✅ E2E workflow: Collection → Banner → Resolve → Assessment works

---

### References

**Existing Infrastructure**:
- `backend/app/models/canonical_applications/collection_flow_app.py` - CollectionFlowApplication model
- `backend/app/services/application_deduplication/canonical_operations.py` - Deduplication service
- `src/components/collection/application-input/ApplicationDeduplicationManager.tsx` - Reusable UI

**Analysis**:
- `backend/ASSET_RESOLUTION_REDUNDANCY_ANALYSIS.md` - Full 500-line redundancy analysis

**ADRs**:
- ADR-016: Collection Flow for Intelligent Data Enrichment - Designed for this use case
- ADR-012: Flow Status Management Separation - Master/child flow coordination

**Serena Memories**:
- `collection_flow_phase_status_fixes_2025_10` - Explicitly mentioned as "future enhancement"




