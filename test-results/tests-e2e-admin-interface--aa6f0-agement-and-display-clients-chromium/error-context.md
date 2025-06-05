# Test info

- Name: Admin Interface - Complete Workflow Tests >> Client Management >> should navigate to client management and display clients
- Location: /Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/admin-interface.spec.ts:125:5

# Error details

```
Error: Timed out 5000ms waiting for expect(locator).toContainText(expected)

Locator: locator('h1').first()
Expected string: "Client Management"
Received string: "Admin Console"
Call log:
  - expect.toContainText with timeout 5000ms
  - waiting for locator('h1').first()
    9 × locator resolved to <h1 data-lov-name="h1" data-component-line="72" data-component-name="h1" data-component-file="AdminLayout.tsx" class="text-lg font-semibold text-gray-900" data-lov-id="src/components/admin/AdminLayout.tsx:72:14" data-component-path="src/components/admin/AdminLayout.tsx" data-component-content="%7B%22text%22%3A%22Admin%20Console%22%2C%22className%22%3A%22text-lg%20font-semibold%20text-gray-900%22%7D">Admin Console</h1>
      - unexpected value "Admin Console"

    at /Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/admin-interface.spec.ts:129:48
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
    - img
  - link "Engagement Management Manage engagements":
    - /url: /admin/engagements
    - img
    - text: Engagement Management Manage engagements
  - link "User Approvals Review pending users":
    - /url: /admin/users/approvals
    - img
    - text: User Approvals Review pending users
- link "Back to Main App":
  - /url: /
  - img
  - text: Back to Main App
- img
- text: Administration
- button "Admin User admin":
  - img
  - text: Admin User admin
- heading "Client Management" [level=1]
- paragraph: Manage client accounts and business relationships
- button "Export":
  - img
  - text: Export
- button "Import":
  - img
  - text: Import
- link "New Client":
  - /url: /admin/clients/create
  - img
  - text: New Client
- img
- textbox "Search clients..."
- combobox: Industry
- combobox: Company Size
- heading "Client Accounts" [level=3]
- paragraph: 4 clients found
- table:
  - rowgroup:
    - row "Client Industry Contact Engagements Cloud Strategy Status Actions":
      - cell "Client"
      - cell "Industry"
      - cell "Contact"
      - cell "Engagements"
      - cell "Cloud Strategy"
      - cell "Status"
      - cell "Actions"
  - rowgroup:
    - row "Complete Test Client New York, NY Medium (100-1000) Technology John Smith john.smith@testcomplete.com +1-555-123-4567 1 active 1 total Active":
      - cell "Complete Test Client New York, NY Medium (100-1000)":
        - text: Complete Test Client
        - img
        - text: New York, NY Medium (100-1000)
      - cell "Technology"
      - cell "John Smith john.smith@testcomplete.com +1-555-123-4567":
        - text: John Smith
        - img
        - text: john.smith@testcomplete.com
        - img
        - text: +1-555-123-4567
      - cell "1 active 1 total"
      - cell
      - cell "Active":
        - img
        - text: Active
      - cell:
        - button:
          - img
    - row "Test Client Company Medium (100-1000) Technology 0 active 0 total Active":
      - cell "Test Client Company Medium (100-1000)":
        - text: Test Client Company
        - img
        - text: Medium (100-1000)
      - cell "Technology"
      - cell:
        - img
      - cell "0 active 0 total"
      - cell
      - cell "Active":
        - img
        - text: Active
      - cell:
        - button:
          - img
    - row "Marathon Petroleum Findlay, OH Enterprise (5000+) Energy Barry Huff bhuff1@marathonpetroleum.com 14752188441 0 active 1 total Active":
      - cell "Marathon Petroleum Findlay, OH Enterprise (5000+)":
        - text: Marathon Petroleum
        - img
        - text: Findlay, OH Enterprise (5000+)
      - cell "Energy"
      - cell "Barry Huff bhuff1@marathonpetroleum.com 14752188441":
        - text: Barry Huff
        - img
        - text: bhuff1@marathonpetroleum.com
        - img
        - text: "14752188441"
      - cell "0 active 1 total"
      - cell
      - cell "Active":
        - img
        - text: Active
      - cell:
        - button:
          - img
    - row "Acme Corporation Enterprise (1000+ employees) Technology 1 active 1 total Active":
      - cell "Acme Corporation Enterprise (1000+ employees)":
        - text: Acme Corporation
        - img
        - text: Enterprise (1000+ employees)
      - cell "Technology"
      - cell:
        - img
      - cell "1 active 1 total"
      - cell
      - cell "Active":
        - img
        - text: Active
      - cell:
        - button:
          - img
- button "Open AI Assistant and Feedback":
  - img
```

# Test source

```ts
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
   64 |       await expect(firstUserRow).toBeVisible();
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
> 129 |       await expect(page.locator('h1').first()).toContainText('Client Management');
      |                                                ^ Error: Timed out 5000ms waiting for expect(locator).toContainText(expected)
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
  165 |         page.waitForSelector('text=updated successfully', { timeout: 15000 }),
  166 |         page.waitForSelector('text=Error', { timeout: 15000 }),
  167 |         page.waitForSelector('text=Failed', { timeout: 15000 })
  168 |       ]);
  169 |       
  170 |       // Check result
  171 |       const successMessage = page.locator('text=updated successfully');
  172 |       const errorMessage = page.locator('text=Error, text=Failed');
  173 |       
  174 |       if (await successMessage.isVisible()) {
  175 |         console.log('✅ Client update succeeded');
  176 |       } else if (await errorMessage.isVisible()) {
  177 |         console.log('❌ Client update failed');
  178 |         throw new Error('Client update failed - this indicates a bug');
  179 |       }
  180 |     });
  181 |   });
  182 |
  183 |   test.describe('Engagement Management', () => {
  184 |     test('should navigate to engagement management', async ({ page }) => {
  185 |       await page.click('text=Engagement Management');
  186 |       await page.waitForURL('**/admin/engagements');
  187 |       
  188 |       await expect(page.locator('h1').first()).toContainText('Engagement Management');
  189 |       
  190 |       // Check for "New Engagement" button
  191 |       await expect(page.locator('button:has-text("New Engagement")')).toBeVisible();
  192 |     });
  193 |
  194 |     test('should successfully create a new engagement', async ({ page }) => {
  195 |       await page.click('text=Engagement Management');
  196 |       await page.waitForURL('**/admin/engagements');
  197 |       
  198 |       // Click new engagement button
  199 |       await page.click('button:has-text("New Engagement")');
  200 |       await page.waitForURL('**/admin/engagements/create');
  201 |       
  202 |       // Fill out engagement creation form
  203 |       await expect(page.locator('h1').first()).toContainText('Create New Engagement');
  204 |       
  205 |       // Fill required fields
  206 |       await page.fill('#engagement_name', 'E2E Test Engagement');
  207 |       await page.fill('#project_manager', 'Test Project Manager');
  208 |       await page.fill('textarea[name="description"]', 'This is a test engagement created by E2E tests for validation purposes.');
  209 |       
  210 |       // Select a client account (if dropdown exists)
  211 |       const clientSelect = page.locator('select[name="client_account_id"]');
  212 |       if (await clientSelect.isVisible()) {
  213 |         const options = await clientSelect.locator('option').allTextContents();
  214 |         if (options.length > 1) {
  215 |           await clientSelect.selectOption({ index: 1 }); // Select first non-empty option
  216 |         }
  217 |       }
  218 |       
  219 |       // Set dates
  220 |       await page.fill('input[name="estimated_start_date"]', '2025-02-01');
  221 |       await page.fill('input[name="estimated_end_date"]', '2025-06-30');
  222 |       
  223 |       // Set budget
  224 |       await page.fill('input[name="budget"]', '500000');
  225 |       
  226 |       // Submit the form
  227 |       await page.click('button[type="submit"]:has-text("Create Engagement")');
  228 |       
  229 |       // Wait for success or error message
```