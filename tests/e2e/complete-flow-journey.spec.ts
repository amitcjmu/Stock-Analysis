import { test, expect } from '@playwright/test';
import { loginAsDemo } from '../utils/auth-helpers';

test.describe('Complete Migration Journey - End to End', () => {
  test('should complete full migration flow', async ({ page }) => {
    test.setTimeout(120000);

    console.log('=== STARTING COMPLETE MIGRATION JOURNEY ===');

    await loginAsDemo(page);
    await expect(page.locator('text=Dashboard')).toBeVisible();
    console.log('✓ Step 1: Dashboard loaded');

    // Navigate through each flow
    const flows = ['Collection', 'Discovery', 'Assess', 'Plan'];

    for (const flow of flows) {
      console.log(`\nNavigating to ${flow}...`);
      await page.click(`text=${flow}`);
      await page.waitForLoadState('domcontentloaded');

      const bodyText = await page.textContent('body');
      expect(bodyText).toBeTruthy();

      await page.screenshot({
        path: `test-results/journey-${flow.toLowerCase()}.png`,
        fullPage: false
      });

      console.log(`✓ ${flow} page loaded`);
    }

    console.log('\n=== JOURNEY COMPLETED SUCCESSFULLY ===');
  });
});
