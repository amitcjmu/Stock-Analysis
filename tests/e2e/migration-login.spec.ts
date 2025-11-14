import { test, expect } from '@playwright/test';

test.describe('Migration Platform - Login Page Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
  });

  test('should load login page successfully', async ({ page }) => {
    // Check URL
    await expect(page).toHaveURL(/localhost:8081/);

    // Check page title
    await expect(page).toHaveTitle('AI powered Migration Orchestrator');

    // Check for root div
    const rootDiv = page.locator('#root');
    await expect(rootDiv).toBeVisible();
  });

  test('should display login form elements', async ({ page }) => {
    // Check for email input
    const emailInput = page.locator('input[type="email"], input[placeholder*="Email"]');
    await expect(emailInput).toBeVisible();

    // Check for password input
    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput).toBeVisible();

    // Check for Sign In button
    const signInButton = page.locator('button:has-text("Sign In")');
    await expect(signInButton).toBeVisible();
  });

  test('should show demo credentials', async ({ page }) => {
    // Check for demo credentials text
    const pageText = await page.textContent('body');
    expect(pageText).toContain('Demo Credentials');
    expect(pageText).toContain('demo@demo-corp.com');
  });
});
