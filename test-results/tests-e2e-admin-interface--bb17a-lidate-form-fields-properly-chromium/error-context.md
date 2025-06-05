# Test info

- Name: Admin Interface - Complete Workflow Tests >> Data Validation >> should validate form fields properly
- Location: /Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/admin-interface.spec.ts:298:5

# Error details

```
Error: page.click: Test timeout of 60000ms exceeded.
Call log:
  - waiting for locator('button:has-text("New Engagement")')

    at /Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/admin-interface.spec.ts:302:18
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
    - img
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
- heading "Engagement Management" [level=1]
- paragraph: Manage client engagements and migration projects
- button "Export":
  - img
  - text: Export
- button "Import":
  - img
  - text: Import
- link "New Engagement":
  - /url: /admin/engagements/create
  - img
  - text: New Engagement
- img
- textbox "Search engagements..."
- combobox: Client
- combobox: Phase
- heading "Active Engagements" [level=3]
- paragraph: 2 engagements found
- table:
  - rowgroup:
    - row "Engagement Client Team Timeline Budget Progress Actions":
      - cell "Engagement"
      - cell "Client"
      - cell "Team"
      - cell "Timeline"
      - cell "Budget"
      - cell "Progress"
      - cell "Actions"
  - rowgroup:
    - 'row "Test Engagement 2 migration AWS 0 sessions EM: TL: Invalid Date Invalid Date No budget set 0.0%"':
      - cell "Test Engagement 2 migration AWS":
        - text: Test Engagement 2 migration
        - img
        - text: AWS
      - cell "0 sessions"
      - 'cell "EM: TL:"'
      - cell "Invalid Date Invalid Date":
        - img
        - text: Invalid Date
        - img
        - text: Invalid Date
      - cell "No budget set"
      - cell "0.0%"
      - cell:
        - button:
          - img
    - 'row "Cloud Migration Initiative 2024 migration AWS 2 sessions EM: TL: Invalid Date Invalid Date No budget set 0.0%"':
      - cell "Cloud Migration Initiative 2024 migration AWS":
        - text: Cloud Migration Initiative 2024 migration
        - img
        - text: AWS
      - cell "2 sessions"
      - 'cell "EM: TL:"'
      - cell "Invalid Date Invalid Date":
        - img
        - text: Invalid Date
        - img
        - text: Invalid Date
      - cell "No budget set"
      - cell "0.0%"
      - cell:
        - button:
          - img
- button "Open AI Assistant and Feedback":
  - img
```

# Test source

```ts
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
  230 |       await Promise.race([
  231 |         page.waitForSelector('text=created successfully', { timeout: 15000 }),
  232 |         page.waitForSelector('text=Engagement Created Successfully', { timeout: 15000 }),
  233 |         page.waitForSelector('text=Error', { timeout: 15000 }),
  234 |         page.waitForSelector('text=Failed', { timeout: 15000 })
  235 |       ]);
  236 |       
  237 |       // Check result
  238 |       const successMessage = page.locator('text=created successfully, text=Engagement Created Successfully');
  239 |       const errorMessage = page.locator('text=Error, text=Failed');
  240 |       
  241 |       if (await successMessage.isVisible()) {
  242 |         console.log('✅ Engagement creation succeeded');
  243 |         
  244 |         // Should redirect back to engagement management
  245 |         await page.waitForURL('**/admin/engagements');
  246 |         await expect(page.locator('h1').first()).toContainText('Engagement Management');
  247 |       } else if (await errorMessage.isVisible()) {
  248 |         console.log('❌ Engagement creation failed');
  249 |         throw new Error('Engagement creation failed - this indicates a bug');
  250 |       }
  251 |     });
  252 |   });
  253 |
  254 |   test.describe('Navigation and General UI', () => {
  255 |     test('should navigate between all admin sections', async ({ page }) => {
  256 |       // Test navigation to each admin section
  257 |       const sections = [
  258 |         { name: 'Dashboard', url: '**/admin' },
  259 |         { name: 'Client Management', url: '**/admin/clients' },
  260 |         { name: 'Engagement Management', url: '**/admin/engagements' },
  261 |         { name: 'User Approvals', url: '**/admin/users/approvals' }
  262 |       ];
  263 |       
  264 |       for (const section of sections) {
  265 |         await page.click(`text=${section.name}`);
  266 |         await page.waitForURL(section.url);
  267 |         console.log(`✅ Successfully navigated to ${section.name}`);
  268 |       }
  269 |     });
  270 |
  271 |     test('should display error messages properly when API calls fail', async ({ page }) => {
  272 |       // This test will help us identify frontend-backend integration issues
  273 |       
  274 |       // Go to user management
  275 |       await page.click('text=User Approvals');
  276 |       await page.waitForURL('**/admin/users/approvals');
  277 |       
  278 |       // Intercept API calls to simulate failures
  279 |       await page.route('**/api/v1/auth/deactivate-user', route => {
  280 |         route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Test error simulation' }) });
  281 |       });
  282 |       
  283 |       await page.click('text=Active Users');
  284 |       
  285 |       // Try to deactivate a user (which should fail due to our mock)
  286 |       const deactivateButton = page.locator('button:has-text("Deactivate")').first();
  287 |       if (await deactivateButton.isVisible()) {
  288 |         await deactivateButton.click();
  289 |         
  290 |         // Should show error message
  291 |         await expect(page.locator('text=Error, text=Failed')).toBeVisible({ timeout: 10000 });
  292 |         console.log('✅ Error handling working correctly');
  293 |       }
  294 |     });
  295 |   });
  296 |
  297 |   test.describe('Data Validation', () => {
  298 |     test('should validate form fields properly', async ({ page }) => {
  299 |       // Test engagement creation validation
  300 |       await page.click('text=Engagement Management');
  301 |       await page.waitForURL('**/admin/engagements');
> 302 |       await page.click('button:has-text("New Engagement")');
      |                  ^ Error: page.click: Test timeout of 60000ms exceeded.
  303 |       
  304 |       // Try to submit empty form
  305 |       await page.click('button[type="submit"]:has-text("Create Engagement")');
  306 |       
  307 |       // Should show validation errors
  308 |       await expect(page.locator('text=required, text=error')).toBeVisible();
  309 |       console.log('✅ Form validation working correctly');
  310 |     });
  311 |   });
  312 | }); 
```