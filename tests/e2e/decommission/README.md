# Decommission Flow E2E Tests

## Overview

This directory contains comprehensive end-to-end tests for the Decommission Flow feature (Issues #942-946).

## Test Files

1. **overview.spec.ts** - Overview page tests (23 tests)
   - Basic navigation and UI rendering
   - Metrics cards display
   - Decommission Assistant insights
   - Phase pipeline visualization
   - Schedule Decommission modal
   - System selection functionality
   - Console and network validation

2. **planning.spec.ts** - Planning page tests (3 active + 6 placeholder)
   - Access control (requires flow_id)
   - Redirect behavior
   - Placeholder tests for full functionality

3. **data-migration.spec.ts** - Data Migration page tests (3 active + 6 placeholder)
   - Access control (requires flow_id)
   - Redirect behavior
   - Placeholder tests for tabs and features

4. **shutdown.spec.ts** - Shutdown page tests (3 active + 7 placeholder)
   - Access control (requires flow_id)
   - Redirect behavior
   - Placeholder tests for shutdown workflow

5. **export.spec.ts** - Export page tests (3 active + 8 placeholder)
   - Access control (requires flow_id)
   - Redirect behavior
   - Placeholder tests for export formats

## Running Tests

### All Decommission Tests
```bash
npm run test:e2e -- tests/e2e/decommission/
```

### Specific Page Tests
```bash
# Overview page only
npm run test:e2e -- tests/e2e/decommission/overview.spec.ts

# Planning page only
npm run test:e2e -- tests/e2e/decommission/planning.spec.ts

# Data Migration page only
npm run test:e2e -- tests/e2e/decommission/data-migration.spec.ts

# Shutdown page only
npm run test:e2e -- tests/e2e/decommission/shutdown.spec.ts

# Export page only
npm run test:e2e -- tests/e2e/decommission/export.spec.ts
```

### Run with UI Mode (Debugging)
```bash
npm run test:e2e -- tests/e2e/decommission/ --ui
```

### Run Specific Test
```bash
npm run test:e2e -- tests/e2e/decommission/overview.spec.ts -g "should display all 4 metrics cards"
```

## Test Coverage

### Current Status
- **Total Tests:** 62
- **Active Tests:** 35 (runnable now)
- **Placeholder Tests:** 27 (require backend flow APIs)
- **Pass Rate:** 100% (all active tests passing)

### Active Tests Cover:
- ✅ Navigation and routing
- ✅ UI component rendering
- ✅ Access control (flow_id requirement)
- ✅ Redirect behavior
- ✅ Toast notifications
- ✅ Modal interactions
- ✅ Form controls (checkboxes, buttons)
- ✅ Console error detection
- ✅ Network request validation
- ✅ ADR compliance (snake_case, MFO pattern)

### Placeholder Tests Will Cover (After Backend Integration):
- ⏳ Flow initialization via API
- ⏳ Risk assessment metrics
- ⏳ Cost estimation breakdown
- ⏳ Dependency analysis tables
- ⏳ Compliance checklists
- ⏳ Data migration workflows
- ⏳ Archive job management
- ⏳ Shutdown execution
- ⏳ Rollback functionality
- ⏳ Export generation (PDF/Excel/JSON)

## Prerequisites

1. **Docker Environment Running**
   ```bash
   cd config/docker && docker-compose up -d
   ```

2. **Services Healthy**
   - Frontend: http://localhost:8081
   - Backend: http://localhost:8000
   - Database: localhost:5433
   - Redis: localhost:6379

3. **Test User Credentials**
   - Email: chockas@hcltech.com
   - Password: Testing123!

## Known Limitations

### Phase 4 (Current)
- Pages Planning, Data Migration, Shutdown, and Export redirect to Overview when accessed without flow_id
- This is **expected behavior** - pages are protected until flow initialization is implemented

### Next Phase (Backend Integration)
To enable full testing of all placeholder tests:

1. **Implement Flow Initialization API**
   - POST `/api/v1/decommission-flow/`
   - Accept system IDs
   - Return flow_id

2. **Implement Phase APIs**
   - GET `/api/v1/decommission-flow/{flow_id}/planning`
   - GET `/api/v1/decommission-flow/{flow_id}/data-migration`
   - GET `/api/v1/decommission-flow/{flow_id}/shutdown`
   - POST `/api/v1/decommission-flow/{flow_id}/export`

3. **Update Test Helper**
   ```typescript
   // Add to test helpers
   async function initializeDecommissionFlow(page: Page, systemIds: string[]): Promise<string> {
     // POST to API
     // Return flow_id
   }
   ```

4. **Un-skip Placeholder Tests**
   - Remove `.skip` from placeholder tests
   - Add flow initialization to beforeEach hooks

## Architecture Compliance

### ADR-027: Snake_case Field Names
All tests are designed to work with snake_case API responses:
- `flow_id` (not flowId)
- `client_account_id` (not clientAccountId)
- `retention_period` (not retentionPeriod)

### ADR-006: MFO Pattern
Tests verify:
- Pages expect `flow_id` query parameter
- HTTP polling hooks for real-time updates
- Proper flow state management

## Debugging Failed Tests

### View Test Report
```bash
npm run test:e2e -- tests/e2e/decommission/ --reporter=html
```

### Run in Debug Mode
```bash
npm run test:e2e -- tests/e2e/decommission/ --debug
```

### Check Docker Logs
```bash
# Backend errors
docker logs migration_backend -f

# Frontend errors
docker logs migration_frontend -f
```

### Verify Services
```bash
# Check all containers
docker-compose ps

# Test backend API
curl http://localhost:8000/api/v1/health
```

## Contributing

When adding new tests:

1. **Follow Existing Patterns**
   - Use descriptive test names
   - Group related tests in describe blocks
   - Add comments for complex interactions

2. **Test User Experience**
   - Verify visible elements
   - Check error messages
   - Test loading states
   - Validate user feedback

3. **Maintain Coverage**
   - Add tests for new features
   - Update placeholder tests when backend ready
   - Keep test data realistic

4. **Document Findings**
   - Update TEST_REPORT.md with results
   - Create issues for bugs found
   - Add screenshots for visual bugs

## Test Report

See `TEST_REPORT.md` for detailed test results, findings, and recommendations.

## Contact

For questions about these tests:
- Review `TEST_REPORT.md` for detailed findings
- Check `/docs/analysis/Notes/000-lessons.md` for architectural context
- See ADR-027 and ADR-006 for compliance requirements
