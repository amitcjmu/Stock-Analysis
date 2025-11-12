# Test Suite Documentation

## Current Coverage: Phase 1 - Smoke Tests

### Purpose
Fast smoke tests for CI/CD pipeline to catch catastrophic failures:
- Build broken
- Services down
- Pages return 404
- Navigation completely broken

### What These Tests DO
✅ Verify pages load
✅ Check basic navigation works
✅ Confirm login/auth functions
✅ Validate UI elements exist

### What These Tests DON'T DO
❌ Validate backend functionality
❌ Check database state
❌ Test actual feature completion (questionnaires, 6R, waves)
❌ Verify cross-flow data persistence

### Known Limitations
These smoke tests would NOT have caught these production bugs:
- Issue #994: Discovery flow missing flow_id
- Issue #995: Attribute mapping requires active flow
- Issue #996: Questionnaire generation never completes
- Issue #997: Asset selection lost after failure
- Issue #998: Progress page shows inconsistent status
- Issue #999: Assessment flow missing 6R recommendations
- Issue #1000: Wave creation SQLAlchemy transaction error

## Phase 2: Comprehensive E2E Tests

See Issue #1008 for Phase 2 implementation tracking.

Phase 2 will add:
- Database validation using PostgreSQL client
- Backend log collection and analysis
- Actual functionality testing (not just UI checks)
- State persistence verification across flows
- Tests specifically for bugs #994-#1000

## Test Structure

### E2E Tests (`tests/e2e/`)
- **Flow tests:** Basic page loading and navigation for each flow
- **Migration tests:** Authentication and dashboard navigation
- **Complete flow tests:** End-to-end journey across multiple flows

### Authentication Helpers (`tests/utils/auth-helpers.ts`)
- `loginAsDemo()` - Login with demo credentials
- `loginAndNavigateToFlow()` - Login and navigate to specific flow

### Running Tests
```bash
# Run all E2E tests
npx playwright test tests/e2e/

# Run specific test file
npx playwright test tests/e2e/flow-discovery.spec.ts

# Run with UI
npx playwright test tests/e2e/ --ui

# Run in headed mode (see browser)
npx playwright test tests/e2e/ --headed
```

### CI/CD Integration
- Tests run automatically on PR creation/update
- Fails fast if basic functionality is broken
- Screenshots and traces saved on failure

## Next Steps

Phase 2 comprehensive testing tracked in **Issue #1008**.
