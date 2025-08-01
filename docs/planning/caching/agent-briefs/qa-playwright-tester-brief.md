# Task Brief: qa-playwright-tester

## Mission
Create comprehensive Playwright test suites to validate cache functionality, performance improvements, multi-tenant isolation, and ensure the caching implementation meets all quality and security requirements.

## Context
We're implementing a Redis caching solution that must reduce API calls by 70-80% and page load times by 50%. Your tests will validate these improvements while ensuring no functionality is broken and security is maintained.

## Primary Objectives

### 1. Cache Functionality Testing (Week 2-3)
- Test cache hit/miss scenarios
- Validate ETag and conditional requests
- Test cache invalidation triggers
- Verify WebSocket cache events

### 2. Performance Testing (Week 3-4)
- Measure API call reduction
- Track page load improvements
- Monitor memory usage
- Validate response times

### 3. Security Testing (Week 3)
- Test multi-tenant cache isolation
- Verify encrypted data in cache
- Test unauthorized access attempts
- Validate cache poisoning prevention

### 4. Integration Testing (Week 4-5)
- Test frontend-backend cache sync
- Validate graceful degradation
- Test feature flag functionality
- Verify rollback procedures

## Specific Deliverables

### Week 2-3: Cache Functionality Tests

```typescript
// File: tests/e2e/cache/cache-operations.spec.ts
import { test, expect } from '@playwright/test';
import { CacheTestUtils } from './utils/cache-test-utils';

test.describe('Cache Operations', () => {
  let cacheUtils: CacheTestUtils;
  
  test.beforeEach(async ({ page }) => {
    cacheUtils = new CacheTestUtils(page);
    await cacheUtils.clearAllCaches();
  });
  
  test('should return 304 Not Modified for unchanged data', async ({ page }) => {
    // First request - cache miss
    const response1 = await page.request.get('/api/v1/context/me');
    expect(response1.status()).toBe(200);
    expect(response1.headers()['x-cache']).toBe('MISS');
    
    const etag = response1.headers()['etag'];
    expect(etag).toBeTruthy();
    
    // Second request with ETag - cache hit
    const response2 = await page.request.get('/api/v1/context/me', {
      headers: { 'If-None-Match': etag }
    });
    expect(response2.status()).toBe(304);
  });
  
  test('should invalidate cache on user update', async ({ page }) => {
    // Load user context
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="user-context"]')).toBeVisible();
    
    // Get initial cache state
    const initialCalls = await cacheUtils.getApiCallCount('/api/v1/context/me');
    
    // Update user role
    await page.goto('/admin/users');
    await page.click('[data-testid="edit-user-btn"]');
    await page.selectOption('[data-testid="user-role-select"]', 'admin');
    await page.click('[data-testid="save-btn"]');
    
    // Navigate back to dashboard
    await page.goto('/dashboard');
    
    // Verify cache was invalidated (new API call made)
    const newCalls = await cacheUtils.getApiCallCount('/api/v1/context/me');
    expect(newCalls).toBe(initialCalls + 1);
  });
  
  test('should handle WebSocket cache invalidation', async ({ page }) => {
    await page.goto('/discovery/field-mappings');
    
    // Set up WebSocket listener
    const wsMessages: any[] = [];
    page.on('websocket', ws => {
      ws.on('message', data => wsMessages.push(JSON.parse(data)));
    });
    
    // Trigger bulk approval
    await page.click('[data-testid="select-all-mappings"]');
    await page.click('[data-testid="bulk-approve-btn"]');
    
    // Verify WebSocket invalidation event
    await expect.poll(() => 
      wsMessages.some(msg => 
        msg.type === 'cache_invalidation' && 
        msg.entity === 'field_mappings'
      )
    ).toBeTruthy();
    
    // Verify UI updated without manual refresh
    await expect(page.locator('[data-testid="approval-count"]')).toHaveText(/Approved: \d+/);
  });
});
```

### Week 3-4: Performance Tests

```typescript
// File: tests/e2e/cache/performance.spec.ts
import { test, expect } from '@playwright/test';
import { PerformanceMonitor } from './utils/performance-monitor';

test.describe('Cache Performance', () => {
  let monitor: PerformanceMonitor;
  
  test.beforeEach(async ({ page }) => {
    monitor = new PerformanceMonitor(page);
    await monitor.startMonitoring();
  });
  
  test.afterEach(async () => {
    const metrics = await monitor.getMetrics();
    console.log('Performance Metrics:', metrics);
  });
  
  test('should reduce API calls by 70%', async ({ page }) => {
    // Baseline: measure without cache
    await page.addInitScript(() => {
      window.FEATURE_FLAGS = { DISABLE_ALL_CACHING: true };
    });
    
    await page.goto('/dashboard');
    await page.goto('/discovery/flows');
    await page.goto('/dashboard'); // Return to dashboard
    
    const baselineMetrics = await monitor.getMetrics();
    
    // With cache enabled
    await page.reload();
    await page.addInitScript(() => {
      window.FEATURE_FLAGS = { DISABLE_ALL_CACHING: false };
    });
    
    await page.goto('/dashboard');
    await page.goto('/discovery/flows');
    await page.goto('/dashboard');
    
    const cachedMetrics = await monitor.getMetrics();
    
    // Verify 70% reduction
    const reduction = 1 - (cachedMetrics.apiCalls / baselineMetrics.apiCalls);
    expect(reduction).toBeGreaterThanOrEqual(0.7);
  });
  
  test('should reduce page load time by 50%', async ({ page }) => {
    // Measure initial load time (cold cache)
    const startCold = Date.now();
    await page.goto('/discovery/field-mappings');
    await page.waitForLoadState('networkidle');
    const coldLoadTime = Date.now() - startCold;
    
    // Measure with warm cache
    const startWarm = Date.now();
    await page.reload();
    await page.waitForLoadState('networkidle');
    const warmLoadTime = Date.now() - startWarm;
    
    // Verify 50% improvement
    const improvement = 1 - (warmLoadTime / coldLoadTime);
    expect(improvement).toBeGreaterThanOrEqual(0.5);
  });
});
```

### Week 3: Security Tests

```typescript
// File: tests/e2e/cache/security.spec.ts
import { test, expect } from '@playwright/test';
import { SecurityTestUtils } from './utils/security-test-utils';

test.describe('Cache Security', () => {
  let security: SecurityTestUtils;
  
  test.beforeEach(async ({ page }) => {
    security = new SecurityTestUtils(page);
  });
  
  test('should isolate cache by tenant', async ({ browser }) => {
    // Create two contexts for different tenants
    const tenant1 = await browser.newContext();
    const tenant2 = await browser.newContext();
    
    // Login as users from different tenants
    const page1 = await tenant1.newPage();
    await security.loginAsUser(page1, 'tenant1_user@example.com');
    
    const page2 = await tenant2.newPage();
    await security.loginAsUser(page2, 'tenant2_user@example.com');
    
    // Load same endpoint for both
    await page1.goto('/api/v1/clients');
    await page2.goto('/api/v1/clients');
    
    // Verify different data returned
    const data1 = await page1.evaluate(() => 
      fetch('/api/v1/clients').then(r => r.json())
    );
    const data2 = await page2.evaluate(() => 
      fetch('/api/v1/clients').then(r => r.json())
    );
    
    expect(data1).not.toEqual(data2);
    
    // Verify cache keys include tenant context
    const cacheKeys1 = await security.getCacheKeys(page1);
    const cacheKeys2 = await security.getCacheKeys(page2);
    
    expect(cacheKeys1.every(k => k.includes('tenant:tenant1'))).toBeTruthy();
    expect(cacheKeys2.every(k => k.includes('tenant:tenant2'))).toBeTruthy();
  });
  
  test('should prevent cache poisoning', async ({ page }) => {
    await security.loginAsUser(page, 'attacker@example.com');
    
    // Attempt to poison cache with malicious data
    const maliciousResponse = await page.request.put('/api/v1/context/me', {
      data: {
        user: { id: 'admin', role: 'super_admin' }
      }
    });
    
    // Verify request rejected
    expect(maliciousResponse.status()).toBe(403);
    
    // Verify cache not poisoned
    await security.loginAsUser(page, 'normal_user@example.com');
    const context = await page.request.get('/api/v1/context/me');
    const data = await context.json();
    
    expect(data.user.role).not.toBe('super_admin');
  });
});
```

### Week 4-5: Integration Tests

```typescript
// File: tests/e2e/cache/integration.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Cache Integration', () => {
  test('should gracefully degrade when Redis unavailable', async ({ page }) => {
    // Simulate Redis failure
    await page.route('**/health/redis', route => 
      route.fulfill({ status: 503 })
    );
    
    // Application should still work
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    
    // Verify degraded mode indicator
    await expect(page.locator('[data-testid="cache-status"]')).toHaveText('Degraded');
  });
  
  test('should respect feature flags', async ({ page }) => {
    // Disable caching via feature flag
    await page.addInitScript(() => {
      window.FEATURE_FLAGS = {
        USE_REDIS_CACHE: false,
        USE_CUSTOM_API_CACHE: true
      };
    });
    
    await page.goto('/dashboard');
    
    // Verify Redis not used
    const requests = await page.evaluate(() => 
      performance.getEntriesByType('resource')
        .filter(r => r.name.includes('/api/'))
    );
    
    for (const req of requests) {
      const response = await page.request.get(req.name);
      expect(response.headers()['x-cache']).toBeUndefined();
    }
  });
});
```

## Test Utilities

```typescript
// File: tests/e2e/cache/utils/cache-test-utils.ts
export class CacheTestUtils {
  constructor(private page: Page) {}
  
  async clearAllCaches() {
    // Clear browser cache
    await this.page.context().clearCookies();
    await this.page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // Clear server cache via API
    await this.page.request.post('/api/v1/admin/cache/clear', {
      headers: { 'X-Admin-Token': process.env.ADMIN_TOKEN }
    });
  }
  
  async getApiCallCount(endpoint: string): Promise<number> {
    return this.page.evaluate((ep) => {
      return performance.getEntriesByType('resource')
        .filter(r => r.name.includes(ep)).length;
    }, endpoint);
  }
  
  async getCacheMetrics(): Promise<CacheMetrics> {
    const response = await this.page.request.get('/api/v1/admin/cache/metrics');
    return response.json();
  }
}
```

## Success Criteria

### Functional Requirements
- All cache operations work correctly
- Cache invalidation triggers properly
- WebSocket events deliver reliably
- Feature flags control behavior

### Performance Requirements
- 70%+ reduction in API calls
- 50%+ reduction in page load time
- Cache operations < 50ms
- No memory leaks

### Security Requirements
- 100% tenant isolation
- No cache poisoning vulnerabilities
- Encrypted sensitive data
- Proper access controls

## Test Environment Setup

```yaml
# File: tests/e2e/cache/playwright.config.ts
export default defineConfig({
  use: {
    baseURL: process.env.TEST_URL || 'http://localhost:3000',
    extraHTTPHeaders: {
      'X-Test-Mode': 'true',
    },
  },
  
  projects: [
    {
      name: 'Cache Tests',
      testDir: './cache',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'tests/auth/user.json',
      },
    },
  ],
  
  webServer: {
    command: 'docker compose up -d && npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
});
```

## Communication
- Daily test results in progress dashboard
- Immediate escalation of critical bugs
- Weekly test coverage reports
- Coordinate with all team members on test scenarios

## Timeline
- Week 2-3: Core functionality tests
- Week 3-4: Performance and security tests
- Week 4-5: Integration and regression tests
- Week 6: Final validation and signoff

---
**Assigned by**: Claude Code (Orchestrator)
**Start Date**: Week 2 of project
**Priority**: Critical for quality assurance