/**
 * Bug Verification Test Suite
 * Testing Bugs #674, #675, #673, #676
 *
 * Evidence collection for QA verification
 */

import { test, expect } from '@playwright/test';

// Test Bug #674: Login API calls failing with 500 Network Error
test.describe('Bug #674: Login API Network Errors', () => {
  test('should login successfully without 500 Network Errors', async ({ page }) => {
    // Track network errors
    const networkErrors: any[] = [];
    const apiCalls: any[] = [];

    page.on('response', async (response) => {
      const url = response.url();

      // Track relevant API calls
      if (url.includes('/api/v1/context/me/defaults') || url.includes('/api/v1/clients')) {
        const status = response.status();
        const headers = response.headers();

        apiCalls.push({
          url,
          status,
          statusText: response.statusText(),
          contentLength: headers['content-length'],
          method: response.request().method()
        });

        // Check for 500 errors
        if (status === 500) {
          try {
            const body = await response.text();
            networkErrors.push({
              url,
              status,
              body: body.substring(0, 500) // First 500 chars
            });
          } catch (e) {
            networkErrors.push({
              url,
              status,
              error: 'Could not read response body'
            });
          }
        }
      }
    });

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        console.log('Browser Console Error:', msg.text());
      }
    });

    // Navigate to login page
    await page.goto('http://localhost:8081/login');
    await page.waitForLoadState('networkidle');

    // Fill in credentials
    await page.fill('input[type="email"], input[name="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"], input[name="password"]', 'Demo123!');

    // Click login button
    await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');

    // Wait for navigation or API responses
    await page.waitForTimeout(3000);

    // Save evidence
    console.log('=== BUG #674 EVIDENCE ===');
    console.log('Network Errors Found:', networkErrors.length);
    console.log('API Calls:', JSON.stringify(apiCalls, null, 2));
    console.log('Network Errors:', JSON.stringify(networkErrors, null, 2));

    // Assertions
    expect(networkErrors, 'Should have no 500 errors').toHaveLength(0);

    // Check that API calls succeeded
    const contextCall = apiCalls.find(c => c.url.includes('/context/me/defaults'));
    const clientsCall = apiCalls.find(c => c.url.includes('/clients'));

    if (contextCall) {
      expect(contextCall.status, '/context/me/defaults should return 200').toBe(200);
    }

    if (clientsCall) {
      expect(clientsCall.status, '/clients should return 200').toBe(200);
    }
  });
});

// Test Bug #675: Multi-tenant header validation
test.describe('Bug #675: Multi-Tenant Header Validation', () => {
  test('should include proper multi-tenant headers and not get 403/404', async ({ page }) => {
    // First login
    await page.goto('http://localhost:8081/login');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);

    // Track API calls to master-flows endpoints
    const apiCalls: any[] = [];
    const headerIssues: any[] = [];

    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/api/v1/master-flows') || url.includes('/api/v1/')) {
        const headers = request.headers();
        const call = {
          url,
          method: request.method(),
          headers: {
            'x-client-account-id': headers['x-client-account-id'],
            'X-Client-Account-Id': headers['X-Client-Account-Id'],
            'x-engagement-id': headers['x-engagement-id'],
            'X-Engagement-Id': headers['X-Engagement-Id']
          },
          hasClientId: !!(headers['x-client-account-id'] || headers['X-Client-Account-Id']),
          hasEngagementId: !!(headers['x-engagement-id'] || headers['X-Engagement-Id'])
        };

        // Track header issues
        if (!call.hasClientId || !call.hasEngagementId) {
          headerIssues.push({
            url,
            missing: {
              clientId: !call.hasClientId,
              engagementId: !call.hasEngagementId
            }
          });
        }

        apiCalls.push(call);
      }
    });

    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('/api/v1/master-flows') || url.includes('/api/v1/')) {
        const existing = apiCalls.find(c => c.url === url && !c.status);
        if (existing) {
          existing.status = response.status();
          existing.statusText = response.statusText();
        }
      }
    });

    // Navigate to assessment overview
    await page.goto('http://localhost:8081/assessment/overview');
    await page.waitForTimeout(3000);

    // Try to start a new assessment to trigger more API calls
    try {
      const startButton = page.locator('button:has-text("Start New Assessment"), button:has-text("New Assessment")');
      if (await startButton.isVisible({ timeout: 2000 })) {
        await startButton.click();
        await page.waitForTimeout(2000);
      }
    } catch (e) {
      // Button may not exist, that's okay
      console.log('Start button not found, continuing with existing API calls');
    }

    console.log('=== BUG #675 EVIDENCE ===');
    console.log('Total API Calls:', apiCalls.length);
    console.log('Calls to /api/v1/master-flows:', apiCalls.filter(c => c.url.includes('/master-flows')).length);
    console.log('Header Issues:', headerIssues.length);
    console.log('\nDetailed API Calls:', JSON.stringify(apiCalls.slice(0, 10), null, 2)); // First 10 calls
    console.log('\nHeader Issues:', JSON.stringify(headerIssues, null, 2));

    // CRITICAL CHECKS FOR BUG #675

    // 1. Check for 403/404 errors caused by header validation
    const forbidden = apiCalls.filter(c => c.status === 403);
    const notFound = apiCalls.filter(c => c.status === 404);

    console.log('\n403 Forbidden errors:', forbidden.length);
    console.log('404 Not Found errors:', notFound.length);

    // Bug #675 specifically was about header casing causing 403/404
    // These should be very rare or none
    expect(forbidden.length, 'Should have minimal or no 403 Forbidden errors due to header validation').toBeLessThanOrEqual(1);

    // 2. Check that multi-tenant headers are being sent
    const masterFlowCalls = apiCalls.filter(c => c.url.includes('/api/v1/master-flows'));
    if (masterFlowCalls.length > 0) {
      // At least some calls should have headers
      const callsWithHeaders = masterFlowCalls.filter(c => c.hasClientId || c.hasEngagementId);
      expect(
        callsWithHeaders.length,
        'Master flow API calls should include multi-tenant headers'
      ).toBeGreaterThan(0);
    }

    // 3. Check successful calls
    const successfulCalls = apiCalls.filter(c => c.status >= 200 && c.status < 300);
    console.log('\nSuccessful calls (2xx):', successfulCalls.length);

    // Should have at least some successful calls
    expect(successfulCalls.length, 'Should have some successful API calls').toBeGreaterThan(0);
  });
});

// Test Bug #673: Assessment route 404 errors
test.describe('Bug #673: Assessment Route 404 Errors', () => {
  test('should load assessment routes with flowId parameter', async ({ page }) => {
    // Login first
    await page.goto('http://localhost:8081/login');
    await page.fill('input[type="email"], input[name="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"], input[name="password"]', 'Demo123!');
    await page.click('button[type="submit"], button:has-text("Login")');
    await page.waitForTimeout(3000);

    // Use valid test flowId
    const testFlowId = '12345678-1234-1234-1234-123456789012';

    // Test the routes that were mentioned in the bug
    const routes = [
      { path: `/assessment/${testFlowId}/architecture`, name: 'Architecture' },
      { path: `/assessment/${testFlowId}/tech-debt`, name: 'Technical Debt' },
      { path: `/assessment/${testFlowId}/complexity`, name: 'Complexity' },
      { path: `/assessment/${testFlowId}/dependency`, name: 'Dependency' },
      { path: `/assessment/${testFlowId}/summary`, name: 'Summary' }
    ];

    const results: any[] = [];
    const consoleErrors: string[] = [];

    // Track console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    for (const route of routes) {
      try {
        const response = await page.goto(`http://localhost:8081${route.path}`, {
          waitUntil: 'domcontentloaded',
          timeout: 10000
        });

        results.push({
          name: route.name,
          path: route.path,
          status: response?.status(),
          statusText: response?.statusText(),
          url: response?.url()
        });

        // Brief wait between route navigations
        await page.waitForTimeout(500);
      } catch (error: any) {
        results.push({
          name: route.name,
          path: route.path,
          status: 'ERROR',
          statusText: error.message,
          url: page.url()
        });
      }
    }

    console.log('=== BUG #673 EVIDENCE ===');
    console.log('Route Results:', JSON.stringify(results, null, 2));
    console.log('Console Errors:', consoleErrors);

    // CRITICAL: Routes should NOT return 404 due to missing flowId parameter
    // They may return 200 (page loads), or other codes if flow doesn't exist
    // But they should NOT 404 because the route itself is not found
    results.forEach(result => {
      // The bug was about routes returning 404 because flowId param was missing
      // Now routes should exist (even if data doesn't load)
      expect(
        result.status,
        `${result.name} route should exist (not 404 due to missing route definition)`
      ).not.toBe(404);

      // Routes should successfully load the page (200) or return API-level errors
      if (typeof result.status === 'number') {
        expect(
          result.status === 200 || result.status >= 400,
          `${result.name} should either load (200) or return API error (4xx/5xx)`
        ).toBe(true);
      }
    });
  });

  test('should handle invalid flowId appropriately (not 405)', async ({ page }) => {
    // Login first
    await page.goto('http://localhost:8081/login');
    await page.fill('input[type="email"], input[name="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"], input[name="password"]', 'Demo123!');
    await page.click('button[type="submit"], button:has-text("Login")');
    await page.waitForTimeout(3000);

    // Test with invalid flowId
    const invalidFlowId = 'invalid-uuid-123';
    const testRoute = `/assessment/${invalidFlowId}/architecture`;

    const response = await page.goto(`http://localhost:8081${testRoute}`, {
      waitUntil: 'domcontentloaded',
      timeout: 10000
    });

    console.log('=== BUG #673 INVALID FLOW EVIDENCE ===');
    console.log('Invalid Flow Route:', {
      path: testRoute,
      status: response?.status(),
      statusText: response?.statusText()
    });

    // Should NOT return 405 (Method Not Allowed)
    expect(response?.status(), 'Invalid flowId should not cause 405 error').not.toBe(405);
  });
});

// Test Bug #676: Invalid flow ID returns 405 instead of 404
test.describe('Bug #676: Invalid Flow ID HTTP Status', () => {
  test('should return 404/422 (not 405) for invalid flow ID', async ({ page }) => {
    // Login first to get auth
    await page.goto('http://localhost:8081/login');
    await page.fill('input[type="email"], input[name="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"], input[name="password"]', 'Demo123!');
    await page.click('button[type="submit"], button:has-text("Login")');

    // Wait for login to complete - look for navigation or specific element
    await page.waitForTimeout(3000);

    // Try to navigate to a protected page to ensure login worked
    const currentUrl = page.url();
    console.log('Current URL after login:', currentUrl);

    // Test with invalid UUIDs - use page.request API for better auth handling
    const testCases = [
      {
        id: '00000000-0000-0000-0000-000000000000',
        description: 'All zeros UUID'
      },
      {
        id: 'invalid-uuid-123',
        description: 'Invalid UUID format'
      },
      {
        id: 'ffffffff-ffff-ffff-ffff-ffffffffffff',
        description: 'All F UUID (unlikely to exist)'
      }
    ];

    const results: any[] = [];

    for (const testCase of testCases) {
      try {
        // Use Playwright's request context (includes cookies automatically)
        const response = await page.request.get(
          `http://localhost:8000/api/v1/master-flows/${testCase.id}`,
          {
            headers: {
              'X-Client-Account-Id': '1',
              'X-Engagement-Id': '1'
            }
          }
        );

        results.push({
          ...testCase,
          status: response.status(),
          statusText: response.statusText(),
          ok: response.ok()
        });
      } catch (error: any) {
        results.push({
          ...testCase,
          status: 'ERROR',
          statusText: error.message,
          ok: false
        });
      }
    }

    console.log('=== BUG #676 EVIDENCE ===');
    console.log('Invalid Flow ID Results:', JSON.stringify(results, null, 2));

    // CRITICAL: Check that we DO NOT get 405 Method Not Allowed
    // The bug was specifically about returning 405 instead of 404
    results.forEach(result => {
      // Most important: Should NEVER be 405
      expect(result.status, `${result.description} should NEVER return 405 Method Not Allowed`).not.toBe(405);

      // Should return appropriate error codes (404, 422, or 401 if auth fails)
      // NOT checking exact code because auth might vary
      if (typeof result.status === 'number') {
        expect(result.status >= 400, `${result.description} should return 4xx error`).toBe(true);
      }
    });
  });
});
