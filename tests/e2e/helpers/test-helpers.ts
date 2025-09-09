/**
 * E2E Test Helper Utilities
 * Provides reusable functions for Playwright E2E tests
 */

import { Page, expect, BrowserContext } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Test configuration
export const TEST_CONFIG = {
  baseURL: process.env.BASE_URL || 'http://localhost:8081',
  // For E2E tests, all API calls go through the Vite proxy at baseURL
  // The proxy forwards /api/* requests to the backend at localhost:8000
  apiURL: process.env.API_URL || 'http://localhost:8081', // Changed to use proxy
  directBackendURL: 'http://localhost:8000', // Direct backend access for API context tests
  defaultTimeout: 60000,
  networkTimeout: 30000,
  retryAttempts: 3,
  screenshots: true,
};

// Test users
export const TEST_USERS = {
  admin: {
    email: 'admin@demo.com',
    password: 'Admin123!',
    role: 'admin'
  },
  manager: {
    email: 'manager@demo-corp.com',
    password: 'Demo123!',
    role: 'manager'
  },
  analyst: {
    email: 'analyst@demo-corp.com',
    password: 'Demo123!',
    role: 'analyst'
  },
  viewer: {
    email: 'viewer@demo-corp.com',
    password: 'Demo123!',
    role: 'viewer'
  },
  demo: {
    email: 'demo@demo-corp.com',
    password: 'Demo123!',  // Fixed: was 'demo123', should be 'Demo123!'
    role: 'user'
  }
};

// Test data generation
export function generateTestCSV(recordCount: number = 10): string {
  const headers = 'Name,Type,Status,Environment,IP_Address,OS,Department,Owner,Location,Description';
  const rows = [];

  for (let i = 1; i <= recordCount; i++) {
    const type = ['Application', 'Server', 'Device'][i % 3];
    const status = ['Active', 'Inactive', 'Maintenance'][i % 3];
    const env = ['Production', 'Development', 'Testing'][i % 3];

    rows.push(
      `TEST-${type.toUpperCase()}-${String(i).padStart(3, '0')},` +
      `${type},${status},${env},` +
      `10.0.${Math.floor(i / 255)}.${i % 255},` +
      `${['Linux', 'Windows', 'Unix'][i % 3]},` +
      `${['IT', 'Finance', 'HR'][i % 3]},` +
      `Owner${i},` +
      `${['US-East', 'US-West', 'EU-Central'][i % 3]},` +
      `Test ${type.toLowerCase()} ${i} description`
    );
  }

  return `${headers}\n${rows.join('\n')}`;
}

// Login helper
export async function login(page: Page, user = TEST_USERS.demo): Promise<void> {
  await page.goto(`${TEST_CONFIG.baseURL}/login`);
  await page.waitForLoadState('networkidle');

  // Fill login form
  await page.fill('input[type="email"]', user.email);
  await page.fill('input[type="password"]', user.password);

  // Click login button
  await page.click('button[type="submit"]');

  // Wait for successful login and navigation
  // The app uses Vite proxy: requests to localhost:8081/api/* get proxied to localhost:8000/api/*
  // So we need to wait for the proxied response (which appears to come from baseURL, not apiURL)
  await page.waitForResponse(response => {
    const url = response.url();
    const isLoginEndpoint = url.includes('/api/v1/auth/login');
    const isSuccessful = response.status() === 200;
    const isFromCorrectOrigin = url.startsWith(TEST_CONFIG.baseURL); // Should be from the proxied frontend port

    return isLoginEndpoint && isSuccessful && isFromCorrectOrigin;
  }, { timeout: 15000 });

  // Wait for successful navigation to main page
  await page.waitForURL('**/');

  // Wait for the main page to load
  await page.waitForSelector('text=AI Modernize Migration Platform', { timeout: 10000 });
}

// Navigation helpers
export async function navigateToDiscovery(page: Page): Promise<void> {
  // Click Discovery in menu
  await page.click('text=Discovery');
  await page.waitForTimeout(500); // Wait for menu expansion

  // Click Overview
  await page.click('a[href="/discovery/overview"]');
  await page.waitForURL('**/discovery/overview');
}

export async function navigateToCollection(page: Page): Promise<void> {
  // Click Collection in menu
  await page.click('text=Collection');
  await page.waitForTimeout(500); // Wait for menu expansion

  // Click Overview
  await page.click('a[href="/collection/overview"]');
  await page.waitForURL('**/collection/overview');
}

export async function navigateToAssessment(page: Page): Promise<void> {
  // Click Assessment in menu
  await page.click('text=Assessment');
  await page.waitForTimeout(500); // Wait for menu expansion

  // Click Overview
  await page.click('a[href="/assessment/overview"]');
  await page.waitForURL('**/assessment/overview');
}

// File upload helper
export async function uploadFile(
  page: Page,
  filePath: string,
  selector: string = 'input[type="file"]'
): Promise<void> {
  const fileInput = await page.locator(selector);
  await fileInput.setInputFiles(filePath);
  await page.waitForTimeout(1000); // Wait for file processing
}

// Wait for API response helper
export async function waitForAPIResponse(
  page: Page,
  urlPattern: string | RegExp,
  timeout: number = 30000
): Promise<any> {
  const response = await page.waitForResponse(
    (resp) => {
      if (typeof urlPattern === 'string') {
        return resp.url().includes(urlPattern);
      }
      return urlPattern.test(resp.url());
    },
    { timeout }
  );

  return await response.json();
}

// Check for console errors
export async function checkForConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  return errors;
}

// Screenshot helper
export async function takeScreenshot(
  page: Page,
  name: string,
  fullPage: boolean = false
): Promise<void> {
  const screenshotDir = path.join(process.cwd(), 'tests', 'e2e', 'screenshots');

  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${name}_${timestamp}.png`;

  await page.screenshot({
    path: path.join(screenshotDir, filename),
    fullPage
  });
}

// Wait for element helper with retry
export async function waitForElement(
  page: Page,
  selector: string,
  options: { timeout?: number; state?: 'visible' | 'hidden' | 'attached' | 'detached' } = {}
): Promise<void> {
  const { timeout = 30000, state = 'visible' } = options;

  await page.waitForSelector(selector, { timeout, state });
}

// Click with retry helper
export async function clickWithRetry(
  page: Page,
  selector: string,
  retries: number = 3
): Promise<void> {
  for (let i = 0; i < retries; i++) {
    try {
      await page.click(selector, { timeout: 5000 });
      return;
    } catch (error) {
      if (i === retries - 1) throw error;
      await page.waitForTimeout(1000);
    }
  }
}

// Form fill helper
export async function fillForm(
  page: Page,
  formData: Record<string, string>
): Promise<void> {
  for (const [selector, value] of Object.entries(formData)) {
    const element = await page.locator(selector);
    const tagName = await element.evaluate((el) => el.tagName);

    if (tagName === 'SELECT') {
      await element.selectOption(value);
    } else if (tagName === 'INPUT' || tagName === 'TEXTAREA') {
      await element.fill(value);
    }
  }
}

// Check element text
export async function expectElementText(
  page: Page,
  selector: string,
  expectedText: string | RegExp
): Promise<void> {
  const element = await page.locator(selector);
  await expect(element).toHaveText(expectedText);
}

// Check flow status
export async function checkFlowStatus(
  page: Page,
  expectedStatus: string
): Promise<void> {
  const statusElement = await page.locator('[data-testid="flow-status"]');
  await expect(statusElement).toContainText(expectedStatus);
}

// Wait for persistent agents to initialize
export async function waitForAgents(
  page: Page,
  timeout: number = 30000
): Promise<void> {
  // Wait for agent initialization messages in console
  await page.waitForFunction(
    () => {
      const logs = (window as any).__consoleLogs || [];
      return logs.some((log: string) =>
        log.includes('persistent agent') ||
        log.includes('agent pool')
      );
    },
    { timeout }
  );
}

// Export test data for reuse
export const TEST_DATA = {
  sampleCSV: generateTestCSV(10),
  sampleJSON: [
    { name: 'App1', type: 'Application', status: 'Active' },
    { name: 'Server1', type: 'Server', status: 'Active' },
    { name: 'Device1', type: 'Device', status: 'Inactive' }
  ],
  fieldMappings: {
    'Name': 'asset_name',
    'Type': 'asset_type',
    'Status': 'status',
    'Environment': 'environment',
    'IP_Address': 'ip_address',
    'OS': 'operating_system',
    'Department': 'department',
    'Owner': 'owner',
    'Location': 'location',
    'Description': 'description'
  }
};

// Cleanup helper
export async function cleanup(context: BrowserContext): Promise<void> {
  // Clear cookies
  await context.clearCookies();

  // Clear local storage
  const pages = context.pages();
  for (const page of pages) {
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  }
}

// Flow management helpers
export async function deleteAllFlows(page: Page): Promise<void> {
  console.log('Checking for existing flows to delete...');

  try {
    // Navigate to discovery overview to check for flows
    await navigateToDiscovery(page);
    await page.waitForTimeout(2000);

    // Look for existing flows and delete them
    const manageFlowsButton = page.locator('button:has-text("Manage Flows"), button:has-text("Delete"), [data-testid="manage-flows"]');

    if (await manageFlowsButton.isVisible({ timeout: 5000 })) {
      console.log('Found Manage Flows button, clicking to delete existing flows...');
      await manageFlowsButton.click();
      await page.waitForTimeout(1000);

      // Look for delete buttons or flow management UI
      const deleteButtons = page.locator('button:has-text("Delete"), [data-testid="delete-flow"], .delete-flow-btn');
      const deleteCount = await deleteButtons.count();

      if (deleteCount > 0) {
        console.log(`Found ${deleteCount} flows to delete`);

        // Delete all flows one by one
        for (let i = 0; i < deleteCount; i++) {
          const deleteBtn = deleteButtons.nth(i);
          if (await deleteBtn.isVisible({ timeout: 3000 })) {
            await deleteBtn.click();
            await page.waitForTimeout(1000);

            // Handle confirmation dialog if it appears
            const confirmButtons = [
              'button:has-text("Confirm")',
              'button:has-text("Yes")',
              'button:has-text("Delete Permanently")'
            ];

            for (const buttonSelector of confirmButtons) {
              const confirmButton = page.locator(buttonSelector).first();
              if (await confirmButton.isVisible({ timeout: 3000 })) {
                await confirmButton.click();
                await page.waitForTimeout(1000);
                break;
              }
            }
          }
        }

        console.log('All flows deleted successfully');
      } else {
        console.log('No flows found to delete');
      }
    }

    // Alternative approach: Check for upload blocked message and handle it
    const uploadBlockedMessage = page.locator('text="Upload Blocked"');
    if (await uploadBlockedMessage.isVisible({ timeout: 3000 })) {
      console.log('Upload blocked message found, attempting to resolve...');

      // Click manage flows from the blocked upload message
      const manageFromBlock = page.locator('button:has-text("Manage Flows")');
      if (await manageFromBlock.isVisible()) {
        await manageFromBlock.click();
        await page.waitForTimeout(2000);

        // Delete the blocking flow
        const deleteFlow = page.locator('button:has-text("Delete"), [data-testid="delete-flow"]');
        if (await deleteFlow.isVisible()) {
          await deleteFlow.click();
          await page.waitForTimeout(1000);

          // Confirm deletion
          const confirmButtons = [
            'button:has-text("Confirm")',
            'button:has-text("Yes")',
            'button:has-text("Delete Permanently")'
          ];

          for (const buttonSelector of confirmButtons) {
            const confirmButton = page.locator(buttonSelector).first();
            if (await confirmButton.isVisible({ timeout: 3000 })) {
              await confirmButton.click();
              await page.waitForTimeout(1000);
              break;
            }
          }
        }
      }
    }

    console.log('Flow cleanup completed');
  } catch (error) {
    console.log(`Flow cleanup encountered an issue: ${error.message}`);
    // Don't throw error as this is cleanup - just log and continue
  }
}

export async function handleBlockingFlows(page: Page): Promise<boolean> {
  console.log('Checking for blocking flows...');

  try {
    // Check if upload is blocked
    const uploadBlockedMessage = page.locator('text="Upload Blocked"');

    if (await uploadBlockedMessage.isVisible({ timeout: 3000 })) {
      console.log('Upload blocked - handling blocking flows...');

      // Click Manage Flows button
      const manageFlowsBtn = page.locator('button:has-text("Manage Flows")');
      if (await manageFlowsBtn.isVisible({ timeout: 5000 })) {
        await manageFlowsBtn.click();
        await page.waitForTimeout(2000);

        // Delete the blocking flow
        const deleteButton = page.locator('button:has-text("Delete"), [data-testid="delete-flow"], .delete-btn').first();
        if (await deleteButton.isVisible({ timeout: 5000 })) {
          await deleteButton.click();
          await page.waitForTimeout(1000);

          // Handle confirmation dialog
          const confirmButtons = [
            'button:has-text("Confirm")',
            'button:has-text("Yes")',
            'button:has-text("Delete Permanently")',
            '[data-testid="confirm-delete"]'
          ];

          for (const selector of confirmButtons) {
            const confirmBtn = page.locator(selector).first();
            if (await confirmBtn.isVisible({ timeout: 3000 })) {
              await confirmBtn.click();
              await page.waitForTimeout(1000);
              break;
            }
          }

          console.log('✓ Blocking flow deleted successfully');

          // Navigate back to data import
          await navigateToDiscovery(page);
          await clickWithRetry(page, 'text=Data Import');
          await page.waitForURL('**/discovery/cmdb-import', { timeout: 15000 });

          return true;
        }
      }
    }

    console.log('No blocking flows detected');
    return false;
  } catch (error) {
    console.log(`Error handling blocking flows: ${error.message}`);
    return false;
  }
}

export async function ensureCleanUploadState(page: Page): Promise<void> {
  console.log('Ensuring clean upload state...');

  // First check if we're already on data import page
  const currentUrl = page.url();
  if (!currentUrl.includes('/discovery/cmdb-import')) {
    await navigateToDiscovery(page);
    await clickWithRetry(page, 'text=Data Import');
    await page.waitForURL('**/discovery/cmdb-import', { timeout: 15000 });
  }

  // Wait for page to stabilize
  await page.waitForTimeout(2000);

  // Check for and handle blocking flows
  await handleBlockingFlows(page);

  // Verify upload area is ready
  await waitForElement(page, 'input[type="file"], .upload-area, .border-dashed');
  console.log('✓ Upload state is clean and ready');
}

// Export all helpers
export default {
  TEST_CONFIG,
  TEST_USERS,
  TEST_DATA,
  generateTestCSV,
  login,
  navigateToDiscovery,
  navigateToCollection,
  navigateToAssessment,
  uploadFile,
  waitForAPIResponse,
  checkForConsoleErrors,
  takeScreenshot,
  waitForElement,
  clickWithRetry,
  fillForm,
  expectElementText,
  checkFlowStatus,
  waitForAgents,
  cleanup,
  deleteAllFlows,
  handleBlockingFlows,
  ensureCleanUploadState
};
