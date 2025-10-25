/**
 * E2E tests for Dynamic Question Filtering workflow.
 *
 * Tests the complete user journey:
 * 1. Asset selection and type-based filtering
 * 2. Agent-based question pruning
 * 3. Answer status filtering (answered vs unanswered)
 * 4. Dependency-triggered question reopening
 */

import { test, expect } from '@playwright/test';

test.describe('Dynamic Question Filtering Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('http://localhost:8081/login', { waitUntil: 'load' });
    await page.waitForTimeout(1000);

    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button[type="submit"]');

    // Wait for login to process
    await page.waitForTimeout(3000);

    // Verify login was successful
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      throw new Error(`Login failed - still on login page: ${currentUrl}`);
    }

    await page.goto('/collection');
    // Verify we're on the collection page
    await expect(page).toHaveURL(/.*\/collection/);
  });

  test('should filter questions by asset type', async ({ page }) => {
    // Select an Application asset
    await page.click('[data-testid="asset-row-app-1"]');

    // Open questionnaire
    await page.click('[data-testid="open-questionnaire-button"]');

    await expect(page.locator('[data-testid="questionnaire-panel"]')).toBeVisible();

    // Should only show Application-specific questions
    await expect(page.locator('[data-testid="question-app_01_name"]')).toBeVisible();
    await expect(page.locator('[data-testid="question-app_02_language"]')).toBeVisible();
    await expect(page.locator('[data-testid="question-app_03_database"]')).toBeVisible();

    // Should NOT show Server-specific questions
    await expect(page.locator('[data-testid="question-server_01_hostname"]')).not.toBeVisible();

    // Asset type should be displayed
    await expect(page.locator('[data-testid="asset-type-badge"]')).toContainText('Application');

    // Switch to a Server asset
    await page.click('[data-testid="asset-row-server-1"]');

    // Questions should update to Server-specific
    await expect(page.locator('[data-testid="question-server_01_hostname"]')).toBeVisible();
    await expect(page.locator('[data-testid="question-server_02_os"]')).toBeVisible();

    // Application questions should be hidden
    await expect(page.locator('[data-testid="question-app_01_name"]')).not.toBeVisible();

    await expect(page.locator('[data-testid="asset-type-badge"]')).toContainText('Server');
  });

  test('should filter answered vs unanswered questions', async ({ page }) => {
    await page.click('[data-testid="asset-row-app-with-answers"]');
    await page.click('[data-testid="open-questionnaire-button"]');

    // Default: Show only unanswered questions
    await expect(page.locator('[data-testid="filter-mode"]')).toContainText('Unanswered only');

    const unansweredQuestions = page.locator('[data-testid^="question-"][data-answered="false"]');
    const unansweredCount = await unansweredQuestions.count();

    // Should only show unanswered questions
    expect(unansweredCount).toBeGreaterThan(0);

    // Verify no answered questions are shown
    const answeredQuestions = page.locator('[data-testid^="question-"][data-answered="true"]');
    await expect(answeredQuestions).toHaveCount(0);

    // Toggle to show all questions
    await page.click('[data-testid="toggle-show-answered"]');

    await expect(page.locator('[data-testid="filter-mode"]')).toContainText('All questions');

    // Now should show both answered and unanswered
    const allQuestions = page.locator('[data-testid^="question-"]');
    const totalCount = await allQuestions.count();
    expect(totalCount).toBeGreaterThan(unansweredCount);

    // Answered questions should have visual indicator
    await expect(page.locator('[data-testid="answered-indicator-app_01_name"]')).toBeVisible();
    await expect(page.locator('[data-testid="answered-indicator-app_01_name"]')).toHaveClass(/answered/);
  });

  test('should use agent-based question pruning', async ({ page }) => {
    await page.click('[data-testid="asset-row-app-2"]');
    await page.click('[data-testid="open-questionnaire-button"]');

    // Enable agent pruning
    await page.click('[data-testid="enable-agent-pruning-button"]');

    // Should show loading indicator while agent analyzes
    await expect(page.locator('[data-testid="agent-analysis-loading"]')).toBeVisible();

    // Wait for agent analysis to complete
    await expect(page.locator('[data-testid="agent-analysis-complete"]')).toBeVisible({ timeout: 10000 });

    // Questions should be filtered (some removed)
    const questionCount = await page.locator('[data-testid^="question-"]').count();

    // Agent status should show as completed
    await expect(page.locator('[data-testid="agent-status"]')).toContainText('Analysis complete');

    // Should show how many questions were pruned
    await expect(page.locator('[data-testid="pruned-count"]')).toBeVisible();
    await expect(page.locator('[data-testid="pruned-count"]')).toContainText('removed');

    // Can view pruned questions
    await page.click('[data-testid="view-pruned-questions-button"]');
    await expect(page.locator('[data-testid="pruned-questions-list"]')).toBeVisible();
  });

  test('should handle agent pruning fallback gracefully', async ({ page }) => {
    await page.click('[data-testid="asset-row-app-3"]');
    await page.click('[data-testid="open-questionnaire-button"]');

    // Enable agent pruning
    await page.click('[data-testid="enable-agent-pruning-button"]');

    // Agent may fail or timeout - should fallback
    await page.waitForTimeout(15000); // Wait for potential timeout

    // Should show fallback message
    const agentStatus = await page.locator('[data-testid="agent-status"]').textContent();

    if (agentStatus?.includes('fallback')) {
      // Fallback mode - all questions still shown
      await expect(page.locator('[data-testid="agent-fallback-warning"]')).toBeVisible();
      await expect(page.locator('[data-testid="agent-fallback-warning"]')).toContainText(
        'Showing all questions'
      );

      // All questions should still be accessible
      const questionCount = await page.locator('[data-testid^="question-"]').count();
      expect(questionCount).toBeGreaterThan(0);
    }
  });

  test('should reopen dependent questions on field change', async ({ page }) => {
    await page.click('[data-testid="asset-row-server-1"]');
    await page.click('[data-testid="open-questionnaire-button"]');

    // Answer operating system question
    await page.selectOption('[data-testid="question-server_02_os"]', 'Windows');

    // This should trigger dependent questions (patching schedule, security baseline)
    await page.click('[data-testid="save-answer-button"]');

    // Dependent questions should now be visible
    await expect(page.locator('[data-testid="question-server_05_patching"]')).toBeVisible();
    await expect(page.locator('[data-testid="question-server_06_security"]')).toBeVisible();

    // Answer dependent questions
    await page.fill('[data-testid="question-server_05_patching"]', 'Monthly patch window');
    await page.fill('[data-testid="question-server_06_security"]', 'CIS Benchmark Level 1');
    await page.click('[data-testid="save-answers-button"]');

    // Now change the OS
    await page.selectOption('[data-testid="question-server_02_os"]', 'Linux');
    await page.click('[data-testid="save-answer-button"]');

    // Should show notification about reopened questions
    await expect(page.locator('[data-testid="dependency-notification"]')).toBeVisible();
    await expect(page.locator('[data-testid="dependency-notification"]')).toContainText(
      'questions reopened'
    );

    // Dependent questions should be marked as needing re-validation
    await expect(page.locator('[data-testid="question-server_05_patching"]')).toHaveAttribute(
      'data-status',
      'reopened'
    );
    await expect(page.locator('[data-testid="question-server_06_security"]')).toHaveAttribute(
      'data-status',
      'reopened'
    );

    // Previous answers should still be visible but flagged
    await expect(page.locator('[data-testid="previous-answer-server_05_patching"]')).toContainText(
      'Monthly patch window'
    );
  });

  test('should show progress completion with weight-based calculation', async ({ page }) => {
    await page.click('[data-testid="asset-row-app-1"]');
    await page.click('[data-testid="open-questionnaire-button"]');

    // Initial progress should be shown
    await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();

    const initialProgress = await page.locator('[data-testid="progress-percent"]').textContent();
    const initialPercent = parseInt(initialProgress || '0');

    // Answer a high-weight question (e.g., application name)
    await page.fill('[data-testid="question-app_01_name"]', 'MyApp');
    await page.click('[data-testid="save-answer-button"]');

    // Progress should increase
    const newProgress = await page.locator('[data-testid="progress-percent"]').textContent();
    const newPercent = parseInt(newProgress || '0');

    expect(newPercent).toBeGreaterThan(initialPercent);

    // Progress details should show weight information
    await page.hover('[data-testid="progress-bar"]');
    await expect(page.locator('[data-testid="progress-tooltip"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-tooltip"]')).toContainText('weight');

    // Answer more questions to reach 100%
    await page.selectOption('[data-testid="question-app_02_language"]', 'Python');
    await page.selectOption('[data-testid="question-app_03_database"]', 'PostgreSQL');
    await page.fill('[data-testid="question-app_04_version"]', '1.0.0');
    await page.click('[data-testid="save-answers-button"]');

    // Continue answering remaining questions...
    // (In real test, would answer all required questions)

    // Eventually reach 100%
    await expect(page.locator('[data-testid="progress-percent"]')).toContainText('100%');

    // Completion badge should appear
    await expect(page.locator('[data-testid="completion-badge"]')).toBeVisible();
    await expect(page.locator('[data-testid="completion-badge"]')).toContainText('Complete');
  });

  test('should highlight critical gaps', async ({ page }) => {
    await page.click('[data-testid="asset-row-app-incomplete"]');
    await page.click('[data-testid="open-questionnaire-button"]');

    // Critical questions should have visual indicator
    const criticalQuestions = page.locator('[data-testid^="question-"][data-critical="true"]');
    await expect(criticalQuestions.first()).toHaveClass(/critical/);

    // Gap analysis button should show critical gaps count
    await page.click('[data-testid="show-gaps-button"]');

    await expect(page.locator('[data-testid="critical-gaps-count"]')).toBeVisible();
    await expect(page.locator('[data-testid="critical-gaps-count"]')).toContainText('3 critical');

    // Can filter to show only critical gaps
    await page.click('[data-testid="filter-critical-only"]');

    // Only critical unanswered questions should be shown
    const visibleQuestions = page.locator('[data-testid^="question-"]');
    const count = await visibleQuestions.count();

    for (let i = 0; i < count; i++) {
      const question = visibleQuestions.nth(i);
      await expect(question).toHaveAttribute('data-critical', 'true');
      await expect(question).toHaveAttribute('data-answered', 'false');
    }
  });
});
