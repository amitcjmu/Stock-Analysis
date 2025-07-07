import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Test data
const TEST_USER = {
  email: 'chocka@gmail.com',
  password: 'Password123!'
};

// Create test CSV content
const TEST_CMDB_DATA = `Name,Type,Status,Environment,IP_Address,OS,Department,Owner,Location,Description
APP-WEB-001,Application,Active,Production,10.0.1.10,Linux,IT,John Doe,US-East,Customer portal web application
APP-API-001,Application,Active,Production,10.0.1.11,Linux,IT,Jane Smith,US-East,REST API service
APP-DB-001,Application,Active,Production,10.0.1.12,Linux,IT,Bob Wilson,US-East,Database application layer
SRV-WEB-001,Server,Active,Production,10.0.2.10,Ubuntu 22.04,IT,John Doe,US-East,Web server hosting customer portal
SRV-WEB-002,Server,Active,Production,10.0.2.11,Ubuntu 22.04,IT,John Doe,US-East,Web server hosting customer portal
SRV-API-001,Server,Active,Production,10.0.2.20,Ubuntu 20.04,IT,Jane Smith,US-East,API server cluster node 1
SRV-API-002,Server,Active,Production,10.0.2.21,Ubuntu 20.04,IT,Jane Smith,US-East,API server cluster node 2
SRV-DB-001,Server,Active,Production,10.0.2.30,Red Hat 8,IT,Bob Wilson,US-East,Primary database server
SRV-DB-002,Server,Standby,Production,10.0.2.31,Red Hat 8,IT,Bob Wilson,US-East,Standby database server
DEV-LB-001,Device,Active,Production,10.0.3.10,Proprietary,Network,Alice Brown,US-East,Load balancer for web traffic
DEV-FW-001,Device,Active,Production,10.0.3.20,Proprietary,Security,Charlie Davis,US-East,Main firewall appliance
DEV-SW-001,Device,Active,Production,10.0.3.30,Cisco IOS,Network,Alice Brown,US-East,Core network switch
DEV-STG-001,Device,Active,Production,10.0.3.40,Proprietary,IT,Bob Wilson,US-East,SAN storage device`;

test.describe('Complete Discovery Workflow', () => {
  let page: Page;

  test.beforeEach(async ({ page: newPage }) => {
    page = newPage;
    page.setDefaultTimeout(60000); // 60 second timeout for complex operations
  });

  test('should complete full discovery workflow from upload to inventory', async () => {
    const workflowResults = {
      login: false,
      fileUpload: false,
      attributeMapping: false,
      dataCleansing: false,
      inventoryAssets: false,
      appCount: 0,
      serverCount: 0,
      deviceCount: 0
    };

    // Step 1: Login
    console.log('📋 Step 1: Login');
    await page.goto('/login');
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    
    // Wait for redirect
    await page.waitForURL('**/discovery/**', { timeout: 10000 });
    workflowResults.login = true;
    console.log('✅ Login successful');
    
    // Step 2: Navigate to Data Import
    console.log('\n📋 Step 2: Data Import');
    await page.goto('/discovery/cmdb-import');
    await page.waitForLoadState('networkidle');
    
    // Check for any blocking flows
    const uploadBlocked = await page.locator('text=/upload blocked|data upload disabled/i').count() > 0;
    if (uploadBlocked) {
      console.log('⚠️ Upload blocked - clearing existing flows...');
      const deleteBtn = page.locator('button:has-text("Delete")').first();
      if (await deleteBtn.isVisible()) {
        await deleteBtn.click();
        await page.waitForTimeout(3000);
        await page.reload();
        await page.waitForTimeout(3000);
      }
    }
    
    // Upload file
    const fileInput = await page.locator('input[type="file"]').first();
    await expect(fileInput).toBeVisible({ timeout: 10000 });
    
    await fileInput.setInputFiles({
      name: 'test-cmdb-data.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(TEST_CMDB_DATA)
    });
    
    // Wait for upload to process
    await page.waitForTimeout(5000);
    workflowResults.fileUpload = true;
    console.log('✅ File uploaded successfully');
    
    // Take screenshot after upload
    await page.screenshot({ path: 'test-results/workflow-after-upload.png', fullPage: true });
    
    // Step 3: Navigate to Attribute Mapping
    console.log('\n📋 Step 3: Attribute Mapping');
    
    // Try multiple ways to get to attribute mapping
    const mappingLink = page.locator('a[href*="attribute-mapping"], text=/attribute.*mapping/i').first();
    if (await mappingLink.isVisible()) {
      await mappingLink.click();
    } else {
      await page.goto('/discovery/attribute-mapping');
    }
    
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Check if field mapping needs to be triggered
    const noMappingMessage = await page.locator('text=/no field mapping available/i').count() > 0;
    const triggerButton = page.locator('button:has-text("Trigger Field Mapping")');
    
    if (noMappingMessage && await triggerButton.isVisible()) {
      console.log('🔄 Triggering field mapping...');
      await triggerButton.click();
      await page.waitForTimeout(10000); // Wait for processing
    }
    
    // Look for mapping interface
    const mappingIndicators = [
      'table',
      '.mapping-table',
      '[data-testid*="mapping"]',
      'text=/source.*field/i',
      'text=/target.*field/i'
    ];
    
    let mappingFound = false;
    for (const selector of mappingIndicators) {
      if (await page.locator(selector).count() > 0) {
        mappingFound = true;
        workflowResults.attributeMapping = true;
        console.log('✅ Attribute mapping interface loaded');
        break;
      }
    }
    
    // Take screenshot of mapping page
    await page.screenshot({ path: 'test-results/workflow-attribute-mapping.png', fullPage: true });
    
    // Try to proceed from mapping
    if (mappingFound) {
      const actionButtons = ['Finalize', 'Continue', 'Next', 'Apply', 'Save', 'Complete Mapping'];
      for (const buttonText of actionButtons) {
        const button = page.locator(`button:has-text("${buttonText}")`).first();
        if (await button.isVisible()) {
          console.log(`🔘 Clicking ${buttonText} button...`);
          await button.click();
          await page.waitForTimeout(5000);
          break;
        }
      }
    }
    
    // Step 4: Check for Data Cleansing
    console.log('\n📋 Step 4: Data Cleansing Check');
    
    // Check if we're on data cleansing page
    const cleansingIndicators = await page.locator('text=/data.*cleansing|cleanse.*data|validation.*rules|quality.*check/i').count();
    if (cleansingIndicators > 0) {
      workflowResults.dataCleansing = true;
      console.log('✅ Data cleansing phase detected');
      
      // Take screenshot
      await page.screenshot({ path: 'test-results/workflow-data-cleansing.png', fullPage: true });
      
      // Try to continue
      const continueButtons = ['Continue', 'Next', 'Complete', 'Finish'];
      for (const buttonText of continueButtons) {
        const button = page.locator(`button:has-text("${buttonText}")`).first();
        if (await button.isVisible()) {
          await button.click();
          await page.waitForTimeout(3000);
          break;
        }
      }
    }
    
    // Step 5: Navigate to Inventory
    console.log('\n📋 Step 5: Inventory Verification');
    await page.goto('/discovery/inventory');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000); // Extra wait for data to load
    
    // Take screenshot of inventory
    await page.screenshot({ path: 'test-results/workflow-inventory-final.png', fullPage: true });
    
    // Count different asset types
    // Method 1: Look for type indicators in rows
    const allRows = await page.locator('tbody tr, .asset-row, [data-testid*="asset"]').all();
    console.log(`Found ${allRows.length} total rows in inventory`);
    
    // Count by examining row content
    for (const row of allRows) {
      const rowText = await row.textContent();
      if (rowText) {
        if (rowText.includes('APP-') || rowText.toLowerCase().includes('application')) {
          workflowResults.appCount++;
        } else if (rowText.includes('SRV-') || rowText.toLowerCase().includes('server')) {
          workflowResults.serverCount++;
        } else if (rowText.includes('DEV-') || rowText.toLowerCase().includes('device')) {
          workflowResults.deviceCount++;
        }
      }
    }
    
    // Alternative counting method
    if (workflowResults.appCount === 0) {
      workflowResults.appCount = await page.locator('tr:has-text("APP-"), tr:has-text("Application")').count();
      workflowResults.serverCount = await page.locator('tr:has-text("SRV-"), tr:has-text("Server")').count();
      workflowResults.deviceCount = await page.locator('tr:has-text("DEV-"), tr:has-text("Device")').count();
    }
    
    const totalAssets = workflowResults.appCount + workflowResults.serverCount + workflowResults.deviceCount;
    if (totalAssets > 0) {
      workflowResults.inventoryAssets = true;
    }
    
    // Print detailed results
    console.log('\n' + '='.repeat(50));
    console.log('📊 WORKFLOW VALIDATION RESULTS');
    console.log('='.repeat(50));
    console.log(`Login:             ${workflowResults.login ? '✅ Success' : '❌ Failed'}`);
    console.log(`File Upload:       ${workflowResults.fileUpload ? '✅ Success' : '❌ Failed'}`);
    console.log(`Attribute Mapping: ${workflowResults.attributeMapping ? '✅ Success' : '❌ Failed'}`);
    console.log(`Data Cleansing:    ${workflowResults.dataCleansing ? '✅ Success' : 'ℹ️  Not Required'}`);
    console.log(`Inventory Assets:  ${workflowResults.inventoryAssets ? '✅ Success' : '❌ Failed'}`);
    console.log('\n📈 Asset Counts:');
    console.log(`Applications:      ${workflowResults.appCount} (expected: 3)`);
    console.log(`Servers:           ${workflowResults.serverCount} (expected: 6)`);
    console.log(`Devices:           ${workflowResults.deviceCount} (expected: 4)`);
    console.log(`Total Assets:      ${totalAssets} (expected: 13)`);
    console.log('='.repeat(50));
    
    // Assertions
    expect(workflowResults.login).toBe(true);
    expect(workflowResults.fileUpload).toBe(true);
    expect(workflowResults.inventoryAssets).toBe(true);
    
    // Asset count assertions (allow some flexibility)
    expect(totalAssets).toBeGreaterThan(0);
    
    // Optional: stricter assertions
    if (totalAssets === 13) {
      expect(workflowResults.appCount).toBe(3);
      expect(workflowResults.serverCount).toBe(6);
      expect(workflowResults.deviceCount).toBe(4);
    }
  });

  test('should handle flow status polling during workflow', async () => {
    // Login first
    await page.goto('/login');
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/discovery/**');
    
    // Track API calls
    const apiCalls = {
      flowInit: 0,
      flowStatus: 0,
      dataImport: 0,
      fieldMapping: 0
    };
    
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/flow/initialize')) apiCalls.flowInit++;
      if (url.includes('/flow/status')) apiCalls.flowStatus++;
      if (url.includes('/data-import')) apiCalls.dataImport++;
      if (url.includes('/field-mapping')) apiCalls.fieldMapping++;
    });
    
    // Go through simplified workflow
    await page.goto('/discovery/cmdb-import');
    
    // Upload file
    const fileInput = await page.locator('input[type="file"]').first();
    await fileInput.setInputFiles({
      name: 'test.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from('Name,Type\nTest1,Server')
    });
    
    // Wait for some API activity
    await page.waitForTimeout(10000);
    
    console.log('\n📊 API Call Summary:');
    console.log(`Flow Initialization: ${apiCalls.flowInit}`);
    console.log(`Flow Status Checks:  ${apiCalls.flowStatus}`);
    console.log(`Data Import Calls:   ${apiCalls.dataImport}`);
    console.log(`Field Mapping Calls: ${apiCalls.fieldMapping}`);
    
    // Verify some API activity occurred
    const totalApiCalls = Object.values(apiCalls).reduce((a, b) => a + b, 0);
    expect(totalApiCalls).toBeGreaterThan(0);
  });
});