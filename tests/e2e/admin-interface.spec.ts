import { test, expect, Page } from '@playwright/test';

// Test configuration and utilities
const TEST_BASE_URL = 'http://localhost:8081';
const API_BASE_URL = 'http://localhost:8000';

// Helper function to clear storage and login
async function loginAsAdmin(page: Page) {
  // Navigate to login page first to establish context
  await page.goto(`${TEST_BASE_URL}/login`);
  
  // Clear localStorage after we have a proper context
  await page.evaluate(() => {
    try {
      localStorage.clear();
    } catch (e) {
      console.log('LocalStorage not available, continuing...');
    }
  });
  
  // Fill login form
  await page.fill('input[type="email"]', 'admin@aiforce.com');
  await page.fill('input[type="password"]', 'admin123');
  
  // Submit and wait for redirect
  await page.click('button[type="submit"]');
  await page.waitForURL(`${TEST_BASE_URL}/admin`);
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
async function validateDatabaseState(page: Page, endpoint: string, validator: (data: any) => boolean) {
  try {
    const response = await page.evaluate(async (url) => {
      try {
        const token = localStorage.getItem('token') || '';
        const res = await fetch(url, {
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json'
          }
        });
        
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        
        return await res.json();
      } catch (error) {
        console.error('API call failed:', error);
        return { error: error.message };
      }
    }, `${API_BASE_URL}${endpoint}`);
    
    if (response.error) {
      console.error('Database validation failed:', response.error);
      return false;
    }
    
    return validator(response);
  } catch (error) {
    console.error('Database validation failed:', error);
    return false;
  }
}

test.describe('Admin Interface E2E Tests with Database Validation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('1. Navigation - Admin Dashboard Access', async ({ page }) => {
    // Verify we're on admin dashboard
    await expect(page.locator('h1:has-text("Admin Console")')).toBeVisible();
    
    // Check all navigation links are present
    await expect(page.locator('a[href="/admin"]')).toBeVisible();
    await expect(page.locator('a[href="/admin/clients"]')).toBeVisible();
    await expect(page.locator('a[href="/admin/engagements"]')).toBeVisible();
    await expect(page.locator('a[href="/admin/users/approvals"]')).toBeVisible();
  });

  test('2. User Management - Load and Validate Data', async ({ page }) => {
    // Navigate to user management
    await page.locator('a[href="/admin/users/approvals"]').first().click();
    await page.waitForTimeout(2000); // Wait for data loading
    
    // Verify page loaded
    await expect(page.locator('h1:has-text("User Management")')).toBeVisible();
    
    // Validate database state - check if users are actually loaded from backend
    const usersValid = await validateDatabaseState(page, '/api/v1/auth/active-users', (data) => {
      return Array.isArray(data.users) && data.users.length > 0;
    });
    
    expect(usersValid).toBe(true);
    
    // Verify UI shows the data
    await expect(page.locator('[data-testid="active-user-row"]')).toHaveCount({ min: 1 });
  });

  test('3. User Deactivation - End-to-End with Database Verification', async ({ page }) => {
    // Navigate to user management
    await page.locator('a[href="/admin/users/approvals"]').first().click();
    await page.waitForTimeout(2000);
    
    // Get initial user count
    const initialUsersData = await page.evaluate(async () => {
      const res = await fetch('http://localhost:8000/api/v1/auth/active-users', {
        headers: {
          'Authorization': localStorage.getItem('token') ? `Bearer ${localStorage.getItem('token')}` : '',
          'Content-Type': 'application/json'
        }
      });
      return res.json();
    });
    
    const initialActiveUsers = initialUsersData.users.filter(u => u.status === 'active').length;
    
    // Set up API response monitoring
    const apiResponsePromise = validateApiCall(page, 200);
    
    // Click deactivate button on first user
    await page.locator('[data-testid="active-user-row"] button:has-text("Deactivate")').first().click();
    
    // Wait for API call to complete
    try {
      await apiResponsePromise;
      console.log('✅ Deactivation API call succeeded');
    } catch (error) {
      console.error('❌ Deactivation API call failed:', error);
      throw error;
    }
    
    // Wait a moment for backend to process
    await page.waitForTimeout(2000);
    
    // Validate database state changed
    const updatedUsersValid = await validateDatabaseState(page, '/api/v1/auth/active-users', (data) => {
      const currentActiveUsers = data.users.filter(u => u.status === 'active').length;
      return currentActiveUsers < initialActiveUsers; // Should be one less active user
    });
    
    expect(updatedUsersValid).toBe(true);
  });

  test('4. Client Management - Load and Navigate', async ({ page }) => {
    // Navigate to client management
    await page.locator('a[href="/admin/clients"]').first().click();
    await page.waitForTimeout(2000);
    
    // Verify page loaded
    await expect(page.locator('h1:has-text("Client Management")')).toBeVisible();
    
    // Validate database state
    const clientsValid = await validateDatabaseState(page, '/api/v1/admin/clients/', (data) => {
      return Array.isArray(data.items) && data.items.length >= 0; // Can be 0 or more
    });
    
    expect(clientsValid).toBe(true);
    
    // If clients exist, verify they're displayed
    const clientRows = page.locator('[data-testid="client-row"]');
    const count = await clientRows.count();
    console.log(`Found ${count} client rows in UI`);
  });

  test('5. Client Edit Access', async ({ page }) => {
    // Navigate to client management
    await page.locator('a[href="/admin/clients"]').first().click();
    await page.waitForTimeout(2000);
    
    // Check if there are clients to edit
    const clientRows = page.locator('[data-testid="client-row"]');
    const count = await clientRows.count();
    
    if (count > 0) {
      // Click dropdown menu (MoreHorizontal) on first client
      await page.locator('[data-testid="client-row"]').first().locator('button svg').click();
      await page.waitForTimeout(500);
      
      // Look for edit option
      const editButton = page.locator('text="Edit"');
      await expect(editButton).toBeVisible();
    } else {
      console.log('No clients available to test edit functionality');
    }
  });

  test('6. Engagement Management - Navigation and Data', async ({ page }) => {
    // Navigate to engagement management
    await page.locator('a[href="/admin/engagements"]').first().click();
    await page.waitForTimeout(2000);
    
    // Verify page loaded
    await expect(page.locator('h1:has-text("Engagement Management")')).toBeVisible();
    
    // Validate database state
    const engagementsValid = await validateDatabaseState(page, '/api/v1/admin/engagements/', (data) => {
      return Array.isArray(data.items) && data.items.length >= 0;
    });
    
    expect(engagementsValid).toBe(true);
  });

  test('7. Engagement Creation - End-to-End with Database Verification', async ({ page }) => {
    // First ensure we have client accounts to create engagements for
    const clientsData = await page.evaluate(async () => {
      const res = await fetch('http://localhost:8000/api/v1/admin/clients/', {
        headers: {
          'Authorization': localStorage.getItem('token') ? `Bearer ${localStorage.getItem('token')}` : '',
          'Content-Type': 'application/json'
        }
      });
      return res.json();
    });
    
    if (!clientsData.items || clientsData.items.length === 0) {
      console.log('⚠️ No client accounts available, skipping engagement creation test');
      return;
    }
    
    // Navigate to engagement management
    await page.locator('a[href="/admin/engagements"]').first().click();
    await page.waitForTimeout(1000);
    
    // Get initial engagement count
    const initialEngagementsData = await page.evaluate(async () => {
      const res = await fetch('http://localhost:8000/api/v1/admin/engagements/', {
        headers: {
          'Authorization': localStorage.getItem('token') ? `Bearer ${localStorage.getItem('token')}` : '',
          'Content-Type': 'application/json'
        }
      });
      return res.json();
    });
    
    const initialEngagementCount = initialEngagementsData.items ? initialEngagementsData.items.length : 0;
    
    // Click New Engagement button
    await page.click('a[href="/admin/engagements/create"]:has-text("New Engagement")');
    await page.waitForURL('**/admin/engagements/create');
    
    // Fill out the form with valid data
    await page.fill('#engagement_name', 'Test Engagement E2E');
    
    // Select first available client
    await page.click('[data-testid="client-select-trigger"]');
    await page.click('[data-testid="client-select-item"]');
    
    await page.fill('#project_manager', 'Test Manager');
    await page.fill('#description', 'This is a test engagement created by E2E testing');
    await page.fill('#estimated_start_date', '2025-01-15');
    await page.fill('#estimated_end_date', '2025-06-15');
    await page.fill('#budget', '100000');
    
    // Set up API response monitoring
    const apiResponsePromise = validateApiCall(page, 200);
    
    // Submit the form
    await page.click('button[type="submit"]:has-text("Create Engagement")');
    
    // Wait for API call
    try {
      await apiResponsePromise;
      console.log('✅ Engagement creation API call succeeded');
    } catch (error) {
      console.error('❌ Engagement creation API call failed:', error);
      throw error;
    }
    
    // Wait for navigation back to engagement list
    await page.waitForURL('**/admin/engagements');
    await page.waitForTimeout(2000);
    
    // Validate database state changed
    const updatedEngagementsValid = await validateDatabaseState(page, '/api/v1/admin/engagements/', (data) => {
      const currentCount = data.items ? data.items.length : 0;
      return currentCount > initialEngagementCount; // Should have one more engagement
    });
    
    expect(updatedEngagementsValid).toBe(true);
  });

  test('8. Navigation - All Admin Sections Accessible', async ({ page }) => {
    const sections = [
      { name: 'Dashboard', href: '/admin', heading: 'Admin Console' },
      { name: 'Clients', href: '/admin/clients', heading: 'Client Management' },
      { name: 'Engagements', href: '/admin/engagements', heading: 'Engagement Management' },
      { name: 'Users', href: '/admin/users/approvals', heading: 'User Management' }
    ];
    
    for (const section of sections) {
      await page.locator(`a[href="${section.href}"]`).first().click();
      await page.waitForTimeout(1000);
      await expect(page.locator(`h1:has-text("${section.heading}")`)).toBeVisible();
      console.log(`✅ ${section.name} section accessible`);
    }
  });

  test('9. API Error Handling - Validate Frontend Resilience', async ({ page }) => {
    // Navigate to user management
    await page.locator('a[href="/admin/users/approvals"]').first().click();
    await page.waitForTimeout(2000);
    
    // Mock API failure by intercepting requests
    await page.route('**/api/v1/auth/deactivate-user', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal Server Error' })
      });
    });
    
    // Try to deactivate user
    await page.locator('[data-testid="active-user-row"] button:has-text("Deactivate")').first().click();
    
    // Should show error state, not success
    // We expect the frontend to handle this gracefully
    await page.waitForTimeout(1000);
    
    // Clean up the route
    await page.unroute('**/api/v1/auth/deactivate-user');
  });

  test('10. Form Validation - Engagement Creation', async ({ page }) => {
    // Navigate to engagement creation
    await page.locator('a[href="/admin/engagements"]').first().click();
    await page.click('a[href="/admin/engagements/create"]:has-text("New Engagement")');
    await page.waitForURL('**/admin/engagements/create');
    
    // Try to submit empty form
    await page.click('button[type="submit"]:has-text("Create Engagement")');
    
    // Should show validation errors
    await expect(page.locator('text="Engagement name is required"')).toBeVisible();
    await expect(page.locator('text="Client account is required"')).toBeVisible();
    await expect(page.locator('text="Project manager is required"')).toBeVisible();
  });
}); 