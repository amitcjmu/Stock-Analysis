import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Comprehensive test for file upload and Discovery flow initiation
 * Tests the complete workflow from login -> file upload -> Discovery flow creation -> validation
 */
async function testFileUploadAndDiscoveryFlow() {
  console.log('🚀 Starting File Upload and Discovery Flow Test...\n');

  let browser;
  let page;

  try {
    // Launch browser
    browser = await chromium.launch({
      headless: false, // Show browser for debugging
      slowMo: 500 // Slow down actions
    });

    const context = await browser.newContext({
      viewport: { width: 1280, height: 720 }
    });

    page = await context.newPage();

    // Set longer timeout
    page.setDefaultTimeout(30000);

    // Step 1: Login
    console.log('🔐 Step 1: Logging in as platform admin...');
    await page.goto('http://localhost:8081/login');

    await page.fill('input[name="email"]', 'chocka@gmail.com');
    await page.fill('input[name="password"]', 'Password123!');
    await page.click('button[type="submit"]');

    // Wait for successful login
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    console.log('✅ Successfully logged in');

    // Step 2: Navigate to Discovery
    console.log('🔍 Step 2: Navigating to Discovery section...');
    const discoveryLink = page.locator('nav a, a[href*="discovery"]').filter({ hasText: 'Discovery' }).first();
    await discoveryLink.click();
    await page.waitForTimeout(2000);

    // Handle different discovery page states
    const currentUrl = page.url();
    console.log(`📍 Current URL: ${currentUrl}`);

    if (!currentUrl.includes('cmdb-import')) {
      console.log('📋 Navigating to CMDB Import...');
      try {
        const dataImportLink = page.locator('a, button').filter({
          hasText: /Data Import|CMDB Import|Upload Data/i
        }).first();

        if (await dataImportLink.isVisible({ timeout: 5000 })) {
          await dataImportLink.click();
        } else {
          await page.goto('http://localhost:8081/discovery/cmdb-import');
        }
      } catch (e) {
        console.log('⚠️ Direct navigation to CMDB import...');
        await page.goto('http://localhost:8081/discovery/cmdb-import');
      }
    }

    await page.waitForTimeout(2000);
    console.log('✅ On CMDB Import page');

    // Step 3: Create and upload test file
    console.log('📁 Step 3: Preparing test file upload...');

    const testCsvContent = `hostname,application_name,ip_address,operating_system,cpu_cores,memory_gb,storage_gb,environment,criticality,six_r_strategy
server001.prod,Customer Portal,192.168.1.10,Ubuntu 20.04,4,16,500,Production,High,Rehost
server002.prod,Payment Gateway,192.168.1.11,RHEL 8.5,8,32,1000,Production,Critical,Refactor
server003.prod,Admin Dashboard,192.168.1.12,Windows Server 2019,4,16,250,Production,Medium,Replatform
db001.prod,Database Server,192.168.1.20,Ubuntu 22.04,8,64,2000,Production,Critical,Rehost
cache001.prod,Redis Cache,192.168.1.21,Ubuntu 20.04,2,8,100,Production,High,Rehost
api001.prod,Mobile API,192.168.1.30,Ubuntu 22.04,4,16,500,Production,High,Modernize
analytics001.dev,Analytics Engine,192.168.2.10,CentOS 7,16,128,5000,Development,Low,Retire
test001.staging,Test Environment,192.168.3.10,Ubuntu 20.04,2,8,200,Staging,Low,Retire`;

    // Try to find upload areas and upload file
    let uploadSuccessful = false;
    const uploadStrategies = [
      // Strategy 1: Look for upload zones with file input
      async () => {
        const fileInput = page.locator('input[type="file"]').first();
        if (await fileInput.isVisible({ timeout: 3000 })) {
          console.log('📤 Found file input, uploading...');
          const buffer = Buffer.from(testCsvContent);
          await fileInput.setInputFiles({
            name: 'comprehensive_test.csv',
            mimeType: 'text/csv',
            buffer: buffer
          });
          return true;
        }
        return false;
      },

      // Strategy 2: Click upload areas to trigger file chooser
      async () => {
        const uploadAreas = page.locator('.border-dashed, .dropzone, .upload-zone').filter({
          hasText: /upload|drop|choose/i
        });

        if (await uploadAreas.first().isVisible({ timeout: 3000 })) {
          console.log('📤 Found upload area, clicking...');
          const [fileChooser] = await Promise.all([
            page.waitForEvent('filechooser', { timeout: 5000 }),
            uploadAreas.first().click()
          ]);

          await fileChooser.setFiles({
            name: 'comprehensive_test.csv',
            mimeType: 'text/csv',
            buffer: Buffer.from(testCsvContent)
          });
          return true;
        }
        return false;
      }
    ];

    for (const strategy of uploadStrategies) {
      try {
        if (await strategy()) {
          uploadSuccessful = true;
          break;
        }
      } catch (e) {
        console.log(`⚠️ Upload strategy failed: ${e.message}`);
      }
    }

    if (!uploadSuccessful) {
      console.log('❌ No upload method worked. Taking screenshot for debugging...');
      await page.screenshot({ path: 'upload-interface-debug.png', fullPage: true });
      throw new Error('Could not upload file');
    }

    console.log('✅ File upload initiated');

    // Step 4: Wait for processing
    console.log('⏳ Step 4: Waiting for file processing...');
    await page.waitForTimeout(5000);

    // Look for processing completion indicators
    const successIndicators = [
      'text=/upload.*complete|processing.*complete|flow.*created/i',
      'text=/flow-\\d{8}-\\d{6}/', // Flow ID pattern
      '.success-message',
      '.upload-success'
    ];

    let processingComplete = false;
    for (let i = 0; i < 20; i++) { // Wait up to 20 seconds
      for (const selector of successIndicators) {
        try {
          if (await page.locator(selector).first().isVisible({ timeout: 1000 })) {
            console.log('✅ Processing completed');
            processingComplete = true;

            // Try to extract flow ID
            const flowIdElement = page.locator('text=/flow-\\d{8}-\\d{6}/');
            if (await flowIdElement.isVisible()) {
              const flowId = await flowIdElement.textContent();
              console.log(`🔄 Flow ID: ${flowId}`);
            }
            break;
          }
        } catch (e) {
          // Continue checking
        }
      }
      if (processingComplete) break;
      await page.waitForTimeout(1000);
    }

    // Step 5: Verify Discovery flow data
    console.log('🔍 Step 5: Verifying Discovery flow initiation...');

    // Navigate to attribute mapping to verify flow
    await page.goto('http://localhost:8081/discovery/attribute-mapping');
    await page.waitForTimeout(3000);

    const flowDataIndicators = [
      'text=/field mapping|critical attributes|source fields/i',
      'table',
      '.mapping-table',
      '.field-mapping-section'
    ];

    let flowDataFound = false;
    for (const selector of flowDataIndicators) {
      try {
        if (await page.locator(selector).first().isVisible({ timeout: 5000 })) {
          flowDataFound = true;
          console.log('✅ Flow data detected on attribute mapping page');
          break;
        }
      } catch (e) {
        // Continue checking
      }
    }

    // Check for no data messages
    const noDataMessage = await page.locator('text=/no.*data|no.*field.*mapping/i').first().isVisible({ timeout: 3000 });

    if (noDataMessage && !flowDataFound) {
      console.log('⚠️ No flow data detected. Checking flow selector...');

      // Look for flow selector
      const flowSelector = page.locator('select').filter({ hasText: /flow/i }).first();
      if (await flowSelector.isVisible({ timeout: 3000 })) {
        console.log('🔽 Flow selector found, selecting available flow...');
        const options = await flowSelector.locator('option').all();
        if (options.length > 1) {
          await flowSelector.selectOption({ index: 1 });
          await page.waitForTimeout(2000);

          // Re-check for flow data
          for (const selector of flowDataIndicators) {
            try {
              if (await page.locator(selector).first().isVisible({ timeout: 3000 })) {
                flowDataFound = true;
                console.log('✅ Flow data loaded after selection');
                break;
              }
            } catch (e) {
              // Continue
            }
          }
        }
      }
    }

    // Step 6: Check Discovery overview
    console.log('📊 Step 6: Checking Discovery overview...');
    await page.goto('http://localhost:8081/discovery');
    await page.waitForTimeout(3000);

    // Look for asset inventory indicators
    const assetIndicators = [
      'text=/\\d+.*asset|\\d+.*server|\\d+.*application/i',
      'text=/discovered.*\\d+/i'
    ];

    let assetsDetected = false;
    for (const selector of assetIndicators) {
      try {
        const element = page.locator(selector).first();
        if (await element.isVisible({ timeout: 3000 })) {
          const text = await element.textContent();
          console.log(`📦 Asset count: ${text}`);

          // Check if count > 0
          const match = text?.match(/(\d+)/);
          if (match && parseInt(match[1]) > 0) {
            assetsDetected = true;
            console.log('✅ Assets detected in inventory');
          }
          break;
        }
      } catch (e) {
        // Continue
      }
    }

    // Final results
    console.log('\n📋 TEST RESULTS SUMMARY:');
    console.log(`✅ Login: SUCCESS`);
    console.log(`✅ Navigation: SUCCESS`);
    console.log(`✅ File Upload: ${uploadSuccessful ? 'SUCCESS' : 'FAILED'}`);
    console.log(`⏳ Processing: ${processingComplete ? 'DETECTED' : 'PARTIAL'}`);
    console.log(`📋 Flow Data: ${flowDataFound ? 'SUCCESS' : 'NOT FOUND'}`);
    console.log(`📦 Asset Detection: ${assetsDetected ? 'SUCCESS' : 'NOT DETECTED'}`);

    // Take final screenshot
    await page.screenshot({ path: 'test-final-state.png', fullPage: true });

    if (uploadSuccessful && (processingComplete || flowDataFound || assetsDetected)) {
      console.log('\n🎉 TEST PASSED: File upload and Discovery flow initiation working!');
      return true;
    } else {
      console.log('\n⚠️ TEST PARTIAL: Some aspects working, others need investigation');
      return false;
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    if (page) {
      await page.screenshot({ path: 'test-error-state.png', fullPage: true });
    }
    return false;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Run the test
testFileUploadAndDiscoveryFlow()
  .then(success => {
    console.log(success ? '\n✅ Overall test result: PASSED' : '\n❌ Overall test result: FAILED');
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
  });
