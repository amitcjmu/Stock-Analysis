# Asset-Agnostic Data Collection Remedial Plan V2
## Based on GPT5 Review and Codebase Evidence

## Executive Summary

After GPT5 review and thorough codebase analysis, we've discovered:
1. **Most infrastructure already exists** - JSON fields, import tables, completeness endpoints
2. **Advanced EAV schema already designed** - Production-ready migration awaiting deployment
3. **Modular gap analysis tools exist** - 8 specialized tools instead of monolithic approach
4. **UI components ready** - CompletenessDashboard, MaintenanceWindowForm/Table available
5. **Critical gaps confirmed** - Application gates block flow, mock data hardcoded, conflicts endpoint missing

## Validated Issues (Confirmed by Evidence)

### 1. Application Gates Block Asset-Agnostic Flow
- **Evidence**: Multiple selection barriers in ApplicationSelection.tsx, EnhancedApplicationSelection.tsx
- **Impact**: Cannot start collection for servers/databases/devices without application

### 2. Mock Data in Production UI
- **Evidence**: DataIntegration.tsx lines 50-152 contain hardcoded mock conflicts
- **Impact**: Users see fake data instead of real conflicts

### 3. Missing Conflicts API Endpoint
- **Evidence**: No `/collection/assets/{asset_id}/conflicts` endpoint exists
- **Impact**: Cannot fetch real conflicts from backend

## Updated Solution Architecture

### Phase 1: Immediate Fixes (Week 1)
**Focus: Unblock asset-agnostic collection using existing infrastructure**

#### 1.1 Database - Minimal Conflict Table Only
```sql
-- Single table for conflicts (not full EAV yet)
CREATE TABLE IF NOT EXISTS migration.asset_field_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES migration.assets(id),
    field_name VARCHAR(255) NOT NULL,
    conflicting_values JSONB NOT NULL, -- Array of {value, source, timestamp, confidence}
    resolution_status VARCHAR(50) DEFAULT 'pending' CHECK (resolution_status IN ('pending', 'auto_resolved', 'manual_resolved')),
    resolved_value TEXT,
    resolved_by UUID,
    resolution_rationale TEXT,
    client_account_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_asset_field_conflict UNIQUE (asset_id, field_name, client_account_id, engagement_id)
);

CREATE INDEX idx_conflicts_asset_field ON migration.asset_field_conflicts (asset_id, field_name);
CREATE INDEX idx_conflicts_tenant ON migration.asset_field_conflicts (client_account_id, engagement_id);
```

#### 1.2 Leverage Existing Infrastructure
- **Use** `assets.custom_attributes` and `assets.technical_details` JSON fields (confirmed to exist)
- **Use** `raw_import_records` table for data provenance (confirmed to exist)
- **Use** `ImportFieldMapping` for field mappings (confirmed to exist)
- **Enhance** existing modular gap analysis tools (8 specialized tools found)

#### 1.3 Backend - Add Missing Endpoints Only
```python
# Add to /backend/app/api/v1/endpoints/collection_gaps/collection_flows.py

@router.post("/assets/start")
async def start_asset_collection(
    scope: str,  # "tenant" | "engagement" | "asset"
    scope_id: str,  # UUID of the scoped entity
    asset_type: Optional[str] = None,  # "server" | "database" | "device" | "application"
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Start collection for any asset without requiring application"""
    # Store scope in collection_flows.flow_metadata (field exists)

@router.get("/assets/{asset_id}/conflicts")
async def get_asset_conflicts(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Get real conflicts from asset_field_conflicts table"""

@router.post("/assets/{asset_id}/conflicts/resolve")
async def resolve_asset_conflict(
    asset_id: str,
    field_name: str,
    resolution: ConflictResolution,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Resolve a specific field conflict"""
```

### Phase 2: Frontend Fixes (Week 1)
**Focus: Remove gates and replace mock data**

#### 2.1 Remove Application Gates
```typescript
// Replace hard gates with optional scope dialog
const ScopeSelectionDialog: React.FC<{
  onScopeSelect: (scope: 'tenant' | 'engagement' | 'asset', id: string) => void;
  allowSkip?: boolean;
}> = ({ onScopeSelect, allowSkip = true }) => {
  // Allow starting collection without application
};
```

#### 2.2 Replace Mock Data in DataIntegration.tsx
```typescript
// Replace lines 50-152 mock conflicts with:
const { data: conflicts, isLoading } = useQuery({
  queryKey: ['asset-conflicts', assetId],
  queryFn: () => collectionFlowService.getAssetConflicts(assetId),
  enabled: !!assetId
});
```

#### 2.3 Create Collection Gaps Dashboard
```typescript
// New unified dashboard using existing components
const CollectionGapsDashboard = () => {
  return (
    <>
      <CompletenessDashboard />  // Exists
      <MaintenanceWindowsCard />  // Use MaintenanceWindowTable
      <ConflictsOverviewCard />   // New - shows conflict stats
    </>
  );
};
```

### Phase 3: Conflict Detection Service (Week 2)
**Focus: Build real conflict detection using existing data**

#### 3.1 Conflict Detection Service
```python
class ConflictDetectionService:
    def __init__(self, db: AsyncSession, client_account_id: int, engagement_id: int):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def detect_conflicts_for_asset(self, asset_id: str) -> List[AssetFieldConflict]:
        """
        Aggregate data from multiple sources:
        - assets.custom_attributes (JSON)
        - assets.technical_details (JSON)
        - raw_import_records (existing table)
        - questionnaire responses
        """
        conflicts = []

        # Get data from all sources
        asset_data = await self._get_asset_data(asset_id)
        import_data = await self._get_import_data(asset_id)
        response_data = await self._get_response_data(asset_id)

        # Compare field values across sources
        all_fields = self._extract_all_fields(asset_data, import_data, response_data)

        for field_name in all_fields:
            values = self._get_field_values_from_sources(field_name, sources)
            if len(set(values)) > 1:  # Conflict detected
                conflict = await self._create_conflict_record(
                    asset_id, field_name, values
                )
                conflicts.append(conflict)

        return conflicts
```

#### 3.2 Enhance Existing Gap Analysis Tools
```python
# Enhance existing GapIdentifierTool (found in gap_analysis/)
class EnhancedGapIdentifierTool(GapIdentifierTool):
    """Extend existing tool to include conflict-based gaps"""

    def identify_gaps(self, asset_data: Dict) -> List[Gap]:
        gaps = super().identify_gaps(asset_data)

        # Add conflict-based gaps
        conflicts = self._get_conflicts(asset_data['asset_id'])
        for conflict in conflicts:
            gaps.append(Gap(
                field=conflict.field_name,
                type='conflict',
                severity='high' if conflict.confidence_spread > 0.3 else 'medium'
            ))

        return gaps
```

### Phase 4: Deploy Advanced Features (Week 3-4)
**Focus: Deploy production-ready EAV schema when needed**

#### 4.1 Deploy Existing EAV Migration (When Ready)
```bash
# The migration already exists and is production-ready
alembic upgrade head  # Runs add_asset_agnostic_conflict_detection_schema.py
```

#### 4.2 Feature Flag pgvector
```python
# Use feature flag for vector similarity
if feature_flags.is_enabled('collection.gaps.pgvector'):
    # Use pgvector for similarity matching
    similar_assets = await find_similar_assets_by_vector(asset_embedding)
else:
    # Use traditional matching
    similar_assets = await find_similar_assets_by_attributes(asset_attributes)
```

## Implementation Priorities (Based on Evidence)

### Immediate (Do Now)
1. ✅ **Create minimal conflicts table** - Single table, not full EAV
2. ✅ **Add 3 missing endpoints** - start/conflicts/resolve under `/collection/assets/*`
3. ✅ **Remove application gates** - Allow any asset type collection
4. ✅ **Replace mock data** - Wire to real conflicts endpoint

### Short Term (Week 2)
1. ⚠️ **Build ConflictDetectionService** - Aggregate from existing sources
2. ⚠️ **Enhance existing tools** - Don't create new ones, extend the 8 existing
3. ⚠️ **Create unified dashboard** - Reuse existing components

### Long Term (When Needed)
1. 🔄 **Deploy EAV schema** - Already designed, deploy when scale requires
2. 🔄 **Enable pgvector** - Behind feature flag for similarity matching
3. 🔄 **Advanced conflict resolution** - ML-based auto-resolution

## What NOT to Do (Based on Evidence)

❌ **Don't create GapAnalysisTool** - 8 modular tools already exist and are better
❌ **Don't recreate completeness endpoints** - Already exist at `/flows/{flowId}/completeness`
❌ **Don't import Asset model** - Doesn't exist, likely by design
❌ **Don't deploy full EAV immediately** - Use JSON fields first
❌ **Don't create parallel API structure** - Stay under `/api/v1/collection/*`

## Success Validation

### Week 1 Deliverables
- [ ] Users can start collection for ANY asset type
- [ ] Conflicts table created in migration schema
- [ ] Real conflicts displayed instead of mock data
- [ ] Application gates removed or optional

### Week 2 Deliverables
- [ ] Conflict detection aggregates from multiple sources
- [ ] Confidence scores calculated and displayed
- [ ] Manual conflict resolution working
- [ ] Collection Gaps dashboard with real metrics

### Production Readiness Gates
- [ ] No mock data in production UI
- [ ] All endpoints return real data
- [ ] Multi-tenant isolation verified
- [ ] Performance < 2 seconds for 100 fields

## Code-Level Fixes Required

### Backend
```python
# 1. Router registration (already done correctly)
# 2. Add feature flag check
if not feature_flags.is_enabled('collection.gaps.v1'):
    raise HTTPException(403, "Feature not enabled")

# 3. Use existing flow_metadata field for scope
flow.flow_metadata = {
    "scope": request.scope,  # "tenant" | "engagement" | "asset"
    "scope_id": request.scope_id,
    "asset_type": request.asset_type
}
```

### Frontend
```typescript
// 1. Remove application requirement
// Replace: if (!selectedApplication) return <ApplicationSelection />
// With: optional scope dialog

// 2. Replace mock conflicts
// Remove: const mockConflicts = [...] (lines 50-152)
// Add: useQuery to fetch real conflicts

// 3. Support both field types (already working)
// date/date_input and number/numeric_input both supported
```

## Risk Mitigation

### Technical Risks
- **JSON field performance**: Monitor query times, add GIN indexes if needed
- **Conflict detection scale**: Batch processing for large datasets
- **Multi-source aggregation**: Use async/await for parallel fetching

### Business Risks
- **User confusion**: Clear UI showing why conflicts exist
- **Data quality**: Show confidence scores prominently
- **Adoption**: Gradual rollout with feature flags

## Approval Requirements

This plan addresses GPT5's feedback while leveraging existing infrastructure:

- ✅ Uses existing JSON fields instead of immediate EAV
- ✅ Leverages 8 existing modular gap tools
- ✅ Stays under `/api/v1/collection/*` API structure
- ✅ Reuses existing UI components
- ✅ Minimal new code, maximum reuse

**Ready for implementation with focus on immediate fixes first.**