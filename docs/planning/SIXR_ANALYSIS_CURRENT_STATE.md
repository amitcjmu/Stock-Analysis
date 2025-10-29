# 6R Analysis - Current State Documentation

**Status**: Pre-Migration Documentation (Phase 1 Complete)
**Created**: 2025-10-28
**Purpose**: Document existing 6R Analysis implementation before removal
**Related Issue**: #837 - Assessment Flow MFO Migration Phase 1
**Parent Issue**: #611 - Assessment Flow Complete
**Migration Plan**: `/docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md`

---

## Executive Summary

This document captures the complete current state of the 6R Analysis implementation, which will be **REMOVED** as part of the Assessment Flow MFO Migration. The 6R Analysis functionality will be **replaced** by the Assessment Flow with proper MFO (Master Flow Orchestrator) integration per ADR-006.

### Why This Is Being Removed

1. **Architectural Violation**: 6R Analysis bypasses the MFO, violating ADR-006
2. **Code Duplication**: Duplicates functionality already present in Assessment Flow
3. **Two Parallel Implementations**: Causes confusion and maintenance burden
4. **No MFO Integration**: Lacks proper master/child flow pattern per ADR-012

### Migration Strategy

**Remove 6R Analysis entirely** and properly implement Assessment Flow with MFO integration.

---

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Database Schema](#database-schema)
3. [Backend File Inventory](#backend-file-inventory)
4. [Frontend File Inventory](#frontend-file-inventory)
5. [Request/Response Schemas](#requestresponse-schemas)
6. [Data Flow](#data-flow)
7. [Dependencies](#dependencies)

---

## API Endpoints

All endpoints are prefixed with `/api/v1/6r/` and are registered in `backend/app/api/v1/router_registry.py`.

### Core Analysis Endpoints

#### 1. Create 6R Analysis
\`\`\`
POST /api/v1/6r/analyze
\`\`\`

**Request Body**:
\`\`\`typescript
{
  application_ids: string[];  // UUID strings
  initial_parameters?: {
    business_value: number;           // 1-10
    technical_complexity: number;     // 1-10
    migration_urgency: number;        // 1-10
    compliance_requirements: number;  // 1-10
    cost_sensitivity: number;         // 1-10
    risk_tolerance: number;           // 1-10
    innovation_priority: number;      // 1-10
    application_type: 'custom' | 'cots' | 'hybrid';
  };
  analysis_name?: string;
}
\`\`\`

**Response**:
\`\`\`typescript
{
  analysis_id: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'requires_input';
  current_iteration: number;
  applications: Array<{id: number}>;
  parameters: SixRParameters;
  qualifying_questions: QualifyingQuestion[];
  progress_percentage: number;
  created_at: string;
  updated_at: string;
}
\`\`\`

**Handler**: `backend/app/api/v1/endpoints/sixr_analysis_modular/handlers/analysis_handlers/create.py`

---

#### 2. Get Analysis Status
\`\`\`
GET /api/v1/6r/{analysis_id}
\`\`\`

**Response**: Same as Create Analysis Response

**Handler**: `backend/app/api/v1/endpoints/sixr_analysis_modular/handlers/analysis_handlers/retrieve.py`

---

#### 3. List All Analyses
\`\`\`
GET /api/v1/6r/
\`\`\`

**Query Parameters**:
- \`status\` (optional): Filter by analysis status
- \`application_id\` (optional): Filter by application UUID
- \`created_after\` (optional): ISO date string
- \`created_before\` (optional): ISO date string
- \`limit\` (optional): Number of results (default: 20)
- \`offset\` (optional): Pagination offset

**Response**:
\`\`\`typescript
{
  analyses: SixRAnalysisResponse[];
  total_count: number;
  page: number;
  page_size: number;
}
\`\`\`

---

#### 4. Update Analysis Parameters
\`\`\`
PUT /api/v1/6r/{analysis_id}/parameters
\`\`\`

**Request Body**:
\`\`\`typescript
{
  parameters: {
    business_value: number;
    technical_complexity: number;
    migration_urgency: number;
    compliance_requirements: number;
    cost_sensitivity: number;
    risk_tolerance: number;
    innovation_priority: number;
    application_type: 'custom' | 'cots' | 'hybrid';
  };
  trigger_reanalysis: boolean;
}
\`\`\`

---

#### 5. Submit Qualifying Questions
\`\`\`
POST /api/v1/6r/{analysis_id}/questions
\`\`\`

**Request Body**:
\`\`\`typescript
{
  responses: Array<{
    question_id: string;
    response_value: any;
    confidence?: number;
  }>;
  is_partial: boolean;
}
\`\`\`

---

#### 6. Submit Inline Answers (Tier 1 Gap Filling - PR #816)
\`\`\`
POST /api/v1/6r/{analysis_id}/inline-answers
\`\`\`

**Request Body**:
\`\`\`typescript
{
  asset_id: string;  // UUID
  answers: Record<string, string>;  // field_name -> field_value
}
\`\`\`

---

#### 7. Create Analysis Iteration
\`\`\`
POST /api/v1/6r/{analysis_id}/iterate
\`\`\`

#### 8. Get 6R Recommendation
\`\`\`
GET /api/v1/6r/{analysis_id}/recommendation
\`\`\`

#### 9. Create Bulk Analysis Job
\`\`\`
POST /api/v1/6r/bulk
\`\`\`

See full endpoint details in `/docs/planning/SIXR_ANALYSIS_CURRENT_STATE_FRONTEND_ONLY.md`

---

## Database Schema

All tables are in the \`migration\` schema.

### Table List

1. **sixr_analyses** - Main analysis records
2. **sixr_iterations** - Analysis refinement cycles
3. **sixr_recommendations** - 6R strategy recommendations
4. **sixr_analysis_parameters** - Analysis parameters per iteration
5. **sixr_parameters** - Global configuration key-value store
6. **sixr_questions** - Master list of qualifying questions
7. **sixr_question_responses** - User responses to questions

### 1. sixr_analyses (Primary Table)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| migration_id | UUID | FK to migrations (nullable) |
| client_account_id | UUID | Multi-tenant isolation (NOT NULL, indexed) |
| engagement_id | UUID | Multi-tenant isolation (NOT NULL, indexed) |
| name | VARCHAR(255) | Analysis name (NOT NULL, indexed) |
| description | TEXT | Analysis description |
| status | ENUM | pending, in_progress, completed, failed, requires_input |
| priority | INTEGER | 1-5 scale (default: 3) |
| application_ids | JSON | List of application UUIDs |
| application_data | JSON | Cached application data |
| current_iteration | INTEGER | Current iteration number |
| progress_percentage | FLOAT | 0-100 progress |
| estimated_completion | TIMESTAMP | Estimated completion time |
| final_recommendation | ENUM | Final 6R strategy |
| confidence_score | FLOAT | 0-1 confidence |
| tier1_gaps_by_asset | JSONB | Tier 1 blocking gaps (PR #816) |
| retry_after_inline | BOOLEAN | Blocked pending inline answers |
| created_at, updated_at, created_by, updated_by | Various | Audit fields |

**Model**: `backend/app/models/sixr_analysis/analysis.py:SixRAnalysis`

---

### 2. sixr_iterations

Tracks analysis refinement cycles. Includes iteration metadata, parameter changes, question responses, and agent insights.

**Model**: `backend/app/models/sixr_analysis/analysis.py:SixRIteration`

---

### 3. sixr_recommendations

Stores 6R strategy recommendations per iteration with confidence scores, strategy scores, estimates, and benefits.

**Model**: `backend/app/models/sixr_analysis/recommendations.py:SixRRecommendation`

---

### 4. sixr_analysis_parameters

Tracks 7 analysis parameters (business_value, technical_complexity, etc.) per iteration.

**Model**: `backend/app/models/sixr_analysis/parameters.py:SixRAnalysisParameters`

---

### 5-7. Other Tables

See full schema details in the comprehensive database section above.

---

## Backend File Inventory

### Total: 72 Files to Delete

#### API Endpoints (26 files)

**Main Routers**:
1. `backend/app/api/v1/endpoints/sixr_analysis.py` - Main router
2. `backend/app/api/v1/endpoints/sixr_analysis_modular.py` - Deprecated modular router

**Modular Handlers** (`sixr_analysis_modular/`): 11 files
- `handlers/analysis_handlers/create.py`
- `handlers/analysis_handlers/list.py`
- `handlers/analysis_handlers/retrieve.py`
- `handlers/bulk_handlers.py`
- `handlers/parameter_handlers.py`
- `handlers/recommendation_handlers.py`
- Plus various `__init__.py` files

**Modular Services** (`sixr_analysis_modular/services/`): 9 files
- `services/analysis_service.py`
- `services/gap_detection_service.py`
- `services/background_tasks/*.py` (5 files)

**Legacy Handlers** (`sixr_handlers/`): 6 files

---

#### Models (6 files)

**Location**: `backend/app/models/sixr_analysis/`

- `analysis.py` - SixRAnalysis, SixRIteration models
- `parameters.py` - Parameters models
- `questions.py` - Question models
- `recommendations.py` - Recommendation model
- `base.py` - Base imports and enums
- `__init__.py`

---

#### Schemas (1 file)

- `backend/app/schemas/sixr_analysis.py` - Pydantic request/response schemas

---

#### Services (22 files)

**Main Service**:
- `backend/app/services/sixr_engine_modular.py`

**Service Handlers** (4 files):
- `sixr_handlers/cost_calculator.py`
- `sixr_handlers/recommendation_engine.py`
- `sixr_handlers/risk_assessor.py`

**Service Tools** (17 files):
- `tools/sixr_tools_modular.py`
- `tools/sixr_handlers/*.py` (5 files)
- `tools/sixr_tools/**/*.py` (10 files organized by function)

---

#### Scripts (2 files)

- `backend/app/scripts/seed_sixr_analysis_demo.py`
- `backend/app/scripts/seed_sixr_questions.py`

---

#### CrewAI Components (15 files)

**Strategy Crew** (`crewai_flows/crews/sixr_strategy_crew/`): 8 files
**IMPORTANT**: These should be MIGRATED to `assessment_strategy_crew/`, not deleted!
- `crew.py`, `agents.py`, `tasks.py`, `tools.py`, `config.py`, etc.

**CrewAI Tools** (`crewai_flows/tools/sixr_tools/`): 7 files
- Analysis, recommendation, validation, question, parameter, export tools

---

## Frontend File Inventory

### Total: 87+ Items to Delete

#### API Clients (2 files)

1. `src/lib/api/sixr.ts` - Main 6R API client (764 lines) ⚠️ **DEPRECATED**
2. `src/hooks/useSixRAnalysis.ts` - React hook for 6R analysis

---

#### Components (43 files in `src/components/sixr/`)

**Main Components** (12 files):
- `ApplicationSelector.tsx`
- `ParameterSliders.tsx`
- `QualifyingQuestions.tsx`
- `RecommendationDisplay.tsx`
- `AnalysisProgress.tsx`
- `Tier1GapFillingModal.tsx` (PR #816)
- `BulkAnalysis.tsx`
- `ErrorBoundary.tsx`
- `LoadingState.tsx`
- `RetryWrapper.tsx`
- `index.ts`
- `types/ApplicationSelectorTypes.ts`

**Bulk Analysis** (9 files):
- `BulkAnalysis/index.tsx`
- `BulkAnalysis/components/*.tsx` (4 files)
- `BulkAnalysis/utils/analysisUtils.ts`
- `BulkAnalysis/types.ts`
- `BulkAnalysis/hooks/useBulkAnalysis.ts`
- `BulkAnalysis/index.barrel.ts`

**Analysis History** (15 files):
- `AnalysisHistory/index.tsx`
- `AnalysisHistory/components/*.tsx` (7 files)
- `AnalysisHistory/utils/dateUtils.ts`
- `AnalysisHistory/types.ts`
- `AnalysisHistory/hooks/*.ts` (3 files)
- `AnalysisHistory/constants.ts`

**Shared Components** (4 files):
- `components/ApplicationSelectionActions.tsx`
- `components/ApplicationTable.tsx`
- `components/FilterPanel.tsx`
- `components/QueueManagement.tsx`

**Hooks** (2 files):
- `hooks/useApplicationFilters.ts`
- `hooks/useApplicationSelection.ts`

---

#### Types (50+ files in `src/types/api/sixr-strategy/`)

**Shared Types** (13 files):
- `shared/index.ts`
- `shared/base-types.ts`
- `shared/flow-*.ts` (10 files covering state, status, management, integration, analytics, notifications)

**Decommission Strategy Types** (28 files):
- `decommission/index.ts`
- `decommission/*.ts` (27 files covering analytics, approval, business processes, compliance, cutover, data migration, execution plans, risks, stakeholders, timeline, validation)

**Assessment & Modernize Types** (2 files):
- `assessment/index.ts`
- `modernize/index.ts`

**Main Index**: `index.ts`

---

#### Tests (2 files)

- `__tests__/QualifyingQuestions.test.tsx`
- `__tests__/ParameterSliders.test.tsx`

---

## Request/Response Schemas

### Pydantic Schemas (Backend)

**Location**: `backend/app/schemas/sixr_analysis.py`

#### Enums

\`\`\`python
class ApplicationType(str, Enum):
    CUSTOM = "custom"
    COTS = "cots"
    HYBRID = "hybrid"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_INPUT = "requires_input"

class QuestionType(str, Enum):
    TEXT = "text"
    SELECT = "select"
    MULTISELECT = "multiselect"
    FILE_UPLOAD = "file_upload"
    BOOLEAN = "boolean"
    NUMERIC = "numeric"
\`\`\`

#### Request Schemas

\`\`\`python
class SixRParameterBase(BaseModel):
    business_value: float = Field(default=5.0, ge=1.0, le=10.0)
    technical_complexity: float = Field(default=5.0, ge=1.0, le=10.0)
    migration_urgency: float = Field(default=5.0, ge=1.0, le=10.0)
    compliance_requirements: float = Field(default=5.0, ge=1.0, le=10.0)
    cost_sensitivity: float = Field(default=5.0, ge=1.0, le=10.0)
    risk_tolerance: float = Field(default=5.0, ge=1.0, le=10.0)
    innovation_priority: float = Field(default=5.0, ge=1.0, le=10.0)
    application_type: ApplicationType = ApplicationType.CUSTOM

class SixRAnalysisRequest(BaseModel):
    application_ids: List[UUID]
    initial_parameters: Optional[SixRParameterBase] = None
    analysis_name: Optional[str] = None
\`\`\`

See full schemas in `backend/app/schemas/sixr_analysis.py`

---

## Data Flow

### Standard Analysis Flow

\`\`\`
1. User selects applications
   ↓
2. POST /6r/analyze
   - Create SixRAnalysis record
   - Create initial SixRAnalysisParameters
   - Generate qualifying questions
   - Start background analysis task
   ↓
3. Background Task (TenantScopedAgentPool)
   - Analyze application data
   - Generate SixRRecommendation
   - Update analysis status
   ↓
4. GET /6r/{analysis_id}
   - Fetch analysis status
   - Return recommendation if complete
   ↓
5. [Optional] PUT /6r/{analysis_id}/parameters
   - Update parameters
   - Create new SixRIteration
   - Trigger re-analysis
   ↓
6. GET /6r/{analysis_id}/recommendation
   - Fetch final recommendation
   - Display 6R strategy to user
\`\`\`

### Tier 1 Gap Filling Flow (PR #816)

\`\`\`
1. Analysis detects missing critical fields
   ↓
2. Analysis status → 'requires_input'
   - tier1_gaps_by_asset populated
   - retry_after_inline = true
   ↓
3. Frontend displays Tier1GapFillingModal
   ↓
4. User fills in missing fields
   ↓
5. POST /6r/{analysis_id}/inline-answers
   - Update asset record directly
   - Analysis automatically resumes
\`\`\`

---

## Dependencies

### Backend Dependencies

- **FastAPI**: REST API framework
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Request/response validation
- **litellm**: LLM integration (via TenantScopedAgentPool)
- **CrewAI**: Agent orchestration (strategy crew)

### Frontend Dependencies

- **React**: UI framework
- **TanStack Query**: Data fetching and caching
- **TypeScript**: Type safety

---

## Notes on Deprecation

### Deprecation Warnings Added (Phase 1 Complete)

The frontend API client (`src/lib/api/sixr.ts`) includes deprecation warnings in browser console:

\`\`\`
⚠️ DEPRECATION WARNING: sixrApi

📋 Use assessmentFlowApi instead for all 6R recommendation workflows.

📖 Migration Details:
   - Plan: /docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md
   - Issue: #837 (Phase 1)
   - Parent: #611
\`\`\`

### Timeline

- **Phase 1** (Complete): Documentation and deprecation warnings
- **Phase 2-3** (Weeks 1-2): Enable Assessment Flow with MFO, migrate frontend
- **Phase 4** (Week 3): Remove backend 6R Analysis code
- **Phase 5** (Week 4): Remove frontend 6R Analysis code
- **Phase 6-7** (Weeks 4-5): Complete features, verification

---

## Related Documentation

- **Detailed Frontend Analysis**: `/docs/planning/SIXR_ANALYSIS_CURRENT_STATE_FRONTEND_ONLY.md`
- **Migration Plan**: `/docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md`
- **ADR-006**: Master Flow Orchestrator architecture
- **ADR-012**: Flow Status Management Separation
- **Issue #837**: Assessment Flow MFO Migration Phase 1
- **Issue #611**: Assessment Flow Complete - Treatments Visible
- **PR #816**: Two-Tier Inline Gap-Filling implementation

---

**Document Status**: Phase 1 Complete
**Last Updated**: 2025-10-28
**Next Phase**: Phase 2 - Enable Assessment Flow with MFO Integration
