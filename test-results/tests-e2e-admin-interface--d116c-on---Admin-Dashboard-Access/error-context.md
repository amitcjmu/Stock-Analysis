# Test info

- Name: Admin Interface E2E Tests with Database Validation >> 1. Navigation - Admin Dashboard Access
- Location: /Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/admin-interface.spec.ts:92:3

# Error details

```
Error: page.waitForSelector: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('h1:has-text("Admin Console")') to be visible

    at /Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/admin-interface.spec.ts:89:16
```

# Page snapshot

```yaml
- region "Notifications (F8)":
  - list
- img
- heading "Sign In" [level=3]
- paragraph: Access AI Force Migration Platform
- text: Email
- img
- textbox "Email"
- text: Password
- img
- textbox "Password"
- button:
  - img
- heading "Demo Credentials:" [level=4]
- strong: "Admin:"
- text: admin@democorp.com / admin123
- strong: "User:"
- text: demo@democorp.com / user123
- button "Sign In"
- button "Need access? Request an account"
- link "Back to Platform":
  - /url: /
- button "Open AI Assistant and Feedback":
  - img
```

# Test source

```ts
   1 | import { test, expect, Page } from '@playwright/test';
   2 |
   3 | // Test configuration and utilities
   4 | const TEST_BASE_URL = 'http://localhost:8081';
   5 | const API_BASE_URL = 'http://localhost:8000';
   6 |
   7 | // Helper function to clear storage and login
   8 | async function loginAsAdmin(page: Page) {
   9 |   await page.goto(`${TEST_BASE_URL}/login`);
   10 |   await page.evaluate(() => localStorage.clear());
   11 |   await page.goto(`${TEST_BASE_URL}/login`, { waitUntil: 'networkidle' });
   12 |   
   13 |   await page.fill('input[type="email"]', 'admin@democorp.com');
   14 |   await page.fill('input[type="password"]', 'admin123');
   15 |   
   16 |   // Click and then wait for navigation, with better debugging
   17 |   await page.click('button[type="submit"]');
   18 |   try {
   19 |     await page.waitForURL(`${TEST_BASE_URL}/admin`, { timeout: 15000 });
   20 |   } catch(e) {
   21 |     console.error("Failed to navigate to admin page after login.", e);
   22 |     await page.screenshot({ path: 'playwright-debug/login-failure.png' });
   23 |     throw e;
   24 |   }
   25 | }
   26 |
   27 | // Helper function to validate API response
   28 | async function validateApiCall(page: Page, expectedStatus: number = 200) {
   29 |   return new Promise((resolve, reject) => {
   30 |     let responseReceived = false;
   31 |     
   32 |     const responseListener = (response) => {
   33 |       if (response.url().includes('/api/v1/')) {
   34 |         responseReceived = true;
   35 |         if (response.status() === expectedStatus) {
   36 |           resolve(response);
   37 |         } else {
   38 |           reject(new Error(`API call failed with status ${response.status()}: ${response.url()}`));
   39 |         }
   40 |       }
   41 |     };
   42 |     
   43 |     page.on('response', responseListener);
   44 |     
   45 |     // Timeout after 10 seconds
   46 |     setTimeout(() => {
   47 |       page.off('response', responseListener);
   48 |       if (!responseReceived) {
   49 |         reject(new Error('No API response received within timeout'));
   50 |       }
   51 |     }, 10000);
   52 |   });
   53 | }
   54 |
   55 | // Helper function to validate database state via API
   56 | async function validateDatabaseState(page: Page, endpoint: string, validator: (data: any) => boolean, token?: string) {
   57 |   const finalToken = token || await page.evaluate(() => localStorage.getItem('token'));
   58 |
   59 |   const response = await page.evaluate(async ({ url, authToken }) => {
   60 |     const res = await fetch(url, {
   61 |       headers: {
   62 |         'Authorization': `Bearer ${authToken}`,
   63 |         'Content-Type': 'application/json'
   64 |       }
   65 |     });
   66 |     if (!res.ok) throw new Error(`API Error: ${res.status} ${res.statusText}`);
   67 |     return res.json();
   68 |   }, { url: `${API_BASE_URL}${endpoint}`, authToken: finalToken });
   69 |
   70 |   return validator(response);
   71 | }
   72 |
   73 | test.describe('Admin Interface E2E Tests with Database Validation', () => {
   74 |   let adminToken: string;
   75 |
   76 |   test.beforeAll(async ({ browser }) => {
   77 |     const page = await browser.newPage();
   78 |     await loginAsAdmin(page);
   79 |     adminToken = await page.evaluate(() => localStorage.getItem('token') || '');
   80 |     await page.close();
   81 |   });
   82 |
   83 |   test.beforeEach(async ({ page }) => {
   84 |     await page.goto(TEST_BASE_URL);
   85 |     await page.evaluate((token) => {
   86 |         localStorage.setItem('token', token);
   87 |     }, adminToken);
   88 |     await page.goto(`${TEST_BASE_URL}/admin`);
>  89 |     await page.waitForSelector('h1:has-text("Admin Console")');
      |                ^ Error: page.waitForSelector: Test timeout of 30000ms exceeded.
   90 |   });
   91 |
   92 |   test('1. Navigation - Admin Dashboard Access', async ({ page }) => {
   93 |     await expect(page.locator('h1:has-text("Admin Console")')).toBeVisible();
   94 |     await expect(page.locator('a[href="/admin/clients"]')).toBeVisible();
   95 |     await expect(page.locator('a[href="/admin/engagements"]')).toBeVisible();
   96 |     await expect(page.locator('a[href="/admin/user-approvals"]')).toBeVisible();
   97 |   });
   98 |
   99 |   test('2. User Management - Load and Validate Data', async ({ page }) => {
  100 |     await page.click('a[href="/admin/user-approvals"]');
  101 |     await page.waitForSelector('h1:has-text("User Approvals")');
  102 |     
  103 |     const usersValid = await validateDatabaseState(page, '/api/v1/admin/users', (data) => {
  104 |       return Array.isArray(data.items) && data.items.length > 0;
  105 |     }, adminToken);
  106 |     
  107 |     expect(usersValid).toBe(true);
  108 |     await expect(page.locator('[data-testid="user-approval-row"]')).toHaveCountGreaterThan(0);
  109 |   });
  110 |
  111 |   test('3. User Deactivation - End-to-End with Database Verification', async ({ page }) => {
  112 |     await page.goto(`${TEST_BASE_URL}/admin/user-approvals`);
  113 |     await page.waitForSelector('[data-testid="user-approval-row"]');
  114 |
  115 |     const initialUsers = await page.evaluate(async (token) => {
  116 |         const res = await fetch(`${API_BASE_URL}/api/v1/admin/users`, {
  117 |             headers: { 'Authorization': `Bearer ${token}` }
  118 |         });
  119 |         return res.json();
  120 |     }, adminToken);
  121 |
  122 |     const activeUsersBefore = initialUsers.items.filter(u => u.is_active).length;
  123 |
  124 |     const firstRow = page.locator('[data-testid="user-approval-row"]').first();
  125 |     await firstRow.locator('button:has-text("Deactivate")').click();
  126 |     
  127 |     await page.waitForResponse(response => 
  128 |       response.url().includes('/api/v1/admin/users/') && response.status() === 200
  129 |     );
  130 |
  131 |     const updatedUsers = await page.evaluate(async (token) => {
  132 |         const res = await fetch(`${API_BASE_URL}/api/v1/admin/users`, {
  133 |             headers: { 'Authorization': `Bearer ${token}` }
  134 |         });
  135 |         return res.json();
  136 |     }, adminToken);
  137 |
  138 |     const activeUsersAfter = updatedUsers.items.filter(u => u.is_active).length;
  139 |     expect(activeUsersAfter).toBeLessThan(activeUsersBefore);
  140 |   });
  141 |
  142 |   test('4. Client Management - Load and Navigate', async ({ page }) => {
  143 |     await page.click('a[href="/admin/clients"]');
  144 |     await page.waitForSelector('h1:has-text("Client Management")');
  145 |     
  146 |     const clientsValid = await validateDatabaseState(page, '/api/v1/admin/clients', (data) => {
  147 |       return Array.isArray(data.items);
  148 |     }, adminToken);
  149 |     
  150 |     expect(clientsValid).toBe(true);
  151 |   });
  152 |
  153 |   test('5. Client Edit Access', async ({ page }) => {
  154 |     await page.goto(`${TEST_BASE_URL}/admin/clients`);
  155 |     await page.waitForSelector('h1:has-text("Client Management")');
  156 |
  157 |     const clientRows = page.locator('[data-testid="client-row"]');
  158 |     if (await clientRows.count() > 0) {
  159 |       await clientRows.first().locator('button[aria-label="Open menu"]').click();
  160 |       await expect(page.locator('button:has-text("Edit Client")')).toBeVisible();
  161 |     } else {
  162 |       console.log('No clients to test edit functionality');
  163 |     }
  164 |   });
  165 |
  166 |   test('6. Engagement Management - Navigation and Data', async ({ page }) => {
  167 |     await page.click('a[href="/admin/engagements"]');
  168 |     await page.waitForSelector('h1:has-text("Engagement Management")');
  169 |     
  170 |     const engagementsValid = await validateDatabaseState(page, '/api/v1/admin/engagements', (data) => {
  171 |       return Array.isArray(data.items);
  172 |     }, adminToken);
  173 |     
  174 |     expect(engagementsValid).toBe(true);
  175 |   });
  176 |
  177 |   test('7. Engagement Creation - End-to-End with Database Verification', async ({ page }) => {
  178 |     const clientsData = await page.evaluate(async (token) => {
  179 |         const res = await fetch(`${API_BASE_URL}/api/v1/admin/clients`, { headers: { 'Authorization': `Bearer ${token}` } });
  180 |         return res.json();
  181 |     }, adminToken);
  182 |
  183 |     if (clientsData.items.length === 0) {
  184 |       console.log('⚠️ No client accounts, skipping engagement creation test');
  185 |       return;
  186 |     }
  187 |
  188 |     await page.goto(`${TEST_BASE_URL}/admin/engagements`);
  189 |     await page.waitForSelector('h1:has-text("Engagement Management")');
```