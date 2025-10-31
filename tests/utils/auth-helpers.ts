import { Page, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8081';

export const TEST_USER = {
  email: 'demo@demo-corp.com',
  password: 'Demo123!',
};

/**
 * Login to the application with demo credentials
 */
export async function loginAsDemo(page: Page): Promise<void> {
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  
  await page.fill('input[type="email"]', TEST_USER.email);
  await page.fill('input[type="password"]', TEST_USER.password);
  await page.click('button:has-text("Sign In")');
  
  // Wait for dashboard to appear instead of networkidle
  await expect(page.locator('text=Dashboard')).toBeVisible({ timeout: 10000 });
}

/**
 * Navigate to a specific flow section
 */
export async function navigateToFlow(
  page: Page, 
  flowName: 'Discovery' | 'Collection' | 'Assess' | 'Plan' | 'Execute' | 'Decommission' | 'FinOps' | 'Modernize'
): Promise<void> {
  // Use simple text selector - more flexible
  await page.click(`text=${flowName}`);
  
  // Wait for page to load
  await page.waitForLoadState('domcontentloaded');
}

/**
 * Login and navigate to a specific flow in one call
 */
export async function loginAndNavigateToFlow(
  page: Page, 
  flowName: 'Discovery' | 'Collection' | 'Assess' | 'Plan' | 'Execute' | 'Decommission' | 'FinOps' | 'Modernize'
): Promise<void> {
  await loginAsDemo(page);
  await navigateToFlow(page, flowName);
}
