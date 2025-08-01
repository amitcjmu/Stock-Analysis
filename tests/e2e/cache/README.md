# Cache Testing Suite

Comprehensive Playwright test suite for validating Redis caching implementation in the AI Force Migration Platform.

## Overview

This test suite validates that the caching implementation achieves:
- **70%+ reduction in API calls**
- **50%+ improvement in page load times**
- **100% multi-tenant isolation**
- **Sub-50ms cache response times**
- **Robust security and error handling**

## Test Structure

```
tests/e2e/cache/
├── utils/
│   ├── cache-test-utils.ts        # Core cache testing utilities
│   ├── performance-monitor.ts     # Performance tracking and metrics
│   └── security-test-utils.ts     # Security validation utilities
├── cache-operations.spec.ts       # Basic cache functionality tests
├── performance.spec.ts           # Performance validation tests
├── security.spec.ts              # Security and isolation tests
├── integration.spec.ts           # Integration and degradation tests
├── websocket-cache.spec.ts       # Real-time cache event tests
├── playwright.config.ts          # Test configuration
├── global-setup.ts              # Test environment setup
├── global-teardown.ts           # Test cleanup
└── README.md                     # This file
```

## Prerequisites

1. **Environment Setup**
   ```bash
   # Install dependencies
   npm install

   # Start the application
   npm run dev

   # Ensure Redis is running
   docker run -d -p 6379:6379 redis:latest
   ```

2. **Environment Variables**
   ```bash
   export TEST_URL=http://localhost:3000
   export ADMIN_TOKEN=your-admin-token
   export REDIS_ENABLED=true
   export CACHE_ANALYTICS_ENABLED=true
   ```

## Running Tests

### Run All Cache Tests
```bash
npx playwright test --config=tests/e2e/cache/playwright.config.ts
```

### Run Specific Test Suites

**Cache Operations**
```bash
npx playwright test cache-operations.spec.ts --config=tests/e2e/cache/playwright.config.ts
```

**Performance Tests**
```bash
npx playwright test performance.spec.ts --config=tests/e2e/cache/playwright.config.ts
```

**Security Tests**
```bash
npx playwright test security.spec.ts --config=tests/e2e/cache/playwright.config.ts
```

**Integration Tests**
```bash
npx playwright test integration.spec.ts --config=tests/e2e/cache/playwright.config.ts
```

**WebSocket Cache Events**
```bash
npx playwright test websocket-cache.spec.ts --config=tests/e2e/cache/playwright.config.ts
```

### Run Tests by Project

**Chrome Desktop (Primary)**
```bash
npx playwright test --project=cache-chrome --config=tests/e2e/cache/playwright.config.ts
```

**Security Testing**
```bash
npx playwright test --project=cache-security --config=tests/e2e/cache/playwright.config.ts
```

**Performance with Network Throttling**
```bash
npx playwright test --project=cache-performance-slow --config=tests/e2e/cache/playwright.config.ts
```

## Test Categories

### 1. Cache Operations Tests (`cache-operations.spec.ts`)

Tests basic caching functionality:
- Cache hit/miss scenarios
- ETag validation and conditional requests
- Cache header validation
- Concurrent request handling
- Cache TTL and expiration
- Error handling and graceful degradation

**Key Validations:**
- ✅ 304 Not Modified responses for unchanged data
- ✅ Proper ETag generation and validation
- ✅ Cache metadata inclusion in responses
- ✅ Multi-tenant cache key isolation

### 2. Performance Tests (`performance.spec.ts`)

Validates performance improvements:
- API call reduction measurement
- Page load time comparisons
- Cache response time validation
- Concurrent load testing
- Memory usage monitoring
- Network efficiency

**Success Criteria:**
- ✅ 70%+ API call reduction with caching
- ✅ 50%+ page load time improvement
- ✅ Sub-50ms cached response times
- ✅ 80%+ cache hit ratio under load

### 3. Security Tests (`security.spec.ts`)

Validates security and isolation:
- Multi-tenant cache isolation
- Cache poisoning prevention
- Unauthorized access blocking
- Input sanitization
- ETag security validation
- Access control validation

**Security Requirements:**
- ✅ 100% tenant data isolation
- ✅ No cache poisoning vulnerabilities
- ✅ Proper access controls
- ✅ Secure cache key generation

### 4. Integration Tests (`integration.spec.ts`)

Tests system integration:
- Graceful degradation when Redis unavailable
- Feature flag functionality
- Cache synchronization across tabs
- Navigation cache behavior
- Authentication state changes
- End-to-end workflows

**Integration Validations:**
- ✅ Application works without Redis
- ✅ Feature flags control cache behavior
- ✅ Cache persists across page refreshes
- ✅ Authentication changes handled properly

### 5. WebSocket Cache Events (`websocket-cache.spec.ts`)

Tests real-time cache invalidation:
- WebSocket connection establishment
- Cache invalidation event delivery
- Multi-client event broadcasting
- Connection recovery
- Event subscription management
- Error handling

**Real-time Features:**
- ✅ WebSocket connections established
- ✅ Cache events delivered in real-time
- ✅ Multi-client synchronization
- ✅ Connection resilience

## Test Utilities

### CacheTestUtils
Core utilities for cache testing:
```typescript
const cacheUtils = new CacheTestUtils(page);

// Clear all caches
await cacheUtils.clearAllCaches();

// Get cache metrics
const metrics = await cacheUtils.getCacheMetrics();

// Test ETag conditional requests
const result = await cacheUtils.testETagConditionalRequest('/api/v1/context/me');

// Wait for cache invalidation events
const eventReceived = await cacheUtils.waitForCacheInvalidation('user', 'user-123');
```

### PerformanceMonitor
Performance tracking and analysis:
```typescript
const monitor = new PerformanceMonitor(page);

// Start monitoring
await monitor.startMonitoring();

// Capture baseline metrics
const baseline = await monitor.captureBaseline();

// Get comprehensive metrics
const metrics = await monitor.getMetrics();

// Generate comparison report
const report = monitor.generateComparisonReport(cachedMetrics, uncachedMetrics);
```

### SecurityTestUtils
Security validation utilities:
```typescript
const security = new SecurityTestUtils(page, browser);

// Test multi-tenant isolation
const result = await security.testMultiTenantIsolation('tenant1@example.com', 'tenant2@example.com', '/api/v1/context/me');

// Test cache poisoning prevention
const poisonResult = await security.testCachePoisoningPrevention(maliciousPayload);

// Run comprehensive security suite
const suiteResults = await security.runSecurityTestSuite();
```

## Test Reports

### HTML Report
Interactive HTML report with detailed test results:
```bash
npx playwright show-report cache-test-results
```

### JSON Report
Machine-readable test results:
```bash
cat cache-test-results.json | jq '.suites[].specs[] | select(.ok == false)'
```

### Performance Metrics
View performance comparison data:
```bash
cat cache-test-summary.json | jq '.performance'
```

## Troubleshooting

### Common Issues

**Redis Connection Failed**
```bash
# Check Redis is running
docker ps | grep redis

# Start Redis if needed
docker run -d -p 6379:6379 redis:latest
```

**Authentication Issues**
```bash
# Verify test user exists
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "demo123"}'
```

**WebSocket Connection Failed**
```bash
# Check WebSocket endpoint
wscat -c ws://localhost:3000/api/v1/ws-cache/events?client_account_id=demo-client
```

**Performance Tests Failing**
- Ensure Redis is running and properly configured
- Check network conditions and system load
- Verify baseline measurements are realistic
- Run tests with `--headed` to observe behavior

### Debug Mode

Run tests in debug mode:
```bash
npx playwright test --debug --config=tests/e2e/cache/playwright.config.ts
```

Enable slow motion:
```bash
SLOW_MO=1000 npx playwright test --headed --config=tests/e2e/cache/playwright.config.ts
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Cache Tests
on: [push, pull_request]

jobs:
  cache-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:latest
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - run: npm ci
      - run: npx playwright install
      - run: npm run build

      - name: Run Cache Tests
        run: npx playwright test --config=tests/e2e/cache/playwright.config.ts
        env:
          REDIS_ENABLED: true
          TEST_URL: http://localhost:3000

      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: cache-test-results
          path: cache-test-results/
```

## Success Criteria Summary

### Performance Targets
- [ ] **70%+ API call reduction** with caching enabled
- [ ] **50%+ page load time improvement** on subsequent visits
- [ ] **Sub-50ms response times** for cached requests
- [ ] **80%+ cache hit ratio** under normal load
- [ ] **95%+ uptime** with graceful degradation

### Security Requirements
- [ ] **100% tenant isolation** - no data leakage between tenants
- [ ] **Zero cache poisoning** vulnerabilities
- [ ] **Proper access controls** on admin endpoints
- [ ] **Secure cache keys** with no sensitive data exposure
- [ ] **Input sanitization** for all cache operations

### Functional Requirements
- [ ] **ETag support** with 304 Not Modified responses
- [ ] **Real-time invalidation** via WebSocket events
- [ ] **Feature flag control** over cache behavior
- [ ] **Graceful degradation** when Redis unavailable
- [ ] **Multi-browser compatibility**

## Contributing

When adding new cache tests:

1. Follow the existing patterns in test utilities
2. Add comprehensive error handling
3. Include performance assertions where applicable
4. Document expected behavior clearly
5. Test both success and failure scenarios
6. Update this README with new test descriptions

## Support

For issues with cache testing:
1. Check the troubleshooting section above
2. Review test logs and HTML reports
3. Verify environment setup and dependencies
4. Test cache functionality manually first
5. Create detailed issue reports with reproduction steps

Generated by CC (Claude Code)
