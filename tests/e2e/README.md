# E2E Test Suite - Migration Orchestrator

Comprehensive end-to-end tests for the Migration Orchestrator platform using Playwright.

## Overview

This test suite covers all major user flows:
- ✅ Authentication (login/logout)
- ✅ Collection Flow (data import/export)
- ✅ Discovery Flow (application inventory)
- ✅ Assessment Flow (readiness/risk analysis)
- ✅ Planning Flow (migration waves)
- ✅ Execution Flow (migration status)
- ✅ Decommission, FinOps, Modernize flows

**Test Framework**: [Playwright](https://playwright.dev/)  
**Language**: TypeScript  
**Target Environment**: Docker (http://localhost:8081)

## Running Tests

### Run All Tests
```bash
npm run test:e2e
```

### Run Specific Tests
```bash
# Single test file
npx playwright test tests/e2e/flow-discovery.spec.ts

# With headed browser (watch tests execute)
npx playwright test tests/e2e/flow-discovery.spec.ts --headed

# Debug mode
npx playwright test tests/e2e/flow-discovery.spec.ts --debug
```

### View Results
```bash
# Open HTML report
npx playwright show-report test-results/html
```

## Test Structure
```
tests/
├── e2e/                    # Production E2E tests
│   ├── flow-*.spec.ts      # Flow-specific tests
│   └── migration-*.spec.ts # Platform-wide tests
├── utils/                  # Shared utilities
│   └── auth-helpers.ts     # Authentication helpers
├── fixtures/               # Test data
│   └── test-cmdb-data.csv
└── debug/                  # Debug helpers (excluded from CI)
```

## Writing Tests

### Use Shared Helpers
```typescript
import { loginAndNavigateToFlow } from '../utils/auth-helpers';

test.beforeEach(async ({ page }) => {
  await loginAndNavigateToFlow(page, 'Discovery');
});
```

### Use Proper Waits
```typescript
// ✅ Good
await expect(page.locator('.element')).toBeVisible({ timeout: 5000 });

// ❌ Bad
await page.waitForTimeout(2000);
```

### Write Strong Assertions
```typescript
// ✅ Good
expect(count).toBeGreaterThan(0);

// ❌ Bad
console.log('Count:', count);
```

## Best Practices

1. ✅ Use shared helpers - Don't duplicate auth code
2. ✅ Proper waits - No `waitForTimeout`
3. ✅ Strong assertions - Use `expect`, not just `console.log`
4. ✅ Test isolation - Clean up after each test
5. ✅ Clear test names - Describe what is being tested

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
