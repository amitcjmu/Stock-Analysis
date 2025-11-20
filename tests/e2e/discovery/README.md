# Discovery Flow E2E Tests

This directory contains end-to-end tests for the Discovery flow features using Playwright.

---

## Test Files

### 1. `csv-upload-cleansing.spec.ts`
**Purpose**: CSV upload with data cleansing functionality
- Tests malformed CSV handling
- Validates cleansing notifications
- Verifies automatic import continuation

### 2. `attribute-mapping-ag-grid.spec.ts` ✨ NEW
**Purpose**: AG Grid attribute mapping workflow (Issue #1082)
- **Tests**: 22 comprehensive E2E tests
- **Coverage**: Grid rendering, field mapping, bulk actions, persistence
- **Documentation**: See `ATTRIBUTE-MAPPING-AG-GRID-TESTS.md` for full details

---

## Quick Start

### Run All Discovery Tests
```bash
npm run test:e2e -- tests/e2e/discovery/
```

### Run Specific Test File
```bash
# CSV Upload Tests
npm run test:e2e -- tests/e2e/discovery/csv-upload-cleansing.spec.ts

# AG Grid Attribute Mapping Tests
npm run test:e2e -- tests/e2e/discovery/attribute-mapping-ag-grid.spec.ts
```

### Run in Headed Mode (See Browser)
```bash
npm run test:e2e -- tests/e2e/discovery/attribute-mapping-ag-grid.spec.ts --headed
```

### Debug Mode
```bash
npx playwright test tests/e2e/discovery/attribute-mapping-ag-grid.spec.ts --debug
```

---

## Test Data

Test CSV files are located in `/test-data`:
- `test_field_mapping_e2e.csv` - Standard field mapping test data
- `test_40_assets_qa.csv` - Large dataset (40+ columns)
- `attribute-mapping-test-data.csv` - AG Grid specific test data (10 columns, 10 rows)

---

## Prerequisites

1. **Docker Services Running**:
   ```bash
   cd config/docker && docker-compose up -d
   ```

2. **Verify Services**:
   - Frontend: http://localhost:8081
   - Backend: http://localhost:8000
   - Postgres: localhost:5433

3. **Demo User**: `demo@demo-corp.com` / `Demo123!`

---

## Test Coverage Summary

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `csv-upload-cleansing.spec.ts` | 3 | CSV upload, data cleansing, toast notifications |
| `attribute-mapping-ag-grid.spec.ts` | 22 | Grid rendering, mapping operations, bulk actions, persistence |
| **Total** | **25** | **Discovery flow workflows** |

---

## Common Issues

### Issue: Tests Timeout Waiting for Grid
**Solution**: Verify CSV data imported successfully
```bash
docker logs migration_backend --tail 50 | grep "import"
```

### Issue: Demo User Login Fails
**Solution**: Check backend database has demo user seeded
```bash
docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT * FROM migration.users WHERE email='demo@demo-corp.com';"
```

### Issue: Status Badges Not Found
**Solution**: Backend field mapping AI must generate suggestions first
```bash
# Check field mappings in database
docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT * FROM migration.field_mappings LIMIT 5;"
```

---

## CI/CD Integration

Tests run automatically on every PR via GitHub Actions:

```yaml
name: E2E Tests - Discovery Flow
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: docker-compose up -d
      - run: npm run test:e2e -- tests/e2e/discovery/
```

---

## Viewing Test Reports

### HTML Report (Recommended)
```bash
npx playwright show-report playwright-report
```

### JSON Report
```bash
cat test-results/results.json | jq
```

### Screenshots/Videos (On Failure)
```bash
ls -la test-results/
```

---

## Contributing

When adding new Discovery flow features:

1. **Create Test File**: `tests/e2e/discovery/<feature-name>.spec.ts`
2. **Follow Patterns**: Use helpers from `tests/utils/auth-helpers.ts`
3. **Document**: Add README section and detailed test documentation
4. **Test Data**: Add CSV fixtures to `/test-data` directory
5. **Run Locally**: Verify tests pass before pushing

---

## References

- **Playwright Docs**: https://playwright.dev/docs/writing-tests
- **Project Patterns**: `/docs/analysis/Notes/coding-agent-guide.md`
- **Test Helpers**: `tests/utils/auth-helpers.ts`
- **AG Grid Tests**: `ATTRIBUTE-MAPPING-AG-GRID-TESTS.md` (detailed documentation)
