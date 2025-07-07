# Team Zeta - Rapid Testing & Validation Briefing

## Mission Statement
Team Zeta is responsible for updating and utilizing the EXISTING comprehensive test infrastructure in `/tests` folder to validate the aggressive legacy code elimination and ensure all components work together seamlessly.

## Team Objectives (2-3 Hours Max)
1. **UPDATE EXISTING TESTS**: Fix API endpoints and session_id references in existing tests
2. **VALIDATE LEGACY REMOVAL**: Ensure all legacy patterns are eliminated  
3. **END-TO-END VALIDATION**: Test complete discovery flow works
4. **ZERO REGRESSION**: Ensure no functionality broken by cleanup
5. **RAPID VALIDATION**: Complete testing in 2-3 hours with existing infrastructure

## Existing Test Infrastructure Analysis

**Comprehensive test suite already exists:**
- **Backend Tests**: `/tests/backend/` - Python tests for APIs, flows, agents
- **E2E Tests**: `/tests/e2e/` - Playwright browser automation tests
- **Frontend Tests**: `/tests/frontend/` - Component and hook tests
- **Integration Tests**: `/tests/integration/` - Full system integration
- **Test Fixtures**: `/tests/fixtures/` - Sample data (CMDB, assessment data)

## Rapid Execution Tasks

### Task 1: Update Critical Existing Tests (30 minutes)

**HIGH PRIORITY - Fix these existing test files:**

```bash
# E2E Tests - Update endpoint URLs
/tests/e2e/discovery-complete-flow.spec.ts     # Complete discovery flow
/tests/e2e/field-mapping-flow.spec.ts          # Field mapping approval  
/tests/e2e/data-import-flow.spec.ts            # Data import process

# Backend Tests - Fix API calls
/tests/backend/test_discovery_flow_endpoints.py # Change to master-flows
/tests/backend/test_api_integration.py          # Update endpoint patterns

# Frontend Tests - Update hooks
/tests/frontend/discovery/test_unified_discovery_flow_hook.test.ts
```

**Key Updates Needed:**
```typescript
// BEFORE (legacy patterns):
await page.goto('/api/v1/discovery/flows/status');
await fetch('/api/v1/discovery/flow/resume');

// AFTER (master flows):
await page.goto('/api/v1/master-flows/status');
await fetch('/api/v1/master-flows/resume');
```

### Task 2: Run Legacy Elimination Validation (60 minutes)

**Validate zero legacy code remains:**

```bash
# 1. Backend API Tests
cd /tests && python -m pytest backend/test_discovery_flow_endpoints.py -v
cd /tests && python -m pytest backend/test_api_integration.py -v
cd /tests && python -m pytest backend/flows/test_unified_discovery_flow.py -v

# 2. E2E Flow Tests (critical path)
cd /tests && npx playwright test discovery-complete-flow.spec.ts
cd /tests && npx playwright test field-mapping-flow.spec.ts  
cd /tests && npx playwright test data-import-flow.spec.ts

# 3. Frontend Component Tests
cd /tests && npm run test:frontend discovery/

# 4. Legacy Pattern Detection Tests
grep -r "session_id" /tests/ && echo "FAIL: session_id found" || echo "PASS: No session_id"
grep -r "/api/v1/discovery/" /tests/ | grep -v "master-flows" && echo "FAIL: Legacy API" || echo "PASS: No legacy APIs"
grep -r "/api/v3" /tests/ && echo "FAIL: V3 API found" || echo "PASS: No V3 APIs"
```

### Task 3: Complete Flow End-to-End Validation (60 minutes)

**Test complete discovery flow works:**

```bash
# Use existing comprehensive E2E test
cd /tests && npx playwright test complete-user-journey.spec.ts --headed

# Validate specific flow steps
cd /tests && npx playwright test file-upload-discovery-flow.spec.ts
cd /tests && npx playwright test import-and-mapping.spec.ts

# Performance validation
cd /tests && python -m pytest backend/performance/test_discovery_performance.py
```

### Task 4: Final Production Readiness Check (30 minutes)

**Run comprehensive test suite:**

```bash
# All backend tests
cd /tests && python -m pytest backend/ -x --tb=short

# Critical E2E tests  
cd /tests && npx playwright test --project=chromium

# Integration tests
cd /tests && python -m pytest integration/ -v

# Generate test report
cd /tests && python -m pytest --html=test-report.html --self-contained-html
```

## Success Criteria (Binary Pass/Fail)

### Hour 1 Checkpoint
- [ ] All test files updated to use master-flows endpoints
- [ ] Zero session_id references in test files
- [ ] Zero V3 API references in tests
- [ ] Backend API tests pass

### Hour 2 Checkpoint  
- [ ] Complete discovery flow E2E test passes
- [ ] Field mapping approval test works
- [ ] Data import flow test succeeds
- [ ] Frontend component tests pass

### Hour 3 Final
- [ ] All tests in test suite pass
- [ ] Zero legacy pattern detection
- [ ] Performance tests meet benchmarks
- [ ] Test report shows 100% critical path coverage

## Common Issues & Quick Fixes

### Issue 1: E2E Tests Fail on Login
```bash
# Quick fix - update test credentials
# Check /tests/fixtures/ for current test user data
```

### Issue 2: API Endpoint 404s
```bash
# Verify backend is running with correct routes
docker-compose ps
curl http://localhost:8000/api/v1/master-flows/active
```

### Issue 3: Frontend Tests Import Errors
```bash
# Update import paths to match new hook structure
# Replace old hook imports with new unified hooks
```

## Rollback Procedures

**If critical tests fail:**
1. **Document failure clearly** in status report
2. **Identify if it's test issue or code issue**
3. **Fix test if possible within 15 minutes**
4. **Flag for other teams if code issue**
5. **Continue with remaining tests**

## Status Report Template

```yaml
team: Zeta
hour: 1
status: on-track|blocked|completed
tests_updated: 12/15
tests_passing: 8/12
critical_failures:
  - discovery-complete-flow: API 404 error
  - field-mapping: Session_id reference
blockers:
  - Backend not responding on port 8000
next_action: Fix endpoint URLs in E2E tests
confidence: 80%
```

## Resource Requirements

- Access to `/tests` directory
- Docker containers running (backend + frontend)
- Node.js and Python for running tests
- Playwright browsers installed
- Test database with sample data

## Dependencies

- **Team Alpha**: API service consolidation complete
- **Team Beta**: Hook consolidation complete  
- **Team Gamma**: Component updates complete
- **Backend Running**: Docker services operational

## Expected Deliverables

1. **Updated test files** with correct API patterns
2. **Test execution report** showing all tests pass
3. **Legacy elimination report** confirming zero old patterns
4. **Performance validation** meeting benchmarks
5. **Production readiness confirmation**

**Note**: This team has the advantage of comprehensive existing test infrastructure. Focus on UPDATING existing tests rather than creating new ones.