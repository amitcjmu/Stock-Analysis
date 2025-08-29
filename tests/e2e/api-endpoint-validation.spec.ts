import { test, expect, Page } from '@playwright/test';

/**
 * API Endpoint Validation Test Suite
 *
 * Tests specific API endpoints to ensure they are working correctly after the consolidation.
 */

test.describe('API Endpoint Validation Tests', () => {
  test('should validate key API endpoints are accessible', async ({ page }) => {
    const apiTests = [
      {
        name: 'Backend Health',
        url: 'http://localhost:8000/api/v1/health',
        expectStatus: 200
      },
      {
        name: 'Database Health',
        url: 'http://localhost:8000/api/v1/health/database',
        expectStatus: 200
      },
      {
        name: 'Unified Discovery Health',
        url: 'http://localhost:8000/api/v1/unified-discovery/health',
        expectStatus: 200
      },
      {
        name: 'Flow Health (plural convention)',
        url: 'http://localhost:8000/api/v1/flows/health',
        expectStatus: [200, 400, 401] // May return auth errors but shouldn't 404
      }
    ];

    for (const apiTest of apiTests) {
      console.log(`Testing ${apiTest.name}...`);

      const response = await page.goto(apiTest.url);
      expect(response).not.toBeNull();

      const status = response!.status();
      console.log(`${apiTest.name}: HTTP ${status}`);

      if (Array.isArray(apiTest.expectStatus)) {
        expect(apiTest.expectStatus).toContain(status);
      } else {
        expect(status).toBe(apiTest.expectStatus);
      }

      // Ensure it's not a 404
      expect(status).not.toBe(404);
    }
  });

  test('should verify unified discovery endpoints use plural flows', async ({ page }) => {
    const apiCalls: { url: string; status: number }[] = [];

    // Monitor all API calls
    page.on('response', (response) => {
      if (response.url().includes('/api/v1/')) {
        apiCalls.push({
          url: response.url(),
          status: response.status()
        });
      }
    });

    // Navigate to Discovery Dashboard to trigger API calls
    await page.goto('http://localhost:8081/discover');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    console.log('All API calls detected:', apiCalls);

    // Check for any calls to legacy singular endpoints
    const legacySingularCalls = apiCalls.filter(call => {
      const url = call.url;
      return (
        url.includes('/unified-discovery/flow/') ||
        url.match(/\/flow\/[^/]+\/status/) ||
        url.match(/\/flow\/[^/]+\/execute/) ||
        url.includes('/flow/initialize') ||
        url.includes('/flow/active')
      ) && !url.includes('/flows/'); // Exclude if it's actually /flows/
    });

    if (legacySingularCalls.length > 0) {
      console.error('Legacy singular endpoints found:', legacySingularCalls);
      expect(legacySingularCalls).toEqual([]);
    }

    // Check that no flow-related endpoints returned 404
    const flowRelated404s = apiCalls.filter(call =>
      call.status === 404 &&
      (call.url.includes('/flow') || call.url.includes('/flows'))
    );

    if (flowRelated404s.length > 0) {
      console.error('404 errors on flow endpoints:', flowRelated404s);
      expect(flowRelated404s).toEqual([]);
    }
  });

  test('should test API endpoints directly for correct responses', async ({ page }) => {
    // Test active flows endpoint
    const activeFlowsResponse = await page.goto(
      'http://localhost:8000/api/v1/unified-discovery/flows/active'
    );

    // Should not be 404 (may be auth error, but endpoint exists)
    expect(activeFlowsResponse?.status()).not.toBe(404);
    console.log(`Active flows endpoint: HTTP ${activeFlowsResponse?.status()}`);

    // Test health endpoint
    const healthResponse = await page.goto(
      'http://localhost:8000/api/v1/unified-discovery/health'
    );

    expect(healthResponse?.status()).toBe(200);
    console.log(`Discovery health endpoint: HTTP ${healthResponse?.status()}`);
  });

  test('should verify frontend makes correct API calls', async ({ page }) => {
    const requestUrls: string[] = [];

    // Monitor outgoing requests
    page.on('request', (request) => {
      if (request.url().includes('/api/v1/')) {
        requestUrls.push(request.url());
      }
    });

    // Navigate to the app
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');

    // Navigate to discover page
    await page.goto('http://localhost:8081/discover');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    console.log('Frontend API requests:', requestUrls);

    // Verify no legacy singular endpoints are being called
    const legacySingularRequests = requestUrls.filter(url =>
      url.match(/\/flow\/[^/]+\//) && !url.includes('/flows/')
    );

    expect(legacySingularRequests).toEqual([]);
  });
});
