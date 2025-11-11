import { test, expect } from '@playwright/test';
import { loginAsDemo } from '../utils/auth-helpers';

test.describe('Migration Platform - Navigation Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemo(page);
  });

  test('should navigate to Discovery section', async ({ page }) => {
    await page.click('text=Discovery');
    await page.waitForLoadState('domcontentloaded');
    
    const url = page.url();
    console.log('Discovery URL:', url);
  });

  test('should navigate to Collection section', async ({ page }) => {
    await page.click('text=Collection');
    await page.waitForLoadState('domcontentloaded');
    
    const url = page.url();
    console.log('Collection URL:', url);
  });

  test('should navigate to Assess section', async ({ page }) => {
    await page.click('text=Assess');
    await page.waitForLoadState('domcontentloaded');
    
    const url = page.url();
    console.log('Assess URL:', url);
  });
});
