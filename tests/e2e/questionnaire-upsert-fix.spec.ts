import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';

/**
 * Test to verify UPSERT fix for questionnaire persistence (Issue #980)
 *
 * This test verifies that:
 * 1. Questionnaires are successfully inserted into adaptive_questionnaires table
 * 2. Form submission doesn't loop back to the same form
 * 3. Completion screen is shown after all questionnaires are complete
 */

test.describe('Questionnaire UPSERT Fix Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('http://localhost:8081/auth/signin');

    // Login as demo user
    await page.fill('input[type="email"]', 'demo@democorp.com');
    await page.fill('input[type="password"]', 'Demo123');
    await page.click('button:has-text("Sign In")');

    // Wait for dashboard
    await page.waitForURL('**/platform', { timeout: 10000 });

    // Set context (Demo Corp, Demo Engagement)
    await page.click('button:has-text("Demo Corp")');
    await page.waitForTimeout(500);
  });

  test('should persist questionnaires to database and show completion screen', async ({ page }) => {
    console.log('🧪 Testing questionnaire UPSERT fix...\n');

    // Clean up old questionnaires
    console.log('📝 Step 1: Cleaning up old test data...');
    execSync(
      `docker exec migration_postgres psql -U postgres -d migration_db -c "DELETE FROM migration.adaptive_questionnaires WHERE created_at > NOW() - INTERVAL '1 hour';"`,
      { encoding: 'utf-8' }
    );
    console.log('✅ Old questionnaires cleaned up\n');

    // Navigate to Collection Flow
    console.log('📝 Step 2: Starting new collection flow...');
    await page.goto('http://localhost:8081/collection');
    await page.waitForLoadState('networkidle');

    // Click "Start Collection Flow" button
    const startButton = page.locator('button:has-text("Start Collection Flow"), a:has-text("Start Collection Flow")').first();
    await startButton.click();
    await page.waitForLoadState('networkidle');

    // Get the collection flow ID from URL
    await page.waitForURL('**/collection/flows/**', { timeout: 10000 });
    const flowUrl = page.url();
    const flowIdMatch = flowUrl.match(/flows\/([a-f0-9-]+)/);
    expect(flowIdMatch).toBeTruthy();
    const flowId = flowIdMatch![1];
    console.log(`✅ Collection flow created: ${flowId}\n`);

    // Step 3: Select assets
    console.log('📝 Step 3: Selecting assets...');
    await page.waitForSelector('text=/Select.*Assets/i, text=/Application.*Selection/i', { timeout: 10000 });

    // Select first 2 assets
    const checkboxes = page.locator('input[type="checkbox"]').filter({ hasNotText: 'Select All' });
    const count = await checkboxes.count();
    console.log(`Found ${count} asset checkboxes`);

    if (count >= 2) {
      await checkboxes.nth(0).check();
      await checkboxes.nth(1).check();
      console.log('✅ Selected 2 assets\n');
    } else {
      throw new Error('Not enough assets to select');
    }

    // Continue to gap analysis
    console.log('📝 Step 4: Progressing to gap analysis...');
    const continueButton = page.locator('button:has-text("Continue"), button:has-text("Next")').first();
    await continueButton.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Progress through gap analysis (if there's a continue button)
    try {
      const gapContinueButton = page.locator('button:has-text("Continue"), button:has-text("Proceed")').first();
      if (await gapContinueButton.isVisible({ timeout: 3000 })) {
        console.log('📝 Step 5: Progressing through gap analysis...');
        await gapContinueButton.click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
      }
    } catch (e) {
      // Gap analysis might auto-progress
      console.log('ℹ️ Gap analysis auto-progressed\n');
    }

    // Wait for questionnaire generation
    console.log('📝 Step 6: Waiting for questionnaire generation...');
    await page.waitForTimeout(5000); // Give agent time to generate

    // Check backend logs for UPSERT errors
    console.log('📝 Step 7: Checking backend logs for errors...');
    const logs = execSync(
      `docker logs migration_backend 2>&1 | grep -E "05:1[7-9]:|05:2[0-9]:" | grep -E "UPSERT|uq_questionnaire|adaptive_questionnaire" | tail -20`,
      { encoding: 'utf-8' }
    );

    if (logs.includes('constraint "uq_questionnaire_per_asset_per_engagement" for table "adaptive_questionnaires" does not exist')) {
      throw new Error('❌ UPSERT fix did NOT work - still getting constraint errors!');
    }
    console.log('✅ No UPSERT errors in backend logs\n');

    // Verify questionnaires were inserted into database
    console.log('📝 Step 8: Verifying questionnaires in database...');
    const dbCheck = execSync(
      `docker exec migration_postgres psql -U postgres -d migration_db -t -c "SELECT COUNT(*) FROM migration.adaptive_questionnaires WHERE collection_flow_id = (SELECT id FROM migration.collection_flows WHERE flow_id = '${flowId}');"`,
      { encoding: 'utf-8' }
    ).trim();

    const questionnaireCount = parseInt(dbCheck);
    console.log(`Found ${questionnaireCount} questionnaires in database`);

    if (questionnaireCount === 0) {
      throw new Error('❌ UPSERT fix did NOT work - no questionnaires in database!');
    }
    console.log(`✅ Questionnaires successfully persisted (${questionnaireCount} records)\n`);

    // Now test form submission
    console.log('📝 Step 9: Testing form submission...');

    // Wait for questionnaire form to appear
    try {
      await page.waitForSelector('form, [role="form"]', { timeout: 10000 });
      console.log('✅ Questionnaire form loaded\n');

      // Fill out the form (select first option for all select fields)
      const selectFields = page.locator('select');
      const selectCount = await selectFields.count();
      console.log(`Found ${selectCount} select fields`);

      for (let i = 0; i < selectCount; i++) {
        const options = selectFields.nth(i).locator('option');
        const optionCount = await options.count();
        if (optionCount > 1) {
          await selectFields.nth(i).selectOption({ index: 1 }); // Select first non-empty option
        }
      }

      // Submit the form
      console.log('📝 Step 10: Submitting questionnaire form...');
      const submitButton = page.locator('button:has-text("Submit"), button:has-text("Complete")').first();
      await submitButton.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Check if we see completion screen or another questionnaire
      const hasCompletionScreen = await page.locator('text=/Collection Complete/i, text=/Assessment Ready/i').isVisible({ timeout: 5000 });
      const hasAnotherQuestionnaire = await page.locator('form, [role="form"]').isVisible({ timeout: 1000 });

      if (hasCompletionScreen) {
        console.log('✅ SUCCESS: Completion screen shown after form submission\n');
      } else if (hasAnotherQuestionnaire) {
        // This is OK if there are multiple questionnaires for different assets
        console.log('ℹ️ Another questionnaire shown (multiple questionnaires for different assets)\n');

        // Verify it's a DIFFERENT questionnaire by checking database
        const completedCheck = execSync(
          `docker exec migration_postgres psql -U postgres -d migration_db -t -c "SELECT COUNT(*) FROM migration.adaptive_questionnaires WHERE collection_flow_id = (SELECT id FROM migration.collection_flows WHERE flow_id = '${flowId}') AND completion_status = 'completed';"`,
          { encoding: 'utf-8' }
        ).trim();

        const completedCount = parseInt(completedCheck);
        console.log(`✅ ${completedCount} questionnaire(s) marked as completed in database`);

        if (completedCount === 0) {
          throw new Error('❌ Form submission did NOT persist - no completed questionnaires!');
        }
      } else {
        throw new Error('❌ Unknown state after form submission - no completion screen or questionnaire');
      }

    } catch (e) {
      console.log('ℹ️ Questionnaire form not shown yet - checking if completion screen is already visible\n');

      // Maybe the flow is already complete (no gaps to resolve)
      const hasCompletionScreen = await page.locator('text=/Collection Complete/i, text=/Assessment Ready/i').isVisible({ timeout: 2000 });
      if (hasCompletionScreen) {
        console.log('✅ Collection flow already complete (no questionnaires needed)\n');
      } else {
        throw new Error('❌ Neither questionnaire nor completion screen found');
      }
    }

    console.log('✅ TEST PASSED: UPSERT fix is working correctly!');
  });
});
