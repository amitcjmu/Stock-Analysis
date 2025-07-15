import { test, expect } from '@playwright/test';

test.describe('Dialog System', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a page with dialog examples
    // You would need to add a route to the DialogExamples component for testing
    // await page.goto('/examples/dialogs');
  });

  test('confirmation dialog should work with Playwright', async ({ page }) => {
    // This test demonstrates that React-based dialogs work with Playwright
    // Unlike window.confirm(), these dialogs are part of the DOM
    
    // Click a button that shows a confirmation dialog
    await page.click('[data-testid="delete-button"]');
    
    // The dialog should be visible in the DOM
    await expect(page.getByRole('alertdialog')).toBeVisible();
    await expect(page.getByText('Delete Item')).toBeVisible();
    
    // We can interact with the dialog buttons
    await page.getByRole('button', { name: 'Delete' }).click();
    
    // Verify the action was completed
    await expect(page.getByText('Item deleted successfully')).toBeVisible();
  });

  test('prompt dialog should accept user input', async ({ page }) => {
    // Click a button that shows a prompt dialog
    await page.click('[data-testid="rename-button"]');
    
    // The dialog should be visible
    await expect(page.getByRole('dialog')).toBeVisible();
    
    // Enter text in the input field
    await page.fill('input[placeholder="New name..."]', 'New Item Name');
    
    // Click OK
    await page.getByRole('button', { name: 'OK' }).click();
    
    // Verify the name was updated
    await expect(page.getByText('Item renamed to: New Item Name')).toBeVisible();
  });

  test('loading dialog should show progress', async ({ page }) => {
    // Click a button that shows a loading dialog
    await page.click('[data-testid="long-operation-button"]');
    
    // The loading dialog should be visible
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Processing Data')).toBeVisible();
    
    // Wait for progress updates
    await expect(page.getByText('10%')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('50%')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('100%')).toBeVisible({ timeout: 15000 });
    
    // Verify completion
    await expect(page.getByText('Processing completed successfully!')).toBeVisible();
  });

  test('alert dialogs should display different types', async ({ page }) => {
    // Click button to show alerts
    await page.click('[data-testid="show-alerts-button"]');
    
    // Info alert
    await expect(page.getByText('This is an informational message')).toBeVisible();
    await page.getByRole('button', { name: 'OK' }).click();
    
    // Warning alert
    await expect(page.getByText('This is a warning message')).toBeVisible();
    await page.getByRole('button', { name: 'OK' }).click();
    
    // Error alert
    await expect(page.getByText('This is an error message')).toBeVisible();
    await page.getByRole('button', { name: 'OK' }).click();
    
    // Success alert
    await expect(page.getByText('This is a success message')).toBeVisible();
    await page.getByRole('button', { name: 'OK' }).click();
  });

  test('dialog should handle validation', async ({ page }) => {
    // Click rename button
    await page.click('[data-testid="rename-button"]');
    
    // Try to submit with empty input
    await page.fill('input[placeholder="New name..."]', '');
    await page.getByRole('button', { name: 'OK' }).click();
    
    // Should show validation error
    await expect(page.getByText('Name cannot be empty')).toBeVisible();
    
    // Try with too short name
    await page.fill('input[placeholder="New name..."]', 'ab');
    await page.getByRole('button', { name: 'OK' }).click();
    
    // Should show validation error
    await expect(page.getByText('Name must be at least 3 characters')).toBeVisible();
    
    // Enter valid name
    await page.fill('input[placeholder="New name..."]', 'Valid Name');
    await page.getByRole('button', { name: 'OK' }).click();
    
    // Should succeed
    await expect(page.getByText('Item renamed to: Valid Name')).toBeVisible();
  });
});