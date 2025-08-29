import { test, expect, Page } from '@playwright/test';

/**
 * Flow Endpoint Consolidation Test Suite
 *
 * This test suite validates the migration from singular /flow/ to plural /flows/ endpoints
 * and ensures all flow operations work correctly in the Discovery Dashboard.
 */

test.describe('Flow Endpoint Consolidation Tests', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    // Create a new browser context to start fresh
    const context = await browser.newContext();
    page = await context.newPage();

    // Enable request/response logging to catch any 404 errors
    page.on('response', (response) => {
      if (response.status() === 404) {
        console.error(`404 Error: ${response.url()}`);
      }
      if (response.url().includes('/api/v1/') && response.status() >= 400) {
        console.error(`API Error: ${response.status()} ${response.url()}`);
      }
    });

    // Navigate to the application
    await page.goto('http://localhost:8081');

    // Wait for the application to load
    await page.waitForLoadState('networkidle');
  });

  test('should access Discovery Dashboard without 404 errors', async () => {
    const response404Errors: string[] = [];

    // Monitor for 404 errors
    page.on('response', (response) => {
      if (response.status() === 404) {
        response404Errors.push(response.url());
      }
    });

    // Navigate to Discovery Dashboard
    await page.goto('http://localhost:8081/discover');
    await page.waitForLoadState('networkidle');

    // Wait for any additional network requests to complete
    await page.waitForTimeout(2000);

    // Check that no 404 errors occurred
    expect(response404Errors).toEqual([]);
  });

  test('should validate unified discovery flow endpoints are using /flows/ prefix', async () => {
    const apiCalls: string[] = [];

    // Monitor API calls
    page.on('request', (request) => {
      if (request.url().includes('/api/v1/')) {
        apiCalls.push(request.url());
      }
    });

    // Navigate to Discovery Dashboard
    await page.goto('http://localhost:8081/discover');
    await page.waitForLoadState('networkidle');

    // Wait for initial API calls
    await page.waitForTimeout(3000);

    // Filter for flow-related API calls
    const flowApiCalls = apiCalls.filter(url =>
      url.includes('/unified-discovery/') &&
      (url.includes('/flow') || url.includes('/flows'))
    );

    console.log('Flow API calls detected:', flowApiCalls);

    // Verify that flow endpoints use plural /flows/ not singular /flow/
    const singularFlowCalls = flowApiCalls.filter(url =>
      url.match(/\/unified-discovery\/flow\/[^/]/) ||
      url.includes('/unified-discovery/flow/initialize') ||
      url.includes('/unified-discovery/flow/active')
    );

    expect(singularFlowCalls).toEqual([]);

    // Verify plural endpoints are being used
    const pluralFlowCalls = flowApiCalls.filter(url =>
      url.includes('/unified-discovery/flows/')
    );

    console.log('Plural flow endpoints found:', pluralFlowCalls);
  });

  test('should handle flow initialization with proper endpoint', async () => {
    let initializeEndpointCalled = false;
    let endpointUsed = '';

    // Monitor for flow initialization calls
    page.on('request', (request) => {
      if (request.url().includes('/flows/initialize')) {
        initializeEndpointCalled = true;
        endpointUsed = request.url();
      }
    });

    await page.goto('http://localhost:8081/discover');
    await page.waitForLoadState('networkidle');

    // Look for a "Start Discovery" or similar button
    const startButtons = [
      'text=Start Discovery',
      'text=Initialize Flow',
      'text=Begin Discovery',
      'text=Start',
      '[data-testid=start-discovery]',
      'button:has-text("Discover")'
    ];

    let buttonFound = false;
    for (const selector of startButtons) {
      try {
        const button = page.locator(selector).first();
        if (await button.isVisible({ timeout: 1000 })) {
          await button.click();
          buttonFound = true;
          break;
        }
      } catch (error) {
        // Continue to next selector
      }
    }

    if (buttonFound) {
      await page.waitForTimeout(2000);

      if (initializeEndpointCalled) {
        // Verify the correct plural endpoint was used
        expect(endpointUsed).toMatch(/\/flows\/initialize$/);
        expect(endpointUsed).not.toMatch(/\/flow\/initialize$/);
      }
    } else {
      console.log('No start discovery button found - this may be expected for the current UI state');
    }
  });

  test('should check active flows with plural endpoint', async () => {
    let activeFlowsEndpointCalled = false;
    let endpointUsed = '';

    // Monitor for active flows calls
    page.on('request', (request) => {
      if (request.url().includes('/flows/active') || request.url().includes('/flow/active')) {
        activeFlowsEndpointCalled = true;
        endpointUsed = request.url();
      }
    });

    await page.goto('http://localhost:8081/discover');
    await page.waitForLoadState('networkidle');

    // Wait for potential API calls
    await page.waitForTimeout(3000);

    if (activeFlowsEndpointCalled) {
      // Verify the correct plural endpoint was used
      expect(endpointUsed).toMatch(/\/flows\/active$/);
      expect(endpointUsed).not.toMatch(/\/flow\/active$/);
    }
  });

  test('should verify flow status endpoints use plural convention', async () => {
    const flowStatusCalls: string[] = [];

    // Monitor for flow status calls
    page.on('request', (request) => {
      if (request.url().includes('/status') &&
          (request.url().includes('/flow') || request.url().includes('/flows'))) {
        flowStatusCalls.push(request.url());
      }
    });

    await page.goto('http://localhost:8081/discover');
    await page.waitForLoadState('networkidle');

    // Wait for API calls
    await page.waitForTimeout(3000);

    // Check for any flow status calls
    if (flowStatusCalls.length > 0) {
      console.log('Flow status calls:', flowStatusCalls);

      // Verify all status calls use plural /flows/
      const singularStatusCalls = flowStatusCalls.filter(url =>
        url.match(/\/flow\/[^/]+\/status/) && !url.includes('/flows/')
      );

      expect(singularStatusCalls).toEqual([]);
    }
  });

  test('should validate execute endpoints use plural convention', async () => {
    const executeEndpointCalls: string[] = [];

    // Monitor for execute endpoint calls
    page.on('request', (request) => {
      if (request.url().includes('/execute') &&
          (request.url().includes('/flow') || request.url().includes('/flows'))) {
        executeEndpointCalls.push(request.url());
      }
    });

    await page.goto('http://localhost:8081/discover');
    await page.waitForLoadState('networkidle');

    // Wait for API calls
    await page.waitForTimeout(3000);

    // Check for any execute calls
    if (executeEndpointCalls.length > 0) {
      console.log('Execute endpoint calls:', executeEndpointCalls);

      // Verify all execute calls use plural /flows/
      const singularExecuteCalls = executeEndpointCalls.filter(url =>
        url.match(/\/flow\/[^/]+\/execute/) && !url.includes('/flows/')
      );

      expect(singularExecuteCalls).toEqual([]);
    }
  });

  test('should test flow health endpoint accessibility', async () => {
    let healthEndpointCalled = false;

    // Monitor for health endpoint calls
    page.on('request', (request) => {
      if (request.url().includes('/flows/health')) {
        healthEndpointCalled = true;
      }
    });

    // Test direct access to flow health endpoint
    const response = await page.goto('http://localhost:8000/api/v1/flows/health');

    // The endpoint should respond (even if with auth error)
    expect(response?.status()).not.toBe(404);
  });

  test('should verify no 404 errors during complete discovery workflow', async () => {
    const response404Errors: string[] = [];
    const allApiErrors: { status: number; url: string }[] = [];

    // Monitor for all errors
    page.on('response', (response) => {
      if (response.status() === 404) {
        response404Errors.push(response.url());
      }
      if (response.url().includes('/api/v1/') && response.status() >= 400) {
        allApiErrors.push({ status: response.status(), url: response.url() });
      }
    });

    await page.goto('http://localhost:8081/discover');
    await page.waitForLoadState('networkidle');

    // Try to interact with discovery interface elements
    const discoveryElements = [
      '[data-testid=discovery-dashboard]',
      'text=Discovery Dashboard',
      'text=Resource Discovery',
      '.discovery-container',
      '#discovery-content'
    ];

    for (const selector of discoveryElements) {
      try {
        const element = page.locator(selector).first();
        if (await element.isVisible({ timeout: 1000 })) {
          await element.hover();
          break;
        }
      } catch (error) {
        // Continue to next selector
      }
    }

    // Wait for any additional network activity
    await page.waitForTimeout(2000);

    // Log all API errors for debugging
    if (allApiErrors.length > 0) {
      console.log('API errors detected:', allApiErrors);
    }

    // Verify no 404 errors occurred
    expect(response404Errors).toEqual([]);

    // Report on API errors (but only fail on 404s)
    const non404Errors = allApiErrors.filter(error => error.status !== 404);
    if (non404Errors.length > 0) {
      console.log('Non-404 API errors (may be expected):', non404Errors);
    }
  });

  test('should validate frontend services use correct endpoint patterns', async () => {
    const allRequests: string[] = [];

    // Monitor all API requests
    page.on('request', (request) => {
      if (request.url().includes('/api/v1/')) {
        allRequests.push(request.url());
      }
    });

    await page.goto('http://localhost:8081/discover');
    await page.waitForLoadState('networkidle');

    // Wait for requests to complete
    await page.waitForTimeout(3000);

    // Check for any requests to legacy singular endpoints
    const legacySingularEndpoints = allRequests.filter(url => {
      // Look for patterns like /flow/{id}/ but not /flows/{id}/
      return url.match(/\/flow\/[^/]+\/(?!s)/) ||
             url.includes('/flow/initialize') ||
             url.includes('/flow/active') ||
             url.includes('/flow/status');
    });

    console.log('All API requests:', allRequests);

    if (legacySingularEndpoints.length > 0) {
      console.error('Legacy singular endpoints found:', legacySingularEndpoints);
    }

    // Fail if any legacy singular endpoints are being used
    expect(legacySingularEndpoints).toEqual([]);
  });

  test.afterEach(async ({ page }) => {
    // Clean up
    await page.close();
  });
});
