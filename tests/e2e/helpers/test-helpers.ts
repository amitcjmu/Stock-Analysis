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
  apiURL: process.env.API_URL || 'http://localhost:8000',
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
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  // Fill login form
  await page.fill('input[type="email"]', user.email);
  await page.fill('input[type="password"]', user.password);

  // Click login button
  await page.click('button[type="submit"]');

  // Wait for successful login and navigation
  // The app navigates to "/" after login, not "/dashboard"
  await page.waitForResponse(response =>
    response.url().includes('/api/v1/auth/login') && response.status() === 200,
    { timeout: 10000 }
  );

  // Wait for the main page to load
  await page.waitForSelector('text=AI Modernize Migration Platform', { timeout: 5000 });
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
  cleanup
};
