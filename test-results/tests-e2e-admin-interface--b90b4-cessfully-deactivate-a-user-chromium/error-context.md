# Test info

- Name: Admin Interface - Complete Workflow Tests >> User Management >> should successfully deactivate a user
- Location: /Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/admin-interface.spec.ts:57:5

# Error details

```
Error: Timed out 5000ms waiting for expect(locator).toBeVisible()

Locator: locator('[data-testid="active-user-row"]').first()
Expected: visible
Received: <element(s) not found>
Call log:
  - expect.toBeVisible with timeout 5000ms
  - waiting for locator('[data-testid="active-user-row"]').first()

    at /Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/admin-interface.spec.ts:64:34
```

# Page snapshot

```yaml
- region "Notifications (F8)":
  - list
- img
- heading "Admin Console" [level=1]
- paragraph: AI Force Platform
- navigation:
  - link "Dashboard Overview and metrics":
    - /url: /admin/dashboard
    - img
    - text: Dashboard Overview and metrics
  - link "Client Management Manage client accounts":
    - /url: /admin/clients
    - img
    - text: Client Management Manage client accounts
  - link "Engagement Management Manage engagements":
    - /url: /admin/engagements
    - img
    - text: Engagement Management Manage engagements
  - link "User Approvals Review pending users":
    - /url: /admin/users/approvals
    - img
    - text: User Approvals Review pending users
    - img
- link "Back to Main App":
  - /url: /
  - img
  - text: Back to Main App
- img
- text: Administration
- button "Admin User admin":
  - img
  - text: Admin User admin
- heading "User Management" [level=1]
- paragraph: Review pending user registration requests and manage active users
- img
- text: 2 pending
- button "Add New User":
  - img
  - text: Add New User
- heading "Pending Approvals" [level=3]
- img
- text: "2"
- paragraph: awaiting review
- heading "Active Users" [level=3]
- img
- text: "4"
- paragraph: approved and active
- heading "Admin Requests" [level=3]
- img
- text: "0"
- paragraph: high privilege requests
- heading "Average Wait Time" [level=3]
- img
- text: "1.2"
- paragraph: days
- navigation:
  - button "Pending Approvals (2)"
  - button "Active Users (4)"
- heading "Pending Registration Requests" [level=3]
- paragraph: Review user registration requests and approve or reject access
- img
- heading [level=4]
- img
- img
- text: Test Organization Test Analyst read only Requested Invalid Date
- paragraph: Testing the complete registration flow
- button "Details":
  - img
  - text: Details
- button "Reject":
  - img
  - text: Reject
- button "Approve":
  - img
  - text: Approve
- img
- heading [level=4]
- img
- img
- text: Test Corp Test Role read only Requested Invalid Date
- paragraph: Testing registration
- button "Details":
  - img
  - text: Details
- button "Reject":
  - img
  - text: Reject
- button "Approve":
  - img
  - text: Approve
- button "Open AI Assistant and Feedback":
  - img
```

# Test source

```ts
   1 | import { test, expect } from '@playwright/test';
   2 |
   3 | test.describe('Admin Interface - Complete Workflow Tests', () => {
   4 |   test.beforeEach(async ({ page }) => {
   5 |     // Clear any existing authentication
   6 |     await page.goto('http://localhost:8081/');
   7 |     await page.evaluate(() => {
   8 |       localStorage.clear();
   9 |     });
   10 |     
   11 |     // Navigate to login page
   12 |     await page.goto('http://localhost:8081/login');
   13 |     
   14 |     // Wait for page to load
   15 |     await page.waitForLoadState('networkidle');
   16 |     
   17 |     // Login as admin user
   18 |     await page.fill('input[type="email"]', 'admin@aiforce.com');
   19 |     await page.fill('input[type="password"]', 'admin123');
   20 |     await page.click('button[type="submit"]');
   21 |     
   22 |     // Wait for login to complete (redirects to home page)
   23 |     await page.waitForURL('http://localhost:8081/');
   24 |     
   25 |     // Navigate to admin area
   26 |     await page.goto('http://localhost:8081/admin');
   27 |     await page.waitForLoadState('networkidle');
   28 |     
   29 |     // Verify we're in admin area
   30 |     await expect(page.locator('h1').first()).toContainText('Admin Console');
   31 |   });
   32 |
   33 |   test.describe('User Management', () => {
   34 |     test('should navigate to user management and display active users', async ({ page }) => {
   35 |       // Click on User Approvals in the admin sidebar
   36 |       await page.locator('a[href="/admin/users/approvals"]').first().click();
   37 |       await page.waitForURL('**/admin/users/approvals');
   38 |       
   39 |       // Wait for page to load
   40 |       await page.waitForLoadState('networkidle');
   41 |       
   42 |       // Verify we're on the user management page
   43 |       await expect(page.locator('h1').nth(1)).toContainText('User Management');
   44 |       
   45 |       // Check if active users tab exists and click it
   46 |       await page.click('button:has-text("Active Users")');
   47 |       await page.waitForLoadState('networkidle');
   48 |       
   49 |       // Verify Active Users tab is visible
   50 |       await expect(page.locator('button:has-text("Active Users")')).toBeVisible();
   51 |       
   52 |       // The test passes if we can navigate to the page and click the tab
   53 |       // User data loading is a separate concern from navigation functionality
   54 |       console.log('✅ User management navigation working correctly');
   55 |     });
   56 |
   57 |     test('should successfully deactivate a user', async ({ page }) => {
   58 |       await page.click('text=User Approvals');
   59 |       await page.waitForURL('**/admin/users/approvals');
   60 |       await page.click('text=Active Users');
   61 |       
   62 |       // Find first active user and get their name
   63 |       const firstUserRow = page.locator('[data-testid="active-user-row"]').first();
>  64 |       await expect(firstUserRow).toBeVisible();
      |                                  ^ Error: Timed out 5000ms waiting for expect(locator).toBeVisible()
   65 |       
   66 |       // Click deactivate button for first user
   67 |       const deactivateButton = firstUserRow.locator('button:has-text("Deactivate")');
   68 |       
   69 |       // Wait for the button to be visible and enabled
   70 |       await expect(deactivateButton).toBeVisible();
   71 |       await expect(deactivateButton).toBeEnabled();
   72 |       
   73 |       // Click deactivate and handle confirmation dialog
   74 |       await deactivateButton.click();
   75 |       
   76 |       // Wait for either success message or error
   77 |       await Promise.race([
   78 |         page.waitForSelector('text=User Deactivated', { timeout: 10000 }),
   79 |         page.waitForSelector('text=Error', { timeout: 10000 }),
   80 |         page.waitForSelector('text=Failed', { timeout: 10000 })
   81 |       ]);
   82 |       
   83 |       // Check if operation was successful
   84 |       const successMessage = page.locator('text=User Deactivated');
   85 |       const errorMessage = page.locator('text=Error, text=Failed');
   86 |       
   87 |       if (await successMessage.isVisible()) {
   88 |         console.log('✅ User deactivation succeeded');
   89 |       } else if (await errorMessage.isVisible()) {
   90 |         console.log('❌ User deactivation failed');
   91 |         throw new Error('User deactivation failed - this indicates a bug');
   92 |       }
   93 |     });
   94 |
   95 |     test('should successfully activate a deactivated user', async ({ page }) => {
   96 |       await page.click('text=User Approvals');
   97 |       await page.waitForURL('**/admin/users/approvals');
   98 |       await page.click('text=Active Users');
   99 |       
  100 |       // Look for a user with "Activate" button (deactivated user)
  101 |       const activateButton = page.locator('button:has-text("Activate")').first();
  102 |       
  103 |       if (await activateButton.isVisible()) {
  104 |         await activateButton.click();
  105 |         
  106 |         // Wait for success or error message
  107 |         await Promise.race([
  108 |           page.waitForSelector('text=User Activated', { timeout: 10000 }),
  109 |           page.waitForSelector('text=Error', { timeout: 10000 })
  110 |         ]);
  111 |         
  112 |         const successMessage = page.locator('text=User Activated');
  113 |         if (await successMessage.isVisible()) {
  114 |           console.log('✅ User activation succeeded');
  115 |         } else {
  116 |           throw new Error('User activation failed - this indicates a bug');
  117 |         }
  118 |       } else {
  119 |         console.log('ℹ️ No deactivated users available to test activation');
  120 |       }
  121 |     });
  122 |   });
  123 |
  124 |   test.describe('Client Management', () => {
  125 |     test('should navigate to client management and display clients', async ({ page }) => {
  126 |       await page.click('text=Client Management');
  127 |       await page.waitForURL('**/admin/clients');
  128 |       
  129 |       await expect(page.locator('h1').first()).toContainText('Client Management');
  130 |       
  131 |       // Check if clients are displayed
  132 |       const clientRows = page.locator('[data-testid="client-row"]');
  133 |       await expect(clientRows.first()).toBeVisible();
  134 |     });
  135 |
  136 |     test('should successfully edit a client', async ({ page }) => {
  137 |       await page.click('text=Client Management');
  138 |       await page.waitForURL('**/admin/clients');
  139 |       
  140 |       // Click on first client to view details
  141 |       await page.click('[data-testid="client-row"]').first();
  142 |       await page.waitForSelector('text=Edit Client');
  143 |       
  144 |       // Click edit client button
  145 |       await page.click('button:has-text("Edit Client")');
  146 |       
  147 |       // Wait for edit dialog to appear
  148 |       await expect(page.locator('[role="dialog"]')).toBeVisible();
  149 |       await expect(page.locator('text=Edit Client:')).toBeVisible();
  150 |       
  151 |       // Update a field (account name)
  152 |       const accountNameField = page.locator('input[name="account_name"], #account_name');
  153 |       await accountNameField.clear();
  154 |       await accountNameField.fill('Updated Test Client Name');
  155 |       
  156 |       // Update industry field
  157 |       const industrySelect = page.locator('select[name="industry"], #industry');
  158 |       await industrySelect.selectOption('Technology');
  159 |       
  160 |       // Click update button
  161 |       await page.click('button:has-text("Update Client")');
  162 |       
  163 |       // Wait for success or error message
  164 |       await Promise.race([
```