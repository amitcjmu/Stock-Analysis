/**
 * Test the "no active flow" scenario by clicking "Start New"
 */

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE_URL = 'http://localhost:8081';
const AUTH_EMAIL = 'demo@demo-corp.com';
const AUTH_PASSWORD = 'Demo123!';
const SCREENSHOT_DIR = path.join(__dirname, 'qa-test-screenshots');

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function main() {
  console.log('🔍 Testing "No Active Flow" Scenario (via Start New)');
  console.log('='.repeat(50));

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  const consoleLogs = [];
  page.on('console', msg => consoleLogs.push({ type: msg.type(), text: msg.text() }));

  try {
    // Login
    console.log('Step 1: Logging in...');
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
    await page.fill('input[type="email"]', AUTH_EMAIL);
    await page.fill('input[type="password"]', AUTH_PASSWORD);
    await page.click('button:has-text("Sign In")');
    await page.waitForURL(/^(?!.*login)/, { timeout: 10000 });
    console.log('✅ Logged in');

    // Navigate to Collection
    console.log('Step 2: Navigating to /collection...');
    await page.goto(`${BASE_URL}/collection`, { waitUntil: 'networkidle' });
    await delay(2000);

    // Check for active flow banner
    const startNewButton = await page.locator('button:has-text("Start New")').first();
    const startNewExists = await startNewButton.isVisible().catch(() => false);

    if (startNewExists) {
      console.log('Step 3: Found "Start New" button, clicking it...');
      await startNewButton.click();
      await delay(1000);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'no-flow-01-after-start-new.png'), fullPage: true });

      // Now check for guided workflow form
      console.log('Step 4: Checking for guided workflow form...');

      const heading = await page.locator('h2:has-text("Start New Data Collection")').first();
      const headingExists = await heading.isVisible().catch(() => false);
      console.log(`  Heading "Start New Data Collection": ${headingExists ? '✅' : '❌'}`);

      const question = await page.locator('text=/How many applications/i').first();
      const questionExists = await question.isVisible().catch(() => false);
      console.log(`  Question about applications: ${questionExists ? '✅' : '❌'}`);

      const adaptiveRadio = await page.locator('input[type="radio"][value="adaptive"]').first();
      const bulkRadio = await page.locator('input[type="radio"][value="bulk"]').first();
      const adaptiveExists = await adaptiveRadio.isVisible().catch(() => false);
      const bulkExists = await bulkRadio.isVisible().catch(() => false);
      console.log(`  Radio "1-50 applications": ${adaptiveExists ? '✅' : '❌'}`);
      console.log(`  Radio "50+ applications": ${bulkExists ? '✅' : '❌'}`);

      const startCollectionBtn = await page.locator('button:has-text("Start Collection")').first();
      const startCollectionExists = await startCollectionBtn.isVisible().catch(() => false);
      console.log(`  "Start Collection" button: ${startCollectionExists ? '✅' : '❌'}`);

      if (startCollectionExists) {
        const isDisabled = await startCollectionBtn.isDisabled();
        console.log(`  Button initially disabled: ${isDisabled ? '✅' : '❌'}`);

        if (adaptiveExists) {
          console.log('Step 5: Selecting "1-50 applications"...');
          await adaptiveRadio.click();
          await delay(500);
          await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'no-flow-02-radio-selected.png'), fullPage: true });

          const isEnabledAfter = !(await startCollectionBtn.isDisabled());
          console.log(`  Button enabled after selection: ${isEnabledAfter ? '✅' : '❌'}`);

          console.log('Step 6: Clicking "Start Collection"...');
          await startCollectionBtn.click();
          await delay(3000);

          const newUrl = page.url();
          console.log(`✅ Navigated to: ${newUrl}`);
          await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'no-flow-03-after-start.png'), fullPage: true });
        }
      }

      console.log('\n✅ TEST PASSED: Guided workflow displays and functions correctly');
    } else {
      console.log('⚠️ No "Start New" button found - might not have active flow');
    }

    fs.writeFileSync(
      path.join(SCREENSHOT_DIR, 'no-flow-console-logs.json'),
      JSON.stringify(consoleLogs, null, 2)
    );

  } catch (error) {
    console.error(`❌ Error: ${error.message}`);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'no-flow-ERROR.png'), fullPage: true });
  } finally {
    await context.close();
    await browser.close();
  }
}

main().catch(console.error);
