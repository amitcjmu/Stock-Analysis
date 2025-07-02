import { test, expect, type Page } from '@playwright/test';

test.describe('Assessment Flow Feature', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    
    // Mock authentication - adjust based on your auth setup
    await page.goto('http://localhost:3000');
    
    // Set auth token if needed
    await page.evaluate(() => {
      localStorage.setItem('authToken', 'mock-test-token');
      localStorage.setItem('user', JSON.stringify({
        id: 'test-user',
        email: 'test@example.com',
        role: 'admin'
      }));
    });
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should initialize assessment flow with selected applications', async () => {
    // Navigate to inventory page
    await page.goto('http://localhost:3000/inventory');
    
    // Wait for applications to load
    await page.waitForSelector('[data-testid="application-row"]');
    
    // Select 2 applications for assessment
    await page.click('[data-testid="application-checkbox-1"]');
    await page.click('[data-testid="application-checkbox-2"]');
    
    // Click assess button
    await page.click('[data-testid="assess-selected-button"]');
    
    // Should navigate to assessment flow initialization
    await expect(page).toHaveURL(/\/assessment\/initialize/);
    
    // Confirm selected applications
    await expect(page.locator('text=2 applications selected')).toBeVisible();
    
    // Start assessment
    await page.click('[data-testid="start-assessment-button"]');
    
    // Should navigate to architecture standards page
    await expect(page).toHaveURL(/\/assessment\/.*\/architecture/);
  });

  test('should complete architecture standards phase', async () => {
    // Navigate directly to assessment flow
    const flowId = 'test-flow-123';
    await page.goto(`http://localhost:3000/assessment/${flowId}/architecture`);
    
    // Wait for page to load
    await page.waitForSelector('h1:has-text("Architecture Standards")');
    
    // Select a template
    await page.click('[data-testid="template-selector"]');
    await page.click('text=Financial Services Template');
    
    // Verify standards loaded
    await expect(page.locator('text=Java 11+')).toBeVisible();
    await expect(page.locator('text=OAuth2 Authentication')).toBeVisible();
    
    // Add custom standard
    await page.click('[data-testid="add-standard-button"]');
    await page.fill('[data-testid="standard-type-input"]', 'custom_requirement');
    await page.fill('[data-testid="standard-description-input"]', 'Custom security requirement');
    await page.click('[data-testid="standard-mandatory-checkbox"]');
    
    // Save and continue
    await page.click('button:has-text("Continue to Tech Debt Analysis")');
    
    // Verify navigation to next phase
    await expect(page).toHaveURL(/\/assessment\/.*\/tech-debt/);
  });

  test('should display tech debt analysis with components', async () => {
    const flowId = 'test-flow-123';
    await page.goto(`http://localhost:3000/assessment/${flowId}/tech-debt`);
    
    // Wait for components to load
    await page.waitForSelector('[data-testid="component-card"]');
    
    // Verify component identification
    await expect(page.locator('text=Frontend Component')).toBeVisible();
    await expect(page.locator('text=Backend API')).toBeVisible();
    await expect(page.locator('text=Database Layer')).toBeVisible();
    
    // Check tech debt scores
    const techDebtScore = await page.locator('[data-testid="tech-debt-score"]').first();
    await expect(techDebtScore).toBeVisible();
    
    // Filter by severity
    await page.click('[data-testid="severity-filter-high"]');
    
    // Verify filtered results
    const highSeverityItems = await page.locator('[data-severity="high"]').count();
    expect(highSeverityItems).toBeGreaterThan(0);
    
    // Continue to next phase
    await page.click('button:has-text("Continue to 6R Strategy Review")');
  });

  test('should allow 6R strategy modification', async () => {
    const flowId = 'test-flow-123';
    await page.goto(`http://localhost:3000/assessment/${flowId}/sixr-review`);
    
    // Wait for strategies to load
    await page.waitForSelector('[data-testid="strategy-matrix"]');
    
    // Verify component treatments
    await expect(page.locator('text=Component Treatments')).toBeVisible();
    
    // Change a strategy
    await page.click('[data-testid="strategy-dropdown-frontend"]');
    await page.click('text=Refactor');
    
    // Verify compatibility warning if applicable
    const compatibilityWarning = page.locator('[data-testid="compatibility-warning"]');
    if (await compatibilityWarning.isVisible()) {
      await expect(compatibilityWarning).toContainText('compatibility');
    }
    
    // Check confidence score
    const confidenceScore = await page.locator('[data-testid="confidence-score"]');
    await expect(confidenceScore).toBeVisible();
    
    // Apply bulk edit
    await page.click('[data-testid="bulk-edit-button"]');
    await page.selectOption('[data-testid="bulk-strategy-select"]', 'replatform');
    await page.click('[data-testid="apply-bulk-edit"]');
    
    // Continue to app-on-page
    await page.click('button:has-text("Continue to Application Review")');
  });

  test('should display comprehensive app-on-page view', async () => {
    const flowId = 'test-flow-123';
    await page.goto(`http://localhost:3000/assessment/${flowId}/app-on-page`);
    
    // Wait for app details to load
    await page.waitForSelector('[data-testid="app-summary-card"]');
    
    // Verify all sections present
    await expect(page.locator('text=Application Summary')).toBeVisible();
    await expect(page.locator('text=Component Breakdown')).toBeVisible();
    await expect(page.locator('text=Technical Debt Analysis')).toBeVisible();
    await expect(page.locator('text=6R Decision Rationale')).toBeVisible();
    await expect(page.locator('text=Architecture Exceptions')).toBeVisible();
    await expect(page.locator('text=Dependencies')).toBeVisible();
    
    // Test print functionality
    await page.click('[data-testid="print-button"]');
    
    // Test export functionality
    await page.click('[data-testid="export-button"]');
    await page.click('text=Export as PDF');
    
    // Navigate between applications
    await page.click('[data-testid="next-app-button"]');
    await expect(page.locator('[data-testid="app-name"]')).not.toContainText('Application 1');
    
    // Finalize assessment
    await page.click('button:has-text("Continue to Summary")');
  });

  test('should complete assessment flow and mark apps ready for planning', async () => {
    const flowId = 'test-flow-123';
    await page.goto(`http://localhost:3000/assessment/${flowId}/summary`);
    
    // Wait for summary to load
    await page.waitForSelector('[data-testid="assessment-summary"]');
    
    // Verify statistics
    await expect(page.locator('text=Assessment Complete')).toBeVisible();
    await expect(page.locator('[data-testid="total-apps-assessed"]')).toContainText('2');
    
    // Check strategy distribution
    await expect(page.locator('[data-testid="strategy-distribution"]')).toBeVisible();
    
    // Mark apps ready for planning
    await page.click('[data-testid="mark-ready-checkbox-all"]');
    await page.click('button:has-text("Finalize Assessment")');
    
    // Verify completion
    await expect(page.locator('text=Assessment Finalized')).toBeVisible();
    
    // Navigate to planning
    await page.click('button:has-text("Continue to Planning")');
    await expect(page).toHaveURL(/\/planning/);
  });

  test('should handle real-time updates during agent processing', async () => {
    const flowId = 'test-flow-123';
    await page.goto(`http://localhost:3000/assessment/${flowId}/tech-debt`);
    
    // Trigger agent processing
    await page.click('[data-testid="analyze-button"]');
    
    // Wait for processing indicator
    await expect(page.locator('[data-testid="agent-processing"]')).toBeVisible();
    
    // Verify real-time updates appear
    await expect(page.locator('text=AI Agents Working')).toBeVisible();
    
    // Wait for completion
    await page.waitForSelector('[data-testid="analysis-complete"]', { timeout: 30000 });
    
    // Verify results updated
    const updatedComponents = await page.locator('[data-testid="component-card"]').count();
    expect(updatedComponents).toBeGreaterThan(0);
  });

  test('should support pause and resume functionality', async () => {
    const flowId = 'test-flow-123';
    await page.goto(`http://localhost:3000/assessment/${flowId}/sixr-review`);
    
    // Make some changes
    await page.click('[data-testid="strategy-dropdown-backend"]');
    await page.click('text=ReArchitect');
    
    // Save progress
    await page.click('[data-testid="save-progress-button"]');
    await expect(page.locator('text=Progress Saved')).toBeVisible();
    
    // Navigate away
    await page.goto('http://localhost:3000/dashboard');
    
    // Return to assessment
    await page.goto(`http://localhost:3000/assessment/${flowId}/sixr-review`);
    
    // Verify changes persisted
    const backendStrategy = await page.locator('[data-testid="strategy-dropdown-backend"]').inputValue();
    expect(backendStrategy).toBe('rearchitect');
  });

  test('should enforce multi-tenant data isolation', async () => {
    // Set different client context
    await page.evaluate(() => {
      localStorage.setItem('clientAccountId', '2');
    });
    
    // Try to access flow from different client
    const flowId = 'test-flow-123'; // Flow from client 1
    await page.goto(`http://localhost:3000/assessment/${flowId}/architecture`);
    
    // Should show error or redirect
    await expect(page.locator('text=Access Denied').or(page.locator('text=Not Found'))).toBeVisible();
  });
});

// Performance tests
test.describe('Assessment Flow Performance', () => {
  test('should handle large number of applications', async ({ page }) => {
    // This would need mock data setup for 50+ applications
    await page.goto('http://localhost:3000/assessment/test-large-flow/tech-debt');
    
    // Verify pagination works
    await expect(page.locator('[data-testid="pagination"]')).toBeVisible();
    
    // Test filtering performance
    const startTime = Date.now();
    await page.fill('[data-testid="search-input"]', 'application');
    await page.waitForSelector('[data-testid="filtered-results"]');
    const filterTime = Date.now() - startTime;
    
    // Should filter quickly even with many apps
    expect(filterTime).toBeLessThan(1000); // Less than 1 second
  });
});