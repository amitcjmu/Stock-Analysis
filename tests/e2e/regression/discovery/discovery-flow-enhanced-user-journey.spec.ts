/**
 * Enhanced Discovery Flow E2E Test - User Journey with Full Validation
 *
 * This enhanced version:
 * 1. Follows actual user journey (including blocking flows)
 * 2. Validates UI elements on each page
 * 3. Verifies database persistence
 * 4. Reports errors by layer (Frontend/Middleware/Backend/Database)
 */

import { test, expect, Page, APIRequestContext } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import {
  TEST_CONFIG,
  TEST_USERS,
  generateTestCSV,
  login,
  navigateToDiscovery,
  captureFlowState,
  takeScreenshot
} from '../../helpers/test-helpers';

// Import existing interfaces and types from the original test
interface EnhancedPhaseResult {
  name: string;
  status: 'PASS' | 'FAIL' | 'SKIP';
  duration: number;
  flowId: string | null;
  currentPage: string;  // Added: Track which page we're on
  steps: StepResult[];
  databaseValidation: DatabaseValidation;
  apiValidation: ApiValidation;
  frontendValidation: FrontendValidation;
  fieldNamingValidation: FieldNamingValidation;
  userJourneyValidation: UserJourneyValidation;  // Added: User journey tracking
}

interface UserJourneyValidation {
  expectedPath: string[];
  actualPath: string[];
  blockingFlowDetected: boolean;
  blockingFlowType?: string;
  requiredActionsCompleted: boolean;
  canProceedToNextStep: boolean;
}

interface DatabaseValidation {
  tablesChecked: string[];
  recordCounts: Record<string, number>;
  relationships: Record<string, boolean>;
  constraints: Record<string, boolean>;
  dataIntegrity: Record<string, any>;  // Added: Verify actual data saved
}

interface StepResult {
  step: string;
  page: string;  // Added: Which page this step occurred on
  status: 'PASS' | 'FAIL' | 'SKIP';
  duration: number;
  errors: LayeredError[];  // Enhanced error structure
  warnings: string[];
  validations: ValidationResult[];  // Added: Detailed validations
}

interface LayeredError {
  layer: 'frontend' | 'middleware' | 'backend' | 'database';
  type: string;
  message: string;
  details?: any;
  stackTrace?: string;
  timestamp: string;
}

interface ValidationResult {
  type: 'ui' | 'api' | 'database' | 'business_logic';
  element?: string;
  expected: any;
  actual: any;
  passed: boolean;
  message?: string;
}

// Enhanced error tracking by layer
const errorsByLayer = {
  frontend: [] as LayeredError[],
  middleware: [] as LayeredError[],
  backend: [] as LayeredError[],
  database: [] as LayeredError[]
};

// Helper to add errors with layer information
function addLayeredError(layer: keyof typeof errorsByLayer, type: string, message: string, details?: any) {
  const error: LayeredError = {
    layer,
    type,
    message,
    details,
    timestamp: new Date().toISOString()
  };
  errorsByLayer[layer].push(error);
  console.error(`❌ [${layer.toUpperCase()}] ${type}: ${message}`, details || '');
  return error;
}

// Helper to validate UI elements
async function validateUIElement(
  page: Page,
  selector: string,
  elementName: string,
  validations: ValidationResult[]
): Promise<boolean> {
  try {
    const element = page.locator(selector);
    const isVisible = await element.isVisible({ timeout: 5000 });
    const isEnabled = isVisible ? await element.isEnabled() : false;

    validations.push({
      type: 'ui',
      element: elementName,
      expected: { visible: true, enabled: true },
      actual: { visible: isVisible, enabled: isEnabled },
      passed: isVisible && isEnabled,
      message: `${elementName}: visible=${isVisible}, enabled=${isEnabled}`
    });

    return isVisible && isEnabled;
  } catch (error) {
    validations.push({
      type: 'ui',
      element: elementName,
      expected: { visible: true },
      actual: { error: error.message },
      passed: false,
      message: `Failed to validate ${elementName}: ${error.message}`
    });
    return false;
  }
}

// Helper to verify database persistence
async function verifyDatabasePersistence(
  apiContext: APIRequestContext,
  tableName: string,
  expectedData: any,
  tenantHeaders: any
): Promise<ValidationResult> {
  try {
    // Query the database through a diagnostic endpoint
    const response = await apiContext.post('/api/v1/test/diagnostics/query', {
      headers: tenantHeaders,
      data: {
        table: tableName,
        filters: expectedData.filters || {},
        fields: expectedData.fields || ['*']
      }
    });

    if (!response.ok()) {
      throw new Error(`Database query failed: ${response.status()}`);
    }

    const data = await response.json();
    const validation: ValidationResult = {
      type: 'database',
      expected: expectedData.expected,
      actual: data,
      passed: false,
      message: ''
    };

    // Verify data matches expectations
    if (expectedData.count !== undefined) {
      validation.passed = data.length === expectedData.count;
      validation.message = `Expected ${expectedData.count} records, found ${data.length}`;
    }

    if (expectedData.fields && data.length > 0) {
      const record = data[0];
      for (const [field, value] of Object.entries(expectedData.fields)) {
        if (record[field] !== value) {
          validation.passed = false;
          validation.message += `\nField ${field}: expected ${value}, got ${record[field]}`;
        }
      }
    }

    return validation;
  } catch (error) {
    return {
      type: 'database',
      expected: expectedData,
      actual: { error: error.message },
      passed: false,
      message: `Database verification failed: ${error.message}`
    };
  }
}

// Main test suite with enhanced user journey
test.describe('Discovery Flow - Enhanced User Journey with Full Validation', () => {
  let apiContext: APIRequestContext;
  const discoveryFlowId: string | null = null;
  let tenantHeaders: any = {};
  let testDataFile: string;

  test.beforeAll(async ({ playwright }) => {
    apiContext = await playwright.request.newContext({
      baseURL: TEST_CONFIG.apiURL,
      ignoreHTTPSErrors: true,
      extraHTTPHeaders: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });

    // Use real demo UUIDs from database
    tenantHeaders = {
      'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
      'X-Engagement-ID': '22222222-2222-2222-2222-222222222222'
    };

    // Create test data
    const testDir = path.join(process.cwd(), 'tests', 'e2e', 'test-data');
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }

    const csvContent = generateTestCSV(20);
    testDataFile = path.join(testDir, `e2e-enhanced-${Date.now()}.csv`);
    fs.writeFileSync(testDataFile, csvContent);
  });

  test.afterAll(async () => {
    await apiContext.dispose();
    if (testDataFile && fs.existsSync(testDataFile)) {
      fs.unlinkSync(testDataFile);
    }
  });

  test.beforeEach(async ({ page }) => {
    // Reset error tracking
    errorsByLayer.frontend = [];
    errorsByLayer.middleware = [];
    errorsByLayer.backend = [];
    errorsByLayer.database = [];

    // Enhanced error monitoring
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        addLayeredError('frontend', 'Console Error', msg.text());
      }
    });

    page.on('response', async (response) => {
      const url = response.url();
      const status = response.status();

      if (status >= 500) {
        addLayeredError('backend', `HTTP ${status}`, url, {
          statusText: response.statusText(),
          headers: response.headers()
        });
      } else if (status >= 400) {
        addLayeredError('middleware', `HTTP ${status}`, url, {
          statusText: response.statusText()
        });
      }
    });

    // Login
    await login(page, TEST_USERS.demo);
    await takeScreenshot(page, 'login-complete');
  });

  test('Complete User Journey - From Login to Discovery Completion', async ({ page }) => {
    const testStart = Date.now();
    const journeyValidation: UserJourneyValidation = {
      expectedPath: ['login', 'dashboard', 'blocking-flow', 'attribute-mapping', 'data-import', 'discovery-dashboard'],
      actualPath: ['login'],
      blockingFlowDetected: false,
      requiredActionsCompleted: false,
      canProceedToNextStep: false
    };

    const allValidations: ValidationResult[] = [];
    const allSteps: StepResult[] = [];

    try {
      console.log('🚀 Starting Enhanced User Journey Test');

      // ============= STEP 1: Dashboard & Blocking Flow Detection =============
      console.log('\n📍 Step 1: Check Dashboard for Blocking Flows');
      const step1Start = Date.now();
      const step1Validations: ValidationResult[] = [];

      // Navigate to dashboard
      await page.goto(`${TEST_CONFIG.baseURL}/`);
      await page.waitForLoadState('networkidle');
      journeyValidation.actualPath.push('dashboard');

      // Validate dashboard UI elements
      await validateUIElement(page, 'text=AI Modernize Migration Platform', 'Dashboard Title', step1Validations);
      await validateUIElement(page, 'text=Discovery/Collection', 'Discovery Card', step1Validations);

      // Check for blocking flow banner
      const blockingFlowBanner = page.locator('[data-testid="blocking-flow-banner"], .blocking-flow-notification, .alert-warning');
      const hasBlockingFlow = await blockingFlowBanner.isVisible({ timeout: 3000 }).catch(() => false);

      if (hasBlockingFlow) {
        console.log('⚠️ Blocking flow detected!');
        journeyValidation.blockingFlowDetected = true;

        // Get blocking flow details
        const blockingFlowText = await blockingFlowBanner.textContent();
        journeyValidation.blockingFlowType = blockingFlowText?.includes('attribute') ? 'attribute-mapping' :
                                              blockingFlowText?.includes('import') ? 'data-import' : 'unknown';

        // Find and click continue button
        const continueButton = page.locator('button:has-text("Continue"), button:has-text("Resume"), [data-testid="continue-flow"]');
        const canContinue = await continueButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (canContinue) {
          await continueButton.click();
          await page.waitForLoadState('networkidle');
          journeyValidation.actualPath.push('blocking-flow');

          // Verify we were redirected to the right place
          const currentUrl = page.url();
          if (currentUrl.includes('attribute-mapping')) {
            journeyValidation.actualPath.push('attribute-mapping');
          } else if (currentUrl.includes('data-import')) {
            journeyValidation.actualPath.push('data-import');
          }
        }
      }

      allSteps.push({
        step: 'Dashboard & Blocking Flow Check',
        page: 'dashboard',
        status: step1Validations.every(v => v.passed) ? 'PASS' : 'FAIL',
        duration: Date.now() - step1Start,
        errors: [],
        warnings: hasBlockingFlow ? ['Blocking flow detected'] : [],
        validations: step1Validations
      });

      // ============= STEP 2: Handle Attribute Mapping if Required =============
      if (journeyValidation.blockingFlowType === 'attribute-mapping' || page.url().includes('attribute-mapping')) {
        console.log('\n📍 Step 2: Attribute Mapping Validation');
        const step2Start = Date.now();
        const step2Validations: ValidationResult[] = [];
        const step2Errors: LayeredError[] = [];

        // Validate we're on the attribute mapping page
        await validateUIElement(page, '[data-testid="attribute-mapping-page"], h1:has-text("Attribute Mapping")', 'Attribute Mapping Page', step2Validations);

        // Fetch field mappings from API
        const mappingsResponse = await apiContext.get(
          `/api/v1/unified-discovery/flows/${discoveryFlowId || 'current'}/field-mappings`,
          { headers: tenantHeaders }
        );

        if (!mappingsResponse.ok()) {
          step2Errors.push(addLayeredError('backend', 'API Error', `Failed to fetch mappings: ${mappingsResponse.status()}`));
        } else {
          const mappings = await mappingsResponse.json();

          // CRITICAL: Validate mappings exist and are complete
          if (!mappings || mappings.length === 0) {
            step2Errors.push(addLayeredError('business_logic', 'No Mappings', 'No field mappings found - flow is blocked'));

            // Verify UI shows unmapped fields
            const unmappedIndicator = page.locator('.unmapped-field, [data-testid="unmapped-field"]');
            const hasUnmappedFields = await unmappedIndicator.count() > 0;

            step2Validations.push({
              type: 'business_logic',
              expected: 'All fields mapped',
              actual: `${mappings?.length || 0} mappings, unmapped fields visible: ${hasUnmappedFields}`,
              passed: false,
              message: 'Field mapping incomplete - user cannot proceed'
            });
          } else {
            // Check for unmapped fields
            const unmappedFields = mappings.filter(m => !m.target_field || m.status === 'pending');

            if (unmappedFields.length > 0) {
              step2Errors.push(addLayeredError('business_logic', 'Unmapped Fields',
                `${unmappedFields.length} fields are unmapped: ${unmappedFields.map(f => f.source_field).join(', ')}`
              ));

              step2Validations.push({
                type: 'business_logic',
                expected: 'All fields mapped',
                actual: `${unmappedFields.length} unmapped fields`,
                passed: false,
                message: 'User must complete mapping before proceeding'
              });
            }

            // Verify database persistence of mappings
            const dbValidation = await verifyDatabasePersistence(apiContext, 'import_field_mappings', {
              filters: { flow_id: discoveryFlowId },
              expected: { count: mappings.length },
              fields: { status: 'approved' }
            }, tenantHeaders);

            step2Validations.push(dbValidation);
          }
        }

        // Check if proceed button is enabled
        const proceedButton = page.locator('button:has-text("Proceed"), button:has-text("Continue"), button:has-text("Next")');
        const canProceed = await proceedButton.isEnabled().catch(() => false);

        journeyValidation.canProceedToNextStep = canProceed;

        step2Validations.push({
          type: 'ui',
          element: 'Proceed Button',
          expected: { enabled: true },
          actual: { enabled: canProceed },
          passed: canProceed,
          message: canProceed ? 'User can proceed' : 'User blocked - must complete mappings'
        });

        allSteps.push({
          step: 'Attribute Mapping',
          page: 'attribute-mapping',
          status: step2Validations.every(v => v.passed) ? 'PASS' : 'FAIL',
          duration: Date.now() - step2Start,
          errors: step2Errors,
          warnings: [],
          validations: step2Validations
        });
      }

      // ============= STEP 3: Data Import =============
      console.log('\n📍 Step 3: Data Import Process');
      const step3Start = Date.now();
      const step3Validations: ValidationResult[] = [];
      const step3Errors: LayeredError[] = [];

      // Navigate to data import
      if (!page.url().includes('cmdb-import')) {
        await page.goto(`${TEST_CONFIG.baseURL}/discovery/cmdb-import`);
        await page.waitForLoadState('networkidle');
      }
      journeyValidation.actualPath.push('data-import');

      // Validate import page UI
      await validateUIElement(page, '[data-testid="cmdb-import-page"], h1:has-text("Import")', 'Import Page', step3Validations);
      await validateUIElement(page, 'input[type="file"], [data-testid="file-upload"]', 'File Upload Input', step3Validations);

      // Upload test file
      const fileInput = page.locator('input[type="file"]');
      if (await fileInput.isVisible()) {
        await fileInput.setInputFiles(testDataFile);

        // Wait for upload processing
        await page.waitForTimeout(2000);

        // Verify file was processed
        const uploadStatus = page.locator('.upload-success, [data-testid="upload-success"]');
        const uploadSuccess = await uploadStatus.isVisible({ timeout: 5000 }).catch(() => false);

        step3Validations.push({
          type: 'ui',
          element: 'Upload Status',
          expected: 'File uploaded successfully',
          actual: uploadSuccess ? 'Success' : 'Failed',
          passed: uploadSuccess,
          message: uploadSuccess ? 'File processed' : 'Upload failed'
        });

        // Verify database persistence
        const importDbValidation = await verifyDatabasePersistence(apiContext, 'data_imports', {
          filters: { client_account_id: tenantHeaders['X-Client-Account-ID'] },
          expected: { hasRecords: true }
        }, tenantHeaders);

        step3Validations.push(importDbValidation);
      }

      allSteps.push({
        step: 'Data Import',
        page: 'cmdb-import',
        status: step3Validations.every(v => v.passed) ? 'PASS' : 'FAIL',
        duration: Date.now() - step3Start,
        errors: step3Errors,
        warnings: [],
        validations: step3Validations
      });

      // ============= FINAL: Generate Comprehensive Report =============
      const testDuration = Date.now() - testStart;
      const allPassed = allSteps.every(s => s.status === 'PASS');

      console.log('\n' + '='.repeat(80));
      console.log('📊 ENHANCED USER JOURNEY TEST REPORT');
      console.log('='.repeat(80));

      console.log('\n🛤️ User Journey Path:');
      console.log('  Expected:', journeyValidation.expectedPath.join(' → '));
      console.log('  Actual:  ', journeyValidation.actualPath.join(' → '));

      console.log('\n📍 Step Results:');
      for (const step of allSteps) {
        const icon = step.status === 'PASS' ? '✅' : '❌';
        console.log(`  ${icon} ${step.step} (${step.page}): ${step.status} - ${step.duration}ms`);

        if (step.errors.length > 0) {
          console.log('     Errors:');
          for (const error of step.errors) {
            console.log(`       [${error.layer}] ${error.message}`);
          }
        }

        const failedValidations = step.validations.filter(v => !v.passed);
        if (failedValidations.length > 0) {
          console.log('     Failed Validations:');
          for (const validation of failedValidations) {
            console.log(`       ${validation.message}`);
          }
        }
      }

      console.log('\n🔍 Error Summary by Layer:');
      console.log(`  Frontend:   ${errorsByLayer.frontend.length} errors`);
      console.log(`  Middleware: ${errorsByLayer.middleware.length} errors`);
      console.log(`  Backend:    ${errorsByLayer.backend.length} errors`);
      console.log(`  Database:   ${errorsByLayer.database.length} errors`);

      console.log('\n⚠️ Blocking Flow Status:');
      console.log(`  Detected: ${journeyValidation.blockingFlowDetected ? 'YES' : 'NO'}`);
      if (journeyValidation.blockingFlowDetected) {
        console.log(`  Type: ${journeyValidation.blockingFlowType}`);
        console.log(`  Can Proceed: ${journeyValidation.canProceedToNextStep ? 'YES' : 'NO'}`);
      }

      console.log('\n' + '='.repeat(80));
      console.log(`📈 Overall Result: ${allPassed ? 'PASS ✅' : 'FAIL ❌'}`);
      console.log(`⏱️  Total Duration: ${testDuration}ms`);
      console.log('='.repeat(80));

      // Generate detailed JSON report
      const detailedReport = {
        testName: 'Enhanced User Journey Test',
        timestamp: new Date().toISOString(),
        duration: testDuration,
        status: allPassed ? 'PASS' : 'FAIL',
        userJourney: journeyValidation,
        steps: allSteps,
        errorsByLayer,
        validationSummary: {
          total: allValidations.length,
          passed: allValidations.filter(v => v.passed).length,
          failed: allValidations.filter(v => !v.passed).length
        }
      };

      const reportPath = path.join(process.cwd(), 'tests', 'e2e', 'test-results', `enhanced-journey-${Date.now()}.json`);
      fs.writeFileSync(reportPath, JSON.stringify(detailedReport, null, 2));
      console.log(`\n📄 Detailed report saved to: ${reportPath}`);

      // Assert test passes
      expect(allPassed).toBeTruthy();

    } catch (error) {
      console.error('❌ Test failed with error:', error);
      throw error;
    }
  });
});
