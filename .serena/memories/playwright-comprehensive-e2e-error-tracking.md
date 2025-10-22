# Playwright Comprehensive E2E Testing with Error Tracking

## Pattern: Complete Error Detection in Browser Tests

### Test Structure with Error Tracking

```typescript
import { test, expect } from '@playwright/test';

test.describe('Comprehensive Flow Testing', () => {
  let consoleErrors: string[] = [];
  let consoleWarnings: string[] = [];
  let networkErrors: Array<{ url: string; status: number }> = [];

  test.beforeEach(async ({ page }) => {
    // Reset error collectors
    consoleErrors = [];
    consoleWarnings = [];
    networkErrors = [];

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(msg.text());
      }
    });

    // Capture network errors (4xx, 5xx)
    page.on('response', response => {
      if (response.status() >= 400) {
        networkErrors.push({
          url: response.url(),
          status: response.status()
        });
      }
    });

    // Capture uncaught exceptions
    page.on('pageerror', error => {
      consoleErrors.push(`Uncaught exception: ${error.message}`);
    });
  });

  test.afterEach(async () => {
    // Report errors at end of each test
    if (consoleErrors.length > 0) {
      console.log('Console Errors:', JSON.stringify(consoleErrors, null, 2));
    }
    if (networkErrors.length > 0) {
      console.log('Network Errors:', JSON.stringify(networkErrors, null, 2));
    }
  });
});
```

### Multi-Tenant Header Configuration

```typescript
// Fixture for authenticated context with multi-tenant headers
test.beforeEach(async ({ page }) => {
  // Set multi-tenant headers for ALL requests
  await page.route('**/*', async (route) => {
    const headers = {
      ...route.request().headers(),
      'X-Client-Account-Id': '1',
      'X-Engagement-Id': '1',
    };
    await route.continue({ headers });
  });

  // Login flow
  await page.goto('http://localhost:8081/login');
  await page.fill('[name="email"]', 'demo@demo-corp.com');
  await page.fill('[name="password"]', 'Demo123!');
  await page.click('button[type="submit"]');
  await page.waitForURL(/.*\//, { timeout: 10000 });
});
```

### Comprehensive Route Testing Pattern

```typescript
test('All assessment routes load successfully', async ({ page }) => {
  // Step 1: Create or get flow ID
  await page.goto('http://localhost:8081/assessment/overview');

  // Extract flowId from URL after creation/selection
  await page.click('text=Start New Assessment');
  await page.waitForURL(/\/assessment\/[a-f0-9-]+\/architecture/);

  const url = page.url();
  const flowId = url.match(/\/assessment\/([a-f0-9-]+)\//)?.[1];
  expect(flowId).toBeTruthy();

  // Step 2: Test all phase routes
  const routes = [
    'architecture',
    'technical-debt',
    'risk',
    'complexity'
  ];

  for (const route of routes) {
    const response = await page.goto(
      `http://localhost:8081/assessment/${flowId}/${route}`
    );
    expect(response.status()).toBe(200);

    // Verify phase-specific content loads
    await expect(page.locator('h1')).toBeVisible({ timeout: 5000 });
  }

  // Step 3: Verify no errors accumulated
  expect(consoleErrors.filter(e =>
    !e.includes('Download the React DevTools')
  )).toHaveLength(0);
  expect(networkErrors).toHaveLength(0);
});
```

### API Endpoint Testing Pattern

```typescript
test('API endpoints return correct status codes', async ({ page }) => {
  // Test valid flow ID
  const validResponse = await page.request.get(
    '/api/v1/master-flows/valid-uuid-here',
    {
      headers: {
        'X-Client-Account-Id': '1',
        'X-Engagement-Id': '1'
      }
    }
  );
  expect(validResponse.status()).toBe(200);

  // Test invalid flow ID - should be 404, NOT 405
  const invalidResponse = await page.request.get(
    '/api/v1/master-flows/00000000-0000-0000-0000-000000000000',
    {
      headers: {
        'X-Client-Account-Id': '1',
        'X-Engagement-Id': '1'
      }
    }
  );
  expect(invalidResponse.status()).toBe(404);
  expect(invalidResponse.status()).not.toBe(405); // Verify not "Method Not Allowed"
});
```

### Database State Verification

```typescript
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

test('Flow persisted to database', async ({ page }) => {
  // Create flow in UI
  await page.goto('http://localhost:8081/assessment/overview');
  await page.click('text=Start New Assessment');
  await page.waitForURL(/\/assessment\/[a-f0-9-]+\//);

  const flowId = page.url().match(/\/assessment\/([a-f0-9-]+)\//)?.[1];

  // Verify in database
  const { stdout } = await execAsync(
    `docker exec -i migration_postgres psql -U postgres -d migration_db -c "SELECT flow_id FROM migration.discovery_flows WHERE flow_id = '${flowId}';" -t`
  );

  expect(stdout.trim()).toBe(flowId);
});
```

### Backend Log Verification

```typescript
test('No backend errors during flow', async ({ page }) => {
  // Capture timestamp before test
  const startTime = new Date().toISOString();

  // Perform test actions
  await page.goto('http://localhost:8081/assessment/overview');
  // ... test steps

  // Check backend logs for errors after test
  const { stdout } = await execAsync(
    `docker logs migration_backend --since ${startTime} 2>&1 | grep -i "error\\|exception\\|traceback"`
  );

  // Filter expected warnings
  const errors = stdout.split('\n').filter(line =>
    line.trim() &&
    !line.includes('INFO') &&
    !line.includes('WARNING')
  );

  expect(errors).toHaveLength(0);
});
```

## Test Organization Pattern

```
tests/e2e/
├── assessment-flow-comprehensive.spec.ts    # Full E2E testing
├── bug-verification-*.spec.ts               # Targeted bug verification
└── helpers/
    ├── error-tracking.ts                    # Error collector utilities
    ├── auth.ts                              # Login/auth helpers
    └── database.ts                          # DB verification utilities
```

### Error Tracking Helpers

```typescript
// tests/e2e/helpers/error-tracking.ts
import { Page } from '@playwright/test';

export interface ErrorCollector {
  consoleErrors: string[];
  networkErrors: Array<{ url: string; status: number; statusText: string }>;
  uncaughtExceptions: string[];
}

export function setupErrorTracking(page: Page): ErrorCollector {
  const collector: ErrorCollector = {
    consoleErrors: [],
    networkErrors: [],
    uncaughtExceptions: []
  };

  page.on('console', msg => {
    if (msg.type() === 'error') {
      collector.consoleErrors.push(msg.text());
    }
  });

  page.on('response', response => {
    if (response.status() >= 400) {
      collector.networkErrors.push({
        url: response.url(),
        status: response.status(),
        statusText: response.statusText()
      });
    }
  });

  page.on('pageerror', error => {
    collector.uncaughtExceptions.push(error.message);
  });

  return collector;
}

export function filterExpectedErrors(errors: string[]): string[] {
  const expectedPatterns = [
    /Download the React DevTools/,
    /favicon\.ico/
  ];

  return errors.filter(error =>
    !expectedPatterns.some(pattern => pattern.test(error))
  );
}
```

### Usage in Test

```typescript
import { setupErrorTracking, filterExpectedErrors } from './helpers/error-tracking';

test('Flow with error tracking', async ({ page }) => {
  const errors = setupErrorTracking(page);

  // Perform test
  await page.goto('http://localhost:8081/assessment');
  // ... test steps

  // Verify no unexpected errors
  const unexpectedErrors = filterExpectedErrors(errors.consoleErrors);
  expect(unexpectedErrors).toHaveLength(0);
  expect(errors.networkErrors).toHaveLength(0);
});
```

## Test Evidence Collection

```typescript
test('Full flow with evidence collection', async ({ page }, testInfo) => {
  const errors = setupErrorTracking(page);

  try {
    // Test steps
    await page.goto('http://localhost:8081/assessment/overview');
    // ...
  } catch (error) {
    // Capture screenshot on failure
    const screenshot = await page.screenshot();
    await testInfo.attach('failure-screenshot', {
      body: screenshot,
      contentType: 'image/png'
    });

    // Capture error logs
    await testInfo.attach('console-errors', {
      body: JSON.stringify(errors.consoleErrors, null, 2),
      contentType: 'application/json'
    });

    await testInfo.attach('network-errors', {
      body: JSON.stringify(errors.networkErrors, null, 2),
      contentType: 'application/json'
    });

    throw error;
  }
});
```

## Playwright Configuration

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    baseURL: 'http://localhost:8081',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure'
  },

  // Retry failed tests once
  retries: 1,

  // Run tests in parallel
  workers: 1, // Use 1 for Docker environment

  // Global timeout
  timeout: 30000,

  // Test output directory
  outputDir: 'test-results/',

  // Projects
  projects: [
    {
      name: 'chrome',
      use: {
        browserName: 'chromium',
        viewport: { width: 1280, height: 720 }
      }
    }
  ]
});
```

## Best Practices

1. **Always capture errors** - Console, network, and exceptions
2. **Filter expected errors** - DevTools warnings, favicon 404s
3. **Test with real headers** - Multi-tenant headers on all requests
4. **Verify backend state** - Check database and logs
5. **Collect evidence on failure** - Screenshots, videos, traces
6. **Use helpers** - Reusable error tracking and auth utilities
7. **Test error paths** - Invalid IDs, missing data, edge cases

## Common Patterns

### Pattern: Wait for API Response
```typescript
const responsePromise = page.waitForResponse(
  response => response.url().includes('/api/v1/master-flows')
);
await page.click('button');
const response = await responsePromise;
expect(response.status()).toBe(200);
```

### Pattern: Verify Loading States
```typescript
await expect(page.locator('.loading')).toBeVisible();
await expect(page.locator('.loading')).not.toBeVisible({ timeout: 10000 });
```

### Pattern: Multi-Step Flow
```typescript
// Step 1: Login
await loginAs(page, 'demo@demo-corp.com', 'Demo123!');

// Step 2: Navigate
await page.goto('/assessment/overview');

// Step 3: Create flow
const flowId = await createAssessment(page);

// Step 4: Complete phases
await completeArchitecturePhase(page, flowId);
await completeTechnicalDebtPhase(page, flowId);

// Step 5: Verify
expect(errors.consoleErrors).toHaveLength(0);
```

## Benefits

- **Comprehensive Coverage**: Catches console, network, and exception errors
- **Evidence Collection**: Automatic screenshots and logs on failure
- **Regression Prevention**: Tests remain for future verification
- **Multi-Tenant Testing**: Proper header injection for all requests
- **Database Verification**: Confirms backend persistence
