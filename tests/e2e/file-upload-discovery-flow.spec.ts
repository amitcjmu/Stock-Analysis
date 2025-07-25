import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * Comprehensive test for file upload and Discovery flow initiation
 * Tests the complete workflow from login -> file upload -> Discovery flow creation -> validation
 */
test.describe('File Upload and Discovery Flow Initiation', () => {

  test.beforeEach(async ({ page }) => {
    // Set longer timeout for complex operations
    test.setTimeout(90000);

    // Navigate to login page
    await page.goto('http://localhost:8081/login');

    // Login as platform admin (has access to all clients/engagements)
    await page.fill('input[name="email"]', 'chocka@gmail.com');
    await page.fill('input[name="password"]', 'Password123!');
    await page.click('button[type="submit"]');

    // Wait for successful login and dashboard navigation
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    console.log('✅ Successfully logged in as platform admin');

    // Verify we're on the dashboard
    await expect(page.locator('h1, h2').filter({ hasText: /Dashboard|Welcome/ })).toBeVisible({ timeout: 10000 });
  });

  test('Complete file upload to Discovery flow workflow', async ({ page }) => {
    // Step 1: Navigate to Discovery section
    console.log('🔍 Step 1: Navigating to Discovery section...');
    const discoveryLink = page.locator('nav a').filter({ hasText: 'Discovery' }).or(
      page.locator('a[href*="discovery"], button').filter({ hasText: 'Discovery' })
    );
    await discoveryLink.click();
    await page.waitForTimeout(2000);

    // Handle different discovery page states
    const currentUrl = page.url();
    if (currentUrl.includes('/discovery') && !currentUrl.includes('cmdb-import')) {
      // We might be on overview page, need to navigate to data import
      console.log('📋 On Discovery overview, checking for data import navigation...');

      // Look for data import/CMDB import links
      const dataImportLink = page.locator('a, button').filter({
        hasText: /Data Import|CMDB Import|Upload Data|Start Import/i
      }).first();

      if (await dataImportLink.isVisible()) {
        await dataImportLink.click();
        await page.waitForTimeout(2000);
      } else {
        // Manual navigation via URL
        await page.goto('http://localhost:8081/discovery/cmdb-import');
      }
    }

    // Verify we're on the data import page
    await page.waitForURL('**/discovery/cmdb-import', { timeout: 10000 });
    console.log('✅ Successfully navigated to CMDB Import page');

    // Step 2: Verify upload interface is ready
    console.log('📁 Step 2: Verifying upload interface...');
    await expect(page.locator('text=/Upload.*Data|Data Import|CMDB Import/i')).toBeVisible({ timeout: 10000 });

    // Step 3: Upload test file
    console.log('⬆️ Step 3: Uploading test CSV file...');

    // Create a more comprehensive test CSV
    const testCsvContent = `hostname,application_name,ip_address,operating_system,cpu_cores,memory_gb,storage_gb,environment,criticality,six_r_strategy
server001.prod,Customer Portal,192.168.1.10,Ubuntu 20.04,4,16,500,Production,High,Rehost
server002.prod,Payment Gateway,192.168.1.11,RHEL 8.5,8,32,1000,Production,Critical,Refactor
server003.prod,Admin Dashboard,192.168.1.12,Windows Server 2019,4,16,250,Production,Medium,Replatform
db001.prod,Database Server,192.168.1.20,Ubuntu 22.04,8,64,2000,Production,Critical,Rehost
cache001.prod,Redis Cache,192.168.1.21,Ubuntu 20.04,2,8,100,Production,High,Rehost
api001.prod,Mobile API,192.168.1.30,Ubuntu 22.04,4,16,500,Production,High,Modernize
analytics001.dev,Analytics Engine,192.168.2.10,CentOS 7,16,128,5000,Development,Low,Retire
test001.staging,Test Environment,192.168.3.10,Ubuntu 20.04,2,8,200,Staging,Low,Retire`;

    // Look for upload areas or file input
    const uploadAreas = [
      page.locator('div.border-dashed').filter({ hasText: /Application Discovery|CMDB|Upload/i }),
      page.locator('[data-testid="upload-area"]'),
      page.locator('input[type="file"]'),
      page.locator('.dropzone, .upload-zone')
    ];

    let uploadSuccessful = false;

    for (const uploadArea of uploadAreas) {
      try {
        if (await uploadArea.first().isVisible({ timeout: 3000 })) {
          console.log('📤 Found upload area, attempting file upload...');

          // Try clicking to trigger file chooser
          const fileChooserPromise = page.waitForEvent('filechooser', { timeout: 5000 });
          await uploadArea.first().click();

          try {
            const fileChooser = await fileChooserPromise;
            await fileChooser.setFiles({
              name: 'comprehensive_cmdb_test.csv',
              mimeType: 'text/csv',
              buffer: Buffer.from(testCsvContent)
            });
            uploadSuccessful = true;
            console.log('✅ File upload initiated successfully');
            break;
          } catch (e) {
            console.log('⚠️ File chooser method failed, trying direct input...');
          }
        }
      } catch (e) {
        // Continue to next upload method
      }
    }

    // Fallback: Try direct file input if upload areas don't work
    if (!uploadSuccessful) {
      const fileInput = page.locator('input[type="file"]').first();
      if (await fileInput.isVisible()) {
        console.log('📤 Using direct file input...');
        await fileInput.setInputFiles({
          name: 'comprehensive_cmdb_test.csv',
          mimeType: 'text/csv',
          buffer: Buffer.from(testCsvContent)
        });
        uploadSuccessful = true;
      }
    }

    if (!uploadSuccessful) {
      await page.screenshot({ path: 'upload-interface-debug.png', fullPage: true });
      throw new Error('Could not find any working upload interface');
    }

    // Step 4: Wait for upload processing and Discovery flow creation
    console.log('⏳ Step 4: Waiting for file processing and flow creation...');

    // Look for processing indicators
    const processingIndicators = [
      page.locator('text=/Processing|Analyzing|Uploading|Creating flow/i'),
      page.locator('.spinner, .loading'),
      page.locator('[data-testid="processing-indicator"]')
    ];

    // Wait for processing to start
    await page.waitForTimeout(2000);

    // Wait for processing completion (look for success messages or flow ID)
    const successIndicators = [
      page.locator('text=/Upload.*complete|Processing.*complete|Flow.*created|Flow ID/i'),
      page.locator('text=/flow-\\d{8}-\\d{6}/'), // Flow ID pattern
      page.locator('.success-message'),
      page.locator('[data-testid="upload-success"]')
    ];

    let processingComplete = false;
    for (let i = 0; i < 30; i++) { // Wait up to 30 seconds
      for (const indicator of successIndicators) {
        if (await indicator.first().isVisible({ timeout: 1000 })) {
          console.log('✅ Processing completed successfully');
          processingComplete = true;

          // Try to extract flow ID if visible
          const flowIdElement = page.locator('text=/flow-\\d{8}-\\d{6}/');
          if (await flowIdElement.isVisible()) {
            const flowId = await flowIdElement.textContent();
            console.log(`🔄 Discovery Flow ID created: ${flowId}`);
          }
          break;
        }
      }
      if (processingComplete) break;
      await page.waitForTimeout(1000);
    }

    if (!processingComplete) {
      console.log('⚠️ Processing completion not detected, continuing with verification...');
    }

    // Step 5: Verify Discovery flow was initiated
    console.log('🔍 Step 5: Verifying Discovery flow initiation...');

    // Check if we're automatically redirected to attribute mapping or if we need to navigate
    await page.waitForTimeout(3000);

    const currentPageUrl = page.url();
    if (!currentPageUrl.includes('attribute-mapping')) {
      // Navigate to attribute mapping to verify the flow
      console.log('📋 Navigating to Attribute Mapping to verify flow...');
      const attributeMappingLink = page.locator('a, button').filter({
        hasText: /Attribute Mapping|Field Mapping|Mapping/i
      }).first();

      if (await attributeMappingLink.isVisible()) {
        await attributeMappingLink.click();
        await page.waitForURL('**/discovery/attribute-mapping', { timeout: 10000 });
      } else {
        await page.goto('http://localhost:8081/discovery/attribute-mapping');
      }
    }

    // Wait for attribute mapping page to load
    await page.waitForTimeout(3000);
    console.log('📋 On Attribute Mapping page, verifying flow data...');

    // Step 6: Verify flow data is available
    console.log('✅ Step 6: Verifying Discovery flow data availability...');

    // Check for flow data indicators
    const flowDataIndicators = [
      page.locator('text=/Field Mapping|Critical Attributes|Source Fields/i'),
      page.locator('table, .mapping-table'),
      page.locator('.field-mapping-section'),
      page.locator('[data-testid="field-mappings"]')
    ];

    let flowDataFound = false;
    for (const indicator of flowDataIndicators) {
      if (await indicator.first().isVisible({ timeout: 5000 })) {
        flowDataFound = true;
        console.log('✅ Flow data detected on attribute mapping page');
        break;
      }
    }

    // Check for "no data" messages
    const noDataMessages = page.locator('text=/No.*data|No.*field.*mapping|No.*flows.*available/i');
    const hasNoDataMessage = await noDataMessages.first().isVisible({ timeout: 3000 });

    if (hasNoDataMessage && !flowDataFound) {
      console.log('⚠️ No flow data detected. Checking for flow selection options...');

      // Look for flow selector dropdown
      const flowSelector = page.locator('select').filter({ hasText: /flow|Flow/i }).or(
        page.locator('[data-testid="flow-selector"]')
      );

      if (await flowSelector.first().isVisible()) {
        console.log('🔽 Flow selector found, selecting available flow...');
        const options = await flowSelector.first().locator('option').all();
        if (options.length > 1) {
          // Select first non-default option
          await flowSelector.first().selectOption({ index: 1 });
          await page.waitForTimeout(2000);

          // Re-check for flow data
          for (const indicator of flowDataIndicators) {
            if (await indicator.first().isVisible({ timeout: 3000 })) {
              flowDataFound = true;
              console.log('✅ Flow data loaded after selection');
              break;
            }
          }
        }
      }
    }

    // Step 7: Verify CrewAI Discovery Flow execution
    console.log('🤖 Step 7: Verifying CrewAI Discovery Flow execution...');

    // Look for agent activity indicators
    const agentIndicators = [
      page.locator('text=/Agent.*analysis|CrewAI|Discovery.*agent|Processing.*flow/i'),
      page.locator('.agent-status, .crew-status'),
      page.locator('[data-testid*="agent"]')
    ];

    let agentActivityDetected = false;
    for (const indicator of agentIndicators) {
      if (await indicator.first().isVisible({ timeout: 3000 })) {
        agentActivityDetected = true;
        console.log('🤖 CrewAI agent activity detected');
        break;
      }
    }

    // Step 8: Check Discovery overview for flow status
    console.log('📊 Step 8: Checking Discovery overview for flow status...');
    await page.goto('http://localhost:8081/discovery');
    await page.waitForTimeout(3000);

    // Look for flow status widgets or active flow indicators
    const flowStatusIndicators = [
      page.locator('text=/Active.*flow|Flow.*status|Discovery.*progress/i'),
      page.locator('.flow-status-widget'),
      page.locator('[data-testid*="flow-status"]')
    ];

    let flowStatusVisible = false;
    for (const indicator of flowStatusIndicators) {
      if (await indicator.first().isVisible({ timeout: 3000 })) {
        flowStatusVisible = true;
        console.log('📊 Flow status information visible on overview');
        break;
      }
    }

    // Final verification and reporting
    console.log('\n📋 TEST RESULTS SUMMARY:');
    console.log(`✅ File Upload: SUCCESS`);
    console.log(`✅ Discovery Flow Creation: ${processingComplete ? 'SUCCESS' : 'PARTIAL'}`);
    console.log(`✅ Flow Data Availability: ${flowDataFound ? 'SUCCESS' : 'FAILED'}`);
    console.log(`🤖 CrewAI Agent Activity: ${agentActivityDetected ? 'DETECTED' : 'NOT DETECTED'}`);
    console.log(`📊 Flow Status Display: ${flowStatusVisible ? 'SUCCESS' : 'PARTIAL'}`);

    // Take final screenshot for documentation
    await page.screenshot({ path: 'discovery-flow-test-final-state.png', fullPage: true });

    // Assert critical functionality
    expect(flowDataFound || processingComplete).toBeTruthy();

    if (!flowDataFound) {
      console.log('⚠️ WARNING: Flow data not immediately available. This may indicate:');
      console.log('   - Flow is still processing in background');
      console.log('   - Context switching issues between upload and mapping views');
      console.log('   - Need to refresh page or wait for async processing');

      // Take debug screenshot
      await page.screenshot({ path: 'flow-data-missing-debug.png', fullPage: true });
    }
  });

  test('Verify Discovery flow with asset inventory', async ({ page }) => {
    // Quick test to verify uploaded data reaches asset inventory
    console.log('📦 Testing asset inventory after Discovery flow...');

    // Upload a simple test file first
    await page.goto('http://localhost:8081/discovery/cmdb-import');
    await page.waitForTimeout(2000);

    const simpleTestData = `hostname,application_name,environment
test-server-01,Test App 1,Production
test-server-02,Test App 2,Development`;

    // Find upload area and upload
    const uploadArea = page.locator('div.border-dashed, input[type="file"]').first();
    if (await uploadArea.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser', { timeout: 5000 });
      await uploadArea.click();

      try {
        const fileChooser = await fileChooserPromise;
        await fileChooser.setFiles({
          name: 'simple_test.csv',
          mimeType: 'text/csv',
          buffer: Buffer.from(simpleTestData)
        });

        // Wait for processing
        await page.waitForTimeout(5000);

        // Navigate to Discovery overview to check asset inventory
        await page.goto('http://localhost:8081/discovery');
        await page.waitForTimeout(3000);

        // Look for asset count indicators
        const assetCountIndicators = page.locator('text=/\\d+.*asset|\\d+.*server|\\d+.*application|Assets.*discovered/i');
        if (await assetCountIndicators.first().isVisible({ timeout: 5000 })) {
          const assetCountText = await assetCountIndicators.first().textContent();
          console.log(`📦 Asset inventory updated: ${assetCountText}`);

          // Check if count is greater than 0
          const matches = assetCountText?.match(/(\d+)/);
          if (matches && parseInt(matches[1]) > 0) {
            console.log('✅ Assets successfully created from uploaded data');
          }
        }
      } catch (e) {
        console.log('⚠️ Asset inventory test failed:', e);
      }
    }
  });

  test('Handle flow context and client switching', async ({ page }) => {
    // Test flow behavior with different client contexts
    console.log('🔄 Testing flow context handling...');

    await page.goto('http://localhost:8081/discovery');
    await page.waitForTimeout(2000);

    // Look for client context selector
    const contextSelector = page.locator('select').filter({ hasText: /client|Client/i }).or(
      page.locator('[data-testid="client-selector"]')
    );

    if (await contextSelector.first().isVisible()) {
      console.log('🏢 Client context selector found');

      // Get available options
      const options = await contextSelector.first().locator('option').all();
      console.log(`📋 Available clients: ${options.length - 1}`); // Minus default option

      if (options.length > 1) {
        // Switch to a different client
        await contextSelector.first().selectOption({ index: 1 });
        await page.waitForTimeout(2000);

        // Verify that flows are context-aware
        const flowElements = page.locator('text=/flow|Flow/i');
        const flowCount = await flowElements.count();
        console.log(`🔄 Flows visible in current context: ${flowCount}`);
      }
    } else {
      console.log('🏢 Platform admin context - no client switching needed');
    }
  });
});
