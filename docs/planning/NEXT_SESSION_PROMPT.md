# Session Handoff Prompt: Assessment Architecture & Enrichment Pipeline Implementation

**Purpose**: This document provides complete context for a new Claude Code session to implement the comprehensive solution for assessment architecture and enrichment pipeline gaps.

**Date Created**: October 15, 2025
**Session ID**: Continue from context limit
**Phase**: Ready for Phase 1 Implementation (Database & Data Model)

---

## Executive Context

You are tasked with implementing a **comprehensive, long-term architectural solution** for 9 identified gaps in the asset enrichment and assessment pipeline. This is NOT a band-aid fix but a proper architectural implementation addressing root causes.

### Vision

Create a fully automated, multi-asset-type enrichment and assessment pipeline where:
- Assets automatically enrich through discovery/collection/bulk import
- Canonical application deduplication happens universally
- Assessment flow seamlessly handles multiple asset types
- Users have full visibility into readiness, blockers, and progress
- AI agents automatically populate enrichment tables

### Critical Architectural Principles (MUST FOLLOW)

Per CLAUDE.md and ADR requirements:

1. **NO Band-Aid Solutions**: Dig deep to understand root causes, fix underlying problems regardless of time required. Correctness over expediency.

2. **Prefer Modifying Existing Code**: Check existing code and Git history before adding new implementations. Extend/refactor existing patterns rather than creating new ones.

3. **Seven-Layer Enterprise Architecture**: This is REQUIRED for enterprise resilience, not over-engineering:
   - API Layer (FastAPI routes)
   - Service Layer (business logic)
   - Repository Layer (data access)
   - Model Layer (SQLAlchemy/Pydantic)
   - Cache Layer (performance)
   - Queue Layer (async processing)
   - Integration Layer (external services)

4. **ADR Compliance (Non-Negotiable)**:
   - **ADR-006**: All flows must register with Master Flow Orchestrator
   - **ADR-015**: Use `TenantScopedAgentPool` for persistent agents
   - **ADR-024**: Use `TenantMemoryManager` for agent learning (CrewAI memory DISABLED)
   - **ADR-027**: Use `FlowTypeConfig` pattern for phase management
   - **LLM Tracking**: ALL LLM calls use `multi_model_service.generate_response()`

5. **Field Naming Convention**: ALWAYS use `snake_case` for ALL field names (backend and frontend). NO camelCase.

6. **API Request Patterns**: POST/PUT/DELETE use request body, NEVER query parameters.

7. **Multi-Tenant Isolation**: ALL queries scoped by `client_account_id` + `engagement_id`.

---

## Problem Statement: 9 Identified Gaps

### P0 Gaps (Critical Blockers)

**Gap #1: Assessment Applications Endpoint Lacks Canonical Grouping**
- Location: `backend/app/api/v1/master_flows/master_flows_assessment.py:199-331`
- Issue: Endpoint EXISTS but returns flat asset list using Discovery metadata
- Impact: Users see "3 assets" when it should show "1 application (3 assets)"
- Root Cause: Doesn't use `canonical_applications` and `collection_flow_applications` junction table

**Gap #2: Assessment Blockers Invisible**
- Issue: Backend populates `assessment_blockers` and `completeness_score` correctly
- Frontend: NO UI component displays this data
- Impact: Users confused: "Why can't I start assessment?"
- Files: `src/pages/assessment/AssessmentFlowOverview.tsx` has no readiness widget

**Gap #3: Assessment Data Model Semantic Mismatch**
- Issue: `assessment_flows.selected_application_ids` stores ASSET UUIDs (not application UUIDs)
- Impact: Semantic confusion, inefficient queries, no grouping
- Root Cause: Data model didn't evolve with Collection's multi-asset-type support

### P1 Gaps (High Impact)

**Gap #4: Canonical Linkage Missing in Bulk Import**
- Location: `backend/app/api/v1/endpoints/collection.py:276-333`
- Issue: Bulk import creates assets but NO canonical deduplication
- Missing: `CanonicalApplication.find_or_create_canonical()` call
- Missing: `collection_flow_applications` entries

**Gap #5: Enrichment Tables Not Auto-Populated**
- Issue: 7 enrichment models EXIST but remain empty (manual entry only)
- Tables: `asset_compliance_flags`, `asset_licenses`, `asset_vulnerabilities`, `asset_resilience`, `asset_dependencies`, `asset_product_links`, `asset_field_conflicts`
- Need: AI agent pipeline to auto-populate after asset creation

**Gap #6: Collection → Assessment Handoff Incomplete**
- Location: `backend/app/services/flow_commands.py: create_assessment_flow()`
- Missing: Canonical application resolution, asset grouping, enrichment status, readiness summary

### P2 Gaps (Enhanced UX)

**Gap #7: Asset-Application Grouping Not Visible**
- UI shows flat list of assets, not hierarchical application view

**Gap #8: Gap Remediation Not Automated**
- Users must fill EVERY gap manually; no AI suggestions from similar assets

**Gap #9: Assessment Progress Tracking Limited**
- Phase-level only; no attribute-level granularity (22 critical attributes)

---

## Solution Architecture Overview

```
UNIFIED ENRICHMENT PIPELINE
├─→ Discovery Flow, Collection Flow, Bulk Import
│   └─→ Asset Creation
│       └─→ CANONICAL DEDUPLICATION SERVICE (SHA-256 + 384D vector similarity)
│           └─→ collection_flow_applications link created
│               └─→ AUTOMATED ENRICHMENT PIPELINE
│                   ├─→ Compliance Agent → asset_compliance_flags
│                   ├─→ Licensing Agent → asset_licenses
│                   ├─→ Vulnerability Agent → asset_vulnerabilities
│                   ├─→ Resilience Agent → asset_resilience
│                   ├─→ Dependency Agent → asset_dependencies
│                   └─→ Product Matcher → asset_product_links
│                       └─→ ASSESSMENT READINESS CALCULATOR
│                           └─→ 22 Critical Attributes Check
│                               └─→ Update assessment_readiness, completeness_score, blockers
└─→ ASSESSMENT FLOW (Proper Data Model)
    ├─→ Initialization: Resolve asset_ids → canonical_application_ids
    ├─→ Build application_asset_groups structure
    ├─→ Calculate enrichment_status + readiness_summary
    └─→ Store in enhanced assessment_flows table
        └─→ FRONTEND UI ENHANCEMENTS
            ├─→ ApplicationGroupsWidget (hierarchical display)
            ├─→ ReadinessDashboard (blockers, completeness)
            └─→ ProgressTracker (attribute-level granularity)
```

---

## Key Technical Concepts

### 22 Critical Attributes for 6R Assessment

**Infrastructure (6)**:
1. Application Name (Required)
2. Technology Stack (Required)
3. Operating System (Required)
4. CPU Cores
5. Memory GB (Required)
6. Storage GB

**Application (8)**:
7. Business Criticality (Required)
8. Application Type (Required)
9. Architecture Pattern
10. Dependencies (Required)
11. User Base
12. Data Sensitivity (Required)
13. Compliance Requirements
14. SLA Requirements

**Business (4)**:
15. Business Owner (Required)
16. Annual Operating Cost
17. Business Value (Required)
18. Strategic Importance

**Technical Debt (4)**:
19. Code Quality Score
20. Last Update Date (Required)
21. Support Status
22. Known Vulnerabilities (Required)

**Readiness Scoring**:
- < 50% = LOW (Cannot proceed)
- 50-74% = MODERATE (Manual review required)
- ≥ 75% = GOOD (Ready for automated 6R analysis)

### Database Architecture

**Unified Assets Table** (`migration.assets` - 78 columns):
- Universal registry for all asset types: `server`, `database`, `application`, `device`, `network_device`
- Assessment fields: `assessment_readiness`, `assessment_blockers`, `completeness_score`, `assessment_readiness_score`
- Multi-tenant: `client_account_id`, `engagement_id`

**Canonical Applications** (`migration.canonical_applications`):
- Master application registry with deduplication
- SHA-256 hashing + 384D vector embeddings (pgvector)
- Method: `find_or_create_canonical()` for fuzzy matching

**Junction Table** (`migration.collection_flow_applications`):
- Links: `asset_id` → `canonical_application_id`
- Tracks: `deduplication_method`, `match_confidence`

**Assessment Flows** (`migration.assessment_flows`):
- CURRENT: `selected_application_ids` (actually stores asset IDs - semantic mismatch)
- NEW: `selected_asset_ids`, `selected_canonical_application_ids`, `application_asset_groups`, `enrichment_status`, `readiness_summary`

**7 Enrichment Tables** (all with FK to `assets.id`):
- `asset_compliance_flags`: Compliance scopes, data classification
- `asset_licenses`: Software licensing info
- `asset_vulnerabilities`: CVE tracking
- `asset_resilience`: HA, DR, backup config
- `asset_dependencies`: Relationship mapping
- `asset_product_links`: Vendor catalog matching
- `asset_field_conflicts`: Conflict resolution

---

## Implementation Plan (6 Weeks, 30 Days)

### Phase 1: Database & Data Model (Week 1) ← **START HERE**

**Days 1-2: Database Migration**
- [ ] Create `backend/alembic/versions/093_assessment_data_model_refactor.py`
- [ ] Convention: Use 3-digit prefix (e.g., `093_`, NOT `228e0eae6242_`)
- [ ] Must be idempotent with `IF EXISTS`/`IF NOT EXISTS`
- [ ] Add columns: `selected_asset_ids`, `selected_canonical_application_ids`, `application_asset_groups`, `enrichment_status`, `readiness_summary` to `assessment_flows`
- [ ] Add GIN indexes for JSONB performance
- [ ] Migrate existing data: `selected_application_ids` → `selected_asset_ids`
- [ ] Mark `selected_application_ids` as DEPRECATED with comment
- [ ] Test on Docker staging database: `docker exec -it migration_postgres psql -U postgres -d migration_db`

**Days 3-4: SQLAlchemy & Pydantic Models**
- [ ] Update `backend/app/models/assessment_flow/core_models.py` (AssessmentFlow model)
- [ ] Create Pydantic schemas in `backend/app/schemas/assessment_flow.py`:
  - `ApplicationAssetGroup`: canonical_application_id, canonical_application_name, asset_ids, asset_count, asset_types, readiness_summary
  - `EnrichmentStatus`: compliance_flags, licenses, vulnerabilities, resilience, dependencies, product_links, field_conflicts
  - `ReadinessSummary`: total_assets, ready, not_ready, in_progress, avg_completeness_score
- [ ] Update `AssessmentFlowCreate` schema with new fields
- [ ] Write unit tests: `backend/tests/backend/unit/schemas/test_assessment_flow.py`

**Day 5: Assessment Application Resolver Service**
- [ ] Create `backend/app/services/assessment/application_resolver.py`
- [ ] Class: `AssessmentApplicationResolver`
- [ ] Method: `resolve_assets_to_applications(asset_ids, collection_flow_id=None)` → List[ApplicationAssetGroup]
  - Query: `assets` ← `collection_flow_applications` ← `canonical_applications`
  - Group by: `canonical_application_id`
  - Fallback: Unmapped assets get `canonical_application_id=None`
- [ ] Method: `calculate_enrichment_status(asset_ids)` → Dict[str, int]
  - Count distinct `asset_id` in each enrichment table
- [ ] Method: `calculate_readiness_summary(asset_ids)` → Dict[str, Any]
  - Aggregate `assessment_readiness` counts + avg `assessment_readiness_score`
- [ ] Unit tests: `backend/tests/backend/unit/services/test_assessment_application_resolver.py`

### Phase 2: Backend Services & Endpoints (Week 2)

**Days 6-7: Enhance Assessment Applications Endpoint**
- [ ] Modify existing `backend/app/api/v1/master_flows/master_flows_assessment.py:199-331`
- [ ] Replace Discovery-based logic with `AssessmentApplicationResolver`
- [ ] Use `assessment_flow.application_asset_groups` if pre-computed, else compute on-the-fly
- [ ] Create NEW endpoint: `GET /master-flows/{flow_id}/assessment-readiness`
  - Return: asset-level readiness, missing attributes, blockers, actionable guidance
- [ ] Create NEW endpoint: `GET /master-flows/{flow_id}/assessment-progress`
  - Return: attribute-level progress by category (Infrastructure, Application, Business, Technical Debt)
- [ ] Update response schemas: `AssessmentApplicationsListResponse`, `AssessmentApplicationResponse`
- [ ] Integration tests: `backend/tests/backend/integration/api/test_assessment_endpoints.py`

**Days 8-9: Enhanced Assessment Initialization**
- [ ] Update `backend/app/services/flow_commands.py: create_assessment_flow()`
- [ ] Add canonical application resolution using `AssessmentApplicationResolver`
- [ ] Build `application_asset_groups` structure
- [ ] Calculate `enrichment_status` and `readiness_summary`
- [ ] Store in new assessment_flows fields
- [ ] Integration test: Collection → Assessment handoff with rich metadata

**Day 10: Canonical Deduplication in Bulk Import**
- [ ] Update `backend/app/api/v1/endpoints/collection.py:276-333`
- [ ] After asset creation, add call to `CanonicalApplication.find_or_create_canonical()`
- [ ] Create `collection_flow_applications` entries with `deduplication_method="bulk_import_auto"`
- [ ] Trigger enrichment pipeline for all created assets
- [ ] Test: Bulk import CSV → verify canonical deduplication + enrichment

### Phase 3: Automated Enrichment Pipeline (Week 3)

**Days 11-12: Enrichment Pipeline Framework**
- [ ] Create `backend/app/services/enrichment/auto_enrichment_pipeline.py`
- [ ] Class: `AutoEnrichmentPipeline`
- [ ] **CRITICAL ADR COMPLIANCE**:
  - Use `TenantScopedAgentPool` for persistent agents (ADR-015)
  - Integrate `TenantMemoryManager` for storing/retrieving learned patterns (ADR-024)
  - Set `memory=False` when creating CrewAI crews
- [ ] Method: `trigger_auto_enrichment(asset_ids)` → runs agents concurrently with `asyncio.gather()`
- [ ] Method: `_recalculate_readiness(asset_ids)` → update `assessment_readiness` after enrichment
- [ ] Add async task queue integration (Celery or similar) for production

**Days 13-15: Enrichment Agents Implementation**
- [ ] Create directory: `backend/app/services/enrichment/agents/`
- [ ] Implement 6 agents (each as separate file):
  1. `compliance_agent.py` → `asset_compliance_flags`
  2. `licensing_agent.py` → `asset_licenses`
  3. `vulnerability_agent.py` → `asset_vulnerabilities`
  4. `resilience_agent.py` → `asset_resilience`
  5. `dependency_agent.py` → `asset_dependencies`
  6. `product_matching_agent.py` → `asset_product_links`
- [ ] **Each agent MUST**:
  - Use `multi_model_service.generate_response()` for LLM calls (automatic tracking)
  - Store learned patterns via `TenantMemoryManager.store_learning()`
  - Retrieve similar patterns before processing via `TenantMemoryManager.retrieve_similar_patterns()`
  - Use persistent agent instances from `TenantScopedAgentPool`
- [ ] Unit tests for each agent: `backend/tests/backend/unit/services/enrichment/agents/`

**Day 16: Integration & Testing**
- [ ] Integrate enrichment pipeline into asset creation flow
- [ ] Test with 50+ sample assets (servers, databases, applications, network devices)
- [ ] Verify enrichment tables populated correctly
- [ ] Performance testing: 100 assets < 10 minutes

### Phase 4: Frontend UI Implementation (Week 4)

**Days 17-18: Application Groups Widget**
- [ ] Create `src/components/assessment/ApplicationGroupsWidget.tsx`
- [ ] Features:
  - Hierarchical display with collapsible groups
  - Show: `canonical_application_name`, asset count, asset types
  - Per-group readiness summary: X% ready (Y/Z assets)
  - Expanded view: List all assets under application with icons (Server, Database, Network)
  - Unmapped assets flagged with badge
- [ ] Use `snake_case` for all field names
- [ ] Component tests: `src/components/assessment/__tests__/ApplicationGroupsWidget.test.tsx`

**Days 19-20: Readiness Dashboard Widget**
- [ ] Create `src/components/assessment/ReadinessDashboardWidget.tsx`
- [ ] Features:
  - Summary cards: Ready, Not Ready, In Progress, Avg Completeness
  - Assessment Blockers section: Per-asset display of missing attributes
  - Critical attributes descriptions (22 attributes)
  - Progress bar for completeness score
  - "Collect Missing Data" button → navigate to Collection flow
- [ ] Component tests: `src/components/assessment/__tests__/ReadinessDashboardWidget.test.tsx`

**Day 21: Frontend Service Layer**
- [ ] Update `src/services/api/masterFlowService.ts`
- [ ] Add methods (all use `snake_case` fields):
  - `getAssessmentApplications(flow_id)`: Fetch application groups
  - `getAssessmentReadiness(flow_id)`: Fetch readiness data
  - `getAssessmentProgress(flow_id)`: Fetch progress data
- [ ] Ensure POST/PUT use request body (NOT query params)
- [ ] Add TypeScript interfaces matching backend schemas

**Day 22: Integration into Assessment Overview**
- [ ] Update `src/pages/assessment/AssessmentFlowOverview.tsx`
- [ ] Integrate `ApplicationGroupsWidget`
- [ ] Integrate `ReadinessDashboardWidget`
- [ ] Add loading states and error boundaries
- [ ] Test with real Assessment flows: `http://localhost:8081/assessment/{flow_id}`

### Phase 5: Testing & Validation (Week 5)

**Days 23-24: Integration Testing**
- [ ] E2E test: Discovery → Collection → Assessment (verify canonical grouping)
- [ ] E2E test: Bulk Import → Enrichment → Assessment (verify auto-population)
- [ ] Test multi-asset-type scenarios: server + database + network_device
- [ ] Test canonical deduplication: "SAP ERP" vs "SAP-ERP-Production" → same canonical app
- [ ] Test enrichment pipeline: 100+ assets

**Day 25: UI/UX Testing**
- [ ] Manual testing on `http://localhost:8081`
- [ ] Responsive design: mobile, tablet, desktop
- [ ] Accessibility testing (WCAG compliance)
- [ ] User acceptance testing with sample data

**Day 26: Performance & Load Testing**
- [ ] Load test: 500+ assets
- [ ] Query performance: `/assessment-applications` < 500ms (95th percentile)
- [ ] Enrichment pipeline: 100 assets < 10 minutes
- [ ] Frontend rendering: Assessment Overview < 2 seconds

**Day 27: Bug Fixes & Polish**
- [ ] Fix issues from testing phase
- [ ] Code review and refactoring
- [ ] Update documentation
- [ ] Prepare deployment checklist

### Phase 6: Deployment & Monitoring (Week 6)

**Day 28: Staging Deployment**
- [ ] Deploy database migration to staging: `docker exec -it migration_backend bash -c "cd backend && alembic upgrade head"`
- [ ] Deploy backend changes to staging
- [ ] Deploy frontend changes to staging
- [ ] Smoke test all endpoints

**Day 29: Production Deployment**
- [ ] Database migration to production
- [ ] Backend deployment (zero-downtime)
- [ ] Frontend deployment
- [ ] Verify all endpoints working

**Day 30: Monitoring & Support**
- [ ] Set up monitoring dashboards
- [ ] Configure alerts for errors
- [ ] Monitor LLM usage: Navigate to `/finops/llm-costs` to track enrichment agent costs
- [ ] Gather user feedback
- [ ] Document lessons learned

---

## Critical File Locations

### Backend Files to Modify/Create

**Database**:
- `backend/alembic/versions/093_assessment_data_model_refactor.py` (NEW)

**Models**:
- `backend/app/models/assessment_flow/core_models.py` (MODIFY: lines 78-83)
- `backend/app/schemas/assessment_flow.py` (MODIFY: add new schemas)

**Services**:
- `backend/app/services/assessment/application_resolver.py` (NEW)
- `backend/app/services/flow_commands.py` (MODIFY: create_assessment_flow)
- `backend/app/services/enrichment/auto_enrichment_pipeline.py` (NEW)
- `backend/app/services/enrichment/agents/compliance_agent.py` (NEW)
- `backend/app/services/enrichment/agents/licensing_agent.py` (NEW)
- `backend/app/services/enrichment/agents/vulnerability_agent.py` (NEW)
- `backend/app/services/enrichment/agents/resilience_agent.py` (NEW)
- `backend/app/services/enrichment/agents/dependency_agent.py` (NEW)
- `backend/app/services/enrichment/agents/product_matching_agent.py` (NEW)

**Endpoints**:
- `backend/app/api/v1/master_flows/master_flows_assessment.py` (MODIFY: lines 199-331, ADD new endpoints)
- `backend/app/api/v1/endpoints/collection.py` (MODIFY: lines 276-333)

### Frontend Files to Modify/Create

**Components**:
- `src/components/assessment/ApplicationGroupsWidget.tsx` (NEW)
- `src/components/assessment/ReadinessDashboardWidget.tsx` (NEW)

**Pages**:
- `src/pages/assessment/AssessmentFlowOverview.tsx` (MODIFY: integrate new widgets)

**Services**:
- `src/services/api/masterFlowService.ts` (MODIFY: add new methods)

### Documentation Reference

**MUST READ BEFORE STARTING**:
- `docs/planning/COMPREHENSIVE_SOLUTION_APPROACH.md` - Full solution details
- `docs/planning/ASSET_ENRICHMENT_COMPLETE_ARCHITECTURE.md` - Database architecture
- `docs/adr/006-master-flow-orchestrator.md` - Master Flow Orchestrator pattern
- `docs/adr/015-persistent-multi-tenant-agent-architecture.md` - Persistent agents
- `docs/adr/024-tenant-memory-manager-architecture.md` - TenantMemoryManager
- `docs/analysis/Notes/000-lessons.md` - Critical architectural lessons
- `docs/analysis/Notes/coding-agent-guide.md` - Implementation patterns
- `/.claude/agent_instructions.md` - Subagent requirements

---

## Success Metrics

**Functional Metrics**:
- [ ] 100% of Assessment flows display selected applications correctly
- [ ] 100% of assets show assessment readiness status
- [ ] 90%+ of bulk imported applications deduplicated via canonical registry
- [ ] 70%+ of assets have enrichment data auto-populated within 24 hours
- [ ] 0 critical bugs in production for 7 days

**Performance Metrics**:
- [ ] `/assessment-applications` endpoint responds < 500ms (95th percentile)
- [ ] Enrichment pipeline processes 100 assets < 10 minutes
- [ ] UI loads Assessment Overview < 2 seconds

**User Experience Metrics**:
- [ ] Users can identify missing data in < 30 seconds
- [ ] 80%+ reduction in support tickets for "Why can't I assess?"
- [ ] 60%+ faster gap remediation with AI suggestions

---

## Development Environment Setup

**CRITICAL: Docker-Only Development (ADR-010)**:
- ALL development MUST occur within Docker containers
- NO local services (Python, Node.js, PostgreSQL) on dev machine
- Use `docker exec` for all command execution

**Start Services**:
```bash
cd config/docker && docker-compose up -d
```

**Access Containers**:
```bash
# Backend
docker exec -it migration_backend bash

# Database
docker exec -it migration_postgres psql -U postgres -d migration_db

# Frontend logs
docker logs migration_frontend -f
```

**Run Alembic Migration**:
```bash
docker exec -it migration_backend bash -c "cd backend && alembic upgrade head"
```

**Access Application**:
- Frontend: http://localhost:8081 (NOT 3000)
- Backend: http://localhost:8000

---

## Common Pitfalls to Avoid

1. **DO NOT** use camelCase field names - ALWAYS `snake_case`
2. **DO NOT** use query parameters for POST/PUT/DELETE - use request body
3. **DO NOT** create new agent instances - use `TenantScopedAgentPool`
4. **DO NOT** enable CrewAI memory - use `TenantMemoryManager` (set `memory=False`)
5. **DO NOT** make direct LLM calls - use `multi_model_service.generate_response()`
6. **DO NOT** forget multi-tenant scoping - `client_account_id` + `engagement_id`
7. **DO NOT** skip pre-commit checks - run at least once before `--no-verify`
8. **DO NOT** assume API endpoints exist - verify in `router_registry.py`

---

## Next Steps for New Session

**Immediate Action**:
1. Read this document completely
2. Read `docs/planning/COMPREHENSIVE_SOLUTION_APPROACH.md` for full solution details
3. Read relevant ADRs: 006, 015, 024, 027
4. Start Phase 1, Day 1: Create database migration

**First Command**:
```bash
# Find next migration number
docker exec -it migration_backend bash -c "ls -1 backend/alembic/versions/ | grep '^[0-9]' | tail -1"

# Create migration file
docker exec -it migration_backend bash -c "cd backend && alembic revision -m 'assessment_data_model_refactor'"
```

**First Task**:
Create `backend/alembic/versions/093_assessment_data_model_refactor.py` following the SQL provided in `COMPREHENSIVE_SOLUTION_APPROACH.md` Solution 1.

---

**Good luck! Remember: Correctness over expediency. Dig deep, fix root causes, and follow ADR patterns.**
