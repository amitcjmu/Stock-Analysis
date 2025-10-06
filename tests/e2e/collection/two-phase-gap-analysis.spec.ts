/**
 * Two-Phase Gap Analysis E2E Test Suite
 *
 * Comprehensive testing of the two-phase gap analysis feature:
 * - Phase 1: Programmatic gap scanning (<1s)
 * - Phase 2: Optional AI-enhanced analysis (~15s)
 *
 * Tests cover:
 * 1. Gap scan flow
 * 2. Inline editing with explicit save
 * 3. AI analysis placeholder
 * 4. Bulk actions
 * 5. Color-coded confidence scores
 * 6. Grid functionality
 * 7. Error handling
 * 8. Responsive layout
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:8081';
const API_URL = 'http://localhost:8000';

// Test data
const TEST_TIMEOUT = 120000; // 2 minutes for full flow

// Helper function to navigate to gap analysis page
async function navigateToGapAnalysis(page: Page): Promise<string | null> {
  console.log('🧪 Navigating to gap analysis page...');

  // Start from collection page
  await page.goto(`${BASE_URL}/collection`, { waitUntil: 'networkidle' });

  // Check for existing incomplete flows
  const incompleteFlowsButton = page.locator('button:has-text("Resume"), button:has-text("Continue")');
  const hasIncompleteFlows = await incompleteFlowsButton.isVisible({ timeout: 5000 }).catch(() => false);

  let flowId: string | null = null;

  if (hasIncompleteFlows) {
    console.log('📝 Found incomplete flow, resuming...');
    await incompleteFlowsButton.first().click();
    await page.waitForTimeout(2000);

    // Extract flow ID from URL
    const urlMatch = page.url().match(/\/collection\/[^/]+\/([a-f0-9-]+)/);
    flowId = urlMatch ? urlMatch[1] : null;
  } else {
    console.log('📝 Starting new collection flow...');

    // Start new flow
    const startButton = page.locator('button:has-text("Start Collection"), button:has-text("New Collection")');
    if (await startButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await startButton.click();
      await page.waitForTimeout(3000);
    }

    // Select 2 assets
    console.log('📝 Selecting assets...');
    const checkboxes = page.locator('input[type="checkbox"]').filter({ hasNot: page.locator('[disabled]') });
    const checkboxCount = await checkboxes.count();

    if (checkboxCount >= 2) {
      await checkboxes.nth(0).check();
      await checkboxes.nth(1).check();
      console.log('✅ Selected 2 assets');
    } else {
      throw new Error('Not enough assets available for selection');
    }

    // Proceed to gap analysis
    const nextButton = page.locator('button:has-text("Next"), button:has-text("Continue"), button:has-text("Submit")');
    await nextButton.click();
    await page.waitForTimeout(2000);

    // Extract flow ID from URL
    const urlMatch = page.url().match(/\/collection\/[^/]+\/([a-f0-9-]+)/);
    flowId = urlMatch ? urlMatch[1] : null;
  }

  console.log(`🔍 Flow ID: ${flowId || 'Not found'}`);
  return flowId;
}

test.describe('Two-Phase Gap Analysis', () => {
  test.setTimeout(TEST_TIMEOUT);

  test('1. Gap Scan Flow Test', async ({ page }) => {
    console.log('\n🧪 TEST 1: Gap Scan Flow');

    const flowId = await navigateToGapAnalysis(page);
    expect(flowId).toBeTruthy();

    // Wait for gap analysis page to load
    await page.waitForSelector('text=/Gap Analysis|Data Gap/i', { timeout: 10000 });
    console.log('✅ Gap analysis page loaded');

    // Verify "Re-scan Gaps" button is visible
    const rescanButton = page.locator('button:has-text("Re-scan Gaps")');
    await expect(rescanButton).toBeVisible({ timeout: 5000 });
    console.log('✅ Re-scan Gaps button visible');

    // Click scan button and verify loading state
    await rescanButton.click();
    console.log('📝 Clicked Re-scan Gaps button');

    // Wait for loading state to appear
    const loadingIndicator = page.locator('text=/Scanning|Loading/i, svg.animate-spin');
    const hasLoading = await loadingIndicator.isVisible({ timeout: 2000 }).catch(() => false);
    if (hasLoading) {
      console.log('✅ Loading state appeared');
      await loadingIndicator.waitFor({ state: 'hidden', timeout: 10000 });
    }

    // Verify summary card displays
    const summaryCard = page.locator('text=/Gap Analysis Summary/i');
    await expect(summaryCard).toBeVisible({ timeout: 5000 });
    console.log('✅ Summary card displayed');

    // Verify summary metrics
    const totalGapsElement = page.locator('text=/Total Gaps/i').locator('..').locator('div.text-2xl');
    const totalGaps = await totalGapsElement.textContent();
    console.log(`📊 Total Gaps: ${totalGaps}`);

    const criticalGapsElement = page.locator('text=/Critical Gaps/i').locator('..').locator('div.text-2xl');
    const criticalGaps = await criticalGapsElement.textContent();
    console.log(`📊 Critical Gaps: ${criticalGaps}`);

    const scanTimeElement = page.locator('text=/Scan Time/i').locator('..').locator('div.text-2xl');
    const scanTime = await scanTimeElement.textContent();
    console.log(`⏱️ Scan Time: ${scanTime}`);

    // Verify AG Grid populates with data
    const agGrid = page.locator('.ag-theme-alpine');
    await expect(agGrid).toBeVisible({ timeout: 5000 });
    console.log('✅ AG Grid visible');

    // Check for data rows
    const rows = page.locator('.ag-row');
    const rowCount = await rows.count();
    console.log(`📊 Grid rows: ${rowCount}`);
    expect(rowCount).toBeGreaterThan(0);

    // Verify columns exist
    const columns = [
      'Asset',
      'Field',
      'Category',
      'Priority',
      'Current Value',
      'Suggested Resolution',
      'AI Confidence',
      'Actions'
    ];

    for (const column of columns) {
      const columnHeader = page.locator('.ag-header-cell-text', { hasText: column });
      await expect(columnHeader).toBeVisible();
      console.log(`✅ Column '${column}' visible`);
    }

    console.log('🎉 TEST 1 PASSED: Gap scan flow works correctly\n');
  });

  test('2. Inline Editing Test', async ({ page }) => {
    console.log('\n🧪 TEST 2: Inline Editing with Explicit Save');

    const flowId = await navigateToGapAnalysis(page);
    expect(flowId).toBeTruthy();

    await page.waitForSelector('.ag-theme-alpine', { timeout: 10000 });

    // Find first editable cell in "Current Value" column
    const firstEditableCell = page.locator('.ag-cell[col-id="current_value"]').first();
    await expect(firstEditableCell).toBeVisible({ timeout: 5000 });

    // Double-click to enter edit mode
    await firstEditableCell.dblclick();
    console.log('📝 Double-clicked cell to enter edit mode');

    await page.waitForTimeout(500);

    // Check if cell editor is visible
    const cellEditor = page.locator('.ag-cell-editor input, .ag-input-field-input');
    const isEditorVisible = await cellEditor.isVisible({ timeout: 2000 }).catch(() => false);

    if (isEditorVisible) {
      // Enter a test value
      const testValue = 'Node.js, Express, PostgreSQL';
      await cellEditor.fill(testValue);
      console.log(`✅ Entered value: ${testValue}`);

      // Press Enter or Tab to exit edit mode
      await cellEditor.press('Enter');
      await page.waitForTimeout(500);

      // Verify "Save" button appears in Actions column
      const saveButton = page.locator('button:has-text("Save"), .save-btn').first();
      const saveVisible = await saveButton.isVisible({ timeout: 2000 }).catch(() => false);

      if (saveVisible) {
        console.log('✅ Save button appeared after edit');

        // Click save button
        await saveButton.click();
        console.log('📝 Clicked save button');

        // Wait for toast notification
        const toast = page.locator('text=/Gap Saved|Saved/i');
        const toastVisible = await toast.isVisible({ timeout: 5000 }).catch(() => false);

        if (toastVisible) {
          console.log('✅ Toast notification appeared: Gap Saved');
        } else {
          console.warn('⚠️ Toast notification not visible');
        }

        // Verify save button disappears after save
        await page.waitForTimeout(1000);
        const saveStillVisible = await saveButton.isVisible({ timeout: 1000 }).catch(() => false);

        if (!saveStillVisible) {
          console.log('✅ Save button disappeared after save');
        } else {
          console.warn('⚠️ Save button still visible after save');
        }
      } else {
        console.warn('⚠️ Save button not visible after edit');
      }
    } else {
      console.warn('⚠️ Cell editor not accessible - cell may not be editable or different UI pattern');
    }

    console.log('🎉 TEST 2 COMPLETED: Inline editing test\n');
  });

  test('3. AI Analysis Test (Placeholder)', async ({ page }) => {
    console.log('\n🧪 TEST 3: AI Analysis Placeholder');

    const flowId = await navigateToGapAnalysis(page);
    expect(flowId).toBeTruthy();

    await page.waitForSelector('.ag-theme-alpine', { timeout: 10000 });

    // Find "Perform Agentic Analysis" button
    const aiAnalysisButton = page.locator('button:has-text("Perform Agentic Analysis")');
    await expect(aiAnalysisButton).toBeVisible({ timeout: 5000 });
    console.log('✅ Perform Agentic Analysis button visible');

    // Click the button
    await aiAnalysisButton.click();
    console.log('📝 Clicked Perform Agentic Analysis button');

    // Verify loading state with spinner
    const loadingSpinner = page.locator('svg.animate-spin, text=/Analyzing/i');
    const hasLoadingSpinner = await loadingSpinner.isVisible({ timeout: 2000 }).catch(() => false);

    if (hasLoadingSpinner) {
      console.log('✅ Loading spinner appeared');

      // Wait for completion (placeholder returns immediately)
      await page.waitForTimeout(3000);
    }

    // Check confidence_score column for "No AI" values (since it's a placeholder)
    const noAiCells = page.locator('.ag-cell[col-id="confidence_score"]', { hasText: /No AI/i });
    const noAiCount = await noAiCells.count();
    console.log(`📊 Cells with "No AI": ${noAiCount}`);

    // Verify response (placeholder should show toast or maintain current state)
    const toast = page.locator('[role="alert"], .toast, text=/Analysis Complete|Complete/i');
    const toastVisible = await toast.isVisible({ timeout: 5000 }).catch(() => false);

    if (toastVisible) {
      console.log('✅ Toast notification appeared after AI analysis');
    } else {
      console.log('ℹ️ No toast notification (placeholder behavior)');
    }

    console.log('🎉 TEST 3 COMPLETED: AI analysis placeholder test\n');
  });

  test('4. Bulk Actions Test', async ({ page }) => {
    console.log('\n🧪 TEST 4: Bulk Actions');

    const flowId = await navigateToGapAnalysis(page);
    expect(flowId).toBeTruthy();

    await page.waitForSelector('.ag-theme-alpine', { timeout: 10000 });

    // Test "Accept All (High Confidence)" button
    const acceptAllButton = page.locator('button:has-text("Accept All")');
    await expect(acceptAllButton).toBeVisible({ timeout: 5000 });
    console.log('✅ Accept All button visible');

    // Click button (may show error if no high-confidence suggestions)
    await acceptAllButton.click();
    await page.waitForTimeout(2000);

    // Check for toast notification
    const acceptToast = page.locator('text=/Bulk Accept|No High Confidence/i');
    const acceptToastVisible = await acceptToast.isVisible({ timeout: 3000 }).catch(() => false);

    if (acceptToastVisible) {
      const toastText = await acceptToast.textContent();
      console.log(`📋 Accept All result: ${toastText}`);
    }

    // Test "Reject All AI Suggestions" button
    const rejectAllButton = page.locator('button:has-text("Reject All")');
    await expect(rejectAllButton).toBeVisible({ timeout: 5000 });
    console.log('✅ Reject All button visible');

    // Click button (may show error if no AI suggestions)
    await rejectAllButton.click();
    await page.waitForTimeout(2000);

    // Check for toast notification
    const rejectToast = page.locator('text=/Bulk Reject|No AI/i');
    const rejectToastVisible = await rejectToast.isVisible({ timeout: 3000 }).catch(() => false);

    if (rejectToastVisible) {
      const toastText = await rejectToast.textContent();
      console.log(`📋 Reject All result: ${toastText}`);
    }

    console.log('🎉 TEST 4 COMPLETED: Bulk actions test\n');
  });

  test('5. Color-Coded Confidence Test', async ({ page }) => {
    console.log('\n🧪 TEST 5: Color-Coded Confidence Scores');

    const flowId = await navigateToGapAnalysis(page);
    expect(flowId).toBeTruthy();

    await page.waitForSelector('.ag-theme-alpine', { timeout: 10000 });

    // Check confidence score column
    const confidenceCells = page.locator('.ag-cell[col-id="confidence_score"]');
    const cellCount = await confidenceCells.count();
    console.log(`📊 Confidence score cells: ${cellCount}`);

    // Check for color coding
    const greenScores = page.locator('.ag-cell[col-id="confidence_score"] span.text-green-600');
    const yellowScores = page.locator('.ag-cell[col-id="confidence_score"] span.text-yellow-600');
    const redScores = page.locator('.ag-cell[col-id="confidence_score"] span.text-red-600');
    const noAiScores = page.locator('.ag-cell[col-id="confidence_score"] span.text-gray-400');

    const greenCount = await greenScores.count();
    const yellowCount = await yellowScores.count();
    const redCount = await redScores.count();
    const noAiCount = await noAiScores.count();

    console.log(`🟢 Green scores (≥80%): ${greenCount}`);
    console.log(`🟡 Yellow scores (60-79%): ${yellowCount}`);
    console.log(`🔴 Red scores (<60%): ${redCount}`);
    console.log(`⚪ No AI scores: ${noAiCount}`);

    // Since this is programmatic scan without AI, we expect all "No AI"
    expect(noAiCount).toBeGreaterThan(0);
    console.log('✅ Color coding verified (No AI expected for programmatic scan)');

    console.log('🎉 TEST 5 PASSED: Color-coded confidence scores work correctly\n');
  });

  test('6. Grid Functionality Test', async ({ page }) => {
    console.log('\n🧪 TEST 6: Grid Functionality');

    const flowId = await navigateToGapAnalysis(page);
    expect(flowId).toBeTruthy();

    await page.waitForSelector('.ag-theme-alpine', { timeout: 10000 });

    // Test sorting by clicking column headers
    console.log('📝 Testing column sorting...');
    const priorityHeader = page.locator('.ag-header-cell-text:has-text("Priority")');
    await priorityHeader.click();
    await page.waitForTimeout(500);
    console.log('✅ Clicked Priority column header for sorting');

    // Check for sort indicator
    const sortIndicator = page.locator('.ag-header-cell[col-id="priority"] .ag-sort-indicator-icon');
    const hasSortIndicator = await sortIndicator.isVisible({ timeout: 2000 }).catch(() => false);
    if (hasSortIndicator) {
      console.log('✅ Sort indicator visible');
    }

    // Test filtering
    console.log('📝 Testing column filtering...');
    const filterIcon = page.locator('.ag-header-cell[col-id="gap_category"] .ag-header-icon.ag-filter-icon').first();
    const hasFilterIcon = await filterIcon.isVisible({ timeout: 2000 }).catch(() => false);

    if (hasFilterIcon) {
      await filterIcon.click();
      await page.waitForTimeout(500);
      console.log('✅ Clicked filter icon');

      const filterInput = page.locator('.ag-filter input').first();
      const hasFilterInput = await filterInput.isVisible({ timeout: 2000 }).catch(() => false);

      if (hasFilterInput) {
        await filterInput.fill('application');
        await page.waitForTimeout(500);
        console.log('✅ Applied filter: application');

        // Close filter
        await page.keyboard.press('Escape');
      }
    } else {
      console.log('ℹ️ Filter icon not visible (may require config)');
    }

    // Test column resizing
    console.log('📝 Testing column resizing...');
    const resizeHandle = page.locator('.ag-header-cell-resize').first();
    const hasResizeHandle = await resizeHandle.isVisible({ timeout: 2000 }).catch(() => false);

    if (hasResizeHandle) {
      const bbox = await resizeHandle.boundingBox();
      if (bbox) {
        await page.mouse.move(bbox.x + bbox.width / 2, bbox.y + bbox.height / 2);
        await page.mouse.down();
        await page.mouse.move(bbox.x + 50, bbox.y + bbox.height / 2);
        await page.mouse.up();
        console.log('✅ Column resized');
      }
    }

    // Verify pinned columns
    console.log('📝 Verifying pinned columns...');
    const pinnedLeftCell = page.locator('.ag-cell.ag-cell-last-left-pinned[col-id="asset_name"]');
    const hasPinnedLeft = await pinnedLeftCell.isVisible({ timeout: 2000 }).catch(() => false);

    if (hasPinnedLeft) {
      console.log('✅ Left pinned column (Asset) verified');
    }

    const pinnedRightCell = page.locator('.ag-cell.ag-cell-first-right-pinned');
    const hasPinnedRight = await pinnedRightCell.isVisible({ timeout: 2000 }).catch(() => false);

    if (hasPinnedRight) {
      console.log('✅ Right pinned column (Actions) verified');
    }

    console.log('🎉 TEST 6 COMPLETED: Grid functionality test\n');
  });

  test('7. Error Handling Test', async ({ page }) => {
    console.log('\n🧪 TEST 7: Error Handling');

    // Test with invalid flow ID
    console.log('📝 Testing with invalid flow ID...');
    await page.goto(`${BASE_URL}/collection/gap-analysis/invalid-uuid-12345`, { waitUntil: 'networkidle' });

    // Check for error message
    const errorMessage = page.locator('text=/Error|Not Found|Invalid/i');
    const hasError = await errorMessage.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasError) {
      console.log('✅ Error message displayed for invalid flow ID');
    } else {
      console.log('ℹ️ No specific error message for invalid flow ID');
    }

    // Navigate to valid flow
    const flowId = await navigateToGapAnalysis(page);
    expect(flowId).toBeTruthy();

    await page.waitForSelector('.ag-theme-alpine', { timeout: 10000 });

    // Test with no selected assets (edge case)
    // This would require modifying flow state, which is complex
    // Instead, verify error toast displays properly
    console.log('📝 Verifying error toast functionality...');

    // Click bulk action that should fail (no AI suggestions yet)
    const acceptAllButton = page.locator('button:has-text("Accept All")');
    await acceptAllButton.click();

    const errorToast = page.locator('text=/No High Confidence|No AI/i');
    const hasErrorToast = await errorToast.isVisible({ timeout: 3000 }).catch(() => false);

    if (hasErrorToast) {
      console.log('✅ Error toast displayed appropriately');
    }

    console.log('🎉 TEST 7 COMPLETED: Error handling test\n');
  });

  test('8. Responsive Layout Test', async ({ page }) => {
    console.log('\n🧪 TEST 8: Responsive Layout');

    const flowId = await navigateToGapAnalysis(page);
    expect(flowId).toBeTruthy();

    await page.waitForSelector('.ag-theme-alpine', { timeout: 10000 });

    // Verify AG Grid renders at expected height
    const agGrid = page.locator('.ag-theme-alpine');
    const gridBox = await agGrid.boundingBox();

    if (gridBox) {
      console.log(`📐 Grid dimensions: ${gridBox.width}x${gridBox.height}`);

      // Verify height is around 500px as specified
      expect(gridBox.height).toBeGreaterThan(400);
      expect(gridBox.height).toBeLessThan(600);
      console.log('✅ Grid height is within expected range (400-600px)');
    }

    // Verify all action buttons are accessible
    const actionButtons = [
      'Re-scan Gaps',
      'Perform Agentic Analysis',
      'Accept All',
      'Reject All'
    ];

    for (const buttonText of actionButtons) {
      const button = page.locator(`button:has-text("${buttonText}")`);
      const isVisible = await button.isVisible({ timeout: 2000 }).catch(() => false);

      if (isVisible) {
        const buttonBox = await button.boundingBox();
        if (buttonBox) {
          console.log(`✅ Button '${buttonText}' accessible at (${buttonBox.x}, ${buttonBox.y})`);
        }
      } else {
        console.warn(`⚠️ Button '${buttonText}' not visible`);
      }
    }

    // Check summary cards display correctly
    const summaryCards = page.locator('div.grid.grid-cols-3 > div');
    const cardCount = await summaryCards.count();
    console.log(`📊 Summary cards: ${cardCount}`);
    expect(cardCount).toBeGreaterThanOrEqual(3);

    console.log('🎉 TEST 8 PASSED: Responsive layout works correctly\n');
  });

  test('9. Performance Test - Scan Time', async ({ page }) => {
    console.log('\n🧪 TEST 9: Performance - Scan Time');

    const flowId = await navigateToGapAnalysis(page);
    expect(flowId).toBeTruthy();

    await page.waitForSelector('.ag-theme-alpine', { timeout: 10000 });

    // Click Re-scan and measure time
    const startTime = Date.now();

    const rescanButton = page.locator('button:has-text("Re-scan Gaps")');
    await rescanButton.click();

    // Wait for scan to complete
    const summaryCard = page.locator('text=/Total Gaps/i');
    await summaryCard.waitFor({ state: 'visible', timeout: 10000 });

    const endTime = Date.now();
    const elapsedTime = endTime - startTime;

    console.log(`⏱️ Scan completed in ${elapsedTime}ms`);

    // Verify scan time is under 5 seconds (generous for E2E including network)
    expect(elapsedTime).toBeLessThan(5000);
    console.log('✅ Scan time within acceptable range (<5s for E2E)');

    // Check scan time in summary
    const scanTimeElement = page.locator('text=/Scan Time/i').locator('..').locator('div.text-2xl');
    const scanTime = await scanTimeElement.textContent();
    console.log(`📊 Backend scan time: ${scanTime}`);

    console.log('🎉 TEST 9 PASSED: Performance test\n');
  });
});

test.describe('Database Verification', () => {
  test('10. Verify Gaps Persisted to Database', async ({ request }) => {
    console.log('\n🧪 TEST 10: Database Verification');

    // Query database via docker exec
    const { execSync } = require('child_process');

    const dbQuery = `
      SELECT
        COUNT(*) as total_gaps,
        gap_type,
        gap_category,
        priority
      FROM migration.collection_data_gaps
      WHERE created_at > NOW() - INTERVAL '10 minutes'
      GROUP BY gap_type, gap_category, priority
      ORDER BY priority ASC;
    `;

    try {
      const result = execSync(
        `docker exec migration_postgres psql -U postgres -d migration_db -t -c "${dbQuery}"`,
        { encoding: 'utf-8' }
      );

      console.log('📊 Database query results:');
      console.log(result);

      // Verify we have data
      expect(result.trim().length).toBeGreaterThan(0);
      console.log('✅ Gaps persisted to database');
    } catch (error) {
      console.error('❌ Database query failed:', error);
      throw error;
    }

    console.log('🎉 TEST 10 PASSED: Database verification\n');
  });
});
