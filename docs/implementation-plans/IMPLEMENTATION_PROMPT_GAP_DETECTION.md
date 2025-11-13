# Implementation Prompt: Intelligent Multi-Layer Gap Detection System

## Context

You are continuing implementation of the Intelligent Multi-Layer Gap Detection system for a cloud migration assessment platform. This session focuses on **orchestrating specialized CC agents** to implement the solution design approved in GitHub Issue #980.

**Your Role**: You are the **orchestration agent**. You do NOT write code directly. Instead, you:
1. Break down tasks into agent-appropriate work packages
2. Invoke specialized agents (python-crewai-fastapi-expert, pgvector-data-architect, devsecops-linting-engineer, qa-playwright-tester)
3. Coordinate iterations until all tests pass
4. Orchestrate pre-commit checks and PR creation

---

## Background - What Was Done Previously

### Investigation Phase (Completed - Week 1)
- **Spike 1-5** completed and documented in GitHub issues #975-#979
- **Root Cause Identified**: Gap detection only checks 22 hardcoded columns, ignoring enrichments, JSONB, architecture standards
- **Solution Design Created**: Issue #980 with comprehensive implementation plan
- **GPT-5 Review Completed**: All 8 recommendations accepted and incorporated

### Key Findings from Spikes
1. **Assessment Data Flow**: Application-centric architecture with CanonicalApplication + Assets
2. **Enrichment Tables**: 7 tables (AssetResilience, AssetComplianceFlags, etc.) eager-loaded but unused
3. **Architecture Standards**: Tables exist but not integrated with gap detection
4. **Questionnaire Deduplication**: Working correctly (PR #969)
5. **Current Gap Detection**: Hardcoded 22 attributes in `helpers.py:28-50`

### Existing Code to Reuse (Critical Discovery)
- **`ProgrammaticGapScanner`** (`backend/app/services/collection/gap_scanner/scanner.py`):
  - Already has tenant scoping (client_account_id + engagement_id)
  - Already checks 22 hardcoded attributes via `CriticalAttributesDefinition`
  - Already persists to `CollectionDataGap` table
  - **Needs refactoring**: Replace hardcoded logic with new inspectors

- **`IncrementalGapAnalyzer`** (`backend/app/services/collection/incremental_gap_analyzer.py`):
  - Analyzes gaps from questionnaire responses
  - Fast mode + thorough mode (with dependency traversal)
  - **Can be composed**: Use shared inspectors for gap identification

### GPT-5's Review Recommendations (All Accepted)
1. ✅ Add tenant scoping (client_account_id) to all queries
2. ✅ Reuse/compose with existing ProgrammaticGapScanner and IncrementalGapAnalyzer
3. ✅ Make all inspectors consistently async
4. ✅ Add optional agentic refinement via multi_model_service
5. ✅ Integrate via service layer (AssessmentFlowChildService)
6. ✅ Add frontend compatibility shim for gradual rollout
7. ✅ Populate standards templates with client_account_id
8. ✅ Clamp scores to avoid NaN/Infinity

---

## Implementation Plan - Your Orchestration Roadmap

### Week 2: Core Infrastructure (Days 6-10)

#### **Day 6: Audit & Architecture Design**

**Your Tasks (Orchestration)**:
1. Use `mcp__serena__*` tools to audit existing gap detection code:
   - Read `backend/app/services/collection/gap_scanner/scanner.py`
   - Read `backend/app/services/collection/gap_scanner/gap_detector.py`
   - Read `backend/app/services/collection/critical_attributes.py`
   - Read `backend/app/api/v1/master_flows/assessment/helpers.py`
   - Document current hardcoded logic locations

2. Design shared inspector architecture (create design doc):
   - Location: `docs/design/shared-inspector-architecture.md`
   - Specify how ProgrammaticGapScanner and GapAnalyzer will share inspectors
   - Define interfaces and module boundaries
   - Include tenant scoping requirements

**Deliverables**:
- Audit report documenting existing code
- Architecture design doc for shared inspectors
- List of files to be created/modified

**Acceptance Criteria**:
- [ ] All existing gap detection code locations identified
- [ ] Composition strategy documented
- [ ] No code written yet (design only)

---

#### **Day 7: Inspector Implementation (Columns & Enrichments)**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent** with this task:
   ```
   TASK: Implement ColumnInspector and EnrichmentInspector for multi-layer gap detection

   CONTEXT:
   - Read design doc: docs/design/shared-inspector-architecture.md
   - Read GPT-5's code examples in GitHub issue #980 comment
   - Must be ASYNC (async def inspect)
   - Must include tenant scoping (client_account_id, engagement_id)
   - Must use Pydantic models for reports
   - Must exclude system columns (id, created_at, etc.)

   FILES TO CREATE:
   - backend/app/services/gap_detection/__init__.py
   - backend/app/services/gap_detection/inspectors/__init__.py
   - backend/app/services/gap_detection/inspectors/base.py
   - backend/app/services/gap_detection/inspectors/column_inspector.py
   - backend/app/services/gap_detection/inspectors/enrichment_inspector.py
   - backend/app/services/gap_detection/schemas.py (Pydantic models)

   PYDANTIC MODELS TO CREATE (in schemas.py):
   - ColumnGapReport (missing_attributes, empty_attributes, null_attributes)
   - EnrichmentGapReport (missing_tables, incomplete_tables, completeness_score)

   CODE STYLE:
   - Follow GPT-5's code examples from issue #980
   - Add JSON safety: clamp completeness_score with max(0.0, min(1.0, float(score)))
   - Add structured logging with asset_id, inspector type
   - Use SQLAlchemy 2.0 async patterns

   TESTS TO CREATE:
   - backend/tests/services/gap_detection/test_column_inspector.py
   - backend/tests/services/gap_detection/test_enrichment_inspector.py
   - Fixtures: backend/tests/services/gap_detection/fixtures.py

   ACCEPTANCE CRITERIA:
   - All inspectors are async
   - Tenant scoping included (even if not used yet)
   - Unit tests >90% coverage
   - Performance: <50ms per asset inspection
   ```

2. **After agent completes**: Invoke **qa-playwright-tester agent** to validate:
   ```
   TASK: Verify inspector implementation with unit tests

   RUN:
   cd backend && python -m pytest tests/services/gap_detection/test_column_inspector.py -v
   cd backend && python -m pytest tests/services/gap_detection/test_enrichment_inspector.py -v

   VERIFY:
   - All tests pass
   - Coverage >90%
   - No import errors
   - Async methods work correctly

   IF FAILURES: Report issues back to orchestration agent
   ```

3. **If QA agent reports failures**: Re-invoke python-crewai-fastapi-expert to fix issues, then re-test

4. **Once tests pass**: Proceed to Day 8

**Deliverables**:
- ColumnInspector implementation (async, tenant-scoped)
- EnrichmentInspector implementation (checks all 7 tables)
- Pydantic schemas for gap reports
- Unit tests with >90% coverage

**Acceptance Criteria**:
- [ ] ColumnInspector scans all non-system columns
- [ ] EnrichmentInspector checks all 7 enrichment tables
- [ ] All methods are async
- [ ] Unit tests pass
- [ ] Code follows GPT-5's examples

---

#### **Day 8: Inspector Implementation (JSONB, Application, Standards)**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent**:
   ```
   TASK: Implement JSONBInspector, ApplicationInspector, and StandardsInspector

   CONTEXT:
   - Read design doc: docs/design/shared-inspector-architecture.md
   - Read GPT-5's code examples in GitHub issue #980
   - StandardsInspector queries EngagementArchitectureStandard table
   - Must be async with tenant scoping

   FILES TO CREATE:
   - backend/app/services/gap_detection/inspectors/jsonb_inspector.py
   - backend/app/services/gap_detection/inspectors/application_inspector.py
   - backend/app/services/gap_detection/inspectors/standards_inspector.py

   PYDANTIC MODELS TO ADD (in schemas.py):
   - JSONBGapReport (missing_keys, empty_values, completeness_score)
   - ApplicationGapReport (missing_metadata, incomplete_tech_stack, missing_business_context)
   - StandardViolation (standard_name, requirement_type, violation_details, is_mandatory)
   - StandardsGapReport (violated_standards, missing_mandatory_data, override_required)

   JSONB INSPECTOR:
   - Accepts expected_keys: Dict[str, List[str]] (JSONB field → required keys)
   - Traverses custom_attributes, technical_details, metadata
   - Clamps completeness_score to [0.0, 1.0]

   STANDARDS INSPECTOR:
   - Requires AsyncSession (queries database)
   - Fetches EngagementArchitectureStandard with tenant scoping:
     WHERE client_account_id = ? AND engagement_id = ?
   - Validates asset against minimum_requirements
   - Returns violations with override_available flag

   TESTS TO CREATE:
   - backend/tests/services/gap_detection/test_jsonb_inspector.py
   - backend/tests/services/gap_detection/test_application_inspector.py
   - backend/tests/services/gap_detection/test_standards_inspector.py

   ACCEPTANCE CRITERIA:
   - JSONBInspector handles nested structures
   - ApplicationInspector validates CanonicalApplication metadata
   - StandardsInspector queries with tenant scoping
   - All tests pass with >90% coverage
   ```

2. **After agent completes**: Invoke **qa-playwright-tester** for validation

3. **Iterate until all tests pass**

**Deliverables**:
- 3 additional inspectors implemented
- Pydantic models for all gap report types
- Integration tests with database fixtures

**Acceptance Criteria**:
- [ ] JSONBInspector handles nested JSONB
- [ ] ApplicationInspector validates CanonicalApplication
- [ ] StandardsInspector queries with tenant scoping
- [ ] All unit tests pass

---

#### **Day 9: Requirements Engine Implementation**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent**:
   ```
   TASK: Implement RequirementsEngine with context-aware requirements matrix

   CONTEXT:
   - Read design doc: docs/design/shared-inspector-architecture.md
   - Read GPT-5's code examples in GitHub issue #980
   - Must use LRU caching (@lru_cache decorator)
   - Must merge requirements from multiple contexts

   FILES TO CREATE:
   - backend/app/services/gap_detection/requirements/__init__.py
   - backend/app/services/gap_detection/requirements/requirements_engine.py
   - backend/app/services/gap_detection/requirements/matrix.py

   REQUIREMENTS MATRIX (in matrix.py):
   Define dictionaries for:
   - ASSET_TYPE_REQUIREMENTS (server, database, application, network_device)
   - SIX_R_STRATEGY_REQUIREMENTS (rehost, replatform, refactor, repurchase, retire, retain)
   - COMPLIANCE_REQUIREMENTS (GDPR, HIPAA, PCI-DSS, SOC2)
   - CRITICALITY_REQUIREMENTS (tier_1_critical, tier_2_important, tier_3_standard)

   REQUIREMENTS ENGINE:
   - get_requirements() merges all contexts
   - Returns DataRequirements Pydantic model
   - Uses @lru_cache for performance
   - _merge() method handles dict/list merging

   PYDANTIC MODEL (add to schemas.py):
   - DataRequirements (required_columns, required_enrichments, required_jsonb_keys,
                       required_standards, priority_weights, completeness_threshold)

   TESTS TO CREATE:
   - backend/tests/services/gap_detection/test_requirements_engine.py
   - Test asset type requirements
   - Test 6R strategy requirements
   - Test compliance requirements
   - Test requirement merging

   ACCEPTANCE CRITERIA:
   - RequirementsEngine merges all contexts correctly
   - LRU cache improves performance
   - Unit tests cover all requirement combinations
   ```

2. **After agent completes**: Invoke **qa-playwright-tester** for validation

3. **Performance test**: Verify cache hit rate >95% after warmup

**Deliverables**:
- RequirementsEngine with LRU caching
- Complete requirements matrix
- Unit tests for all combinations

**Acceptance Criteria**:
- [ ] Requirements matrix covers all asset types, 6R strategies, compliance scopes
- [ ] Merging logic handles overlaps correctly
- [ ] Cache improves performance
- [ ] Unit tests pass

---

#### **Day 10: Gap Analyzer Service Implementation**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent**:
   ```
   TASK: Implement main GapAnalyzer service orchestrating all inspectors

   CONTEXT:
   - Read design doc: docs/design/shared-inspector-architecture.md
   - Read GPT-5's code examples in GitHub issue #980
   - Must orchestrate all 5 inspectors
   - Must calculate weighted completeness score
   - Must prioritize gaps by business impact
   - Must include tenant scoping (client_account_id)

   FILES TO CREATE:
   - backend/app/services/gap_detection/gap_analyzer.py

   PYDANTIC MODELS (add to schemas.py):
   - MissingDataItem (attribute_name, data_layer, priority, reason, estimated_effort)
   - ComprehensiveGapReport (column_gaps, enrichment_gaps, jsonb_gaps,
                              application_gaps, standards_gaps, overall_completeness_score,
                              priority_missing_data, assessment_ready, blocking_gaps)

   GAP ANALYZER IMPLEMENTATION:
   - analyze_asset() signature:
     async def analyze_asset(
         self,
         asset: Asset,
         application: Optional[CanonicalApplication],
         client_account_id: str,  # ← CRITICAL
         engagement_id: str,
     ) -> ComprehensiveGapReport

   - Use asyncio.gather() to run inspectors in parallel
   - Calculate weighted score:
     * Columns: 40%
     * Enrichments: 30%
     * JSONB: 15%
     * Application: 10%
     * Standards: 5% (compliance penalty)
   - Clamp final score: max(0.0, min(1.0, float(score)))
   - Prioritize gaps (P1 = critical, P2 = important, P3 = optional)
   - Determine assessment readiness based on completeness threshold

   TESTS TO CREATE:
   - backend/tests/services/gap_detection/test_gap_analyzer.py
   - Integration test with real database fixtures
   - Test server asset with rehost strategy
   - Test database asset with compliance requirements
   - Test incomplete asset (should show not ready)
   - Test complete asset (should show ready)

   ACCEPTANCE CRITERIA:
   - GapAnalyzer orchestrates all inspectors correctly
   - Completeness scoring matches business requirements
   - Gap prioritization orders by impact
   - Integration tests pass with >90% coverage
   - Performance: <200ms per asset
   ```

2. **After agent completes**: Invoke **qa-playwright-tester**:
   ```
   TASK: Run integration tests for GapAnalyzer

   RUN:
   cd backend && python -m pytest tests/services/gap_detection/test_gap_analyzer.py -v

   VERIFY:
   - All tests pass
   - Performance <200ms per asset
   - Completeness scores in [0.0, 1.0] range
   - No NaN or Infinity values

   PERFORMANCE BENCHMARK:
   - Create 100 test assets
   - Run gap analysis on all
   - Average time should be <200ms per asset
   ```

3. **If performance tests fail**: Re-invoke python-crewai-fastapi-expert to optimize

**Deliverables**:
- GapAnalyzer service implementation
- Completeness scoring algorithm
- Gap prioritization logic
- Integration tests

**Acceptance Criteria**:
- [ ] GapAnalyzer orchestrates all 5 inspectors
- [ ] Weighted scoring implemented correctly
- [ ] Gap prioritization by business impact
- [ ] Performance <200ms per asset
- [ ] Integration tests pass

---

### Week 3: API Integration & Frontend (Days 11-15)

#### **Day 11: Service Layer Integration**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent**:
   ```
   TASK: Create AssessmentFlowChildService methods and update API endpoints

   CONTEXT:
   - Read docs/design/shared-inspector-architecture.md
   - Must integrate via service layer (NOT direct DB access)
   - Must replace old get_missing_critical_attributes()

   FILES TO MODIFY:
   - backend/app/services/assessment_flow/assessment_child_flow_service.py
   - backend/app/api/v1/master_flows/assessment/helpers.py
   - backend/app/api/v1/master_flows/assessment/info_endpoints.py

   ASSESSMENT CHILD SERVICE:
   Add method:
   async def get_asset_readiness_with_gaps(
       self,
       assessment_flow_id: str,
       client_account_id: str,
       engagement_id: str,
   ) -> List[AssetReadinessDetail]:
       # Service layer owns data access
       # Orchestrates GapAnalyzer for all assets
       # Returns readiness details with gap breakdown

   HELPERS.PY:
   - KEEP: get_missing_critical_attributes() as get_missing_critical_attributes_v1()
   - ADD: get_comprehensive_gap_analysis() - calls GapAnalyzer
   - ADD: get_missing_attributes_compatible() - feature flag wrapper

   INFO_ENDPOINTS.PY:
   - UPDATE: get_assessment_readiness() to use service layer
   - ADD: get_asset_gap_detail() endpoint for detailed gaps
   - Delegate to AssessmentFlowChildService (no direct DB access)

   NEW ENDPOINT:
   GET /api/v1/master-flows/{flow_id}/asset-gap-detail/{asset_id}
   Returns layer-by-layer gap breakdown with priority action items

   TESTS TO CREATE:
   - backend/tests/api/v1/master_flows/assessment/test_gap_endpoints.py
   - Test assessment_readiness returns new format
   - Test asset_gap_detail endpoint
   - Test backward compatibility with v1

   ACCEPTANCE CRITERIA:
   - Service layer owns business logic
   - Endpoints delegate to service (no direct DB)
   - Old endpoint format preserved for compatibility
   - New endpoint returns comprehensive gaps
   - API tests pass
   ```

2. **After agent completes**: Invoke **qa-playwright-tester**:
   ```
   TASK: Test API endpoints with Playwright

   TESTS:
   1. GET /api/v1/master-flows/{flow_id}/assessment-readiness
      - Verify new response format
      - Verify completeness_score field exists
      - Verify gap_summary breakdown exists

   2. GET /api/v1/master-flows/{flow_id}/asset-gap-detail/{asset_id}
      - Verify detailed gap analysis returned
      - Verify all layers present (column, enrichment, jsonb, standards)
      - Verify priority_missing_data populated

   3. Backward compatibility test:
      - Verify old clients still work with feature flag OFF

   IF FAILURES: Report back to orchestration
   ```

3. **Iterate until all tests pass**

**Deliverables**:
- AssessmentFlowChildService methods
- Updated API endpoints
- New asset-gap-detail endpoint
- API tests

**Acceptance Criteria**:
- [ ] Service layer integration complete
- [ ] Old get_missing_critical_attributes() preserved
- [ ] New endpoints return comprehensive gaps
- [ ] API tests pass
- [ ] Backward compatibility maintained

---

#### **Day 12: Frontend - Readiness Dashboard Update**

**Your Tasks (Orchestration)**:

1. **Invoke nextjs-ui-architect agent**:
   ```
   TASK: Update ReadinessDashboardWidget to show detailed gaps

   CONTEXT:
   - Read docs/design/shared-inspector-architecture.md
   - Read GPT-5's frontend compatibility shim from issue #980
   - Must maintain backward compatibility during rollout

   FILES TO MODIFY:
   - src/types/assessment.ts (TypeScript interfaces)
   - src/components/assessment/ReadinessDashboardWidget.tsx
   - src/lib/api/assessmentFlowApi.ts

   TYPESCRIPT INTERFACES (assessment.ts):
   Add:
   - GapSummary (column_gaps, enrichment_gaps, jsonb_gaps, standards_violations)
   - MissingAttributesByCategory (infrastructure, enrichments, technical_details, standards_compliance)
   - AssetReadinessDetail (updated with completeness_score, assessment_ready, gap_summary, blocking_gaps)

   COMPATIBILITY SHIM (in ReadinessDashboardWidget.tsx):
   const compatMissing = (missing: any): MissingAttributesByCategory => {
     return {
       infrastructure: missing?.infrastructure ?? [],
       enrichments: missing?.enrichments ?? [],
       technical_details: missing?.technical_details ?? ([
         ...(missing?.application ?? []),
         ...(missing?.technical_debt ?? []),
         ...(missing?.business ?? []),
       ]),
       standards_compliance: missing?.standards_compliance ?? [],
     };
   };

   UI UPDATES:
   - Show completeness_score as percentage badge
   - Display gap_summary breakdown (column/enrichment/jsonb/standards)
   - Add "View Gap Details" button per asset
   - Update "Collect Missing Data" button to show count

   MODAL TO CREATE:
   - src/components/assessment/GapDetailsModal.tsx
   - Shows layer-by-layer gap breakdown
   - Tabs for columns, enrichments, technical, standards
   - Priority action items list

   ACCEPTANCE CRITERIA:
   - Completeness scores displayed
   - Gap breakdown visible per asset
   - Gap details modal functional
   - Compatibility shim handles old/new format
   - No breaking changes during rollout
   ```

2. **After agent completes**: Invoke **qa-playwright-tester**:
   ```
   TASK: E2E test assessment readiness dashboard

   SCENARIO 1: Display completeness scores
   - Navigate to assessment flow
   - Verify each asset card shows completeness %
   - Verify gap summary counts displayed

   SCENARIO 2: Gap details modal
   - Click "View Gap Details" on an asset
   - Verify modal opens with tabs
   - Verify each layer shows correct gaps
   - Verify priority items listed

   SCENARIO 3: Collect Missing Data button
   - Verify button shows correct asset count
   - Click button
   - Verify navigates to collection flow
   - Verify missing_attributes passed correctly

   IF FAILURES: Report back to orchestration
   ```

3. **Iterate until all tests pass**

**Deliverables**:
- Updated TypeScript interfaces
- Enhanced ReadinessDashboardWidget
- GapDetailsModal component
- E2E tests

**Acceptance Criteria**:
- [ ] Completeness scores visible
- [ ] Gap breakdown displayed
- [ ] Gap details modal works
- [ ] E2E tests pass

---

#### **Day 13: Collection Flow Integration**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent**:
   ```
   TASK: Refactor ProgrammaticGapScanner to use shared inspectors

   CONTEXT:
   - ProgrammaticGapScanner currently uses hardcoded 22 attributes
   - Must replace with new GapAnalyzer inspectors
   - Must maintain tenant scoping and performance

   FILES TO MODIFY:
   - backend/app/services/collection/gap_scanner/gap_detector.py
   - backend/app/services/collection/gap_scanner/scanner.py

   REFACTORING STRATEGY:
   1. Import GapAnalyzer from gap_detection service
   2. Replace identify_gaps_for_asset() to use inspectors:
      - Call GapAnalyzer.analyze_asset()
      - Convert ComprehensiveGapReport to CollectionDataGap format
      - Maintain existing deduplication logic

   3. Update scan_assets_for_gaps():
      - Use GapAnalyzer instead of CriticalAttributesDefinition
      - Keep tenant scoping (client_account_id, engagement_id)
      - Keep batch processing (BATCH_SIZE = 50)
      - Keep performance optimization

   BACKWARD COMPATIBILITY:
   - Keep existing API response format
   - Map ComprehensiveGapReport fields to existing gap format:
     * column_gaps.missing → field_name, gap_type="missing_field"
     * enrichment_gaps.missing_tables → gap_category="enrichment"
     * jsonb_gaps.missing_keys → gap_category="technical_details"

   TESTS TO UPDATE:
   - backend/tests/backend/services/collection/test_gap_analysis.py
   - Verify refactored scanner still passes all tests
   - Add new tests for enrichment gap detection
   - Add new tests for JSONB gap detection

   ACCEPTANCE CRITERIA:
   - ProgrammaticGapScanner uses shared inspectors
   - All existing tests still pass
   - New gap types detected (enrichments, JSONB)
   - Performance maintained (<200ms per asset)
   ```

2. **After agent completes**: Invoke **qa-playwright-tester**:
   ```
   TASK: Regression test collection gap analysis

   RUN:
   cd backend && python -m pytest tests/backend/services/collection/test_gap_analysis.py -v
   cd backend && python -m pytest tests/backend/integration/test_gap_enriched_data_bug679.py -v

   VERIFY:
   - All existing tests pass (regression check)
   - New gap types detected (enrichments, JSONB)
   - Performance not degraded

   IF FAILURES: Report back for fixes
   ```

3. **Iterate until all tests pass**

**Deliverables**:
- Refactored ProgrammaticGapScanner
- Shared inspector integration
- Updated tests

**Acceptance Criteria**:
- [ ] ProgrammaticGapScanner uses GapAnalyzer
- [ ] All regression tests pass
- [ ] New gap types detected
- [ ] Performance maintained

---

#### **Day 14: Intelligent Questionnaire Generator Integration**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent**:
   ```
   TASK: Integrate IntelligentQuestionnaireGenerator with collection flow

   CONTEXT:
   - Collection flow creates AdaptiveQuestionnaire records
   - Must generate questions based on actual gaps (not generic 22)
   - Must skip questions for existing data

   FILES TO CREATE:
   - backend/app/services/gap_detection/questionnaire_generator.py

   FILES TO MODIFY:
   - backend/app/api/v1/endpoints/collection_crud_create_commands.py

   QUESTIONNAIRE GENERATOR:
   class IntelligentQuestionnaireGenerator:
       async def generate_questionnaire(
           self,
           gap_report: ComprehensiveGapReport,
           asset: Asset,
           application: Optional[CanonicalApplication],
       ) -> AdaptiveQuestionnaire:
           # Generate sections based on actual gaps
           # Infrastructure section (only if column gaps exist)
           # Enrichment section (only if enrichment gaps exist)
           # Technical section (only if JSONB gaps exist)
           # Standards section (only if standards violations exist)
           # Prioritize sections by business impact

   COLLECTION FLOW INTEGRATION (in create_collection_flow):
   After creating collection flow:
   1. For each selected asset:
      - Get gap report from GapAnalyzer
      - Generate adaptive questionnaire
      - Create AdaptiveQuestionnaire record
      - Link to collection flow

   TESTS TO CREATE:
   - backend/tests/services/gap_detection/test_questionnaire_generator.py
   - Test section generation based on gaps
   - Test question skipping for existing data
   - Test prioritization logic

   ACCEPTANCE CRITERIA:
   - Questionnaire generator integrated
   - Questions generated based on actual gaps
   - Existing data skipped
   - Tests pass
   ```

2. **After agent completes**: Invoke **qa-playwright-tester**:
   ```
   TASK: E2E test adaptive questionnaire generation

   SCENARIO:
   1. Create assessment with incomplete asset
   2. Click "Collect Missing Data"
   3. Verify collection flow created
   4. Navigate to adaptive forms
   5. Verify ONLY missing data sections shown
   6. Verify NO questions for existing data

   EXPECTED:
   - Asset with CPU=4 but missing memory → Should NOT ask CPU
   - Asset missing resilience table → SHOULD ask RTO/RPO
   - Asset with empty JSONB → SHOULD ask technical details

   IF FAILURES: Report back for fixes
   ```

3. **Iterate until tests pass**

**Deliverables**:
- IntelligentQuestionnaireGenerator implementation
- Collection flow integration
- E2E tests

**Acceptance Criteria**:
- [ ] Questionnaire generator integrated
- [ ] Questions based on actual gaps
- [ ] Existing data skipped
- [ ] E2E tests pass

---

#### **Day 15: Testing & Documentation**

**Your Tasks (Orchestration)**:

1. **Invoke qa-playwright-tester agent**:
   ```
   TASK: Comprehensive E2E testing of entire flow

   SCENARIO 1: Complete Assessment → Collection Flow
   1. Create assessment with incomplete assets
   2. GET /assessment-readiness → Verify gaps detected
   3. Click "Collect Missing Data"
   4. POST /collection/ensure-flow → Verify flow created
   5. Navigate to adaptive forms
   6. Verify questionnaire only asks about gaps
   7. Answer questions
   8. Verify gaps resolved
   9. Return to assessment
   10. Verify completeness score improved

   SCENARIO 2: Standards Validation
   1. Create engagement with PCI-DSS standards
   2. Create asset without encryption
   3. Run gap analysis
   4. Verify standards violation detected
   5. Verify blocking_gaps includes "Encryption required"

   SCENARIO 3: Performance Test
   1. Create 100 assets with varying completeness
   2. Run gap analysis on all
   3. Verify average time <200ms per asset
   4. Verify no memory leaks

   SCENARIO 4: Tenant Isolation
   1. Create assets for client_account_1
   2. Create assets for client_account_2
   3. Run gap analysis as client_account_1
   4. Verify ONLY client_account_1 assets analyzed
   5. Verify NO cross-tenant data leakage

   GENERATE REPORT:
   - tests/e2e/INTELLIGENT_GAP_DETECTION_E2E_REPORT.md
   - Include all test results
   - Include performance benchmarks
   - Include screenshots

   ACCEPTANCE CRITERIA:
   - All E2E tests pass
   - Performance meets targets
   - Tenant isolation verified
   - Report generated
   ```

2. **Invoke python-crewai-fastapi-expert agent** to create documentation:
   ```
   TASK: Create API documentation and user guide

   FILES TO CREATE:
   - docs/api/gap-detection-v2.md (API reference)
   - docs/user-guide/intelligent-gap-detection.md (user guide)
   - docs/development/gap-detection-architecture.md (developer guide)

   API DOCUMENTATION:
   - Document all endpoints
   - Include request/response examples
   - Document query parameters
   - Document error responses

   USER GUIDE:
   - Explain completeness scores
   - Explain gap categories
   - How to interpret gap details
   - How to collect missing data
   - Screenshots from Playwright tests

   DEVELOPER GUIDE:
   - Architecture overview
   - Inspector interfaces
   - How to add new inspectors
   - How to add new requirements
   - Performance optimization tips

   ACCEPTANCE CRITERIA:
   - All documentation complete
   - Examples tested and working
   - Screenshots included
   ```

3. **Review all documentation yourself** before proceeding

**Deliverables**:
- E2E test report
- API documentation
- User guide
- Developer guide

**Acceptance Criteria**:
- [ ] All E2E tests pass
- [ ] Performance benchmarks met
- [ ] Tenant isolation verified
- [ ] Documentation complete

---

### Week 4: Optimization & Deployment (Days 16-20)

#### **Day 16: Performance Optimization & Caching**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent**:
   ```
   TASK: Implement caching and batch optimization

   CONTEXT:
   - Requirements matrix lookups should be cached
   - Standards queries should be cached per engagement
   - Asset analysis should support batch mode

   FILES TO MODIFY:
   - backend/app/services/gap_detection/requirements/requirements_engine.py (already has @lru_cache)
   - backend/app/services/gap_detection/gap_analyzer.py

   OPTIMIZATIONS:
   1. Batch Analysis:
      async def analyze_assets_batch(
          self,
          assets: List[Asset],
          applications: Dict[str, CanonicalApplication],
          client_account_id: str,
          engagement_id: str,
      ) -> List[ComprehensiveGapReport]:
          # Fetch standards ONCE for all assets
          # Run inspectors in parallel with asyncio.gather
          # Return all reports

   2. Query Optimization:
      - Use selectinload for enrichment relationships
      - Fetch all engagement standards in single query
      - Avoid N+1 queries

   3. Monitoring:
      - Add performance logging
      - Track cache hit rates
      - Log slow analyses (>200ms)

   TESTS TO CREATE:
   - backend/tests/performance/test_gap_detection_performance.py
   - Benchmark batch vs sequential
   - Verify 5x speedup with batching
   - Verify cache hit rate >95%

   ACCEPTANCE CRITERIA:
   - Batch analysis 5x faster
   - Cache hit rate >95%
   - No N+1 queries
   - Performance benchmarks pass
   ```

2. **After agent completes**: Invoke **qa-playwright-tester** for performance validation

**Deliverables**:
- Batch analysis implementation
- Query optimization
- Performance benchmarks

**Acceptance Criteria**:
- [ ] Batch analysis 5x faster
- [ ] Cache hit rate >95%
- [ ] No N+1 queries
- [ ] Benchmarks pass

---

#### **Day 17: Agentic Refinement (Optional Enhancement)**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent**:
   ```
   TASK: Add optional agentic refinement to GapAnalyzer

   CONTEXT:
   - This is OPTIONAL enhancement using LLM
   - Must use multi_model_service (ADR-024 compliant)
   - Must be feature-flagged
   - Must track to llm_usage_logs

   FILES TO MODIFY:
   - backend/app/services/gap_detection/gap_analyzer.py
   - backend/app/core/feature_flags.py

   AGENTIC REFINEMENT:
   Add method to GapAnalyzer:
   async def _agentic_refinement(
       self,
       asset: Asset,
       baseline_score: float,
       column_gaps: ColumnGapReport,
       jsonb_gaps: JSONBGapReport,
       requirements: DataRequirements,
   ) -> tuple[float, List[MissingDataItem]]:
       # Use multi_model_service to identify semantic gaps
       # Examples:
       # - "Payment processing" but no PCI data → flag compliance gap
       # - "High business value" but no cost data → flag financial gap
       # - "Tier 1 critical" but no resilience → flag availability gap

       prompt = f"Analyze data completeness for {asset.asset_name}..."

       response = await multi_model_service.generate_response(
           prompt=prompt,
           task_type="gap_analysis_refinement",
           complexity=TaskComplexity.SIMPLE,
           response_format={"type": "json_object"},
       )

       # Parse and return adjusted score + additional gaps

   FEATURE FLAG:
   - Add AGENTIC_GAP_REFINEMENT flag
   - Default: False (disabled)
   - Enable via engagement config

   TESTS TO CREATE:
   - backend/tests/services/gap_detection/test_agentic_refinement.py
   - Test semantic gap detection
   - Verify LLM tracking to llm_usage_logs
   - Test feature flag on/off

   ACCEPTANCE CRITERIA:
   - Agentic refinement optional
   - Uses multi_model_service (ADR-024)
   - Tracked to llm_usage_logs
   - Feature flagged
   - Tests pass
   ```

2. **After agent completes**: Verify LLM tracking:
   ```sql
   SELECT * FROM migration.llm_usage_logs
   WHERE feature_context = 'gap_analysis_refinement'
   ORDER BY created_at DESC LIMIT 10;
   ```

**Deliverables**:
- Agentic refinement implementation
- Feature flag integration
- LLM usage tracking

**Acceptance Criteria**:
- [ ] Agentic refinement optional
- [ ] LLM tracking verified
- [ ] Feature flag works
- [ ] Tests pass

---

#### **Day 18: Standards Template Population**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent**:
   ```
   TASK: Create standards template loader with PCI-DSS, HIPAA, SOC2 templates

   CONTEXT:
   - Templates populate EngagementArchitectureStandard table
   - Must include client_account_id for tenant scoping
   - Must use on_conflict_do_nothing for idempotency

   FILES TO CREATE:
   - backend/app/services/gap_detection/standards/templates.py
   - backend/app/services/gap_detection/standards/template_loader.py

   TEMPLATES TO DEFINE (in templates.py):
   PCI_DSS_STANDARDS = [
       {
           "requirement_type": "security",
           "standard_name": "Network Segmentation",
           "minimum_requirements": {
               "network_isolation": True,
               "firewall_required": True,
           },
           "is_mandatory": True,
       },
       # ... more PCI-DSS standards
   ]

   HIPAA_STANDARDS = [...]
   SOC2_STANDARDS = [...]

   TEMPLATE LOADER (in template_loader.py):
   async def populate_engagement_standards(
       db: AsyncSession,
       client_account_id: str,  # ← CRITICAL
       engagement_id: str,
       compliance_scopes: List[str],
   ) -> None:
       # For each scope (PCI-DSS, HIPAA, etc.)
       # Insert standards with client_account_id
       # Use on_conflict_do_nothing for idempotency

   INTEGRATION:
   - Call from engagement creation workflow
   - Call when updating compliance scopes

   TESTS TO CREATE:
   - backend/tests/services/gap_detection/test_template_loader.py
   - Test PCI-DSS template population
   - Test HIPAA template population
   - Test SOC2 template population
   - Test tenant scoping
   - Test idempotency

   ACCEPTANCE CRITERIA:
   - All 3 templates defined
   - Template loader includes client_account_id
   - Idempotent inserts
   - Tests pass
   ```

2. **Invoke pgvector-data-architect agent** to update schema:
   ```
   TASK: Update EngagementArchitectureStandard unique constraint

   CONTEXT:
   - Current constraint: (engagement_id, requirement_type, standard_name)
   - Must add client_account_id for tenant scoping

   MIGRATION TO CREATE:
   - backend/alembic/versions/094_update_standards_unique_constraint.py

   MIGRATION STEPS:
   1. Drop old constraint
   2. Add new constraint: (client_account_id, engagement_id, requirement_type, standard_name)
   3. Add index on (client_account_id, engagement_id) for performance

   TEST MIGRATION:
   - Verify idempotent (can run multiple times)
   - Verify upgrade works
   - Verify downgrade works

   ACCEPTANCE CRITERIA:
   - Migration created
   - Unique constraint updated
   - Index added
   - Migration tested
   ```

3. **After agents complete**: Run migration on test database

**Deliverables**:
- Standards templates (PCI-DSS, HIPAA, SOC2)
- Template loader with tenant scoping
- Migration for unique constraint update

**Acceptance Criteria**:
- [ ] All templates defined
- [ ] Template loader working
- [ ] Migration tested
- [ ] Tenant scoping enforced

---

#### **Day 19: Monitoring & Observability**

**Your Tasks (Orchestration)**:

1. **Invoke python-crewai-fastapi-expert agent**:
   ```
   TASK: Add logging, metrics, and Grafana dashboard

   CONTEXT:
   - Add structured logging for all gap operations
   - Add Prometheus metrics
   - Create Grafana dashboard

   FILES TO MODIFY:
   - backend/app/services/gap_detection/gap_analyzer.py
   - backend/app/services/gap_detection/metrics.py (NEW)

   STRUCTURED LOGGING:
   logger.info(
       "gap_analysis_completed",
       asset_id=str(asset.id),
       completeness_score=report.overall_completeness_score,
       assessment_ready=report.assessment_ready,
       column_gaps=len(report.column_gaps.missing_attributes),
       enrichment_gaps=len(report.enrichment_gaps.missing_tables),
   )

   PROMETHEUS METRICS (in metrics.py):
   - gap_analysis_duration_seconds (Histogram)
   - asset_completeness_score (Gauge)
   - gap_detection_errors_total (Counter)
   - blocking_gaps_total (Gauge)

   GRAFANA DASHBOARD:
   - Create JSON definition
   - Average completeness by asset type
   - Assets not ready for assessment
   - Gap analysis performance (p95)
   - Blocking gaps by engagement

   TESTS:
   - Verify metrics exported
   - Verify logging includes all fields
   - Test Grafana dashboard locally

   ACCEPTANCE CRITERIA:
   - Structured logging complete
   - Metrics exported
   - Grafana dashboard created
   - Tests pass
   ```

2. **Review Grafana dashboard yourself** in local environment

**Deliverables**:
- Structured logging
- Prometheus metrics
- Grafana dashboard

**Acceptance Criteria**:
- [ ] Logging captures all operations
- [ ] Metrics exported
- [ ] Dashboard deployed
- [ ] Metrics visible in Grafana

---

#### **Day 20: Deployment & Rollout**

**Your Tasks (Orchestration)**:

1. **Invoke sre-precommit-enforcer agent**:
   ```
   TASK: Run pre-commit checks on all modified files

   FILES TO CHECK:
   - backend/app/services/gap_detection/**/*.py
   - backend/app/services/collection/gap_scanner/**/*.py
   - backend/app/api/v1/master_flows/assessment/**/*.py
   - backend/app/api/v1/endpoints/collection_crud_create_commands.py
   - src/components/assessment/**/*.tsx
   - src/types/assessment.ts

   PRE-COMMIT CHECKS:
   - bandit (security)
   - black (formatting)
   - flake8 (linting)
   - mypy (type checking)
   - Check for hardcoded secrets
   - Check for exposed cloud keys
   - Check Python file length (<400 lines)
   - Check for direct LLM calls bypassing tracking

   FIX ALL ISSUES:
   - Do NOT use --no-verify
   - Fix issues properly
   - Re-run until all pass

   ACCEPTANCE CRITERIA:
   - All pre-commit checks pass
   - No --no-verify used
   - Code quality verified
   ```

2. **After pre-commit passes**: Create PR
   ```
   TASK: Create comprehensive PR for intelligent gap detection

   PR TITLE:
   feat: Intelligent Multi-Layer Gap Detection System

   PR DESCRIPTION:
   See template in docs/templates/PR_TEMPLATE.md

   INCLUDE:
   - Summary of changes
   - Link to issue #980
   - Link to design doc
   - Breaking changes (NONE - backward compatible)
   - Testing performed
   - E2E test report
   - Performance benchmarks
   - Rollout plan (10% → 50% → 100%)

   LABELS:
   - enhancement
   - backend
   - frontend
   - ready-for-review

   REVIEWERS:
   - Request review from technical lead
   - Request review from product owner

   LINKED ISSUES:
   - Closes #980
   - Closes #975
   - Closes #976
   - Closes #977
   - Closes #978
   - Closes #979
   ```

3. **Monitor deployment**:
   - Watch error rates (target: <0.1%)
   - Watch performance (target: p95 <200ms)
   - Watch Grafana dashboard
   - Check user feedback

**Deliverables**:
- All pre-commit checks passed
- PR created and submitted
- Deployment plan documented

**Acceptance Criteria**:
- [ ] Pre-commit checks pass
- [ ] PR created
- [ ] Tests pass in CI
- [ ] Ready for review

---

## Agent Orchestration Pattern

### How You Orchestrate Agents

1. **Task Decomposition**:
   - Break down each day's work into agent-appropriate tasks
   - Provide clear context, files to modify, acceptance criteria
   - Include relevant code examples from issue #980

2. **Agent Invocation**:
   - Use Task tool with appropriate subagent_type
   - Provide comprehensive prompts (don't assume agent knowledge)
   - Include all necessary context and references

3. **Iteration Loop**:
   ```
   LOOP until acceptance criteria met:
       1. Invoke python-crewai-fastapi-expert (or other agent)
       2. Wait for completion
       3. Invoke qa-playwright-tester for validation
       4. IF tests fail:
          - Analyze failures
          - Re-invoke python-crewai-fastapi-expert with fixes
          - GOTO step 2
       5. ELSE:
          - Mark task complete
          - Proceed to next task
   ```

4. **Quality Gates**:
   - NEVER proceed to next day until ALL acceptance criteria met
   - NEVER skip testing
   - NEVER commit code without pre-commit checks passing
   - NEVER create PR with failing tests

5. **Documentation**:
   - Track progress in todo list
   - Document any deviations from plan
   - Update issue #980 with progress updates
   - Create summary at end of each day

---

## Critical Files & References

### Design Documents
- `/docs/implementation-plans/intelligent-gap-detection-solution-design.md` (full design)
- GitHub Issue #980 (solution design with GPT-5's review)
- GitHub Issues #975-#979 (investigation spikes)

### Key Existing Code
- `backend/app/services/collection/gap_scanner/scanner.py` (ProgrammaticGapScanner)
- `backend/app/services/collection/incremental_gap_analyzer.py` (IncrementalGapAnalyzer)
- `backend/app/api/v1/master_flows/assessment/helpers.py` (current gap detection)
- `backend/app/models/asset/models.py` (Asset + enrichments)
- `backend/app/models/assessment_flow/core_models.py` (EngagementArchitectureStandard)

### Serena Memories to Read
- `.serena/memories/automated_bug_fix_multi_agent_workflow_2025_11.md`
- `.serena/memories/frontend_backend_schema_mismatch_patterns_2025_11.md`
- `.serena/memories/qa_validation_cache_invalidation_pattern_2025_11.md`

---

## Success Metrics

### Technical Metrics
- Gap Detection Accuracy: >95%
- Performance: <200ms per asset
- Test Coverage: >90%
- Error Rate: <0.1%

### Agent Orchestration Metrics
- Tasks completed on schedule: 100%
- Tests passing on first try: >70%
- Pre-commit failures: 0
- Code quality violations: 0

### Delivery Metrics
- Implementation complete: 15 days
- PR approved: <2 days after submission
- Production deployment: 100% rollout within 1 week
- Zero rollbacks required

---

## What NOT to Do

❌ **DO NOT write code yourself** - Always delegate to specialized agents
❌ **DO NOT skip testing** - Every code change must be tested
❌ **DO NOT proceed with failing tests** - Fix issues before moving forward
❌ **DO NOT use --no-verify** - Fix pre-commit issues properly
❌ **DO NOT assume tenant scoping** - Verify client_account_id in all queries
❌ **DO NOT create new code** - Reuse existing ProgrammaticGapScanner/IncrementalGapAnalyzer
❌ **DO NOT bypass service layer** - Use AssessmentFlowChildService
❌ **DO NOT break backward compatibility** - Use feature flags and compatibility shims

---

## Your First Action

When this session starts, you should:

1. **Read this entire prompt** to understand the implementation plan
2. **Read Serena memories** for architectural context
3. **Read issue #980** for solution design and GPT-5's review
4. **Create todo list** for Week 2-4 implementation (15 tasks)
5. **Begin Day 6**: Audit existing gap detection code

Good luck! Remember: You are the orchestrator, not the implementer. Delegate to specialized agents and iterate until quality gates pass.
