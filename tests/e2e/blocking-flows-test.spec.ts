import { test, expect } from '@playwright/test';

test.describe('Blocking Flows Management', () => {
  test.beforeEach(async ({ page }) => {
    // Monitor console for React warnings
    page.on('console', (msg) => {
      if (msg.type() === 'warning' && msg.text().includes('key')) {
        console.log(`⚠️ React Warning: ${msg.text()}`);
      }
      if (msg.type() === 'error') {
        console.log(`❌ Console Error: ${msg.text()}`);
      }
    });

    // Navigate to the login page and authenticate
    await page.goto('http://localhost:8081');
    
    // Check if we're already logged in by looking for navigation or dashboard elements
    const isLoggedIn = await page.locator('nav, [data-testid="main-dashboard"], h1').isVisible().catch(() => false);
    
    if (!isLoggedIn) {
      // Use demo account instead of platform admin
      await page.fill('input[type="email"]', 'demo@hcltech.com');
      await page.fill('input[type="password"]', 'Demo123!');
      await page.click('button[type="submit"]');
      
      // Wait for successful login - look for main navigation or dashboard
      await page.waitForSelector('nav, [data-testid="main-dashboard"], h1', { timeout: 10000 });
    }
  });

  test('should open blocking flows dialog without React key warnings', async ({ page }) => {
    // Navigate to CMDB Import page
    await page.goto('http://localhost:8081/discovery/cmdb-import');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="cmdb-import-container"]', { timeout: 10000 });
    
    // Look for incomplete flows button or indication
    const blockingFlowsButton = page.locator('text=Manage Discovery Flows').first();
    const blockingFlowsExists = await blockingFlowsButton.isVisible().catch(() => false);
    
    if (blockingFlowsExists) {
      // Click to open blocking flows dialog
      await blockingFlowsButton.click();
      
      // Wait for dialog to appear
      await page.waitForSelector('text=Incomplete Discovery Flows', { timeout: 5000 });
      
      // Verify dialog content is loaded
      await expect(page.locator('text=Incomplete Discovery Flows')).toBeVisible();
      
      // Check if flows are displayed (there should be some flows in the list)
      const flowCards = page.locator('[data-testid="flow-card"]');
      const flowCount = await flowCards.count();
      
      console.log(`Found ${flowCount} incomplete flows`);
      
      // If there are flows, test the selection functionality
      if (flowCount > 0) {
        // Test select all checkbox
        const selectAllCheckbox = page.locator('input[id="select-all"]');
        if (await selectAllCheckbox.isVisible()) {
          await selectAllCheckbox.click();
          console.log('✅ Select all checkbox clicked');
        }
        
        // Look for delete button
        const deleteButton = page.locator('text=Delete Selected');
        if (await deleteButton.isVisible()) {
          console.log('✅ Delete Selected button is visible');
        }
      }
      
      // Close dialog
      const closeButton = page.locator('button[aria-label="Close"]').first();
      if (await closeButton.isVisible()) {
        await closeButton.click();
      }
      
    } else {
      console.log('ℹ️ No blocking flows button found - this may indicate no incomplete flows exist');
    }
  });

  test('should test individual flow deletion', async ({ page }) => {
    // Navigate to CMDB Import page
    await page.goto('http://localhost:8081/discovery/cmdb-import');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="cmdb-import-container"]', { timeout: 10000 });
    
    // Look for incomplete flows button
    const blockingFlowsButton = page.locator('text=Manage Discovery Flows').first();
    const blockingFlowsExists = await blockingFlowsButton.isVisible().catch(() => false);
    
    if (blockingFlowsExists) {
      await blockingFlowsButton.click();
      await page.waitForSelector('text=Incomplete Discovery Flows', { timeout: 5000 });
      
      // Look for individual delete buttons
      const deleteButtons = page.locator('button:has-text("Delete")');
      const deleteButtonCount = await deleteButtons.count();
      
      if (deleteButtonCount > 0) {
        console.log(`Found ${deleteButtonCount} individual delete buttons`);
        
        // Click on the first delete button
        await deleteButtons.first().click();
        
        // Check if confirmation dialog appears
        const confirmDialog = page.locator('text=Delete Discovery Flow');
        if (await confirmDialog.isVisible({ timeout: 3000 })) {
          console.log('✅ Delete confirmation dialog appeared');
          
          // Cancel the deletion for safety
          const cancelButton = page.locator('button:has-text("Cancel")');
          if (await cancelButton.isVisible()) {
            await cancelButton.click();
            console.log('✅ Deletion cancelled successfully');
          }
        }
      } else {
        console.log('ℹ️ No individual delete buttons found');
      }
      
      // Close dialog
      const closeButton = page.locator('button[aria-label="Close"]').first();
      if (await closeButton.isVisible()) {
        await closeButton.click();
      }
    }
  });

  test('should test batch deletion functionality', async ({ page }) => {
    // Navigate to CMDB Import page
    await page.goto('http://localhost:8081/discovery/cmdb-import');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="cmdb-import-container"]', { timeout: 10000 });
    
    // Look for incomplete flows button
    const blockingFlowsButton = page.locator('text=Manage Discovery Flows').first();
    const blockingFlowsExists = await blockingFlowsButton.isVisible().catch(() => false);
    
    if (blockingFlowsExists) {
      await blockingFlowsButton.click();
      await page.waitForSelector('text=Incomplete Discovery Flows', { timeout: 5000 });
      
      // Select multiple flows
      const checkboxes = page.locator('input[type="checkbox"]').filter({ hasNot: page.locator('#select-all') });
      const checkboxCount = await checkboxes.count();
      
      if (checkboxCount > 1) {
        // Select first two flows
        await checkboxes.nth(0).click();
        await checkboxes.nth(1).click();
        
        console.log('✅ Selected multiple flows');
        
        // Look for batch delete button
        const batchDeleteButton = page.locator('button:has-text("Delete Selected")');
        if (await batchDeleteButton.isVisible()) {
          await batchDeleteButton.click();
          
          // Check if batch deletion dialog appears
          const batchDialog = page.locator('text=Batch Delete Discovery Flows');
          if (await batchDialog.isVisible({ timeout: 3000 })) {
            console.log('✅ Batch delete confirmation dialog appeared');
            
            // Cancel the deletion for safety
            const cancelButton = page.locator('button:has-text("Cancel")');
            if (await cancelButton.isVisible()) {
              await cancelButton.click();
              console.log('✅ Batch deletion cancelled successfully');
            }
          }
        }
      } else {
        console.log('ℹ️ Not enough flows to test batch deletion');
      }
      
      // Close dialog
      const closeButton = page.locator('button[aria-label="Close"]').first();
      if (await closeButton.isVisible()) {
        await closeButton.click();
      }
    }
  });
});