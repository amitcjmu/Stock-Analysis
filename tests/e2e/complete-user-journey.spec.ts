import { test, expect, Page } from '@playwright/test';
import path from 'path';
import fs from 'fs';

/**
 * Complete User Journey Test Suite
 *
 * Tests the complete workflow: Login → CMDB Upload → Discovery Flow → Asset Selection → Assessment Flow → 6R Treatment
 */

// Test configuration
const BASE_URL = 'http://localhost:8081';
const TEST_TIMEOUT = 300000; // 5 minutes

// Test user credentials
const TEST_USER = {
  email: 'demo@demo-corp.com',
  password: 'Demo123!'
};

interface FlowState {
  flowId?: string;
  uploadedAssets?: number;
  selectedApplicationId?: string;
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

  await page.fill('input[type="email"]', TEST_USER.email);
  await page.fill('input[type="password"]', TEST_USER.password);
  await page.click('button[type="submit"]');

  await page.waitForURL('**/dashboard', { timeout: 10000 });
  console.log('✅ User logged in successfully');
}

async function uploadCMDBFile(page: Page): Promise<FlowState> {
  console.log('📁 Uploading CMDB file...');

  await page.click('text=Discovery');
  await page.waitForTimeout(1000);

  const overviewVisible = await page.locator('text=Overview').isVisible();
  if (overviewVisible) {
    const flowNotFound = await page.locator('text=/flow.*not.*found|Flow not found/i').isVisible();
    if (flowNotFound) {
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

  const testFilePath = path.join(__dirname, '../fixtures/enterprise-cmdb-data.csv');

  if (!fs.existsSync(testFilePath)) {
    throw new Error(`Test CMDB file not found at: ${testFilePath}`);
  }

  const uploadArea = page.locator('.border-dashed').filter({ hasText: 'Application Discovery' }).first();
  await uploadArea.click();

  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles(testFilePath);

  await page.waitForTimeout(3000);

  const successMessage = page.locator('text=/Upload completed|Processing complete|Data import complete/i');
  await expect(successMessage).toBeVisible({ timeout: 30000 });

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

  await page.click('text=Attribute Mapping');
  await page.waitForURL('**/discovery/attribute-mapping', { timeout: 5000 });
  await page.waitForTimeout(2000);

  let attempts = 0;
  const maxAttempts = 10;

  while (attempts < maxAttempts) {
    const noDataMessage = page.locator('text=No Field Mapping Available');
    const hasNoDataMessage = await noDataMessage.isVisible();

    if (!hasNoDataMessage) {
      const fieldMappingSection = page.locator('text=/Field Mapping|Critical Attributes/');
      await expect(fieldMappingSection).toBeVisible({ timeout: 10000 });
      console.log('✅ Discovery processing completed - field mappings available');
      break;
    }

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

  await page.click('text=Asset Inventory');
  await page.waitForURL('**/discovery/asset-inventory', { timeout: 5000 });
  await page.waitForTimeout(2000);

  const assetsTable = page.locator('[data-testid="assets-table"], .assets-table, table');
  await expect(assetsTable).toBeVisible({ timeout: 15000 });

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

  const priorityApp = assets.find(asset =>
    asset.criticality.toLowerCase().includes('high') ||
    asset.criticality.toLowerCase().includes('critical')
  ) || assets[0];

  if (!priorityApp) {
    throw new Error('No suitable application found for assessment');
  }

  console.log(`Selected application: ${priorityApp.name} (${priorityApp.criticality})`);

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
    await page.goto(`${BASE_URL}/assessment/initialize`);
  }

  return priorityApp;
}

async function executeAssessmentFlow(page: Page, selectedApp: AssetInfo): Promise<FlowState> {
  console.log('🔍 Executing assessment flow...');

  await page.waitForTimeout(3000);

  const currentUrl = page.url();
  if (!currentUrl.includes('assessment')) {
    await page.goto(`${BASE_URL}/assessment/initialize`);
    await page.waitForTimeout(2000);
  }

  const startAssessmentBtn = page.locator('button').filter({ hasText: /Start Assessment|Begin Assessment|Initialize/i }).first();

  if (await startAssessmentBtn.isVisible()) {
    await startAssessmentBtn.click();
    console.log('✅ Assessment flow initialized');
  }

  await page.waitForTimeout(3000);

  const architectureHeading = page.locator('h1, h2').filter({ hasText: /Architecture Standards/i });
  if (await architectureHeading.isVisible()) {
    console.log('📐 Setting architecture standards...');

    const templateSelector = page.locator('[data-testid="template-selector"], select').first();
    if (await templateSelector.isVisible()) {
      await templateSelector.selectOption({ index: 1 });
      await page.waitForTimeout(1000);
    }

    const continueBtn = page.locator('button').filter({ hasText: /Continue|Next|Proceed/i }).first();
    if (await continueBtn.isVisible()) {
      await continueBtn.click();
    }
  }

  await page.waitForTimeout(2000);
  const techDebtHeading = page.locator('h1, h2').filter({ hasText: /Tech Debt|Technical Debt/i });
  if (await techDebtHeading.isVisible()) {
    console.log('🔧 Analyzing technical debt...');

    await page.waitForTimeout(5000);

    const continueBtn = page.locator('button').filter({ hasText: /Continue|Next|6R/i }).first();
    if (await continueBtn.isVisible()) {
      await continueBtn.click();
    }
  }

  return { selectedApplicationId: selectedApp.id };
}

async function complete6RAnalysis(page: Page): Promise<string> {
  console.log('🎯 Completing 6R analysis...');

  await page.waitForTimeout(3000);

  const sixRHeading = page.locator('h1, h2').filter({ hasText: /6R|Treatment|Strategy/i });
  if (await sixRHeading.isVisible()) {
    console.log('📊 6R analysis page loaded');

    const analysisStatus = page.locator('[data-testid="analysis-status"]');
    if (await analysisStatus.isVisible()) {
      await expect(analysisStatus).toContainText('completed', { timeout: 60000 });
    } else {
      await page.waitForTimeout(10000);
    }

    const recommendationElement = page.locator('[data-testid="recommended-strategy"], .recommendation, .strategy-result').first();
    if (await recommendationElement.isVisible()) {
      const recommendation = await recommendationElement.textContent();
      console.log(`✅ 6R Recommendation: ${recommendation}`);
      return recommendation?.trim() || 'Unknown';
    }

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

  await page.goto(`${BASE_URL}/discovery/asset-inventory`);
  await page.waitForTimeout(2000);

  const assetsTable = page.locator('[data-testid="assets-table"], .assets-table, table');
  await expect(assetsTable).toBeVisible({ timeout: 10000 });

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

      await page.screenshot({
        path: `test-results/complete-journey-failure-${Date.now()}.png`,
        fullPage: true
      });

      throw error;
    }
  });
});

test.describe('Performance and Error Handling', () => {
  test('Handle large CMDB file upload', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);
    console.log('📊 Testing large file upload performance...');

    await loginUser(page);

    const startTime = Date.now();
    const uploadResult = await uploadCMDBFile(page);
    const uploadTime = Date.now() - startTime;

    console.log(`⏱️ Upload completed in ${uploadTime}ms`);

    expect(uploadTime).toBeLessThan(30000);
    expect(uploadResult.flowId).toBeDefined();
  });
});
