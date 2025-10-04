# Collection Gap Analysis E2E Test - NEW Lean Implementation

## Overview

This E2E test (`collection-gap-analysis-new.spec.ts`) validates the **NEW lean single-agent gap analysis implementation** for the Collection Flow feature. It creates a FRESH collection flow and performs comprehensive verification of the entire gap analysis workflow.

## What This Test Does

### Test Flow Steps:

1. **Authentication** - Login with demo credentials (`demo@demo-corp.com` / `Demo123!`)
2. **Navigation** - Go to Collection → Adaptive Forms (`/collection/adaptive-forms`)
3. **Cleanup** - Remove any blocking flows from previous test runs (via database)
4. **Flow Creation** - Start a NEW collection flow
5. **Asset Selection** - Select 2-3 assets (servers, databases, or applications)
6. **Gap Analysis** - Proceed through gap analysis phase
7. **Polling** - Wait for completion (max 60 seconds with 5-second polling intervals)
8. **UI Verification** - Verify "gaps detected" message appears
9. **Database Verification** - Query `migration.collection_data_gaps` table to verify gaps persisted
10. **Questionnaire Check** - Verify questionnaire displayed (if applicable)

### Additional Test Cases:

- **Database Schema Validation** - Verifies the `collection_data_gaps` table structure
- **Gap Statistics** - Checks gap distribution by type, category, and priority

## Prerequisites

### Docker Containers Must Be Running:

```bash
# Check container status
docker ps | grep migration

# Should show:
# migration_backend    (port 8000)
# migration_frontend   (port 8081)
# migration_postgres   (port 5433)
```

### Start Docker Environment (if needed):

```bash
cd /Users/chocka/CursorProjects/migrate-ui-orchestrator/config/docker
docker-compose up -d
```

## Running the Test

### From Project Root:

```bash
# Run the specific test
npm run test:e2e -- tests/e2e/collection-gap-analysis-new.spec.ts

# Or use Playwright directly
npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts --headed

# Run with debugging
npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts --debug

# Run with UI mode (interactive)
npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts --ui
```

### From config/tools directory (alternative):

```bash
cd /Users/chocka/CursorProjects/migrate-ui-orchestrator/config/tools
npx playwright test ../../tests/e2e/collection-gap-analysis-new.spec.ts
```

## Expected Results

### Success Criteria:

- ✅ User successfully logs in
- ✅ Navigation to Adaptive Forms completes
- ✅ New collection flow starts without errors
- ✅ 2-3 assets are selected
- ✅ Gap analysis completes within 60 seconds
- ✅ Minimum 1 gap detected (ideally 5-10 gaps)
- ✅ Gaps persisted to `migration.collection_data_gaps` table
- ✅ Questionnaire displayed (if applicable to flow)

### Database Verification:

The test automatically runs this SQL query to verify gaps:

```sql
SELECT
  COUNT(*) as total_gaps,
  gap_type,
  gap_category,
  priority,
  field_name
FROM migration.collection_data_gaps
WHERE created_at > NOW() - INTERVAL '5 minutes'
GROUP BY gap_type, gap_category, priority, field_name
ORDER BY priority ASC, gap_category, gap_type;
```

Expected gap attributes:
- `gap_type`: Type of data gap (e.g., "missing_field", "incomplete_data")
- `gap_category`: Category (e.g., "infrastructure", "application", "business")
- `field_name`: Specific field with gap
- `priority`: Integer priority (lower = higher priority)
- `collection_flow_id`: References the collection flow

## Test Artifacts

### Screenshots Generated:

All screenshots are saved to `test-results/` directory:

- `01-after-login.png` - Dashboard after successful login
- `02-adaptive-forms-page.png` - Collection Adaptive Forms page
- `03-flow-started.png` - Flow after clicking start
- `04-assets-selected.png` - After selecting 2-3 assets
- `05-gap-analysis-started.png` - Gap analysis phase initiated
- `06-gap-analysis-completed.png` - After analysis completes
- `07-questionnaire-displayed.png` - Questionnaire UI (if shown)
- `08-final-state.png` - Final test state
- `error-gap-analysis.png` - Error state (if occurred)
- `timeout-gap-analysis.png` - Timeout state (if occurred)

### Test Reports:

- HTML report: `test-results/index.html`
- JSON report: `test-results/results.json`
- JUnit XML: `test-results/results.xml`

## Troubleshooting

### Test Fails to Find Assets

**Issue**: No asset checkboxes found for selection

**Solution**:
1. Check if collection flow has pre-loaded assets
2. Verify backend is running: `curl http://localhost:8000/health`
3. Check database has assets: `docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT COUNT(*) FROM migration.assets;"`

### Gap Analysis Timeout

**Issue**: Gap analysis does not complete within 60 seconds

**Solution**:
1. Check backend logs: `docker logs migration_backend --tail 100`
2. Verify CrewAI agent is running: `docker logs migration_backend | grep -i "gap.*analysis"`
3. Check database for flow status: `docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT * FROM migration.collection_flows ORDER BY created_at DESC LIMIT 1;"`

### No Gaps Detected

**Issue**: Gap analysis completes but no gaps in database

**Solution**:
1. Check if agent actually ran: `docker logs migration_backend | grep -i "GapAnalysisAgent"`
2. Verify gap detection logic is enabled
3. Check if assets have sufficient data for gap detection
4. Review agent output in backend logs

### Database Connection Errors

**Issue**: Test cannot query database via docker exec

**Solution**:
```bash
# Verify postgres container is running
docker ps | grep migration_postgres

# Test manual connection
docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT 1;"

# Check postgres logs
docker logs migration_postgres --tail 50
```

## Manual Database Inspection

### View Recent Gaps:

```bash
docker exec migration_postgres psql -U postgres -d migration_db -c "
  SELECT
    flow_id,
    gap_type,
    gap_category,
    field_name,
    priority,
    created_at
  FROM migration.collection_data_gaps
  JOIN migration.collection_flows ON collection_flows.id = collection_data_gaps.collection_flow_id
  ORDER BY created_at DESC
  LIMIT 20;
"
```

### View Gap Statistics:

```bash
docker exec migration_postgres psql -U postgres -d migration_db -c "
  SELECT
    gap_category,
    COUNT(*) as total,
    AVG(priority) as avg_priority
  FROM migration.collection_data_gaps
  WHERE created_at > NOW() - INTERVAL '1 hour'
  GROUP BY gap_category
  ORDER BY total DESC;
"
```

### Clean Up Test Data:

```bash
# Delete gaps from last hour (test data)
docker exec migration_postgres psql -U postgres -d migration_db -c "
  DELETE FROM migration.collection_data_gaps
  WHERE created_at > NOW() - INTERVAL '1 hour';
"

# Delete test collection flows
docker exec migration_postgres psql -U postgres -d migration_db -c "
  DELETE FROM migration.collection_flows
  WHERE created_at > NOW() - INTERVAL '1 hour';
"
```

## Key Features of This Test

### 1. **Fresh Flow Creation**
- Does NOT reuse existing flows
- Cleans up blocking flows before starting
- Creates new flow each test run

### 2. **Real Docker Environment**
- Uses actual backend (localhost:8000)
- Uses actual frontend (localhost:8081)
- Uses actual PostgreSQL database

### 3. **Database Verification**
- Direct SQL queries via docker exec
- Verifies gaps persisted to `collection_data_gaps` table
- Checks gap attributes (type, category, priority, field_name)

### 4. **Comprehensive Logging**
- Detailed console output for each step
- Browser console errors captured
- Network request failures logged
- Database query results shown

### 5. **Flexible Selectors**
- Multiple selector strategies for asset selection
- Handles different UI implementations
- Fallback patterns for robustness

### 6. **Proper Async Handling**
- 5-second polling intervals (not WebSocket)
- 60-second max wait time
- Proper completion detection (multiple indicators)

## Test Configuration

Edit `TEST_CONFIG` object in test file to adjust:

```typescript
const TEST_CONFIG = {
  maxWaitTimeMs: 60000,    // Max wait for gap analysis (60 seconds)
  pollIntervalMs: 5000,    // Poll every 5 seconds
  minExpectedGaps: 1,      // Minimum gaps to pass test
  flowCleanupTimeoutMs: 10000  // Cleanup timeout
};
```

## CI/CD Integration

### GitHub Actions:

```yaml
- name: Run Collection Gap Analysis E2E Test
  run: |
    docker-compose up -d
    npm run test:e2e -- tests/e2e/collection-gap-analysis-new.spec.ts
  env:
    CI: true
```

### Test Reports in CI:

- HTML report artifact uploaded
- JUnit XML for test result parsing
- Screenshots on failure

## Differences from Old Test

### OLD Test (`collection-gap-analysis.spec.ts`):
- May reuse existing flows
- Less comprehensive database verification
- Simpler asset selection logic
- Basic completion detection

### NEW Test (`collection-gap-analysis-new.spec.ts`):
- ✅ **Always creates fresh flow**
- ✅ **Direct database verification via docker exec**
- ✅ **Cleanup of blocking flows before test**
- ✅ **Multiple asset selection strategies**
- ✅ **Comprehensive completion indicators**
- ✅ **Detailed logging and screenshots**
- ✅ **Database schema validation**
- ✅ **Gap statistics verification**

## Related Documentation

- **Collection Flow Redesign**: `/docs/development/collection-flow-redesign.md`
- **Gap Analysis Architecture**: `/docs/adr/XXX-collection-gap-analysis.md`
- **Test Strategy**: `/docs/testing/e2e-test-strategy.md`
- **Playwright Config**: `/config/tools/playwright.config.ts`

## Support

For issues with this test:
1. Check Docker containers are running
2. Review backend logs: `docker logs migration_backend -f`
3. Check database connectivity
4. Verify frontend is accessible at http://localhost:8081
5. Review test artifacts in `test-results/` directory

---

**Generated by CC (Claude Code)** for qa-playwright-tester agent
**Last Updated**: 2025-10-03
**Test Version**: 1.0.0
