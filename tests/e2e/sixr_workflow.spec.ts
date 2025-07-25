import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:8081';
const API_BASE_URL = process.env.E2E_API_BASE_URL || 'http://localhost:8000';

// Test data
const testApplications = [
  {
    id: 1,
    name: 'Customer Portal',
    description: 'Web-based customer service portal',
    technology_stack: ['Java 8', 'Spring', 'MySQL'],
    department: 'Finance',
    business_unit: 'Customer Service',
    criticality: 'high',
    complexity_score: 7
  },
  {
    id: 2,
    name: 'Legacy Billing System',
    description: 'COBOL-based billing application',
    technology_stack: ['COBOL', 'DB2', 'CICS'],
    department: 'Finance',
    business_unit: 'Billing',
    criticality: 'critical',
    complexity_score: 9
  }
];

const testParameters = {
  business_value: 7,
  technical_complexity: 5,
  migration_urgency: 6,
  compliance_requirements: 4,
  cost_sensitivity: 5,
  risk_tolerance: 6,
  innovation_priority: 8,
  application_type: 'custom'
};

// Helper functions
async function navigateToTreatmentPage(page: Page) {
  await page.goto(`${BASE_URL}/assess/treatment`);
  await expect(page.locator('h1')).toContainText('6R Treatment Analysis');
}

async function selectApplication(page: Page, applicationName: string) {
  await page.locator(`[data-testid="application-${applicationName}"]`).click();
  await expect(page.locator(`[data-testid="application-${applicationName}"]`)).toHaveClass(/selected/);
}

async function setParameters(page: Page, parameters: typeof testParameters) {
  // Set business value
  await page.locator('[data-testid="business-value-slider"]').fill(parameters.business_value.toString());

  // Set technical complexity
  await page.locator('[data-testid="technical-complexity-slider"]').fill(parameters.technical_complexity.toString());

  // Set migration urgency
  await page.locator('[data-testid="migration-urgency-slider"]').fill(parameters.migration_urgency.toString());

  // Set compliance requirements
  await page.locator('[data-testid="compliance-requirements-slider"]').fill(parameters.compliance_requirements.toString());

  // Set cost sensitivity
  await page.locator('[data-testid="cost-sensitivity-slider"]').fill(parameters.cost_sensitivity.toString());

  // Set risk tolerance
  await page.locator('[data-testid="risk-tolerance-slider"]').fill(parameters.risk_tolerance.toString());

  // Set innovation priority
  await page.locator('[data-testid="innovation-priority-slider"]').fill(parameters.innovation_priority.toString());

  // Set application type
  await page.locator(`[data-testid="app-type-${parameters.application_type}"]`).click();
}

async function answerQualifyingQuestions(page: Page) {
  // Answer application type question
  await page.locator('[data-testid="question-app_type-custom"]').click();

  // Answer business impact question
  await page.locator('[data-testid="question-business_impact-significant"]').click();

  // Answer user count question
  await page.locator('[data-testid="question-user_count"]').fill('1500');

  // Answer migration timeline question
  await page.locator('[data-testid="question-migration_timeline-6_months"]').click();

  // Answer compliance requirements (multiselect)
  await page.locator('[data-testid="question-compliance_needs-pci_dss"]').click();
  await page.locator('[data-testid="question-compliance_needs-gdpr"]').click();

  // Answer documentation question
  await page.locator('[data-testid="question-has_documentation"]').click();
}

async function waitForAnalysisCompletion(page: Page) {
  // Wait for analysis to start
  await expect(page.locator('[data-testid="analysis-status"]')).toContainText('analyzing');

  // Wait for analysis to complete (with timeout)
  await expect(page.locator('[data-testid="analysis-status"]')).toContainText('completed', { timeout: 60000 });
}

test.describe('6R Analysis Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses for consistent testing
    await page.route(`${API_BASE_URL}/api/v1/sixr/analyze`, async route => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          analysis_id: 123,
          status: 'created',
          estimated_duration: 300
        })
      });
    });

    await page.route(`${API_BASE_URL}/api/v1/sixr/analysis/123`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          analysisId: 123,
          status: 'completed',
          overallProgress: 100,
          steps: [
            {
              id: 'discovery',
              name: 'Data Discovery',
              status: 'completed',
              progress: 100
            },
            {
              id: 'analysis',
              name: 'Initial Analysis',
              status: 'completed',
              progress: 100
            },
            {
              id: 'questions',
              name: 'Question Generation',
              status: 'completed',
              progress: 100
            },
            {
              id: 'processing',
              name: 'Response Processing',
              status: 'completed',
              progress: 100
            },
            {
              id: 'refinement',
              name: 'Analysis Refinement',
              status: 'completed',
              progress: 100
            },
            {
              id: 'validation',
              name: 'Final Validation',
              status: 'completed',
              progress: 100
            }
          ]
        })
      });
    });

    await page.route(`${API_BASE_URL}/api/v1/sixr/analysis/123/recommendation`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          recommended_strategy: 'refactor',
          confidence_score: 0.82,
          strategy_scores: [
            {
              strategy: 'refactor',
              score: 8.2,
              confidence: 0.82,
              rationale: ['High business value', 'Moderate complexity'],
              risk_factors: ['Requires skilled resources'],
              benefits: ['Improved performance', 'Better maintainability']
            },
            {
              strategy: 'replatform',
              score: 7.1,
              confidence: 0.75,
              rationale: ['Lower risk alternative'],
              risk_factors: ['Limited modernization'],
              benefits: ['Quick migration', 'Cost savings']
            }
          ],
          key_factors: [
            'Application type: Custom',
            'Business value: High',
            'Innovation priority: High'
          ],
          assumptions: [
            'Development team has Java expertise',
            'Testing environment available'
          ],
          next_steps: [
            'Conduct detailed code analysis',
            'Define refactoring scope',
            'Establish development timeline'
          ],
          estimated_effort: 'high',
          estimated_timeline: '4-6 months',
          estimated_cost_impact: 'moderate'
        })
      });
    });
  });

  test('Complete 6R analysis workflow - single application', async ({ page }) => {
    // Step 1: Navigate to treatment page
    await navigateToTreatmentPage(page);

    // Step 2: Select application
    await selectApplication(page, 'Customer Portal');

    // Step 3: Start analysis
    await page.locator('[data-testid="start-analysis-btn"]').click();

    // Verify we're on parameters tab
    await expect(page.locator('[data-testid="current-tab"]')).toContainText('parameters');

    // Step 4: Set parameters
    await setParameters(page, testParameters);

    // Step 5: Save parameters and continue
    await page.locator('[data-testid="save-parameters-btn"]').click();

    // Verify we're on questions tab
    await expect(page.locator('[data-testid="current-tab"]')).toContainText('questions');

    // Step 6: Answer qualifying questions
    await answerQualifyingQuestions(page);

    // Step 7: Submit questions
    await page.locator('[data-testid="submit-questions-btn"]').click();

    // Verify we're on progress tab
    await expect(page.locator('[data-testid="current-tab"]')).toContainText('progress');

    // Step 8: Wait for analysis completion
    await waitForAnalysisCompletion(page);

    // Verify we're on recommendation tab
    await expect(page.locator('[data-testid="current-tab"]')).toContainText('recommendation');

    // Step 9: Verify recommendation display
    await expect(page.locator('[data-testid="recommended-strategy"]')).toContainText('refactor');
    await expect(page.locator('[data-testid="confidence-score"]')).toContainText('82%');

    // Step 10: Accept recommendation
    await page.locator('[data-testid="accept-recommendation-btn"]').click();

    // Verify success message
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Recommendation accepted');

    // Verify we're back to selection tab
    await expect(page.locator('[data-testid="current-tab"]')).toContainText('selection');
  });

  test('Parameter adjustment and iteration workflow', async ({ page }) => {
    // Start analysis
    await navigateToTreatmentPage(page);
    await selectApplication(page, 'Customer Portal');
    await page.locator('[data-testid="start-analysis-btn"]').click();

    // Set initial parameters
    await setParameters(page, testParameters);
    await page.locator('[data-testid="save-parameters-btn"]').click();

    // Answer questions
    await answerQualifyingQuestions(page);
    await page.locator('[data-testid="submit-questions-btn"]').click();

    // Wait for completion
    await waitForAnalysisCompletion(page);

    // Reject recommendation to iterate
    await page.locator('[data-testid="reject-recommendation-btn"]').click();

    // Verify we're back on parameters tab
    await expect(page.locator('[data-testid="current-tab"]')).toContainText('parameters');

    // Adjust parameters
    await page.locator('[data-testid="innovation-priority-slider"]').fill('10');
    await page.locator('[data-testid="risk-tolerance-slider"]').fill('8');

    // Start iteration
    await page.locator('[data-testid="iterate-analysis-btn"]').click();

    // Verify iteration number increased
    await expect(page.locator('[data-testid="iteration-number"]')).toContainText('2');

    // Wait for new analysis completion
    await waitForAnalysisCompletion(page);

    // Verify updated recommendation
    await expect(page.locator('[data-testid="recommended-strategy"]')).toBeVisible();
  });

  test('Bulk analysis workflow', async ({ page }) => {
    await navigateToTreatmentPage(page);

    // Navigate to bulk analysis tab
    await page.locator('[data-testid="bulk-tab"]').click();

    // Select multiple applications
    await selectApplication(page, 'Customer Portal');
    await selectApplication(page, 'Legacy Billing System');

    // Configure bulk analysis
    await page.locator('[data-testid="bulk-job-name"]').fill('Test Bulk Analysis');
    await page.locator('[data-testid="bulk-job-description"]').fill('Testing bulk analysis workflow');
    await page.locator('[data-testid="bulk-priority-medium"]').click();

    // Set bulk parameters
    await page.locator('[data-testid="bulk-parallel-limit"]').fill('2');
    await page.locator('[data-testid="bulk-retry-failed"]').check();

    // Start bulk analysis
    await page.locator('[data-testid="start-bulk-analysis-btn"]').click();

    // Verify job creation
    await expect(page.locator('[data-testid="bulk-job-status"]')).toContainText('running');

    // Wait for bulk analysis completion
    await expect(page.locator('[data-testid="bulk-job-status"]')).toContainText('completed', { timeout: 120000 });

    // Verify results
    await expect(page.locator('[data-testid="bulk-results-count"]')).toContainText('2');
  });

  test('Error handling and recovery', async ({ page }) => {
    // Mock API error
    await page.route(`${API_BASE_URL}/api/v1/sixr/analyze`, async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Internal server error'
        })
      });
    });

    await navigateToTreatmentPage(page);
    await selectApplication(page, 'Customer Portal');

    // Try to start analysis
    await page.locator('[data-testid="start-analysis-btn"]').click();

    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Internal server error');

    // Verify retry button is available
    await expect(page.locator('[data-testid="retry-btn"]')).toBeVisible();

    // Mock successful retry
    await page.route(`${API_BASE_URL}/api/v1/sixr/analyze`, async route => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          analysis_id: 123,
          status: 'created',
          estimated_duration: 300
        })
      });
    });

    // Retry operation
    await page.locator('[data-testid="retry-btn"]').click();

    // Verify success
    await expect(page.locator('[data-testid="current-tab"]')).toContainText('parameters');
  });

  test('Real-time progress updates via WebSocket', async ({ page }) => {
    await navigateToTreatmentPage(page);
    await selectApplication(page, 'Customer Portal');
    await page.locator('[data-testid="start-analysis-btn"]').click();

    await setParameters(page, testParameters);
    await page.locator('[data-testid="save-parameters-btn"]').click();

    await answerQualifyingQuestions(page);
    await page.locator('[data-testid="submit-questions-btn"]').click();

    // Verify progress steps are visible
    await expect(page.locator('[data-testid="progress-step-discovery"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-step-analysis"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-step-questions"]')).toBeVisible();

    // Verify progress updates
    await expect(page.locator('[data-testid="overall-progress"]')).toContainText('0%');

    // Simulate WebSocket progress updates
    await page.evaluate(() => {
      // This would be handled by the actual WebSocket connection in real scenario
      window.dispatchEvent(new CustomEvent('websocket-message', {
        detail: {
          type: 'analysis_progress',
          analysis_id: 123,
          data: { progress: 50, step: 'processing', status: 'in_progress' }
        }
      }));
    });

    // Verify progress update
    await expect(page.locator('[data-testid="overall-progress"]')).toContainText('50%');
    await expect(page.locator('[data-testid="current-step"]')).toContainText('processing');
  });

  test('File upload in qualifying questions', async ({ page }) => {
    await navigateToTreatmentPage(page);
    await selectApplication(page, 'Customer Portal');
    await page.locator('[data-testid="start-analysis-btn"]').click();

    await setParameters(page, testParameters);
    await page.locator('[data-testid="save-parameters-btn"]').click();

    // Navigate to file upload question
    await page.locator('[data-testid="question-category-technical"]').click();

    // Upload a test file
    const fileInput = page.locator('[data-testid="file-upload-input"]');
    await fileInput.setInputFiles({
      name: 'test-code.java',
      mimeType: 'text/plain',
      buffer: Buffer.from(`
        public class TestClass {
          public void testMethod() {
            System.out.println("Hello World");
          }
        }
      `)
    });

    // Verify file upload
    await expect(page.locator('[data-testid="uploaded-file-name"]')).toContainText('test-code.java');

    // Continue with analysis
    await page.locator('[data-testid="submit-questions-btn"]').click();
    await waitForAnalysisCompletion(page);

    // Verify recommendation includes code analysis insights
    await expect(page.locator('[data-testid="recommendation-details"]')).toContainText('code analysis');
  });

  test('Analysis history and comparison', async ({ page }) => {
    // Mock analysis history
    await page.route(`${API_BASE_URL}/api/v1/sixr/analyses`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            application_name: 'Customer Portal',
            application_id: 1,
            department: 'Finance',
            analysis_date: new Date().toISOString(),
            analyst: 'Test User',
            status: 'completed',
            recommended_strategy: 'refactor',
            confidence_score: 0.82,
            iteration_count: 1
          },
          {
            id: 2,
            application_name: 'Legacy Billing System',
            application_id: 2,
            department: 'Finance',
            analysis_date: new Date().toISOString(),
            analyst: 'Test User',
            status: 'completed',
            recommended_strategy: 'replace',
            confidence_score: 0.91,
            iteration_count: 2
          }
        ])
      });
    });

    await navigateToTreatmentPage(page);

    // Navigate to history tab
    await page.locator('[data-testid="history-tab"]').click();

    // Verify history is loaded
    await expect(page.locator('[data-testid="history-item-1"]')).toBeVisible();
    await expect(page.locator('[data-testid="history-item-2"]')).toBeVisible();

    // Select analyses for comparison
    await page.locator('[data-testid="compare-checkbox-1"]').check();
    await page.locator('[data-testid="compare-checkbox-2"]').check();

    // Start comparison
    await page.locator('[data-testid="compare-analyses-btn"]').click();

    // Verify comparison view
    await expect(page.locator('[data-testid="comparison-view"]')).toBeVisible();
    await expect(page.locator('[data-testid="comparison-strategy-1"]')).toContainText('refactor');
    await expect(page.locator('[data-testid="comparison-strategy-2"]')).toContainText('replace');
  });

  test('Export functionality', async ({ page }) => {
    await navigateToTreatmentPage(page);
    await page.locator('[data-testid="history-tab"]').click();

    // Select analysis for export
    await page.locator('[data-testid="export-checkbox-1"]').check();

    // Start download
    const downloadPromise = page.waitForDownload();
    await page.locator('[data-testid="export-csv-btn"]').click();

    const download = await downloadPromise;

    // Verify download
    expect(download.suggestedFilename()).toContain('6r_analysis_export.csv');
  });

  test('Accessibility compliance', async ({ page }) => {
    await navigateToTreatmentPage(page);

    // Test keyboard navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');

    // Verify focus management
    const focusedElement = await page.locator(':focus');
    await expect(focusedElement).toBeVisible();

    // Test screen reader compatibility
    await expect(page.locator('[aria-label]')).toHaveCount(await page.locator('[aria-label]').count());
    await expect(page.locator('[role]')).toHaveCount(await page.locator('[role]').count());
  });

  test('Mobile responsiveness', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await navigateToTreatmentPage(page);

    // Verify mobile layout
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();

    // Test mobile navigation
    await page.locator('[data-testid="mobile-menu-toggle"]').click();
    await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible();

    // Test mobile parameter sliders
    await selectApplication(page, 'Customer Portal');
    await page.locator('[data-testid="start-analysis-btn"]').click();

    // Verify sliders work on mobile
    await page.locator('[data-testid="business-value-slider"]').fill('8');
    await expect(page.locator('[data-testid="business-value-display"]')).toContainText('8');
  });
});

test.describe('Performance Tests', () => {
  test('Analysis completion time meets requirements', async ({ page }) => {
    await navigateToTreatmentPage(page);
    await selectApplication(page, 'Customer Portal');
    await page.locator('[data-testid="start-analysis-btn"]').click();

    await setParameters(page, testParameters);
    await page.locator('[data-testid="save-parameters-btn"]').click();

    await answerQualifyingQuestions(page);

    const startTime = Date.now();
    await page.locator('[data-testid="submit-questions-btn"]').click();

    await waitForAnalysisCompletion(page);
    const endTime = Date.now();

    const analysisTime = endTime - startTime;

    // Analysis should complete within 2 minutes for single application
    expect(analysisTime).toBeLessThan(120000);
  });

  test('Bulk analysis performance', async ({ page }) => {
    await navigateToTreatmentPage(page);
    await page.locator('[data-testid="bulk-tab"]').click();

    // Select 10 applications (mock data)
    for (let i = 1; i <= 10; i++) {
      await selectApplication(page, `Test App ${i}`);
    }

    await page.locator('[data-testid="bulk-job-name"]').fill('Performance Test');
    await page.locator('[data-testid="bulk-parallel-limit"]').fill('5');

    const startTime = Date.now();
    await page.locator('[data-testid="start-bulk-analysis-btn"]').click();

    await expect(page.locator('[data-testid="bulk-job-status"]')).toContainText('completed', { timeout: 300000 });
    const endTime = Date.now();

    const bulkAnalysisTime = endTime - startTime;

    // Bulk analysis of 10 applications should complete within 5 minutes
    expect(bulkAnalysisTime).toBeLessThan(300000);
  });
});

test.describe('Integration Tests', () => {
  test('CMDB data integration', async ({ page }) => {
    // Mock CMDB data endpoint
    await page.route(`${API_BASE_URL}/api/v1/cmdb/applications`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(testApplications)
      });
    });

    await navigateToTreatmentPage(page);

    // Verify CMDB data is loaded
    await expect(page.locator('[data-testid="application-Customer Portal"]')).toBeVisible();
    await expect(page.locator('[data-testid="application-Legacy Billing System"]')).toBeVisible();

    // Verify application metadata
    await expect(page.locator('[data-testid="app-tech-stack-1"]')).toContainText('Java 8');
    await expect(page.locator('[data-testid="app-criticality-1"]')).toContainText('high');
  });

  test('Field mapping integration', async ({ page }) => {
    await navigateToTreatmentPage(page);
    await selectApplication(page, 'Customer Portal');
    await page.locator('[data-testid="start-analysis-btn"]').click();

    // Verify field mapping affects parameter suggestions
    await expect(page.locator('[data-testid="suggested-business-value"]')).toContainText('7');
    await expect(page.locator('[data-testid="suggested-complexity"]')).toContainText('7');
  });
});
