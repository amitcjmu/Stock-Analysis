# Collection Gaps Phase 2 Implementation Plan

## Phase 1 Implementation Status

### ✅ COMPLETED in Phase 1

#### Backend Infrastructure
1. **Database Schema** (072_collection_gaps_phase1_schema.py)
   - ✅ vendor_products_catalog table
   - ✅ tenant_vendor_products table
   - ✅ tenant_vendor_product_versions table
   - ✅ asset_vendor_product_links table
   - ✅ lifecycle_milestones table
   - ✅ asset_resilience table
   - ✅ maintenance_windows table
   - ✅ blackout_periods table
   - ✅ governance_requirements table
   - ✅ governance_exceptions table
   - ✅ unified_vendor_products materialized view

2. **Models**
   - ✅ VendorProductsCatalog model
   - ✅ AssetResilience model
   - ✅ MaintenanceWindows model
   - ✅ Governance model
   - ✅ API models in collection_gaps.py

3. **Repositories**
   - ✅ VendorProductRepository
   - ✅ ResilienceRepository
   - ✅ MaintenanceWindowRepository
   - ✅ GovernanceRepository
   - ✅ CollectionFlowRepository

4. **Services**
   - ✅ ResponseMappingService (with modular mappers)
   - ✅ LifecycleEnrichmentService
   - ✅ AgentToolRegistry

5. **Partial API Implementation**
   - ✅ Collection flows handlers (get gaps, questionnaires, responses)
   - ✅ Router registration in router_imports.py

#### Frontend Components
1. **New Components Created**
   - ✅ MaintenanceWindowForm
   - ✅ MaintenanceWindowTable
   - ✅ TechnologyPicker
   - ✅ CompletenessDashboard

2. **AdaptiveForm Enhancements**
   - ✅ date_input field type validation
   - ✅ numeric_input field type validation
   - ✅ multi_select field type validation
   - ✅ technology_selection field type validation

3. **API Service Methods**
   - ✅ Maintenance window CRUD methods
   - ✅ Technology search/normalize methods
   - ✅ Completeness metrics methods
   - ✅ Bulk response submission

### ❌ MISSING from Phase 1 (Must Complete in Phase 2)

#### Critical Backend Endpoints
1. **vendor_products.py router** - MISSING ENTIRELY
   - GET /api/v1/collection/vendor-products (search catalog)
   - POST /api/v1/collection/vendor-products (create entry)
   - PUT /api/v1/collection/vendor-products/{id} (update)
   - DELETE /api/v1/collection/vendor-products/{id}
   - POST /api/v1/collection/vendor-products/normalize

2. **maintenance_windows.py router** - MISSING ENTIRELY
   - GET /api/v1/collection/maintenance-windows
   - POST /api/v1/collection/maintenance-windows
   - PUT /api/v1/collection/maintenance-windows/{id}
   - DELETE /api/v1/collection/maintenance-windows/{id}

3. **governance.py router** - MISSING ENTIRELY
   - GET /api/v1/collection/governance/requirements
   - POST /api/v1/collection/governance/requirements
   - GET /api/v1/collection/governance/exceptions
   - POST /api/v1/collection/governance/exceptions

#### Frontend UI Pages
1. **Collection Gaps Dashboard** - NO UI ACCESS
   - Entry point to access Phase 1 features
   - Navigation to sub-features
   - Overall completeness visualization

2. **Vendor Products Management Page** - NO UI
   - Search and browse catalog
   - Add custom vendor products
   - Link products to assets
   - View lifecycle dates

3. **Maintenance Windows Page** - NO UI
   - List existing windows
   - Create/edit windows using existing components
   - Calendar view

4. **Governance Management Page** - NO UI
   - View compliance requirements
   - Submit exceptions
   - Track approval status

#### Integration Issues
1. **Frontend-Backend Disconnection**
   - Components exist but no pages use them
   - API methods in collection-flow.ts but no UI calls them
   - No navigation to access features

2. **Agent Tool Integration**
   - AgentToolRegistry exists but tools not fully registered
   - Gap analysis tool needs lifecycle date detection
   - Questionnaire generation needs new field types

## Phase 2 Implementation Plan

### Week 1: Complete Missing Phase 1 Backend

#### Router Creation & Registration
- [ ] Create vendor_products.py router with endpoints:
  - GET /collection/vendor-products (search)
  - POST /collection/vendor-products (create)
  - PUT /collection/vendor-products/{id} (update)
  - DELETE /collection/vendor-products/{id} (delete)
  - POST /collection/vendor-products/normalize
- [ ] Create maintenance_windows.py router with CRUD endpoints
- [ ] Create governance.py router aligned with actual model names (approval_requests/migration_exceptions)
- [ ] Register all routers in router_imports.py and router_registry.py
- [ ] Fix __init__.py import errors

#### Critical Fixes & Infrastructure
- [ ] Feature flag gating:
  - Enforce `collection.gaps.v1` on questionnaire generation
  - Gate submit responses and gaps/completeness endpoints
- [ ] Fix collection_flows.py imports:
  - Replace `from app.models.assets import Asset` with `from app.models.asset import Asset`
  - Add `from typing import Any, Dict`
  - Guard status enum: `status = getattr(flow.status, 'value', flow.status) or 'unknown'`
- [ ] Lifecycle mapping integrity:
  - Require `tenant_version_id` or `catalog_version_id` in map_lifecycle_dates
  - Reject requests lacking version context
- [ ] Implement map_product_version handler for tenant_product_versions
- [ ] Add completeness endpoints:
  - GET `/api/v1/collection/flows/{flowId}/completeness`
  - POST `/api/v1/collection/flows/{flowId}/completeness/refresh`
- [ ] Initialize AgentToolRegistry on app startup with logging
- [ ] Add comprehensive integration tests

### Week 2: Frontend UI Implementation & Wiring

#### Field Type Alignment
- [ ] Fix field type mismatch:
  - Server emits `date`/`number`, FormField expects `date_input`/`numeric_input`
  - Either normalize server-side or add support for both in FormField

#### Pages and Navigation
- [ ] Create "Collection Gaps" dashboard page with navigation from collection flow
- [ ] Mount CompletenessDashboard calling get/refresh completeness endpoints
- [ ] Create MaintenanceWindows page using MaintenanceWindowForm/Table tied to CRUD API
- [ ] Integrate TechnologyPicker for `fieldType === 'technology_selection'`
- [ ] Create GovernanceManagement page for compliance
- [ ] Add navigation button/tab from main collection flow

#### Service Integration
- [ ] Replace mock reads with actual API calls
- [ ] Ensure all calls carry tenant headers
- [ ] Preserve snake_case field naming
- [ ] Wire questionnaire generation trigger from UI
- [ ] Show generated sections and submit batch responses to /responses endpoint

### Week 3: Agents & Data Quality

#### Agent Tool Integration
- [ ] Update GapAnalysisTool for lifecycle date detection
- [ ] Update QuestionnaireGenerationTool for new field types
- [ ] Ensure question IDs match mapping registry keys for multi-table writes
- [ ] Validate agent tools registered on startup

#### Data Management
- [ ] Add materialized view refresh (scheduled job or manual endpoint)
- [ ] Dependency mapping UI and persistence
- [ ] Automated lifecycle enrichment from external sources
- [ ] Bulk import/export for vendor products

### Week 4: Monitoring, Testing & Performance

#### Monitoring & Alerting
- [ ] Create dashboards per docs:
  - Lifecycle coverage metrics
  - Response mapping failure rate
  - Batch latency P95
  - Go/no-go signals
- [ ] Set up alerting thresholds

#### Integration Tests
- [ ] E2E test: Lifecycle milestones with version linkage
- [ ] E2E test: RTO/RPO upsert flows
- [ ] E2E test: Maintenance windows CRUD
- [ ] E2E test: Vendor normalization
- [ ] E2E test: Completeness endpoints
- [ ] E2E test: AgentToolRegistry availability on startup

#### Performance Optimization
- [ ] Verify batch boundaries match BATCH_CONFIG (default 500, max 1000)
- [ ] Implement pagination where applicable
- [ ] Add timeouts and circuit breakers
- [ ] Optimize database queries with proper indexing

## Immediate Next Steps

1. **Fix Critical Import Error**
   - Create the 3 missing router files immediately
   - Even if minimal, prevents application crash

2. **Create Access UI**
   - Add "Collection Gaps" button to collection flow page
   - Create dashboard with cards for each feature area

3. **Test Data Seeding**
   - Script to populate sample vendor products
   - Test maintenance windows
   - Sample governance requirements

## Success Metrics

### Phase 1 Completion
- [ ] All 3 missing routers implemented
- [ ] All endpoints accessible via API
- [ ] UI pages created for all features
- [ ] Frontend components integrated with backend
- [ ] Basic CRUD operations working

### Phase 2 Completion
- [ ] Dependency mapping functional
- [ ] Automated enrichment working
- [ ] Bulk operations supported
- [ ] Approval workflows active
- [ ] 90% completeness tracking accuracy

## Risk Mitigation

1. **Import Errors** - Create stub routers immediately
2. **UI Accessibility** - Add temporary dev menu if needed
3. **Data Migration** - Create rollback scripts
4. **Performance** - Add pagination early
5. **Testing** - Automated tests for each endpoint

## Dependencies

- PostgreSQL with pgvector extension
- FastAPI async support
- React Query for polling
- TanStack Table for data grids
- Material-UI components

## Notes

The Phase 1 backend is 80% complete but has critical missing pieces that prevent the features from being accessible. The frontend has good components but no pages to use them. Phase 2 must first complete Phase 1's missing pieces before adding advanced features.