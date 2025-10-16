# Data Flow Analysis Report: Assessment Overview Page

**Analysis Date:** October 16, 2025
**Status:** ✅ PRODUCTION READY (Updated for PR #600)

**Key Changes from Previous Version (2024-07-29)**:
- Replaced mock data with real API endpoints and database integration
- Added **ApplicationGroupsWidget** for canonical application grouping
- Added **ReadinessDashboardWidget** for assessment readiness visualization
- Implemented pre-computed data path with on-the-fly fallback
- Added 3 new API endpoints via Master Flow Orchestrator (MFO)
- Integrated AssessmentApplicationResolver service for asset-to-application resolution
- Enhanced with enrichment status tracking across 7 data tables
- Full multi-tenant scoping on all queries (client_account_id + engagement_id)

---

## 1. Frontend: Components and API Calls

### Page Component
- **Location**: `src/pages/assessment/AssessmentFlowOverview.tsx`
- **Key Features**:
  - Lists all assessment flows for the tenant
  - Displays flow metrics (total, active, completed, apps assessed)
  - Shows detailed assessment widgets for selected flow
  - Provides "Start Assessment" button with readiness gating
  - Integrates with Collection flow for readiness checking

### Widgets Used
- **ApplicationGroupsWidget** (`src/components/assessment/ApplicationGroupsWidget.tsx`, 320 lines)
  - Hierarchical card-based layout showing canonical applications
  - Groups multiple assets (servers, databases, network devices) under canonical application
  - Shows readiness indicators per application (ready/not_ready/in_progress)
  - Displays unmapped assets section for assets without canonical linkage
  - Search and filtering by application name, asset count, readiness percentage
  - Responsive grid layout (1-3 columns based on screen size)

- **ReadinessDashboardWidget** (`src/components/assessment/ReadinessDashboardWidget.tsx`, 325 lines)
  - Summary cards: Ready Assets, Not Ready Assets, In Progress, Avg Completeness
  - Assessment blockers per asset with categorized missing attributes
  - 22 critical attributes reference (infrastructure, application, business, technical debt)
  - "Collect Missing Data" button navigating to Collection flow
  - Progress bars and completeness visualization
  - Export report functionality (placeholder)

- **Supporting Components**:
  - `ApplicationGroupCard` - Individual application card with collapsible asset list
  - `SummaryCard` - Metric card with icon, value, and description
  - `AssetBlockerAccordion` - Collapsible asset with categorized missing attributes
  - `ApplicationGroupsFilters` - Search and sort controls

### API Call Summary

| # | Method | Endpoint | Trigger | Description |
|---|--------|----------|---------|-------------|
| 1 | GET | `/api/v1/master-flows/list` | useQuery on load | Fetches list of all assessment flows for tenant |
| 2 | GET | `/api/v1/master-flows/{flow_id}/assessment-applications` | useQuery when flow selected | Fetches canonical application groups with asset details |
| 3 | GET | `/api/v1/master-flows/{flow_id}/assessment-readiness` | useQuery when flow selected | Fetches readiness summary and assessment blockers |
| 4 | GET | `/api/v1/master-flows/{flow_id}/assessment-progress` | useQuery (optional) | Fetches attribute-level progress by category |
| 5 | GET | `/api/v1/collection-flow/readiness` | useQuery on mount | Checks Collection flow readiness for gating |
| 6 | POST | `/api/v1/assessment-flow/initialize` | User clicks "Start Assessment" | Creates new assessment flow with selected applications |

**Multi-Tenant Headers** (Required on ALL requests):
- `X-Client-Account-ID`: UUID from auth context
- `X-Engagement-ID`: UUID from auth context (optional for some endpoints)

---

## 2. Backend: Services, Endpoints, and Database

### API Endpoint: `GET /api/v1/master-flows/{flow_id}/assessment-applications`

**Route Location**: `backend/app/api/v1/master_flows/assessment/info_endpoints.py:27-139`

**Service Layer**:
- **Service**: `AssessmentApplicationResolver`
- **Location**: `backend/app/services/assessment/application_resolver.py`
- **Method**: `resolve_assets_to_applications(asset_ids, collection_flow_id)`
- **Logic**:
  1. **Fast path**: Check if `assessment_flow.application_asset_groups` exists (pre-computed during initialization)
  2. **Fallback path**: Query database with LEFT JOINs to resolve on-the-fly
  3. Join: `Asset → CollectionFlowApplication → CanonicalApplication`
  4. Group assets by `canonical_application_id` (or create "unmapped-{asset_id}" group for unmapped)
  5. Aggregate asset types, readiness counts per application
  6. Return list of `ApplicationAssetGroup` objects

**Database Tables**:
- **Primary**: `migration.assessment_flows` (stores pre-computed data)
- **Joins**:
  - `migration.assets` (base asset data)
  - `migration.collection_flow_applications` (junction table linking assets to canonical apps)
  - `migration.canonical_applications` (canonical application master data)

**SQL Query** (Fallback path - simplified):
```sql
SELECT
  a.id as asset_id,
  a.asset_name,
  a.asset_type,
  a.assessment_readiness,
  a.assessment_readiness_score,
  cfa.canonical_application_id,
  cfa.match_confidence,
  ca.canonical_name,
  ca.application_type
FROM migration.assets a
LEFT JOIN migration.collection_flow_applications cfa ON a.id = cfa.asset_id
LEFT JOIN migration.canonical_applications ca ON cfa.canonical_application_id = ca.id
WHERE a.id IN (:asset_ids)
  AND a.client_account_id = :client_account_id
  AND a.engagement_id = :engagement_id
GROUP BY cfa.canonical_application_id;
```

**Response Format**:
```json
{
  "flow_id": "uuid",
  "applications": [
    {
      "canonical_application_id": "uuid-or-null",
      "canonical_application_name": "ERP System",
      "asset_ids": ["uuid1", "uuid2"],
      "asset_count": 2,
      "asset_types": ["server", "database"],
      "readiness_summary": {
        "ready": 1,
        "not_ready": 1,
        "in_progress": 0
      }
    }
  ],
  "total_applications": 15,
  "total_assets": 50,
  "unmapped_assets": 3
}
```

---

### API Endpoint: `GET /api/v1/master-flows/{flow_id}/assessment-readiness`

**Route Location**: `backend/app/api/v1/master_flows/assessment/info_endpoints.py:141-276`

**Service Layer**:
- **Service**: `AssessmentApplicationResolver`
- **Method**: `calculate_readiness_summary(asset_ids)`
- **Logic**:
  1. **Fast path**: Check if `assessment_flow.readiness_summary` exists (pre-computed)
  2. **Fallback path**: Query assets for readiness status and scores
  3. Count assets by readiness: ready, not_ready, in_progress
  4. Calculate average completeness score (0.0-1.0)
  5. Query assets NOT ready and extract missing attributes
  6. Categorize missing attributes: infrastructure, application, business, technical_debt
  7. Return readiness summary + asset-level blockers

**Database Tables**:
- **Primary**: `migration.assessment_flows` (stores pre-computed readiness_summary)
- **Query**: `migration.assets` (for readiness status and critical attributes)

**SQL Query** (Fallback path - simplified):
```sql
-- Readiness aggregation
SELECT
  assessment_readiness,
  assessment_readiness_score
FROM migration.assets
WHERE id IN (:asset_ids)
  AND client_account_id = :client_account_id
  AND engagement_id = :engagement_id;

-- Detailed asset data for blockers
SELECT
  id, asset_name, asset_type,
  assessment_readiness, assessment_readiness_score,
  assessment_blockers,
  -- 22 critical attributes (infrastructure)
  cpu_cores, ram_gb, storage_gb, operating_system, network_latency, region,
  -- (application)
  programming_language, framework, database_type, app_dependencies,
  authentication_method, api_endpoints, data_volume_gb, request_rate_per_sec,
  -- (business)
  business_criticality, compliance_requirements, user_base_size, sla_requirements,
  -- (technical_debt)
  last_major_update, code_quality_score, test_coverage, security_scan_date
FROM migration.assets
WHERE id IN (:asset_ids)
  AND assessment_readiness != 'ready'
  AND client_account_id = :client_account_id
  AND engagement_id = :engagement_id;
```

**Response Format**:
```json
{
  "total_assets": 50,
  "readiness_summary": {
    "ready": 35,
    "not_ready": 12,
    "in_progress": 3,
    "avg_completeness_score": 0.78
  },
  "asset_details": [
    {
      "asset_id": "uuid",
      "asset_name": "app-server-01",
      "asset_type": "server",
      "assessment_readiness": "not_ready",
      "assessment_readiness_score": 0.45,
      "completeness_score": 0.45,
      "assessment_blockers": ["Missing CPU cores", "No business criticality set"],
      "missing_attributes": {
        "infrastructure": ["cpu_cores", "ram_gb", "region"],
        "application": ["programming_language"],
        "business": ["business_criticality", "compliance_requirements"],
        "technical_debt": ["code_quality_score"]
      }
    }
  ]
}
```

---

### API Endpoint: `GET /api/v1/master-flows/{flow_id}/assessment-progress`

**Route Location**: `backend/app/api/v1/master_flows/assessment/info_endpoints.py:278-348`

**Service Layer**:
- **Helper**: `calculate_progress_categories(assets)` in `progress_calculator.py`
- **Logic**:
  1. Query all assets for the flow
  2. For each of 4 categories (infrastructure, application, business, technical_debt):
     - Count how many assets have each attribute populated
     - Calculate percentage completion
  3. Calculate overall progress across all 22 attributes
  4. Return category-level and overall progress

**Response Format**:
```json
{
  "flow_id": "uuid",
  "categories": [
    {
      "name": "Infrastructure",
      "completed_attributes": 240,
      "total_attributes": 300,
      "progress_percentage": 80.0
    }
  ],
  "overall_progress": 75.5
}
```

---

## 3. End-to-End Flow Sequence

### Sequence 1: Loading Assessment Overview with Application Groups

1. **User Navigates**: User loads `/assessment` page
2. **Frontend Hook**: `useQuery` for `assessment-flows` triggered
3. **API Call**: GET `/api/v1/master-flows/list`
4. **Backend Route**: FastAPI router directs to master flows list endpoint
5. **Repository Query**: Queries `crewai_flow_state_extensions` for flows with `flow_type='assessment'`
6. **Tenant Scoping**: WHERE clause filters by `client_account_id` and `engagement_id`
7. **DB Execution**: PostgreSQL returns list of assessment flows
8. **Backend Response**: Returns array of flow objects with `id`, `status`, `current_phase`, `progress`
9. **UI Render**: Page renders flow table; auto-selects first processing/initialized flow

10. **Frontend Hook 2**: `useQuery` for `assessment-applications` triggered with selected `flow_id`
11. **API Call**: GET `/api/v1/master-flows/{flow_id}/assessment-applications`
12. **Backend Route**: FastAPI router directs to `get_assessment_applications_via_master()`
13. **Service Layer**: Loads assessment flow, checks for `application_asset_groups` (pre-computed)
14. **Fast Path Hit**: Returns pre-computed groups from `assessment_flows.application_asset_groups` JSONB field
15. **Backend Response**: Returns ApplicationAssetGroup array as JSON
16. **UI Render**: `ApplicationGroupsWidget` displays canonical application cards with asset groupings

### Sequence 2: Loading Readiness Dashboard

17. **Frontend Hook 3**: `useQuery` for `assessment-readiness` triggered with selected `flow_id`
18. **API Call**: GET `/api/v1/master-flows/{flow_id}/assessment-readiness`
19. **Backend Route**: FastAPI router directs to `get_assessment_readiness()`
20. **Service Layer**: Checks for `readiness_summary` (pre-computed) in assessment flow
21. **Fast Path Hit**: Returns pre-computed summary from `assessment_flows.readiness_summary` JSONB field
22. **Fallback Query**: If not pre-computed, queries assets table for readiness status
23. **Blocker Calculation**: Queries assets WHERE `assessment_readiness != 'ready'`
24. **Attribute Extraction**: For each not-ready asset, checks 22 critical attributes for NULL values
25. **Categorization**: Groups missing attributes into 4 categories (infrastructure/application/business/technical_debt)
26. **Backend Response**: Returns readiness summary + asset-level blockers with categorized missing attributes
27. **UI Render**: `ReadinessDashboardWidget` displays summary cards and collapsible asset blockers

### Sequence 3: Pre-Computation During Assessment Initialization

28. **User Action**: User clicks "New Assessment" and selects canonical applications
29. **API Call**: POST `/api/v1/assessment-flow/initialize` with `selected_application_ids`
30. **Backend Service**: `AssessmentFlowInitializer.initialize_flow()`
31. **Asset Resolution**: For each canonical application, lookup assets via `collection_flow_applications`
32. **Pre-Computation**:
    - Calls `AssessmentApplicationResolver.resolve_assets_to_applications()` → stores in `application_asset_groups`
    - Calls `AssessmentApplicationResolver.calculate_enrichment_status()` → stores in `enrichment_status`
    - Calls `AssessmentApplicationResolver.calculate_readiness_summary()` → stores in `readiness_summary`
33. **Database Write**: Atomic transaction stores assessment flow with all 3 pre-computed JSONB fields
34. **Backend Response**: Returns flow_id
35. **UI Navigation**: Redirects to `/assessment/{flow_id}/architecture`

---

## 4. Data Structures

### Frontend TypeScript Interface

```typescript
// src/types/assessment.ts

interface ApplicationAssetGroup {
  canonical_application_id: string | null;
  canonical_application_name: string;
  asset_ids: string[];
  asset_count: number;
  asset_types: string[];
  readiness_summary: {
    ready: number;
    not_ready: number;
    in_progress: number;
  };
}

interface AssessmentReadinessResponse {
  total_assets: number;
  readiness_summary: {
    ready: number;
    not_ready: number;
    in_progress: number;
    avg_completeness_score: number; // 0.0-1.0
  };
  asset_details: AssetDetail[];
}

interface AssetDetail {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  assessment_readiness: 'ready' | 'not_ready' | 'in_progress';
  assessment_readiness_score: number;
  completeness_score: number;
  assessment_blockers: string[];
  missing_attributes: {
    infrastructure: string[];
    application: string[];
    business: string[];
    technical_debt: string[];
  };
}
```

### Backend Pydantic Model

```python
# backend/app/schemas/assessment_flow/base.py

class ApplicationAssetGroup(BaseModel):
    canonical_application_id: Optional[UUID]
    canonical_application_name: str
    asset_ids: List[UUID]
    asset_count: int
    asset_types: List[str]
    readiness_summary: Dict[str, int]  # {"ready": 35, "not_ready": 10, "in_progress": 5}

class ReadinessSummary(BaseModel):
    total_assets: int
    ready: int
    not_ready: int
    in_progress: int
    avg_completeness_score: float  # 0.0-1.0

class EnrichmentStatus(BaseModel):
    compliance_flags: int = 0
    licenses: int = 0
    vulnerabilities: int = 0
    resilience: int = 0
    dependencies: int = 0
    product_links: int = 0
    field_conflicts: int = 0
```

### Database Schema

```sql
-- Migration 093 enhanced assessment_flows table
CREATE TABLE migration.assessment_flows (
  -- Existing fields
  id UUID PRIMARY KEY,
  flow_id UUID NOT NULL,
  master_flow_id UUID,
  client_account_id UUID NOT NULL,
  engagement_id UUID NOT NULL,
  status VARCHAR(50),
  current_phase VARCHAR(100),
  selected_asset_ids JSONB,  -- Array of asset UUIDs

  -- NEW: Pre-computed fields (October 2025)
  selected_canonical_application_ids JSONB,  -- Array of canonical app UUIDs
  application_asset_groups JSONB,  -- Pre-computed ApplicationAssetGroup array
  enrichment_status JSONB,  -- Pre-computed EnrichmentStatus object
  readiness_summary JSONB,  -- Pre-computed ReadinessSummary object

  created_at TIMESTAMP,
  updated_at TIMESTAMP,

  -- Indexes
  INDEX idx_assessment_flow_master (master_flow_id),
  INDEX idx_assessment_flow_tenant (client_account_id, engagement_id)
);

-- GIN indexes for JSONB fields (performance)
CREATE INDEX idx_assessment_flow_app_groups_gin
  ON migration.assessment_flows USING GIN (application_asset_groups);
CREATE INDEX idx_assessment_flow_readiness_gin
  ON migration.assessment_flows USING GIN (readiness_summary);
```

---

## 5. Multi-Tenant Scoping

**All queries MUST include**:
- `client_account_id` (UUID) - Organization isolation
- `engagement_id` (UUID) - Project/session isolation

**Header Requirements**:
- `X-Client-Account-ID`: UUID from auth context
- `X-Engagement-ID`: UUID from auth context

**Enforcement**:
- **Backend**: `RequestContext` dependency extracts from headers
- **Service**: `AssessmentApplicationResolver.__init__()` accepts and stores both tenant fields
- **Database**: WHERE clauses in ALL queries filter by both tenant fields

**Example Multi-Tenant Query**:
```python
query = select(Asset).where(
    Asset.id.in_(asset_ids),
    Asset.client_account_id == context.client_account_id,
    Asset.engagement_id == context.engagement_id
)
```

---

## 6. Troubleshooting Breakpoints

| Breakpoint | Diagnostic Check | Platform-Specific Fix |
|------------|------------------|----------------------|
| **No Application Groups Displayed** | Check browser console for API errors | Verify `application_asset_groups` JSONB field exists in assessment_flows table |
| **Empty application_asset_groups** | Check if flow was created with pre-computation code | Re-create flow with POST `/api/v1/assessment-flow/initialize` or trigger on-the-fly computation |
| **Duplicate Assets in Groups** | Check ApplicationApplicationResolver grouping logic | Fixed in commit 3ea18cb (October 2025) - update code to latest |
| **Frontend Widget Crash** | Check browser console for `missing_attributes` structure errors | Fixed in commit a076e71 (October 2025) - ensure categorized structure returned |
| **API 500 Error** | Check backend logs: `docker logs migration_backend --tail 100` | Verify database schema matches migration 093; check tenant scoping headers present |
| **"Unmapped Assets" Section Empty** | Check collection_flow_applications table has canonical links | Run Collection flow first to establish canonical application mappings |
| **Readiness Summary Shows 0** | Check assets have assessment_readiness field populated | Ensure enrichment pipeline has run (AutoEnrichmentPipeline with 6 agents) |
| **Wrong Flow Selected** | Check flow selection logic in AssessmentFlowOverview.tsx:214-220 | Auto-selects first processing/initialized flow; use dropdown to change |

---

## 7. Performance Considerations

### Fast Path (Pre-Computed Data)
- **Scenario**: Assessment flow created in October 2025 or later
- **Performance**: < 100ms response time
- **Database**: Single SELECT on assessment_flows table, returns JSONB fields directly
- **Use Case**: Production flows after PR #600

### Fallback Path (On-the-Fly Computation)
- **Scenario**: Legacy assessment flows created before October 2025
- **Performance**: 200-500ms for 50 assets (varies with asset count)
- **Database**: Multiple JOINs across 3 tables (assets, collection_flow_applications, canonical_applications)
- **Use Case**: Backward compatibility for existing flows

### Database Indexes
- **GIN Indexes**: On JSONB fields (`application_asset_groups`, `readiness_summary`) for fast retrieval
- **B-Tree Indexes**: On foreign keys (`master_flow_id`) and tenant fields
- **Composite Index**: On `(client_account_id, engagement_id)` for multi-tenant filtering

### Caching Strategy
- **Frontend**: TanStack Query with 30s staleTime, 60s refetchInterval
- **Backend**: Pre-computed data acts as application-level cache
- **Database**: PostgreSQL query plan caching for repeated queries

---

## 8. Related Documentation

- **ADR-027**: Assessment Phase Enum Updates (October 2025)
- **ADR-016**: Collection Flow for Intelligent Data Enrichment (canonical applications)
- **Migration 093**: Assessment Data Model Refactor (JSONB fields)
- **PR #600**: Assessment Architecture & Enrichment Pipeline Implementation
- **Commits**:
  - `3ea18cb`: Fixed duplicate asset grouping bug
  - `a076e71`: Fixed missing_attributes structure for frontend
  - `41a8a48`: Phase 5 completion documentation

---

## 9. Key Architectural Decisions

1. **Pre-Computed vs On-the-Fly**: Fast path uses JSONB storage for instant loads; fallback ensures backward compatibility
2. **Canonical Application Grouping**: Multiple assets (server, database, network) grouped under single canonical application
3. **22 Critical Attributes**: Standardized attribute set across 4 categories for consistent assessment
4. **Multi-Tenant Security**: ALL queries scoped by client_account_id + engagement_id (enterprise requirement)
5. **AssessmentApplicationResolver**: Single service responsible for asset-to-application resolution (separation of concerns)
6. **Collection Flow Integration**: Assessment depends on Collection flow's canonical application mapping
7. **MFO-Only Access**: All endpoints via Master Flow Orchestrator pattern (no direct `/api/v1/discovery/*` calls)
