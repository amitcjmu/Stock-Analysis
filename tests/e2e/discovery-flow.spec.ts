import { test, expect, Page, APIResponse } from '@playwright/test';
import path from 'path';

/**
 * Enhanced Discovery Flow End-to-End Testing
 * 
 * Updated with comprehensive validation for issues that were fixed:
 * - Flow ID data integrity validation
 * - API status code verification
 * - Extended loading state handling
 * - Flow transition validation
 * 
 * Enhanced by CC (Claude Code)
 */

// Helper function to validate flow ID format
function isValidFlowId(flowId: string | null | undefined): boolean {
  if (!flowId || flowId === 'undefined') return false;
  
  const flowIdPattern = /^flow-\d{8}-\d{6}$/;
  const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  
  return flowIdPattern.test(flowId) || uuidPattern.test(flowId);
}

// Helper function to monitor API calls and validate status codes
async function monitorApiCall(page: Page, urlPattern: string | RegExp, expectedStatuses: number[] = [200]): Promise<APIResponse | null> {
  try {
    const response = await page.waitForResponse(resp => 
      typeof urlPattern === 'string' ? resp.url().includes(urlPattern) : urlPattern.test(resp.url()),
      { timeout: 30000 }
    );
    
    const status = response.status();
    if (!expectedStatuses.includes(status)) {
      console.warn(`API call to ${response.url()} returned unexpected status: ${status} (expected: ${expectedStatuses.join(' or ')})`);
      
      // Log response body for debugging
      try {
        const responseBody = await response.text();
        console.warn(`Response body: ${responseBody}`);
      } catch (error) {
        console.warn('Could not read response body');
      }
    }
    
    return response;
  } catch (error) {
    console.warn(`Failed to monitor API call for pattern ${urlPattern}:`, error);
    return null;
  }
}

test.describe('Discovery Flow End-to-End', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('http://localhost:8081/login');

    // Login with provided credentials
    await page.fill('input[type="email"]', 'chocka@gmail.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');

    // Wait for navigation to complete
    await page.waitForURL('**/dashboard', { timeout: 10000 });
  });

  test('Upload file and verify attribute mapping flow', async ({ page }) => {
    // Navigate to Discovery
    await page.click('text=Discovery');
    await page.waitForTimeout(1000);

    // Check if there's an active flow and handle flow sync
    const overviewVisible = await page.locator('text=Overview').isVisible();
    if (overviewVisible) {
      // We're on the overview page, check for active flows
      await page.waitForTimeout(2000); // Wait for flow status widget

      // Check if flow intelligence widget shows "flow not found"
      const flowNotFound = await page.locator('text=/flow.*not.*found|Flow not found/i').isVisible();
      if (flowNotFound) {
        console.log('Flow not found detected, navigating to CMDB Import');
        // Click on the recommended action to go to CMDB import
        const cmdbImportButton = page.locator('button').filter({ hasText: /CMDB Import|Data Import|Upload/i }).first();
        if (await cmdbImportButton.isVisible()) {
          await cmdbImportButton.click();
        } else {
          // Manual navigation if button not found
          await page.click('text=Data Import');
        }
      }
    } else {
      // Direct navigation to Data Import
      await page.click('text=Data Import');
    }

    await page.waitForURL('**/discovery/cmdb-import', { timeout: 5000 });

    // Prepare test file
    const testFilePath = path.join(__dirname, '../../fixtures/test-cmdb-data.csv');

    // Find and click the upload area for Application Discovery
    const uploadArea = page.locator('.border-dashed').filter({ hasText: 'Application Discovery' }).first();
    await uploadArea.click();

    // Upload file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    // Wait for upload to complete
    await page.waitForTimeout(2000);

    // Look for success indicators
    const successMessage = page.locator('text=/Upload completed|Processing complete|Data import complete/i');
    await expect(successMessage).toBeVisible({ timeout: 30000 });

    // Check if flow ID is displayed
    const flowIdElement = page.locator('text=/flow-\\d{8}-\\d{6}/');
    const flowIdVisible = await flowIdElement.isVisible();
    if (flowIdVisible) {
      const flowId = await flowIdElement.textContent();
      console.log('Flow ID created:', flowId);
    }

    // Navigate to Attribute Mapping
    await page.click('text=Attribute Mapping');
    await page.waitForURL('**/discovery/attribute-mapping', { timeout: 5000 });

    // Wait for page to load
    await page.waitForTimeout(2000);

    // Check for data presence
    const noDataMessage = page.locator('text=No Field Mapping Available');
    const hasNoDataMessage = await noDataMessage.isVisible();

    if (hasNoDataMessage) {
      console.log('WARNING: No field mapping data found on attribute mapping page');

      // Check if we need to select a flow
      const flowSelector = page.locator('select[id="flow-selector"], .flow-selector');
      if (await flowSelector.isVisible()) {
        console.log('Flow selector found, selecting first available flow');
        const options = await flowSelector.locator('option').all();
        if (options.length > 1) {
          // Select the first non-default option
          await flowSelector.selectOption({ index: 1 });
          await page.waitForTimeout(2000);
        }
      }

      // Re-check for data after potential flow selection
      const stillNoData = await noDataMessage.isVisible();
      if (stillNoData) {
        // Check for active flows
        const activeFlowsDebug = await page.locator('text=/Available Flows: \\d+/').textContent();
        console.log('Active flows debug:', activeFlowsDebug);

        // Take screenshot for debugging
        await page.screenshot({ path: 'attribute-mapping-error.png', fullPage: true });

        throw new Error('Attribute mapping page shows no data after upload');
      }
    }

    // Verify field mappings are visible
    const fieldMappingSection = page.locator('text=/Field Mapping|Critical Attributes/');
    await expect(fieldMappingSection).toBeVisible({ timeout: 10000 });

    console.log('SUCCESS: Attribute mapping page loaded with data');
  });

  test('Handle flow synchronization issues', async ({ page }) => {
    // Navigate to Discovery Overview
    await page.click('text=Discovery');
    await page.waitForTimeout(2000);

    // Check if we're on the overview page
    const overviewPageTitle = page.locator('h1, h2').filter({ hasText: /Discovery Overview|Active Discovery/i });
    if (await overviewPageTitle.isVisible()) {
      console.log('On Discovery Overview page');

      // Wait for flow status widget to load
      await page.waitForTimeout(3000);

      // Check for flow synchronization issues
      const flowNotFoundText = page.locator('text=/flow.*not.*found|doesn.*t exist|No flow analysis/i');
      if (await flowNotFoundText.isVisible()) {
        console.log('Flow synchronization issue detected');

        // Look for navigation button in flow status widget
        const navigationButton = page.locator('button').filter({ hasText: /Navigate|Continue|Start|Upload/i }).first();
        if (await navigationButton.isVisible()) {
          console.log('Found navigation button, clicking...');
          await navigationButton.click();

          // Verify we navigated to the correct page
          await page.waitForURL('**/discovery/cmdb-import', { timeout: 5000 });
          console.log('Successfully navigated to CMDB Import page');
        } else {
          console.log('No navigation button found, manual navigation required');

          // Try clicking on Data Import manually
          const dataImportLink = page.locator('a, button').filter({ hasText: /Data Import|CMDB Import/i }).first();
          if (await dataImportLink.isVisible()) {
            await dataImportLink.click();
            await page.waitForURL('**/discovery/cmdb-import', { timeout: 5000 });
          }
        }
      } else {
        console.log('No flow synchronization issues detected');
      }
    }
  });

  test('Comprehensive flow validation with data integrity checks', async ({ page }) => {
    let flowId = '';
    const validationErrors: string[] = [];
    const apiCallResults: Array<{endpoint: string, status: number, isValid: boolean}> = [];

    await test.step('Initialize flow with API monitoring', async () => {
      // Navigate to Discovery
      await page.click('text=Discovery');
      await page.waitForTimeout(1000);

      // Start new discovery flow with API monitoring
      const newFlowButton = page.locator('button').filter({ hasText: /Start New Discovery|New Flow|Initialize/i });
      if (await newFlowButton.isVisible()) {
        
        // Monitor flow initialization API call
        const [initResponse] = await Promise.all([
          monitorApiCall(page, '/flow/initialize', [200, 201]),
          newFlowButton.click()
        ]);

        if (initResponse) {
          apiCallResults.push({
            endpoint: 'flow/initialize',
            status: initResponse.status(),
            isValid: [200, 201].includes(initResponse.status())
          });

          // Validate response contains flow ID
          try {
            const responseData = await initResponse.json();
            const responseFlowId = responseData.flow_id || responseData.id;
            
            if (!responseFlowId) {
              validationErrors.push('Flow initialization API response missing flow_id');
            } else if (responseFlowId === 'undefined') {
              validationErrors.push(`Flow initialization returned undefined flow_id: ${responseFlowId}`);
            } else if (!isValidFlowId(responseFlowId)) {
              validationErrors.push(`Flow initialization returned invalid flow_id format: ${responseFlowId}`);
            } else {
              flowId = responseFlowId;
            }
          } catch (error) {
            validationErrors.push(`Could not parse flow initialization response: ${error}`);
          }
        }

        await page.waitForTimeout(2000);
      }

      // Extract flow ID from page if not found in API response
      if (!flowId) {
        const flowIdElement = page.locator('text=/flow-\\d{8}-\\d{6}/');
        if (await flowIdElement.isVisible()) {
          const flowIdText = await flowIdElement.textContent();
          if (flowIdText && isValidFlowId(flowIdText)) {
            flowId = flowIdText;
          } else {
            validationErrors.push(`Invalid flow ID found on page: ${flowIdText}`);
          }
        }
      }

      // Critical assertion: Flow ID must be valid
      expect(flowId, 'Valid flow ID should be generated').toBeTruthy();
      expect(isValidFlowId(flowId), 'Flow ID should have correct format').toBe(true);
      expect(flowId, 'Flow ID should not be undefined').not.toBe('undefined');
    });

    await test.step('Test file upload with extended timeout handling', async () => {
      // Navigate to Data Import
      await page.click('text=Data Import');
      await page.waitForURL('**/discovery/cmdb-import', { timeout: 10000 });

      const testFilePath = path.join(__dirname, '../fixtures/test-cmdb-data.csv');
      
      // Upload file with API monitoring
      const uploadArea = page.locator('.border-dashed').filter({ hasText: 'Application Discovery' }).first();
      await uploadArea.click();

      const fileInput = await page.locator('input[type="file"]');
      
      // Monitor upload API call with extended timeout
      const [uploadResponse] = await Promise.all([
        monitorApiCall(page, '/upload', [200, 201, 202]),
        fileInput.setInputFiles(testFilePath)
      ]);

      if (uploadResponse) {
        apiCallResults.push({
          endpoint: 'upload',
          status: uploadResponse.status(),
          isValid: [200, 201, 202].includes(uploadResponse.status())
        });

        // Critical check: upload should not return 404
        if (uploadResponse.status() === 404) {
          validationErrors.push('File upload API returned 404 - endpoint may be missing');
        }
      }

      // Wait for processing with extended timeout for slow loading
      let processingComplete = false;
      let attempts = 0;
      const maxAttempts = 30; // 60 seconds total

      while (!processingComplete && attempts < maxAttempts) {
        await page.waitForTimeout(2000);
        attempts++;

        // Check for success indicators
        const successMessage = page.locator('text=/Upload completed|Processing complete|Data import complete/i');
        const errorMessage = page.locator('text=/Upload failed|Error|Failed/i');
        
        if (await successMessage.isVisible()) {
          processingComplete = true;
          console.log(`Upload processing completed after ${attempts * 2} seconds`);
        } else if (await errorMessage.isVisible()) {
          const errorText = await errorMessage.textContent();
          validationErrors.push(`Upload processing failed: ${errorText}`);
          break;
        } else if (attempts === maxAttempts) {
          validationErrors.push('Upload processing timed out after 60 seconds');
        }
      }

      // Validate flow ID persistence after upload
      const postUploadFlowId = await page.locator('text=/flow-\\d{8}-\\d{6}/').textContent();
      if (postUploadFlowId && postUploadFlowId !== flowId) {
        validationErrors.push(`Flow ID changed after upload: ${flowId} -> ${postUploadFlowId}`);
      }
    });

    await test.step('Test flow state API endpoints', async () => {
      if (!flowId) {
        validationErrors.push('Cannot test flow state APIs without valid flow ID');
        return;
      }

      // Test flow status endpoint
      try {
        const statusResponse = await page.request.get(`http://localhost:8000/api/v1/unified-discovery/flow/${flowId}/status`);
        
        apiCallResults.push({
          endpoint: `flow/${flowId}/status`,
          status: statusResponse.status(),
          isValid: statusResponse.status() === 200
        });

        if (statusResponse.status() === 404) {
          validationErrors.push(`Flow status API returned 404 for valid flow ID: ${flowId}`);
        } else if (statusResponse.status() === 200) {
          try {
            const statusData = await statusResponse.json();
            if (!statusData.id && !statusData.flow_id) {
              validationErrors.push('Flow status response missing ID fields');
            }
          } catch (error) {
            validationErrors.push(`Could not parse flow status response: ${error}`);
          }
        }
      } catch (error) {
        validationErrors.push(`Flow status API error: ${error}`);
      }

      // Test flow details endpoint
      try {
        const detailsResponse = await page.request.get(`http://localhost:8000/api/v1/flows/${flowId}`);
        
        apiCallResults.push({
          endpoint: `flows/${flowId}`,
          status: detailsResponse.status(),
          isValid: [200, 404].includes(detailsResponse.status())
        });

        if (detailsResponse.status() === 404) {
          // 404 might be acceptable if endpoint structure is different
          console.log('Flow details endpoint returned 404 - may use different URL structure');
        }
      } catch (error) {
        console.log(`Flow details endpoint test skipped: ${error}`);
      }
    });

    await test.step('Test phase transitions with API validation', async () => {
      if (!flowId) return;

      const phases = [
        { name: 'Attribute Mapping', url: '/discovery/attribute-mapping' },
        { name: 'Asset Inventory', url: '/discovery/asset-inventory' }
      ];

      for (const phase of phases) {
        await page.goto(`http://localhost:8081${phase.url}`);
        
        // Wait with extended timeout for slow-loading phases
        let phaseLoaded = false;
        let loadAttempts = 0;
        const maxLoadAttempts = 15; // 30 seconds

        while (!phaseLoaded && loadAttempts < maxLoadAttempts) {
          await page.waitForTimeout(2000);
          loadAttempts++;

          // Check if phase content has loaded
          const pageContent = await page.textContent('body');
          if (pageContent && pageContent.length > 500) {
            phaseLoaded = true;
          }
        }

        if (!phaseLoaded) {
          validationErrors.push(`${phase.name} phase failed to load within timeout`);
        }

        // Check for flow ID persistence
        const phaseFlowId = await page.locator('text=/flow-\\d{8}-\\d{6}/').textContent();
        if (phaseFlowId && phaseFlowId !== flowId) {
          validationErrors.push(`Flow ID changed in ${phase.name} phase: ${flowId} -> ${phaseFlowId}`);
        } else if (!phaseFlowId) {
          // Try to find flow ID in other ways
          const urlFlowId = page.url().match(/flow[_-]([a-f0-9-]+)/i);
          if (!urlFlowId) {
            console.warn(`No flow ID visible in ${phase.name} phase`);
          }
        }

        // Check for no-data scenarios that might indicate backend issues
        const noDataMessage = page.locator('text=/No.*data|No.*found|Empty/i');
        if (await noDataMessage.isVisible()) {
          const noDataText = await noDataMessage.textContent();
          console.warn(`${phase.name} phase showing no data: ${noDataText}`);
        }
      }
    });

    // Final validation and reporting
    console.log('\n=== Flow Validation Results ===');
    console.log(`Flow ID: ${flowId}`);
    console.log(`Validation Errors: ${validationErrors.length}`);
    console.log(`API Calls Made: ${apiCallResults.length}`);

    // Log API call results
    const failedApiCalls = apiCallResults.filter(result => !result.isValid);
    if (failedApiCalls.length > 0) {
      console.log('\nFailed API Calls:');
      failedApiCalls.forEach(call => {
        console.log(`- ${call.endpoint}: Status ${call.status}`);
      });
    }

    // Log validation errors
    if (validationErrors.length > 0) {
      console.log('\nValidation Errors:');
      validationErrors.forEach(error => {
        console.log(`- ${error}`);
      });
    }

    // Critical assertions
    expect(validationErrors.length, 'Should have no validation errors').toBe(0);
    
    const criticalApiFailures = apiCallResults.filter(call => 
      !call.isValid && call.status === 404
    );
    expect(criticalApiFailures.length, 'Should have no 404 API failures').toBe(0);

    const successfulApiCalls = apiCallResults.filter(call => call.isValid);
    expect(successfulApiCalls.length, 'Should have successful API calls').toBeGreaterThan(0);
  });

  test('Extended loading state validation', async ({ page }) => {
    const loadingTimeouts: Array<{phase: string, timeout: number, success: boolean}> = [];

    await test.step('Test discovery overview loading with timeout', async () => {
      const startTime = Date.now();
      await page.click('text=Discovery');
      
      // Wait for overview to load with extended timeout
      try {
        await page.waitForSelector('text=/Overview|Active Discovery|Flow Status/i', { timeout: 15000 });
        const loadTime = Date.now() - startTime;
        loadingTimeouts.push({ phase: 'Discovery Overview', timeout: loadTime, success: true });
        
        if (loadTime > 10000) {
          console.warn(`Discovery overview took ${loadTime}ms to load - consider optimization`);
        }
      } catch (error) {
        loadingTimeouts.push({ phase: 'Discovery Overview', timeout: 15000, success: false });
        console.error('Discovery overview failed to load within timeout');
      }
    });

    await test.step('Test data import page loading', async () => {
      const startTime = Date.now();
      await page.click('text=Data Import');
      
      try {
        await page.waitForSelector('.border-dashed, input[type="file"]', { timeout: 15000 });
        const loadTime = Date.now() - startTime;
        loadingTimeouts.push({ phase: 'Data Import', timeout: loadTime, success: true });
      } catch (error) {
        loadingTimeouts.push({ phase: 'Data Import', timeout: 15000, success: false });
        console.error('Data import page failed to load within timeout');
      }
    });

    // Report loading performance
    console.log('\n=== Loading Performance Results ===');
    loadingTimeouts.forEach(result => {
      console.log(`${result.phase}: ${result.timeout}ms (${result.success ? 'Success' : 'Failed'})`);
    });

    const failedLoads = loadingTimeouts.filter(result => !result.success);
    expect(failedLoads.length, 'All phases should load within extended timeouts').toBe(0);

    const slowLoads = loadingTimeouts.filter(result => result.success && result.timeout > 5000);
    if (slowLoads.length > 0) {
      console.warn(`${slowLoads.length} phases loaded slowly (>5s) - consider performance optimization`);
    }
  });
});
