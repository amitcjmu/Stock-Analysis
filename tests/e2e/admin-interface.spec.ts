import { test, expect, Page } from '@playwright/test';

// Test configuration and utilities
const TEST_BASE_URL = 'http://localhost:8081';
const API_BASE_URL = 'http://localhost:8000';

// Helper function to clear storage and login
async function loginAsAdmin(page: Page) {
  await page.goto(`${TEST_BASE_URL}/login`);
  await page.evaluate(() => localStorage.clear());
  await page.goto(`${TEST_BASE_URL}/login`, { waitUntil: 'networkidle' });
  
  await page.fill('input[type="email"]', 'chocka@gmail.com');
  await page.fill('input[type="password"]', 'Password123!');
  
  // Click and then wait for navigation, with better debugging
  await page.click('button[type="submit"]');
  try {
    await page.waitForURL(`${TEST_BASE_URL}/dashboard`, { timeout: 15000 });
    // Navigate to admin after successful login
    await page.goto(`${TEST_BASE_URL}/admin`);
  } catch(e) {
    console.error("Failed to navigate after login.", e);
    await page.screenshot({ path: 'playwright-debug/login-failure.png' });
    throw e;
  }
}

// Helper function to validate API response
async function validateApiCall(page: Page, expectedStatus: number = 200) {
  return new Promise((resolve, reject) => {
    let responseReceived = false;
    
    const responseListener = (response) => {
      if (response.url().includes('/api/v1/')) {
        responseReceived = true;
        if (response.status() === expectedStatus) {
          resolve(response);
        } else {
          reject(new Error(`API call failed with status ${response.status()}: ${response.url()}`));
        }
      }
    };
    
    page.on('response', responseListener);
    
    // Timeout after 10 seconds
    setTimeout(() => {
      page.off('response', responseListener);
      if (!responseReceived) {
        reject(new Error('No API response received within timeout'));
      }
    }, 10000);
  });
}

// Helper function to validate database state via API
async function validateDatabaseState(page: Page, endpoint: string, validator: (data: unknown) => boolean, token?: string) {
  const finalToken = token || await page.evaluate(() => localStorage.getItem('token'));

  const response = await page.evaluate(async ({ url, authToken }) => {
    const res = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });
    if (!res.ok) throw new Error(`API Error: ${res.status} ${res.statusText}`);
    return res.json();
  }, { url: `${API_BASE_URL}${endpoint}`, authToken: finalToken });

  return validator(response);
}

test.describe('Admin Interface E2E Tests with Database Validation', () => {
  let adminToken: string;

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    await loginAsAdmin(page);
    adminToken = await page.evaluate(() => localStorage.getItem('token') || '');
    await page.close();
  });

  test.beforeEach(async ({ page }) => {
    await page.goto(TEST_BASE_URL);
    await page.evaluate((token) => {
        localStorage.setItem('token', token);
    }, adminToken);
    await page.goto(`${TEST_BASE_URL}/admin`);
    await page.waitForSelector('h1:has-text("Admin Console")');
  });

  test('1. Navigation - Admin Dashboard Access', async ({ page }) => {
    await expect(page.locator('h1:has-text("Admin Console")')).toBeVisible();
    await expect(page.locator('a[href="/admin/clients"]')).toBeVisible();
    await expect(page.locator('a[href="/admin/engagements"]')).toBeVisible();
    await expect(page.locator('a[href="/admin/user-approvals"]')).toBeVisible();
  });

  test('2. User Management - Load and Validate Data', async ({ page }) => {
    await page.click('a[href="/admin/user-approvals"]');
    await page.waitForSelector('h1:has-text("User Approvals")');
    
    const usersValid = await validateDatabaseState(page, '/api/v1/admin/users', (data) => {
      return Array.isArray(data.items) && data.items.length > 0;
    }, adminToken);
    
    expect(usersValid).toBe(true);
    await expect(page.locator('[data-testid="user-approval-row"]')).toHaveCountGreaterThan(0);
  });

  test('3. User Deactivation - End-to-End with Database Verification', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/admin/user-approvals`);
    await page.waitForSelector('[data-testid="user-approval-row"]');

    const initialUsers = await page.evaluate(async (token) => {
        const res = await fetch(`${API_BASE_URL}/api/v1/admin/users`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return res.json();
    }, adminToken);

    const activeUsersBefore = initialUsers.items.filter(u => u.is_active).length;

    const firstRow = page.locator('[data-testid="user-approval-row"]').first();
    await firstRow.locator('button:has-text("Deactivate")').click();
    
    await page.waitForResponse(response => 
      response.url().includes('/api/v1/admin/users/') && response.status() === 200
    );

    const updatedUsers = await page.evaluate(async (token) => {
        const res = await fetch(`${API_BASE_URL}/api/v1/admin/users`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return res.json();
    }, adminToken);

    const activeUsersAfter = updatedUsers.items.filter(u => u.is_active).length;
    expect(activeUsersAfter).toBeLessThan(activeUsersBefore);
  });

  test('4. Client Management - Load and Navigate', async ({ page }) => {
    await page.click('a[href="/admin/clients"]');
    await page.waitForSelector('h1:has-text("Client Management")');
    
    const clientsValid = await validateDatabaseState(page, '/api/v1/admin/clients', (data) => {
      return Array.isArray(data.items);
    }, adminToken);
    
    expect(clientsValid).toBe(true);
  });

  test('5. Client Edit Access', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/admin/clients`);
    await page.waitForSelector('h1:has-text("Client Management")');

    const clientRows = page.locator('[data-testid="client-row"]');
    if (await clientRows.count() > 0) {
      await clientRows.first().locator('button[aria-label="Open menu"]').click();
      await expect(page.locator('button:has-text("Edit Client")')).toBeVisible();
    } else {
      console.log('No clients to test edit functionality');
    }
  });

  test('6. Engagement Management - Navigation and Data', async ({ page }) => {
    await page.click('a[href="/admin/engagements"]');
    await page.waitForSelector('h1:has-text("Engagement Management")');
    
    const engagementsValid = await validateDatabaseState(page, '/api/v1/admin/engagements', (data) => {
      return Array.isArray(data.items);
    }, adminToken);
    
    expect(engagementsValid).toBe(true);
  });

  test('7. Engagement Creation - End-to-End with Database Verification', async ({ page }) => {
    const clientsData = await page.evaluate(async (token) => {
        const res = await fetch(`${API_BASE_URL}/api/v1/admin/clients`, { headers: { 'Authorization': `Bearer ${token}` } });
        return res.json();
    }, adminToken);

    if (clientsData.items.length === 0) {
      console.log('⚠️ No client accounts, skipping engagement creation test');
      return;
    }

    await page.goto(`${TEST_BASE_URL}/admin/engagements`);
    await page.waitForSelector('h1:has-text("Engagement Management")');
    
    const initialEngagements = await page.evaluate(async (token) => {
        const res = await fetch(`${API_BASE_URL}/api/v1/admin/engagements`, { headers: { 'Authorization': `Bearer ${token}` } });
        return res.json();
    }, adminToken);
    const initialCount = initialEngagements.items.length;

    await page.click('button:has-text("Create Engagement")');
    await page.waitForSelector('h2:has-text("Create New Engagement")');

    const engagementName = `Test-Engagement-${Date.now()}`;
    await page.fill('input[name="name"]', engagementName);
    
    await page.click('[role="combobox"]');
    await page.locator('[role="option"]').first().click();

    await page.click('button[type="submit"]');

    await page.waitForResponse(response => 
        response.url().includes('/api/v1/admin/engagements') && response.status() === 201
    );

    const updatedEngagements = await page.evaluate(async (token) => {
        const res = await fetch(`${API_BASE_URL}/api/v1/admin/engagements`, { headers: { 'Authorization': `Bearer ${token}` } });
        return res.json();
    }, adminToken);

    expect(updatedEngagements.items.length).toBeGreaterThan(initialCount);
    expect(updatedEngagements.items.some(e => e.name === engagementName)).toBe(true);
  });

  test('8. Data Import Page - CMDB Upload Flow', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/discovery/data-import`);
    await page.waitForSelector('h1:has-text("Data Import")');

    const filePath = 'sample_cmdb_data.csv';
    
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.locator('text=CMDB Data').first().click() // Assuming this is the dropzone trigger
    ]);
    await fileChooser.setFiles(filePath);

    await page.waitForSelector('div:has-text("File Analysis Summary")');
    
    await expect(page.locator('div:has-text("Detected Type: CSV Data File")')).toBeVisible();
    await expect(page.locator('div:has-text("Confidence: 100%")')).toBeVisible();
    await expect(page.locator('li:has-text("Asset Identification Fields Present")')).toBeVisible();
  });
}); 