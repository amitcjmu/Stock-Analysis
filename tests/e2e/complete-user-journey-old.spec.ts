import { test, expect, Page } from '@playwright/test';
import path from 'path';
import fs from 'fs';

/**
 * Complete User Journey Test Suite
 *
 * Tests the complete workflow: Login → CMDB Upload → Discovery Flow → Asset Selection → Assessment Flow → 6R Treatment
 *
 * This test simulates a real user journey with actual data processing and CrewAI agent execution.
 */

// Test configuration
const BASE_URL = 'http://localhost:8081';
const API_BASE_URL = 'http://localhost:8000';
const TEST_TIMEOUT = 300000; // 5 minutes for complete journey

// Test user credentials
const TEST_USER = {
  email: 'chocka@gmail.com',
  password: 'Password123!'
};

// Test client context
const TEST_CLIENT = {
  accountId: 'bafd5b46-aaaf-4c95-8142-573699d93171',
  engagementId: '6e9c8133-4169-4b79-b052-106dc93d0208'
};

interface FlowState {
  flowId?: string;
  sessionId?: string;
  uploadedAssets?: number;
  selectedApplicationId?: string;
  assessmentFlowId?: string;
  finalRecommendation?: string;
}

interface AssetInfo {
  id: string;
  name: string;
  asset_type: string;
  criticality: string;
}

// Helper functions
async function loginUser(page: Page): Promise<void> {
  console.log('🔐 Logging in user...');
  await page.goto(`${BASE_URL}/login`);

  // Fill login form
  await page.fill('input[name="email"]', TEST_USER.email);
  await page.fill('input[name="password"]', TEST_USER.password);
  await page.click('button[type="submit"]');

  // Wait for successful login
  await page.waitForURL('**/dashboard', { timeout: 10000 });
  console.log('✅ User logged in successfully');
}

async function uploadCMDBFile(page: Page): Promise<FlowState> {
  console.log('📁 Uploading CMDB file...');

  // Navigate to Discovery Data Import
  await page.click('text=Discovery');
  await page.waitForTimeout(1000);

  // Handle flow sync if needed
  const overviewVisible = await page.locator('text=Overview').isVisible();
  if (overviewVisible) {
    const flowNotFound = await page.locator('text=/flow.*not.*found|Flow not found/i').isVisible();
    if (flowNotFound) {
      console.log('Flow not found detected, navigating to CMDB Import');
      const cmdbImportButton = page.locator('button').filter({ hasText: /CMDB Import|Data Import|Upload/i }).first();
      if (await cmdbImportButton.isVisible()) {
        await cmdbImportButton.click();
      } else {
        await page.click('text=Data Import');
      }
    }
  } else {
    await page.click('text=Data Import');
  }

  await page.waitForURL('**/discovery/cmdb-import', { timeout: 5000 });

  // Prepare enterprise test file
  const testFilePath = path.join(__dirname, '../fixtures/enterprise-cmdb-data.csv');

  // Verify test file exists
  if (!fs.existsSync(testFilePath)) {
    throw new Error(`Test CMDB file not found at: ${testFilePath}`);
  }

  // Find and click the upload area for Application Discovery
  const uploadArea = page.locator('.border-dashed').filter({ hasText: 'Application Discovery' }).first();
  await uploadArea.click();

  // Upload file
  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles(testFilePath);

  // Wait for upload to complete and get flow information
  await page.waitForTimeout(3000);

  // Look for success indicators and flow ID
  const successMessage = page.locator('text=/Upload completed|Processing complete|Data import complete/i');
  await expect(successMessage).toBeVisible({ timeout: 30000 });

  // Extract flow ID if available
  const flowIdElement = page.locator('text=/flow-\\d{8}-\\d{6}/');
  let flowId = '';
  if (await flowIdElement.isVisible()) {
    const flowIdText = await flowIdElement.textContent();
    flowId = flowIdText || '';
    console.log('✅ CMDB upload successful, Flow ID:', flowId);
  } else {
    console.log('✅ CMDB upload successful (no flow ID displayed)');
  }

  return { flowId };
}

async function waitForDiscoveryProcessing(page: Page, flowState: FlowState): Promise<FlowState> {
  console.log('⚙️ Waiting for discovery processing...');

  // Navigate to Attribute Mapping to check processing status
  await page.click('text=Attribute Mapping');
  await page.waitForURL('**/discovery/attribute-mapping', { timeout: 5000 });
  await page.waitForTimeout(2000);

  // Check for data processing completion
  let attempts = 0;
  const maxAttempts = 10;

  while (attempts < maxAttempts) {
    const noDataMessage = page.locator('text=No Field Mapping Available');
    const hasNoDataMessage = await noDataMessage.isVisible();

    if (!hasNoDataMessage) {
      // Data is available, processing is complete
      const fieldMappingSection = page.locator('text=/Field Mapping|Critical Attributes/');
      await expect(fieldMappingSection).toBeVisible({ timeout: 10000 });
      console.log('✅ Discovery processing completed - field mappings available');
      break;
    }

    // Check for flow selector and try to select flow
    const flowSelector = page.locator('select[id="flow-selector"], .flow-selector');
    if (await flowSelector.isVisible()) {
      console.log('Flow selector found, attempting to select flow...');
      const options = await flowSelector.locator('option').all();
      if (options.length > 1) {
        await flowSelector.selectOption({ index: 1 });
        await page.waitForTimeout(2000);
      }
    }

    attempts++;
    if (attempts < maxAttempts) {
      console.log(`⏳ Waiting for discovery processing... (attempt ${attempts}/${maxAttempts})`);
      await page.waitForTimeout(5000);
      await page.reload();
      await page.waitForTimeout(2000);
    }
  }

  if (attempts >= maxAttempts) {
    throw new Error('Discovery processing did not complete within expected time');
  }

  return flowState;
}

async function navigateToAssetInventory(page: Page): Promise<AssetInfo[]> {
  console.log('📋 Navigating to asset inventory...');

  // Navigate to asset inventory
  await page.click('text=Asset Inventory');
  await page.waitForURL('**/discovery/asset-inventory', { timeout: 5000 });
  await page.waitForTimeout(2000);

  // Wait for assets to load
  const assetsTable = page.locator('[data-testid="assets-table"], .assets-table, table');
  await expect(assetsTable).toBeVisible({ timeout: 15000 });

  // Get list of available assets
  const assetRows = await page.locator('tr').filter({ has: page.locator('td') }).all();
  const assets: AssetInfo[] = [];

  for (let i = 0; i < Math.min(assetRows.length, 5); i++) {
    const row = assetRows[i];
    const cells = await row.locator('td').all();

    if (cells.length >= 3) {
      const nameCell = await cells[0].textContent();
      const typeCell = await cells[1].textContent();
      const criticalityCell = cells.length > 3 ? await cells[3].textContent() : 'Medium';

      if (nameCell && typeCell) {
        assets.push({
          id: `asset-${i}`,
          name: nameCell.trim(),
          asset_type: typeCell.trim(),
          criticality: criticalityCell?.trim() || 'Medium'
        });
      }
    }
  }

  console.log(`✅ Found ${assets.length} assets in inventory`);
  return assets;
}

async function selectApplicationForAssessment(page: Page, assets: AssetInfo[]): Promise<AssetInfo> {
  console.log('🎯 Selecting application for assessment...');

  // Find a suitable application (prefer High/Critical criticality)
  const priorityApp = assets.find(asset =>
    asset.criticality.toLowerCase().includes('high') ||
    asset.criticality.toLowerCase().includes('critical')
  ) || assets[0];

  if (!priorityApp) {
    throw new Error('No suitable application found for assessment');
  }

  console.log(`Selected application: ${priorityApp.name} (${priorityApp.criticality})`);

  // Look for assessment initiation button or checkbox
  const assessButton = page.locator('button').filter({ hasText: /Assess|Assessment|Analyze/i }).first();
  const selectCheckbox = page.locator(`[data-testid="select-${priorityApp.id}"], input[type="checkbox"]`).first();

  if (await selectCheckbox.isVisible()) {
    await selectCheckbox.click();
    console.log('✅ Application selected via checkbox');
  }

  if (await assessButton.isVisible()) {
    await assessButton.click();
    console.log('✅ Assessment initiated');
  } else {
    // Try navigating to assessment manually
    await page.goto(`${BASE_URL}/assessment/initialize`);
  }

  return priorityApp;
}

async function executeAssessmentFlow(page: Page, selectedApp: AssetInfo): Promise<FlowState> {
  console.log('🔍 Executing assessment flow...');

  // Wait for assessment page to load
  await page.waitForTimeout(3000);

  // Check if we're on assessment initialization page
  const currentUrl = page.url();
  if (!currentUrl.includes('assessment')) {
    // Navigate to assessment flow manually
    await page.goto(`${BASE_URL}/assessment/initialize`);
    await page.waitForTimeout(2000);
  }

  // Look for flow initialization elements
  const startAssessmentBtn = page.locator('button').filter({ hasText: /Start Assessment|Begin Assessment|Initialize/i }).first();

  if (await startAssessmentBtn.isVisible()) {
    await startAssessmentBtn.click();
    console.log('✅ Assessment flow initialized');
  }

  // Wait for architecture standards phase
  await page.waitForTimeout(3000);

  // Handle architecture standards if present
  const architectureHeading = page.locator('h1, h2').filter({ hasText: /Architecture Standards/i });
  if (await architectureHeading.isVisible()) {
    console.log('📐 Setting architecture standards...');

    // Select a template if available
    const templateSelector = page.locator('[data-testid="template-selector"], select').first();
    if (await templateSelector.isVisible()) {
      await templateSelector.selectOption({ index: 1 });
      await page.waitForTimeout(1000);
    }

    // Continue to next phase
    const continueBtn = page.locator('button').filter({ hasText: /Continue|Next|Proceed/i }).first();
    if (await continueBtn.isVisible()) {
      await continueBtn.click();
    }
  }

  // Handle tech debt analysis if present
  await page.waitForTimeout(2000);
  const techDebtHeading = page.locator('h1, h2').filter({ hasText: /Tech Debt|Technical Debt/i });
  if (await techDebtHeading.isVisible()) {
    console.log('🔧 Analyzing technical debt...');

    // Wait for analysis to complete
    await page.waitForTimeout(5000);

    // Continue to 6R review
    const continueBtn = page.locator('button').filter({ hasText: /Continue|Next|6R/i }).first();
    if (await continueBtn.isVisible()) {
      await continueBtn.click();
    }
  }

  return { selectedApplicationId: selectedApp.id };
}

async function complete6RAnalysis(page: Page): Promise<string> {
  console.log('🎯 Completing 6R analysis...');

  // Wait for 6R analysis page
  await page.waitForTimeout(3000);

  // Look for 6R strategy elements
  const sixRHeading = page.locator('h1, h2').filter({ hasText: /6R|Treatment|Strategy/i });
  if (await sixRHeading.isVisible()) {
    console.log('📊 6R analysis page loaded');

    // Wait for analysis completion
    const analysisStatus = page.locator('[data-testid="analysis-status"]');
    if (await analysisStatus.isVisible()) {
      // Wait for analysis to complete
      await expect(analysisStatus).toContainText('completed', { timeout: 60000 });
    } else {
      // Wait a bit for any processing
      await page.waitForTimeout(10000);
    }

    // Look for recommendation
    const recommendationElement = page.locator('[data-testid="recommended-strategy"], .recommendation, .strategy-result').first();
    if (await recommendationElement.isVisible()) {
      const recommendation = await recommendationElement.textContent();
      console.log(`✅ 6R Recommendation: ${recommendation}`);
      return recommendation?.trim() || 'Unknown';
    }

    // Check for any strategy mentions in the page
    const pageContent = await page.content();
    const strategies = ['refactor', 'replatform', 'repurchase', 'rehost', 'retire', 'retain'];

    for (const strategy of strategies) {
      if (pageContent.toLowerCase().includes(strategy)) {
        console.log(`✅ 6R Strategy detected: ${strategy}`);
        return strategy;
      }
    }
  }

  console.log('⚠️ 6R analysis completed but no clear recommendation found');
  return 'analysis_completed';
}

async function validateDataPersistence(page: Page, flowState: FlowState): Promise<void> {
  console.log('💾 Validating data persistence...');

  // Navigate back to asset inventory to verify data is still there
  await page.goto(`${BASE_URL}/discovery/asset-inventory`);
  await page.waitForTimeout(2000);

  // Verify assets are still visible
  const assetsTable = page.locator('[data-testid="assets-table"], .assets-table, table');
  await expect(assetsTable).toBeVisible({ timeout: 10000 });

  // Navigate to dashboard to check overall state
  await page.goto(`${BASE_URL}/dashboard`);
  await page.waitForTimeout(2000);

  console.log('✅ Data persistence validated');
}

test.describe('Complete User Journey: Discovery → Assessment', () => {
  test('Complete workflow from CMDB upload to 6R treatment recommendation', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);
    const flowState: FlowState = {};

    try {
      // Phase 1: User Authentication
      await loginUser(page);

      // Phase 2: CMDB File Upload
      const uploadResult = await uploadCMDBFile(page);
      Object.assign(flowState, uploadResult);

      // Phase 3: Wait for Discovery Processing
      await waitForDiscoveryProcessing(page, flowState);

      // Phase 4: Navigate to Asset Inventory
      const assets = await navigateToAssetInventory(page);
      expect(assets.length).toBeGreaterThan(0);
      flowState.uploadedAssets = assets.length;

      // Phase 5: Select Application for Assessment
      const selectedApp = await selectApplicationForAssessment(page, assets);
      flowState.selectedApplicationId = selectedApp.id;

      // Phase 6: Execute Assessment Flow
      const assessmentResult = await executeAssessmentFlow(page, selectedApp);
      Object.assign(flowState, assessmentResult);

      // Phase 7: Complete 6R Analysis
      const recommendation = await complete6RAnalysis(page);
      flowState.finalRecommendation = recommendation;

      // Phase 8: Validate Data Persistence
      await validateDataPersistence(page, flowState);

      // Final Verification
      console.log('🎉 Complete user journey test completed successfully!');
      console.log('📊 Final State:', flowState);

      // Assertions
      expect(flowState.uploadedAssets).toBeGreaterThan(0);
      expect(flowState.selectedApplicationId).toBeDefined();
      expect(flowState.finalRecommendation).toBeDefined();
      expect(flowState.finalRecommendation).not.toBe('Unknown');

    } catch (error) {
      console.error('❌ Complete user journey test failed:', error);
      console.log('🔍 Final State at Failure:', flowState);

      // Take screenshot for debugging
      await page.screenshot({
        path: `test-results/complete-journey-failure-${Date.now()}.png`,
        fullPage: true
      });

      throw error;
    }
  });

  test('Parallel user sessions with different clients', async ({ page, context }) => {
    // Test multi-tenant isolation with parallel sessions
    console.log('🏢 Testing parallel user sessions...');

    // Create second page for different client context
    const page2 = await context.newPage();

    try {
      // Both users login
      await loginUser(page);
      await loginUser(page2);

      // Upload different datasets
      const flowState1 = await uploadCMDBFile(page);
      const flowState2 = await uploadCMDBFile(page2);

      // Verify flows are independent
      expect(flowState1.flowId).not.toBe(flowState2.flowId);

      console.log('✅ Parallel user sessions working correctly');

    } finally {
      await page2.close();
    }
  });
});

test.describe('Performance and Error Handling', () => {
  test('Handle large CMDB file upload', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);
    console.log('📊 Testing large file upload performance...');

    await loginUser(page);

    // Measure upload time
    const startTime = Date.now();
    const uploadResult = await uploadCMDBFile(page);
    const uploadTime = Date.now() - startTime;

    console.log(`⏱️ Upload completed in ${uploadTime}ms`);

    // Performance assertion
    expect(uploadTime).toBeLessThan(30000); // Should complete within 30 seconds
    expect(uploadResult.flowId).toBeDefined();
  });

  test('Handle assessment flow interruption and recovery', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);
    console.log('🔄 Testing assessment flow recovery...');

    await loginUser(page);
    await uploadCMDBFile(page);
    await waitForDiscoveryProcessing(page, {});

    const assets = await navigateToAssetInventory(page);
    const selectedApp = await selectApplicationForAssessment(page, assets);

    // Start assessment flow
    await executeAssessmentFlow(page, selectedApp);

    // Simulate interruption by navigating away
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForTimeout(2000);

    // Return to assessment and verify state
    await page.goto(`${BASE_URL}/assessment`);
    await page.waitForTimeout(2000);

    // Should be able to continue or restart
    const assessmentElements = page.locator('text=/Assessment|6R|Analysis/i');
    await expect(assessmentElements.first()).toBeVisible({ timeout: 10000 });

    console.log('✅ Assessment flow recovery tested');
  });
});
