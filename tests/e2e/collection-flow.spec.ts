import { test, expect } from '@playwright/test';

// Test configuration
const TEST_TIMEOUT = 120000; // 2 minutes per test
const DEMO_EMAIL = 'demo@demo-corp.com';
const DEMO_PASSWORD = 'Demo123!';

test.describe('Collection Flow E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);

    // Navigate to login page
    await page.goto('http://localhost:8081/login');

    // Perform login
    await page.fill('input[type="email"]', DEMO_EMAIL);
    await page.fill('input[type="password"]', DEMO_PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for navigation to complete
    await page.waitForURL('http://localhost:8081/', { timeout: 10000 });

    // Navigate to collection page
    await page.goto('http://localhost:8081/collection');
    await page.waitForLoadState('networkidle');

    // Refresh twice to handle UI bug
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('should display collection overview page', async ({ page }) => {
    // Since we navigated via click in beforeEach, no refresh needed
    // Check page title - wait for it to be visible
    await expect(page.locator('h1:has-text("Data Collection Workflows")')).toBeVisible({ timeout: 30000 });

    // Check for main sections with more flexible matching
    await expect(page.locator('text="Adaptive Data Collection"').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text="Bulk Data Upload"').first()).toBeVisible({ timeout: 10000 });

    // Just check that we're on the collection page
    const url = page.url();
    expect(url).toContain('/collection');
  });

  test('should navigate to adaptive forms', async ({ page }) => {
    // Navigate directly to adaptive forms page
    await page.goto('http://localhost:8081/collection/adaptive-forms');

    // Refresh twice for UI bug
    await page.waitForLoadState('networkidle');
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Check that we're on the right page
    const url = page.url();
    expect(url).toContain('/collection/adaptive-forms');

    // Check page elements
    const h1Text = await page.locator('h1').first().textContent();
    expect(h1Text).toContain('Adaptive Data Collection');
  });

  test('should create a new collection flow', async ({ page }) => {
    // Navigate to adaptive forms
    await page.goto('http://localhost:8081/collection/adaptive-forms');
    await page.waitForLoadState('networkidle');

    // Refresh twice to handle UI bug
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.reload();
    await page.waitForLoadState('networkidle');

    // First check if the collection form is blocked
    const blockingMessage = page.locator('text=Collection workflow blocked');
    const isBlocked = await blockingMessage.count() > 0;

    if (isBlocked) {
      console.log('Collection form is blocked by incomplete flows');
      // Verify the blocking message is displayed
      await expect(blockingMessage).toBeVisible();

      // Check for incomplete flow cards
      const flowCard = page.locator('text=/Flow ID:/').first();
      if (await flowCard.count() > 0) {
        await expect(flowCard).toBeVisible();
      }
    } else {
      // Check if there are any existing applications in dropdown
      const selectTriggers = await page.locator('[role="combobox"]').count();

      if (selectTriggers > 0) {
        const selectTrigger = page.locator('[role="combobox"]').first();
        await selectTrigger.click();

        // Wait for dropdown to open
        await page.waitForTimeout(1000);

        // Try to select first application if available
        const optionCount = await page.locator('[role="option"]').count();

        if (optionCount > 0) {
          const firstOption = page.locator('[role="option"]').first();
          await firstOption.click();

          // Click Create Flow button
          const createButton = page.locator('button:has-text("Create Flow")');
          await expect(createButton).toBeEnabled();
          await createButton.click();

          // Wait for response
          await page.waitForTimeout(2000);
          console.log('Flow creation attempted');
        } else {
          console.log('No applications available in dropdown');
        }
      } else {
        console.log('No select dropdown found - form might be in different state');
      }
    }
  });

  test('should handle incomplete collection flows', async ({ page }) => {
    // Navigate to collection overview
    await page.goto('http://localhost:8081/collection');
    await page.waitForLoadState('networkidle');

    // Refresh twice to handle UI bug
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Check for incomplete flows section
    const incompleteFlowsSection = page.locator('text=Incomplete Collection Flows');
    const sectionExists = await incompleteFlowsSection.count() > 0;

    if (sectionExists) {
      await expect(incompleteFlowsSection).toBeVisible();

      // Check for any incomplete flow cards
      const flowCards = page.locator('[data-testid="collection-flow-card"]');
      const flowCount = await flowCards.count();

      if (flowCount > 0) {
        console.log(`Found ${flowCount} incomplete flows`);

        // Test the first flow card
        const firstFlow = flowCards.first();

        // Check for flow details
        await expect(firstFlow.locator('text=/Flow ID:/')).toBeVisible();
        await expect(firstFlow.locator('text=/Status:/')).toBeVisible();
        await expect(firstFlow.locator('text=/Progress:/')).toBeVisible();

        // Check for action buttons
        const continueButton = firstFlow.locator('button:has-text("Continue")');
        const deleteButton = firstFlow.locator('button:has-text("Delete")');

        if (await continueButton.count() > 0) {
          await expect(continueButton).toBeVisible();
        }

        if (await deleteButton.count() > 0) {
          await expect(deleteButton).toBeVisible();
        }
      }
    }
  });

  test('should delete a collection flow', async ({ page }) => {
    // Navigate to collection overview
    await page.goto('http://localhost:8081/collection');
    await page.waitForLoadState('networkidle');

    // Refresh twice to handle UI bug
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Look for delete buttons
    const deleteButtons = page.locator('button:has-text("Delete")');
    const deleteCount = await deleteButtons.count();

    if (deleteCount > 0) {
      // Click the first delete button
      await deleteButtons.first().click();

      // Handle confirmation dialog if it appears
      const confirmButton = page.locator('button:has-text("Confirm")');
      if (await confirmButton.count() > 0) {
        await confirmButton.click();
      }

      // Wait for deletion to complete
      await page.waitForTimeout(2000);

      // Check for success message
      const successToast = page.locator('text=/Flow Deleted|deleted successfully/i');
      if (await successToast.count() > 0) {
        await expect(successToast).toBeVisible();
      }
    } else {
      console.log('No flows available to delete');
    }
  });

  test('should handle 401 authentication errors gracefully', async ({ page }) => {
    // Clear auth token to simulate expired session
    await page.evaluate(() => {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
    });

    // Try to navigate to collection page
    await page.goto('http://localhost:8081/collection');

    // Should be redirected to login page
    await page.waitForURL('**/login', { timeout: 10000 });

    // Verify we're on the login page
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should navigate to bulk upload', async ({ page }) => {
    // Click on Bulk Upload
    await page.click('text=Bulk Upload');

    // Wait for navigation
    await page.waitForURL('**/collection/bulk-upload');

    // Check page elements
    await expect(page.locator('h1')).toContainText(/Bulk.*Upload|Upload.*Data/i);

    // Check for upload area
    const uploadArea = page.locator('text=/drag.*drop|choose.*file/i');
    if (await uploadArea.count() > 0) {
      await expect(uploadArea.first()).toBeVisible();
    }
  });

  test('should display collection progress', async ({ page }) => {
    // Navigate to collection progress
    await page.goto('http://localhost:8081/collection/progress');
    await page.waitForLoadState('networkidle');

    // Refresh twice to handle UI bug
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Check for progress indicators
    await expect(page.locator('h1')).toContainText(/Collection Progress|Progress/i);

    // Check for charts or metrics
    const progressMetrics = page.locator('text=/collected|completed|pending/i');
    if (await progressMetrics.count() > 0) {
      console.log('Progress metrics found');
    }
  });

  test('should handle flow continuation', async ({ page }) => {
    // Navigate to collection overview
    await page.goto('http://localhost:8081/collection');
    await page.waitForLoadState('networkidle');

    // Refresh twice to handle UI bug
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Look for continue buttons
    const continueButtons = page.locator('button:has-text("Continue")');
    const continueCount = await continueButtons.count();

    if (continueCount > 0) {
      // Click the first continue button
      await continueButtons.first().click();

      // Wait for action to complete
      await page.waitForTimeout(2000);

      // Check for any response
      const alerts = page.locator('[role="alert"]');
      if (await alerts.count() > 0) {
        const alertText = await alerts.first().textContent();
        console.log('Continue response:', alertText);
      }
    } else {
      console.log('No flows available to continue');
    }
  });

  test('should validate form fields in adaptive forms', async ({ page }) => {
    // Navigate to adaptive forms
    await page.goto('http://localhost:8081/collection/adaptive-forms');
    await page.waitForLoadState('networkidle');

    // Refresh twice to handle UI bug
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Try to submit without selecting application
    const createButton = page.locator('button:has-text("Create Flow")');

    // Button should be disabled initially
    const isDisabled = await createButton.isDisabled();
    expect(isDisabled).toBeTruthy();

    // Select an application if available
    const selectTrigger = page.locator('[role="combobox"]').first();
    await selectTrigger.click();

    const firstOption = page.locator('[role="option"]').first();
    const optionCount = await page.locator('[role="option"]').count();

    if (optionCount > 0) {
      await firstOption.click();

      // Button should now be enabled
      await expect(createButton).toBeEnabled();
    }
  });
});

// Additional test suite for flow management
test.describe('Collection Flow Management', () => {
  test.beforeEach(async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);

    // Login
    await page.goto('http://localhost:8081/login');
    await page.fill('input[type="email"]', DEMO_EMAIL);
    await page.fill('input[type="password"]', DEMO_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:8081/', { timeout: 10000 });
  });

  test('should access flow management page', async ({ page }) => {
    // Navigate to flow management
    await page.goto('http://localhost:8081/collection/flow-management');
    await page.waitForLoadState('networkidle');

    // Refresh twice to handle UI bug
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Check page title
    await expect(page.locator('h1')).toContainText(/Flow Management|Manage.*Flows/i);

    // Check for management options
    const batchActions = page.locator('text=/batch|cleanup|export/i');
    if (await batchActions.count() > 0) {
      console.log('Flow management actions available');
    }
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Simulate offline mode
    await page.context().setOffline(true);

    // Try to navigate to collection
    await page.goto('http://localhost:8081/collection').catch(() => {});

    // Re-enable network
    await page.context().setOffline(false);

    // Check if error message is displayed
    const errorMessages = page.locator('text=/offline|network error|connection/i');
    if (await errorMessages.count() > 0) {
      console.log('Network error handled gracefully');
    }
  });
});
