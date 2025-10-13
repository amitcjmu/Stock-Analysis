### Dependency Mapping → Assessment: Phase 1 MVP Implementation Plan

**Goal**: Resolve the asset→application mismatch when transitioning from Collection to Assessment by inserting a new assessment phase that repurposes the Discovery dependency mapping UI to perform Asset→Application Resolution before 6R analysis.

---

### Context and Problem

- **Observed issue**: Collection passes selected IDs that may be any asset type (e.g., server). Assessment APIs iterate `selected_application_ids` assuming application entities and fetch application metadata, causing zero results or errors.
- **Root causes**:
  - ID payload ambiguity (asset IDs used where application IDs are expected)
  - Missing resolution layer from assets → canonical applications
  - Enum drift across Assessment phases (multiple differing enums), blocking safe phase insertion

Key code paths today:

```282:336:backend/app/api/v1/master_flows/master_flows_assessment.py
@router.get("/{flow_id}/assessment-applications")
async def get_assessment_applications_via_master(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> List[Dict[str, Any]]:
    # ...
    for app_id in flow_state.selected_application_ids:
        metadata = await discovery_integration.get_application_metadata(
            db, str(app_id), client_account_id
        )
    # ...
```

```145:170:backend/app/services/integrations/discovery_integration.py
async def get_application_metadata(
    self, db: AsyncSession, application_id: str, client_account_id: int
) -> Dict[str, Any]:
    stmt = select(Asset).where(
        and_(
            Asset.id == application_id,
            Asset.client_account_id == client_account_id,
        )
    )
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()
    if not asset:
        raise ValueError(f"Application {application_id} not found")
```

---

### Decision

- Insert a new assessment phase: `ASSET_APPLICATION_RESOLUTION` (Phase 1, right after `INITIALIZATION`).
- Repurpose the existing Discovery `DependencyMappingPanel` for a focused Asset→Application mapping workflow.
- Store mappings in a normalized table `migration.asset_application_mappings`, tenant-scoped with audit fields.
- Gate downstream assessment phases until resolution is complete.

---

### Step 0 — Enum Unification (CRITICAL)

Unify all Assessment phases before introducing the new phase to avoid runtime inconsistencies.

- Canonical source: `backend/app/models/assessment_flow_state.py` (preferred).
- Actions:
  - Remove duplicate enum in `backend/app/models/assessment_flow/enums_and_exceptions.py` and import the canonical enum where needed.
  - Update frontend `src/hooks/useAssessmentFlow/types.ts` to exactly mirror backend names.
  - Ensure `backend/app/api/v1/endpoints/assessment_flow_utils.py` phase sequence and navigation helpers reflect the canonical list.

References:

```19:28:backend/app/models/assessment_flow/enums_and_exceptions.py
class AssessmentPhase(str, Enum):
    INITIALIZATION = "initialization"
    ARCHITECTURE_MINIMUMS = "architecture_minimums"
    TECH_DEBT_ANALYSIS = "tech_debt_analysis"
    COMPONENT_SIXR_STRATEGIES = "component_sixr_strategies"
    APP_ON_PAGE_GENERATION = "app_on_page_generation"
    FINAL_REPORT_GENERATION = "final_report_generation"
    COMPLETED = "completed"
```

```30:40:backend/app/models/assessment_flow_state.py
class AssessmentPhase(str, Enum):
    INITIALIZATION = "initialization"
    ARCHITECTURE_MINIMUMS = "architecture_minimums"
    COMPONENT_DISCOVERY = "component_discovery"
    TECH_DEBT_ANALYSIS = "tech_debt_analysis"
    COMPONENT_SIXR_STRATEGIES = "component_sixr_strategies"
    APP_ON_PAGE_GENERATION = "app_on_page_generation"
    FINALIZATION = "finalization"
```

```23:29:src/hooks/useAssessmentFlow/types.ts
export type AssessmentPhase =
  | 'initialization'
  | 'architecture_minimums'
  | 'tech_debt_analysis'
  | 'component_sixr_strategies'
  | 'app_on_page_generation'
  | 'finalization';
```

Acceptance criteria:
- Single authoritative enum definition in backend; all imports updated.
- Frontend type exactly matches backend phase names.
- Phase navigation/utilities updated and build passes.

---

### Step 1 — Add ASSET_APPLICATION_RESOLUTION Phase

1) Backend enum and sequencing

- Add to canonical enum (after `INITIALIZATION`).
- Update phase sequence functions and navigation helpers to include it as Phase 1.

2) Database schema (Alembic migration)

```sql
CREATE TABLE IF NOT EXISTS migration.asset_application_mappings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_flow_id UUID NOT NULL REFERENCES migration.assessment_flows(id) ON DELETE CASCADE,
  asset_id UUID NOT NULL,
  application_id UUID NOT NULL,
  mapping_confidence NUMERIC(3,2) DEFAULT 1.00,
  mapping_method VARCHAR(50) NOT NULL, -- user_manual | agent_suggested | deduplication_auto
  client_account_id UUID NOT NULL,
  engagement_id UUID NOT NULL,
  created_by UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT uq_asset_app_mapping UNIQUE(assessment_flow_id, asset_id)
);
CREATE INDEX IF NOT EXISTS idx_mappings_flow ON migration.asset_application_mappings(assessment_flow_id);
CREATE INDEX IF NOT EXISTS idx_mappings_tenant ON migration.asset_application_mappings(client_account_id, engagement_id);
```

Notes:
- Use idempotent Alembic with explicit `migration` schema.
- Tenant scoping required on all queries.

3) Service layer: `AssetResolutionService`

- Responsibilities:
  - `get_unresolved_assets(assessment_flow_id)` — list selected assets lacking mappings.
  - `map_asset_to_application(assessment_flow_id, asset_id, application_id, method, confidence)` — upsert mapping with tenant checks.
  - `create_application_from_assets(assessment_flow_id, asset_ids)` — create a new `Asset` rows with `asset_type='application'` (if needed), return application ID, and create mappings.
  - `validate_resolution_complete(assessment_flow_id)` — ensure all selected assets have mappings; transition phase when complete.

4) API endpoints (under assessment flow routes)

- `GET /api/v1/assessment-flows/{flow_id}/asset-resolution`
  - Returns: `{ unresolved_assets: [...], existing_mappings: [...] }`
- `POST /api/v1/assessment-flows/{flow_id}/asset-resolution/mappings`
  - Body: `{ asset_id: string, application_id: string, mapping_method?: string, mapping_confidence?: number }`
- `POST /api/v1/assessment-flows/{flow_id}/asset-resolution/complete`
  - Marks resolution done; advances to next phase.

5) Integration with Master Flow Assessment applications

- When serving assessment applications, derive the application set from mappings if resolution is complete; otherwise return an empty array plus a structured "pending resolution" state for the frontend to display a banner and/or redirect to resolution page.

---

### Step 2 — Frontend Integration

1) Types, routing, progress

- Add `asset_application_resolution` to `AssessmentPhase` type and to `flowRoutes` and progress components so it shows in the assessment flow timeline.

2) Resolution page

- New page: `src/pages/assessment/[flowId]/asset-resolution.tsx`
- Reuse `DependencyMappingPanel` with the `app-server` view for Asset→Application mapping. Keep UI scoped to mapping (not full app→app dependencies).
- Features:
  - Show selected assets from collection context.
  - Map to existing applications (dropdown) or create new application then map.
  - Bulk create application from selected assets (e.g., 5 servers → one application).
  - Show AI suggestions (phase 2 enhancement) with confidence and approval.

3) Hook changes

- Update `useAssessmentFlow` to:
  - Detect `asset_application_resolution` as the current phase and block progression until completion.
  - Call the new mapping endpoints for list/create/complete.
  - Once completed, proceed to `architecture_minimums` and `getAssessmentApplications` should then work unchanged.

4) Banner

- Until completed, show a banner on assessment pages with the currently selected asset and the target application mapping (if known) to reduce confusion.

---

### Data Flow (Updated)

Collection (assets selected)
→ Assessment `INITIALIZATION`
→ **`ASSET_APPLICATION_RESOLUTION`** (map assets → applications; write to `asset_application_mappings`)
→ `ARCHITECTURE_MINIMUMS`
→ `COMPONENT_DISCOVERY`
→ `TECH_DEBT_ANALYSIS`
→ `COMPONENT_SIXR_STRATEGIES`
→ `APP_ON_PAGE_GENERATION`
→ `FINALIZATION`

Notes:
- Pre-populate mappings from any deduplication output; allow user to adjust mappings.
- Optionally, after completion, update `selected_application_ids` to canonical application IDs or rely solely on the mappings table for downstream lookups.

---

### Change List by File (initial)

- Backend
  - `backend/app/models/assessment_flow_state.py` — Canonical enum + new phase
  - Remove/replace enum in `backend/app/models/assessment_flow/enums_and_exceptions.py`
  - `backend/app/api/v1/endpoints/assessment_flow_utils.py` — Phase sequence and navigation
  - `backend/alembic/versions/*` — New migration for `asset_application_mappings`
  - `backend/app/services/assessment_flow/asset_resolution_service.py` — New service (tenant-scoped)
  - `backend/app/api/v1/endpoints/assessment_flow/asset_resolution.py` — New endpoints
  - `backend/app/api/v1/master_flows/master_flows_assessment.py` — Read mappings when composing applications

- Frontend
  - `src/hooks/useAssessmentFlow/types.ts` — Add phase
  - `src/config/flowRoutes.ts` — Add route mapping
  - `src/components/collection/progress/FlowDetailsCard.tsx` — Progress timeline update
  - `src/components/collection/progress/TabbedFlowDetails.tsx` — Tabs and navigation
  - `src/pages/assessment/[flowId]/asset-resolution.tsx` — New page (reusing `DependencyMappingPanel`)
  - `src/hooks/useAssessmentFlow/useAssessmentFlow.ts` — Gating + API calls
  - `src/services/api/...` — Add client methods for resolution endpoints

---

### API Contracts (Draft)

1) List unresolved and existing mappings

Request:
```
GET /api/v1/assessment-flows/{flow_id}/asset-resolution
Headers: X-Client-Account-ID, X-Engagement-ID
```

Response:
```json
{
  "status": "ok",
  "unresolved_assets": [
    { "asset_id": "uuid", "name": "DevTestVM01", "asset_type": "server" }
  ],
  "existing_mappings": [
    { "asset_id": "uuid", "application_id": "uuid", "mapping_method": "user_manual", "mapping_confidence": 1.0 }
  ]
}
```

2) Create/update a mapping

Request:
```json
POST /api/v1/assessment-flows/{flow_id}/asset-resolution/mappings
{ "asset_id": "uuid", "application_id": "uuid", "mapping_method": "user_manual", "mapping_confidence": 1.0 }
```

Response:
```json
{ "status": "ok" }
```

3) Complete resolution

Request:
```
POST /api/v1/assessment-flows/{flow_id}/asset-resolution/complete
```

Response:
```json
{ "status": "completed", "next_phase": "architecture_minimums" }
```

---

### Testing Plan

- Backend
  - Unit tests for `AssetResolutionService` (CRUD, tenant scoping, validation)
  - API tests for the three endpoints (auth + scoping + happy/edge cases)
  - Integration: master flow endpoint returns applications only after resolution complete

- Frontend
  - Hook tests: `useAssessmentFlow` gating behavior and API handling
  - Page tests: Render, map, complete, and route to next phase
  - E2E: Collection → Assessment Init → Resolution → Architecture Minimums

---

### Risks & Mitigations

- **User friction**: Auto-resolve 1:1 cases; prompt only for ambiguous mappings.
- **Enum drift regression**: Single canonical enum; CI lint to block reintroduction.
- **Dedup overlap**: Pre-populate suggestions; mark `mapping_method` appropriately.
- **Tenant isolation**: Enforce `client_account_id` and `engagement_id` in repositories and endpoints.

---

### Acceptance Criteria (Phase 1 MVP)

- Enum unified; build and navigation utilities reflect the canonical set.
- New phase present; database migration applied successfully.
- Resolution endpoints functional with tenant scoping and audit fields.
- Frontend page allows mapping and completion; progress updates and routing work.
- After completion, `getAssessmentApplications` returns non-empty results for cases that previously failed.

---

### Effort & Ownership

- Backend: 8–12h (Enums 1–2h, Migration 2h, Service+API 5–8h)
- Frontend: 10–14h (Phases/routes 2–3h, Page 5–6h, Hooks 3–4h, Banner 1–2h)
- Tests: 3–5h

---

### References

- `backend/app/models/assessment_flow_state.py` — canonical phases
- `backend/app/api/v1/master_flows/master_flows_assessment.py` — applications endpoint
- `backend/app/services/integrations/discovery_integration.py` — application metadata resolution
- `src/components/discovery/dependencies/DependencyMappingPanel.tsx` — reusable UI
- `src/pages/discovery/Dependencies.tsx` — current dependency mapping usage


