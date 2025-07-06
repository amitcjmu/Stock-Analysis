import { test, expect, Page } from '@playwright/test';

// Test data fixtures
const testFlowData = {
  name: 'E2E Test Flow',
  client_account_id: 'test-client-e2e',
  engagement_id: 'test-engagement-e2e'
};

const mockFieldMappings = [
  {
    id: 'mapping-test-1',
    sourceField: 'hostname',
    targetAttribute: 'device_name',
    confidence: 0.85,
    status: 'pending'
  },
  {
    id: 'mapping-test-2',
    sourceField: 'ip_address',
    targetAttribute: 'primary_ip',
    confidence: 0.95,
    status: 'pending'
  },
  {
    id: 'mapping-test-3',
    sourceField: 'os_version',
    targetAttribute: 'operating_system',
    confidence: 0.78,
    status: 'pending'
  }
];

test.describe('Field Mapping Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses for consistent testing
    await page.route('**/api/v1/flows/field-mappings**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          mappings: mockFieldMappings
        })
      });
    });

    await page.route('**/api/v1/flows/clarifications**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          page_data: {
            pending_questions: []
          }
        })
      });
    });

    await page.route('**/api/v1/flows/active**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          flows: [
            {
              flow_id: 'test-flow-123',
              name: 'Test Flow',
              flow_type: 'discovery',
              status: 'attribute_mapping',
              data_import_id: 'import-123'
            }
          ]
        })
      });
    });

    await page.route('**/api/v1/flows/test-flow-123/status**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          flow_id: 'test-flow-123',
          flow_type: 'discovery',
          status: 'attribute_mapping',
          data_import_id: 'import-123',
          field_mapping: {
            mappings: {
              hostname: {
                source_column: 'hostname',
                asset_field: 'device_name',
                confidence: 85
              }
            },
            progress: {
              total: 3,
              mapped: 0,
              critical_mapped: 0
            }
          },
          phases: {
            attribute_mapping: false
          }
        })
      });
    });

    // Navigate to field mapping page
    await page.goto('/discovery/attribute-mapping');
    
    // Wait for initial load
    await page.waitForLoadState('networkidle');
  });
  
  test('should complete field mapping workflow', async ({ page }) => {
    // Wait for mappings to load
    await page.waitForSelector('[data-testid="field-mapping-table"]', { timeout: 10000 });
    
    // Verify mappings are displayed
    const mappingRows = page.locator('[data-testid^="mapping-row-"]');
    await expect(mappingRows).toHaveCount(3);
    
    // Test dropdown interaction for first mapping
    const firstDropdown = page.locator('[data-testid="mapping-dropdown-mapping-test-1"]');
    await firstDropdown.click();
    
    // Verify dropdown menu appears
    const dropdownMenu = page.locator('.dropdown-menu').first();
    await expect(dropdownMenu).toBeVisible();
    
    // Click outside to close dropdown
    await page.click('body', { position: { x: 10, y: 10 } });
    await expect(dropdownMenu).not.toBeVisible();
    
    // Mock approval API call
    await page.route('**/api/v1/data-import/mappings/approve-by-field**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Mapping approved successfully'
        })
      });
    });
    
    // Approve a mapping
    const approveButton = page.locator('[data-testid="approve-mapping-mapping-test-1"]');
    await approveButton.click();
    
    // Wait for success feedback
    await expect(page.locator('[data-testid="success-toast"]')).toBeVisible({ timeout: 5000 });
    
    // Verify mapping status updated (would need optimistic update in real app)
    // This test assumes the UI updates optimistically
    const approvedMapping = page.locator('[data-testid="mapping-row-mapping-test-1"]');
    await expect(approvedMapping).toHaveAttribute('data-status', 'approved');
  });
  
  test('should handle reject mapping workflow', async ({ page }) => {
    // Wait for mappings to load
    await page.waitForSelector('[data-testid="field-mapping-table"]');
    
    // Mock rejection API call
    await page.route('**/api/v1/data-import/mappings/reject-by-field**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Mapping rejected successfully'
        })
      });
    });
    
    // Click reject button
    const rejectButton = page.locator('[data-testid="reject-mapping-mapping-test-2"]');
    await rejectButton.click();
    
    // Fill in rejection reason if modal appears
    const rejectionModal = page.locator('[data-testid="rejection-reason-modal"]');
    if (await rejectionModal.isVisible()) {
      await page.fill('[data-testid="rejection-reason-input"]', 'Incorrect field mapping');
      await page.click('[data-testid="confirm-rejection"]');
    }
    
    // Wait for success feedback
    await expect(page.locator('[data-testid="success-toast"]')).toBeVisible({ timeout: 5000 });
  });
  
  test('should handle errors gracefully', async ({ page }) => {
    // Wait for mappings to load
    await page.waitForSelector('[data-testid="field-mapping-table"]');
    
    // Mock network failure for approval
    await page.route('**/api/v1/data-import/mappings/approve-by-field**', async route => {
      await route.abort('failed');
    });
    
    // Try to approve a mapping
    const approveButton = page.locator('[data-testid="approve-mapping-mapping-test-1"]');
    await approveButton.click();
    
    // Verify error toast appears
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible({ timeout: 5000 });
    
    // Verify mapping status didn't change
    const mappingRow = page.locator('[data-testid="mapping-row-mapping-test-1"]');
    await expect(mappingRow).toHaveAttribute('data-status', 'pending');
  });
  
  test('should handle loading states correctly', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/v1/discovery/field-mappings**', async route => {
      // Delay response by 2 seconds
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          mappings: mockFieldMappings
        })
      });
    });
    
    // Navigate to page
    await page.goto('/discovery/attribute-mapping');
    
    // Verify loading state is shown
    await expect(page.locator('[data-testid="field-mapping-loading"]')).toBeVisible();
    
    // Wait for loading to complete
    await page.waitForSelector('[data-testid="field-mapping-table"]', { timeout: 5000 });
    
    // Verify loading state is hidden
    await expect(page.locator('[data-testid="field-mapping-loading"]')).not.toBeVisible();
  });
  
  test('should display mapping confidence scores', async ({ page }) => {
    // Wait for mappings to load
    await page.waitForSelector('[data-testid="field-mapping-table"]');
    
    // Check confidence scores are displayed
    const confidenceScore1 = page.locator('[data-testid="confidence-score-mapping-test-1"]');
    await expect(confidenceScore1).toContainText('85%');
    
    const confidenceScore2 = page.locator('[data-testid="confidence-score-mapping-test-2"]');
    await expect(confidenceScore2).toContainText('95%');
    
    const confidenceScore3 = page.locator('[data-testid="confidence-score-mapping-test-3"]');
    await expect(confidenceScore3).toContainText('78%');
  });
  
  test('should handle mapping change workflow', async ({ page }) => {
    // Wait for mappings to load
    await page.waitForSelector('[data-testid="field-mapping-table"]');
    
    // Open dropdown for first mapping
    const dropdown = page.locator('[data-testid="mapping-dropdown-mapping-test-1"]');
    await dropdown.click();
    
    // Select different target field
    const newOption = page.locator('[data-testid="dropdown-option-system_name"]');
    await newOption.click();
    
    // Mock update API call
    await page.route('**/api/v1/data-import/mappings/mapping-test-1**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Mapping updated successfully'
        })
      });
    });
    
    // Verify update was processed
    await expect(page.locator('[data-testid="success-toast"]')).toBeVisible({ timeout: 5000 });
  });
  
  test('should show progress tracking', async ({ page }) => {
    // Wait for page to load
    await page.waitForSelector('[data-testid="mapping-progress-dashboard"]');
    
    // Check progress indicators
    const totalMappings = page.locator('[data-testid="total-mappings-count"]');
    await expect(totalMappings).toContainText('3');
    
    const pendingMappings = page.locator('[data-testid="pending-mappings-count"]');
    await expect(pendingMappings).toContainText('3');
    
    const approvedMappings = page.locator('[data-testid="approved-mappings-count"]');
    await expect(approvedMappings).toContainText('0');
  });
  
  test('should handle bulk actions', async ({ page }) => {
    // Wait for mappings to load
    await page.waitForSelector('[data-testid="field-mapping-table"]');
    
    // Select multiple mappings
    await page.check('[data-testid="select-mapping-mapping-test-1"]');
    await page.check('[data-testid="select-mapping-mapping-test-2"]');
    
    // Verify bulk actions are enabled
    const bulkApproveButton = page.locator('[data-testid="bulk-approve-button"]');
    await expect(bulkApproveButton).toBeEnabled();
    
    // Mock bulk approval API
    await page.route('**/api/v1/data-import/mappings/bulk-approve**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          approved_count: 2,
          message: '2 mappings approved successfully'
        })
      });
    });
    
    // Execute bulk approval
    await bulkApproveButton.click();
    
    // Confirm in dialog if present
    const confirmButton = page.locator('[data-testid="confirm-bulk-action"]');
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
    }
    
    // Verify success feedback
    await expect(page.locator('[data-testid="success-toast"]')).toBeVisible({ timeout: 5000 });
  });
  
  test('should navigate to next phase when ready', async ({ page }) => {
    // Wait for mappings to load
    await page.waitForSelector('[data-testid="field-mapping-table"]');
    
    // Mock all mappings as approved for continuation
    await page.route('**/api/v1/flows/test-flow-123/status**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          flow_id: 'test-flow-123',
          flow_type: 'discovery',
          status: 'attribute_mapping',
          field_mapping: {
            progress: {
              total: 3,
              mapped: 3,
              critical_mapped: 3
            }
          },
          phases: {
            attribute_mapping: true // Phase completed
          }
        })
      });
    });
    
    // Refresh page to get updated state
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Check if continue button is enabled
    const continueButton = page.locator('[data-testid="continue-to-data-cleansing"]');
    await expect(continueButton).toBeEnabled({ timeout: 10000 });
    
    // Click continue button
    await continueButton.click();
    
    // Verify navigation to next phase
    await expect(page).toHaveURL(/.*data-cleansing.*/);
  });
  
  test('should display field mapping insights', async ({ page }) => {
    // Wait for page to load
    await page.waitForSelector('[data-testid="field-mapping-insights"]');
    
    // Check AI insights are displayed
    const aiInsights = page.locator('[data-testid="ai-mapping-insights"]');
    await expect(aiInsights).toBeVisible();
    
    // Check critical attributes section
    const criticalAttributes = page.locator('[data-testid="critical-attributes-section"]');
    await expect(criticalAttributes).toBeVisible();
    
    // Verify quality metrics
    const qualityMetrics = page.locator('[data-testid="mapping-quality-metrics"]');
    await expect(qualityMetrics).toBeVisible();
  });
});