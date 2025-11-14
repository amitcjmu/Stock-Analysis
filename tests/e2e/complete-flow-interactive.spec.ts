import { test, expect } from '@playwright/test';
import { loginAsDemo } from '../utils/auth-helpers';

test.describe('Complete Migration Journey - Interactive', () => {
  test('should perform interactive operations across all flows', async ({ page }) => {
    test.setTimeout(180000);

    console.log('=== STARTING INTERACTIVE MIGRATION JOURNEY ===');

    await loginAsDemo(page);

    const flows = ['Collection', 'Discovery', 'Assess', 'Plan', 'Execute'];

    for (const flow of flows) {
      console.log(`\n--- ${flow.toUpperCase()} PHASE ---`);
      await page.click(`text=${flow}`);
      await page.waitForLoadState('domcontentloaded');

      const buttons = await page.locator('button:visible').count();
      console.log(`Found ${buttons} buttons in ${flow}`);

      const tables = await page.locator('table, [role="grid"]').count();
      console.log(`Found ${tables} data grids in ${flow}`);
    }

    console.log('\n=== INTERACTIVE JOURNEY COMPLETED ===');

    await page.screenshot({
      path: 'test-results/interactive-complete.png',
      fullPage: true
    });
  });
});
