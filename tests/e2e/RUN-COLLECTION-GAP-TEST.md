# How to Run Collection Gap Analysis E2E Test

## Quick Start

```bash
# 1. Validate environment
bash tests/e2e/validate-test-environment.sh

# 2. Run the test (headless)
npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts

# 3. View results
npx playwright show-report
```

## Test Execution Options

### 1. Headless Mode (CI/CD)
```bash
npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts
```

### 2. Headed Mode (Watch Browser)
```bash
npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts --headed
```

### 3. Debug Mode (Step Through)
```bash
npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts --debug
```

### 4. UI Mode (Interactive)
```bash
npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts --ui
```

### 5. Specific Test Case
```bash
# Run only the main test
npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts -g "should execute complete gap analysis"

# Run only the schema validation test
npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts -g "should verify database schema"
```

## Pre-Test Checklist

- [ ] Docker containers running (`docker ps | grep migration`)
- [ ] Frontend accessible (`curl http://localhost:8081`)
- [ ] Backend healthy (`curl http://localhost:8000/health`)
- [ ] Database accessible (`docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT 1;"`)
- [ ] Assets exist (`docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT COUNT(*) FROM migration.assets;"`)

## Expected Test Duration

- **Login**: ~2 seconds
- **Navigation**: ~2 seconds
- **Flow Setup**: ~5 seconds
- **Asset Selection**: ~3 seconds
- **Gap Analysis**: 15-45 seconds (depends on agent performance)
- **Total**: ~30-60 seconds

## Success Indicators

### Console Output:
```
🧪 Starting NEW Lean Collection Flow Gap Analysis E2E Test...
📝 STEP 1: Logging in as demo user...
✅ Login successful, redirected to: http://localhost:8081/dashboard
📝 STEP 2: Navigating to Collection → Adaptive Forms...
✅ Navigated to Adaptive Forms
📝 STEP 3: Checking for incomplete flows...
📝 STEP 4: Starting NEW collection flow...
✅ Clicked start collection button
📝 STEP 5: Selecting 2-3 assets for gap analysis...
✅ Selected 3 assets
📝 STEP 6: Proceeding to gap analysis phase...
🤖 Gap analysis phase started!
📝 STEP 7: Waiting for gap analysis completion...
✅ Gap analysis completed!
📝 STEP 8: Verifying gaps detected message in UI...
✅ Gaps detected message: "5 gaps detected"
📝 STEP 9: Extracting flow ID and verifying gaps in database...
📊 Database Verification Results:
   Total gaps: 5
✅ Verified 5 gaps persisted to database
📝 STEP 10: Verifying questionnaire display...
✅ Questionnaire displayed in UI
🎉 Test completed successfully!
```

### Database Verification:
```sql
-- Should return at least 1 row with gap data
SELECT * FROM migration.collection_data_gaps
WHERE created_at > NOW() - INTERVAL '5 minutes';
```

## Troubleshooting

### Issue: "No asset checkboxes found"

**Cause**: Asset selection UI not rendering or no assets in database

**Fix**:
```bash
# Check if assets exist
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "SELECT COUNT(*) FROM migration.assets;"

# If 0, seed some test data or adjust test to handle empty state
```

### Issue: "Gap analysis timeout"

**Cause**: CrewAI agent taking too long or failing

**Fix**:
```bash
# Check backend logs for agent errors
docker logs migration_backend --tail 100 | grep -i "gap\|analysis\|agent"

# Check if agent is even executing
docker logs migration_backend | grep -i "GapAnalysisAgent"

# Increase timeout in test (edit TEST_CONFIG.maxWaitTimeMs)
```

### Issue: "No gaps detected in database"

**Cause**: Agent not persisting gaps or gap detection logic not working

**Fix**:
```bash
# Check if gaps table is being written to
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "SELECT COUNT(*) FROM migration.collection_data_gaps WHERE created_at > NOW() - INTERVAL '10 minutes';"

# Check collection flow status
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "SELECT flow_id, status, current_phase FROM migration.collection_flows ORDER BY created_at DESC LIMIT 1;"

# Review backend logs for gap persistence
docker logs migration_backend | grep -i "collection_data_gaps"
```

### Issue: "Login failed"

**Cause**: Credentials incorrect or auth service down

**Fix**:
```bash
# Verify demo user exists
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "SELECT email FROM migration.users WHERE email = 'demo@demo-corp.com';"

# Check auth endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@demo-corp.com","password":"Demo123!"}'
```

### Issue: "Database connection failed"

**Cause**: Postgres container not running or network issues

**Fix**:
```bash
# Restart postgres container
docker restart migration_postgres

# Check postgres logs
docker logs migration_postgres --tail 50

# Verify database is migration_db not postgres
docker exec migration_postgres psql -U postgres -l
```

## Manual Database Cleanup

### Before Test (Clean State):
```bash
# Delete recent test gaps
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "DELETE FROM migration.collection_data_gaps WHERE created_at > NOW() - INTERVAL '1 hour';"

# Delete incomplete flows
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "DELETE FROM migration.collection_flows WHERE status NOT IN ('completed', 'failed', 'cancelled');"
```

### After Test (Inspect Results):
```bash
# View all gaps from last test run
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "SELECT gap_type, gap_category, field_name, priority FROM migration.collection_data_gaps ORDER BY created_at DESC LIMIT 20;"

# View gap statistics
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "SELECT gap_category, COUNT(*) as count FROM migration.collection_data_gaps WHERE created_at > NOW() - INTERVAL '10 minutes' GROUP BY gap_category;"
```

## Test Artifacts

All test artifacts are saved to `test-results/` directory:

### Screenshots:
- `01-after-login.png` - After successful login
- `02-adaptive-forms-page.png` - Collection page loaded
- `03-flow-started.png` - Flow creation
- `04-assets-selected.png` - Assets selected
- `05-gap-analysis-started.png` - Analysis started
- `06-gap-analysis-completed.png` - Analysis completed
- `07-questionnaire-displayed.png` - Questionnaire (if shown)
- `08-final-state.png` - Final state
- `error-gap-analysis.png` - Error state (if occurred)

### Reports:
- `test-results/index.html` - HTML report (open in browser)
- `test-results/results.json` - JSON results
- `test-results/results.xml` - JUnit XML

### Videos:
- `test-results/videos/*.webm` - Screen recording of test execution

## CI/CD Integration

### GitHub Actions Example:
```yaml
name: Collection Gap Analysis E2E Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  e2e-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Start Docker Containers
        run: |
          cd config/docker
          docker-compose up -d

      - name: Wait for Services
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8081; do sleep 2; done'
          timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'

      - name: Install Playwright
        run: |
          npm ci
          npx playwright install --with-deps

      - name: Run E2E Test
        run: |
          npx playwright test tests/e2e/collection-gap-analysis-new.spec.ts

      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/
```

## Performance Benchmarks

Expected performance metrics:

| Phase | Expected Time | Timeout |
|-------|--------------|---------|
| Login | 1-3s | 10s |
| Navigation | 1-2s | 10s |
| Flow Setup | 2-5s | 15s |
| Asset Selection | 2-3s | 10s |
| Gap Analysis | 15-45s | 60s |
| Total Test | 25-60s | 120s |

## Test Coverage

This test validates:

- ✅ User authentication
- ✅ Navigation to collection flow
- ✅ Flow creation and initialization
- ✅ Asset selection UI
- ✅ Gap analysis agent execution
- ✅ Database persistence of gaps
- ✅ Gap data structure (type, category, priority, field_name)
- ✅ UI feedback (gaps detected message)
- ✅ Questionnaire generation (if applicable)
- ✅ Error handling and timeouts
- ✅ Async polling (not WebSocket)
- ✅ Multi-tenant scoping

## Related Files

- **Test Spec**: `tests/e2e/collection-gap-analysis-new.spec.ts`
- **README**: `tests/e2e/README-COLLECTION-GAP-TEST.md`
- **Validation Script**: `tests/e2e/validate-test-environment.sh`
- **Playwright Config**: `config/tools/playwright.config.ts`

## Support

For issues:
1. Run validation: `bash tests/e2e/validate-test-environment.sh`
2. Check Docker: `docker ps` and `docker logs migration_backend`
3. Review screenshots in `test-results/`
4. Check database: `docker exec migration_postgres psql -U postgres -d migration_db`
5. Open issue on GitHub with logs and screenshots

---

**Last Updated**: 2025-10-03
**Test Version**: 1.0.0
**Generated by**: CC (Claude Code) - qa-playwright-tester agent
