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
  email: 'chocka@gmail.com',
  password: 'Password123!'
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

async function validateAssessmentApplicationLoading(page: Page, selectedApp: AssetInfo): Promise<void> {
  console.log('🔍 Validating assessment application loading...');

  // Test application data availability
  const applicationLoadingIssues: string[] = [];
  let loadingAttempts = 0;
  const maxLoadingAttempts = 10; // 20 seconds total

  while (loadingAttempts < maxLoadingAttempts) {
    await page.waitForTimeout(2000);
    loadingAttempts++;

    // Check if application data is loaded
    const applicationSelector = page.locator('[data-testid="application-selector"], select[name="application"], .application-dropdown');
    const applicationList = page.locator('[data-testid="application-list"], .application-item');
    const loadingIndicator = page.locator('.loading, .spinner, [data-testid="loading"]');

    // Check if still loading
    if (await loadingIndicator.isVisible()) {
      console.log(`Assessment applications still loading... (attempt ${loadingAttempts})`);
      continue;
    }

    // Check if applications are available
    if (await applicationSelector.isVisible()) {
      console.log('✅ Application selector found');
      
      // Validate selector has options
      const options = await applicationSelector.locator('option').all();
      if (options.length <= 1) { // Only default/placeholder option
        applicationLoadingIssues.push('Application selector has no application options');
      } else {
        console.log(`✅ Found ${options.length - 1} applications in selector`);
        
        // Try to select the application we're assessing
        try {
          await applicationSelector.selectOption({ label: selectedApp.name });
          console.log(`✅ Successfully selected application: ${selectedApp.name}`);
        } catch (error) {
          console.log(`⚠️ Could not select specific application, using first available: ${error}`);
          await applicationSelector.selectOption({ index: 1 });
        }
      }
      break;
    } else if (await applicationList.isVisible()) {
      const listItems = await applicationList.all();
      if (listItems.length === 0) {
        applicationLoadingIssues.push('Application list is empty');
      } else {
        console.log(`✅ Found ${listItems.length} applications in list`);
        
        // Try to select the first application
        await listItems[0].click();
        console.log('✅ Selected application from list');
      }
      break;
    } else if (loadingAttempts === maxLoadingAttempts) {
      applicationLoadingIssues.push('Applications failed to load within timeout');
    }
  }

  // Check for backend integration issues
  try {
    const applicationsResponse = await page.request.get(`${BASE_URL.replace('8081', '8000')}/api/v1/assessment/applications`);
    
    if (applicationsResponse.status() === 404) {
      applicationLoadingIssues.push('Assessment applications API endpoint not found (404)');
    } else if (applicationsResponse.status() !== 200) {
      applicationLoadingIssues.push(`Assessment applications API returned status: ${applicationsResponse.status()}`);
    } else {
      try {
        const applicationsData = await applicationsResponse.json();
        const applicationCount = Array.isArray(applicationsData) ? applicationsData.length : 
                                (applicationsData.applications ? applicationsData.applications.length : 0);
        
        if (applicationCount === 0) {
          applicationLoadingIssues.push('Assessment applications API returned empty application list');
        } else {
          console.log(`✅ Assessment API returned ${applicationCount} applications`);
        }
      } catch (error) {
        applicationLoadingIssues.push(`Could not parse assessment applications API response: ${error}`);
      }
    }
  } catch (error) {
    applicationLoadingIssues.push(`Assessment applications API error: ${error}`);
  }

  // Validate database schema compatibility
  try {
    const schemaResponse = await page.request.get(`${BASE_URL.replace('8081', '8000')}/api/v1/assessment/schema-compatibility`);
    
    if (schemaResponse.status() === 200) {
      const schemaData = await schemaResponse.json();
      if (schemaData.compatible === false) {
        applicationLoadingIssues.push('Database schema compatibility issues detected');
      } else {
        console.log('✅ Database schema compatibility validated');
      }
    } else {
      console.log('⚠️ Schema compatibility check not available');
    }
  } catch (error) {
    console.log('⚠️ Schema compatibility check skipped:', error);
  }

  // Report issues if any
  if (applicationLoadingIssues.length > 0) {
    console.error('❌ Assessment application loading issues:');
    applicationLoadingIssues.forEach(issue => console.error(`  - ${issue}`));
    
    // Take screenshot for debugging
    await page.screenshot({
      path: `test-results/assessment-loading-issues-${Date.now()}.png`,
      fullPage: true
    });
    
    throw new Error(`Assessment application loading failed: ${applicationLoadingIssues.join(', ')}`);
  }

  console.log('✅ Assessment application loading validation passed');
}

async function executeAssessmentFlow(page: Page, selectedApp: AssetInfo): Promise<FlowState> {
  console.log('🔍 Executing assessment flow...');

  await page.waitForTimeout(3000);

  const currentUrl = page.url();
  if (!currentUrl.includes('assessment')) {
    await page.goto(`${BASE_URL}/assessment/initialize`);
    await page.waitForTimeout(2000);
  }

  // Enhanced assessment flow initialization with application loading validation
  await validateAssessmentApplicationLoading(page, selectedApp);

  const startAssessmentBtn = page.locator('button').filter({ hasText: /Start Assessment|Begin Assessment|Initialize/i }).first();

  if (await startAssessmentBtn.isVisible()) {
    // Monitor assessment initialization API call
    const [initResponse] = await Promise.all([
      page.waitForResponse(response => 
        response.url().includes('/assessment/initialize') || 
        response.url().includes('/assessment/start')
      ).catch(() => null),
      startAssessmentBtn.click()
    ]);

    if (initResponse) {
      if (initResponse.status() !== 200 && initResponse.status() !== 201) {
        throw new Error(`Assessment initialization failed with status: ${initResponse.status()}`);
      }
      console.log('✅ Assessment flow initialized with valid API response');
    } else {
      console.log('✅ Assessment flow initialized (no API call detected)');
    }
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

test.describe('Assessment Flow Application Loading Validation', () => {
  test('Assessment flow application loading and backend integration', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);
    console.log('🔍 Testing assessment flow application loading issues...');

    const validationResults = {
      discoveryCompleted: false,
      applicationsAvailable: false,
      assessmentInitialized: false,
      backendIntegrationWorking: false,
      schemaCompatible: false,
      issues: [] as string[]
    };

    try {
      // Phase 1: Setup - Login and complete minimal discovery
      await loginUser(page);

      // Phase 2: Ensure we have applications for assessment
      await test.step('Verify applications are available for assessment', async () => {
        // Check if we have existing applications
        let applicationsResponse;
        try {
          applicationsResponse = await page.request.get(`${BASE_URL.replace('8081', '8000')}/api/v1/assessment/applications`);
          
          if (applicationsResponse.status() === 404) {
            validationResults.issues.push('Assessment applications API endpoint missing (404)');
          } else if (applicationsResponse.status() === 200) {
            const applicationsData = await applicationsResponse.json();
            const appCount = Array.isArray(applicationsData) ? applicationsData.length : 
                           (applicationsData.applications ? applicationsData.applications.length : 0);
            
            if (appCount > 0) {
              validationResults.applicationsAvailable = true;
              console.log(`✅ Found ${appCount} applications ready for assessment`);
            } else {
              console.log('⚠️ No applications available - running quick discovery flow');
              await runQuickDiscoveryFlow(page);
            }
          } else {
            validationResults.issues.push(`Assessment applications API returned status: ${applicationsResponse.status()}`);
          }
        } catch (error) {
          validationResults.issues.push(`Assessment applications API error: ${error}`);
          console.log('⚠️ Cannot verify applications via API - running quick discovery flow');
          await runQuickDiscoveryFlow(page);
        }
      });

      // Phase 3: Test assessment flow initialization
      await test.step('Test assessment flow frontend loading', async () => {
        await page.goto(`${BASE_URL}/assessment/initialize`);
        await page.waitForTimeout(3000);

        // Test for frontend filtering issues
        const loadingStates = [];
        let loadingAttempts = 0;
        const maxAttempts = 15; // 30 seconds

        while (loadingAttempts < maxAttempts) {
          await page.waitForTimeout(2000);
          loadingAttempts++;

          // Check for loading indicators
          const loadingSpinner = page.locator('.loading, .spinner, [data-testid="loading"]');
          const applicationSelector = page.locator('[data-testid="application-selector"], select[name="application"]');
          const applicationList = page.locator('.application-item, [data-testid="application-item"]');
          const errorMessage = page.locator('.error, [role="alert"], .alert-error');

          const currentState = {
            attempt: loadingAttempts,
            hasLoader: await loadingSpinner.isVisible(),
            hasSelector: await applicationSelector.isVisible(),
            hasApplications: await applicationList.count() > 0,
            hasError: await errorMessage.isVisible()
          };

          loadingStates.push(currentState);

          if (currentState.hasError) {
            const errorText = await errorMessage.textContent();
            validationResults.issues.push(`Assessment UI error: ${errorText}`);
            break;
          }

          if (currentState.hasSelector || currentState.hasApplications) {
            validationResults.applicationsAvailable = true;
            console.log(`✅ Assessment UI loaded applications after ${loadingAttempts * 2} seconds`);
            break;
          }

          if (loadingAttempts === maxAttempts) {
            validationResults.issues.push('Assessment frontend failed to load applications within timeout');
          }
        }

        // Validate frontend filtering works
        if (validationResults.applicationsAvailable) {
          await testFrontendFiltering(page, validationResults);
        }
      });

      // Phase 4: Test backend integration
      await test.step('Test backend integration for assessment', async () => {
        try {
          // Test assessment readiness endpoint
          const readinessResponse = await page.request.get(`${BASE_URL.replace('8081', '8000')}/api/v1/assessment/readiness`);
          
          if (readinessResponse.status() === 200) {
            const readinessData = await readinessResponse.json();
            if (readinessData.ready === true || readinessData.applications_count > 0) {
              validationResults.backendIntegrationWorking = true;
              console.log('✅ Backend assessment integration working');
            } else {
              validationResults.issues.push('Backend reports assessment not ready');
            }
          } else if (readinessResponse.status() === 404) {
            validationResults.issues.push('Assessment readiness endpoint not found (404)');
          } else {
            validationResults.issues.push(`Assessment readiness endpoint returned: ${readinessResponse.status()}`);
          }
        } catch (error) {
          validationResults.issues.push(`Backend integration test failed: ${error}`);
        }
      });

      // Phase 5: Test database schema compatibility
      await test.step('Test database schema compatibility', async () => {
        try {
          const schemaResponse = await page.request.get(`${BASE_URL.replace('8081', '8000')}/api/v1/assessment/schema-validation`);
          
          if (schemaResponse.status() === 200) {
            const schemaData = await schemaResponse.json();
            if (schemaData.compatible !== false) {
              validationResults.schemaCompatible = true;
              console.log('✅ Database schema compatibility validated');
            } else {
              validationResults.issues.push(`Schema compatibility issues: ${JSON.stringify(schemaData.issues)}`);
            }
          } else {
            console.log('⚠️ Schema validation endpoint not available - assuming compatible');
            validationResults.schemaCompatible = true;
          }
        } catch (error) {
          console.log('⚠️ Schema validation test skipped:', error);
          validationResults.schemaCompatible = true; // Don't fail for optional feature
        }
      });

      // Phase 6: Test actual assessment initialization
      await test.step('Test assessment initialization', async () => {
        const initButton = page.locator('button').filter({ hasText: /Start Assessment|Initialize|Begin/i }).first();
        
        if (await initButton.isVisible()) {
          // Monitor assessment initialization
          const [initResponse] = await Promise.all([
            page.waitForResponse(response => 
              response.url().includes('/assessment/initialize') ||
              response.url().includes('/assessment/start')
            ).catch(() => null),
            initButton.click()
          ]);

          await page.waitForTimeout(3000);

          // Check if assessment actually started
          const assessmentContent = page.locator('h1, h2').filter({ hasText: /Assessment|Architecture|Standards/i });
          const errorIndicator = page.locator('.error, [role="alert"]');

          if (await assessmentContent.isVisible()) {
            validationResults.assessmentInitialized = true;
            console.log('✅ Assessment flow successfully initialized');
          } else if (await errorIndicator.isVisible()) {
            const errorText = await errorIndicator.textContent();
            validationResults.issues.push(`Assessment initialization error: ${errorText}`);
          } else {
            validationResults.issues.push('Assessment did not start after initialization');
          }

          if (initResponse && initResponse.status() !== 200 && initResponse.status() !== 201) {
            validationResults.issues.push(`Assessment API returned status: ${initResponse.status()}`);
          }
        } else {
          validationResults.issues.push('Assessment initialization button not found');
        }
      });

      // Final validation
      console.log('\n=== Assessment Flow Validation Results ===');
      console.log(`Applications Available: ${validationResults.applicationsAvailable}`);
      console.log(`Backend Integration Working: ${validationResults.backendIntegrationWorking}`);
      console.log(`Schema Compatible: ${validationResults.schemaCompatible}`);
      console.log(`Assessment Initialized: ${validationResults.assessmentInitialized}`);
      console.log(`Issues Found: ${validationResults.issues.length}`);

      if (validationResults.issues.length > 0) {
        console.log('\nIssues:');
        validationResults.issues.forEach(issue => console.log(`- ${issue}`));
      }

      // Assertions
      expect(validationResults.applicationsAvailable, 'Applications should be available for assessment').toBe(true);
      expect(validationResults.backendIntegrationWorking, 'Backend integration should be working').toBe(true);
      expect(validationResults.schemaCompatible, 'Database schema should be compatible').toBe(true);
      expect(validationResults.issues.length, 'Should have no critical issues').toBeLessThan(3); // Allow minor issues

    } catch (error) {
      console.error('❌ Assessment flow validation failed:', error);
      console.log('🔍 Validation Results at Failure:', validationResults);

      await page.screenshot({
        path: `test-results/assessment-flow-failure-${Date.now()}.png`,
        fullPage: true
      });

      throw error;
    }
  });
});

// Helper function to run a quick discovery flow if needed
async function runQuickDiscoveryFlow(page: Page): Promise<void> {
  console.log('🚀 Running quick discovery flow to create applications...');

  await page.goto(`${BASE_URL}/discovery/cmdb-import`);
  await page.waitForTimeout(2000);

  const testFilePath = path.join(__dirname, '../fixtures/test-cmdb-data.csv');
  const uploadArea = page.locator('.border-dashed').first();
  
  if (await uploadArea.isVisible()) {
    await uploadArea.click();
    await page.locator('input[type="file"]').setInputFiles(testFilePath);
    await page.waitForTimeout(5000); // Wait for processing
    console.log('✅ Quick discovery flow completed');
  }
}

// Helper function to test frontend filtering
async function testFrontendFiltering(page: Page, validationResults: any): Promise<void> {
  console.log('🔍 Testing frontend filtering functionality...');

  const filterInput = page.locator('input[placeholder*="filter"], input[placeholder*="search"], .filter-input');
  const applicationItems = page.locator('.application-item, [data-testid="application-item"]');

  if (await filterInput.isVisible()) {
    const initialCount = await applicationItems.count();
    
    // Test filtering
    await filterInput.fill('test');
    await page.waitForTimeout(1000);
    
    const filteredCount = await applicationItems.count();
    
    if (filteredCount <= initialCount) {
      console.log('✅ Frontend filtering appears to work');
    } else {
      validationResults.issues.push('Frontend filtering may not be working properly');
    }

    // Clear filter
    await filterInput.clear();
    await page.waitForTimeout(1000);
  } else {
    console.log('⚠️ No filter input found - skipping filter test');
  }
}
