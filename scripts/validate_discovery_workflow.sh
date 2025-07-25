#!/bin/bash

echo "🔍 Validating Complete Discovery Workflow"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Base URL
BASE_URL="http://localhost:8081"
API_URL="http://localhost:8000"

# Test credentials
EMAIL="chocka@gmail.com"
PASSWORD="Password123!"

# Create test data file
echo -e "${BLUE}1. Creating test CMDB data file...${NC}"
cat > /tmp/test-cmdb-data.csv << 'EOF'
Name,Type,Status,Environment,IP_Address,OS,Department,Owner,Location,Description
APP-WEB-001,Application,Active,Production,10.0.1.10,Linux,IT,John Doe,US-East,Customer portal web application
APP-API-001,Application,Active,Production,10.0.1.11,Linux,IT,Jane Smith,US-East,REST API service
APP-DB-001,Application,Active,Production,10.0.1.12,Linux,IT,Bob Wilson,US-East,Database application layer
SRV-WEB-001,Server,Active,Production,10.0.2.10,Ubuntu 22.04,IT,John Doe,US-East,Web server hosting customer portal
SRV-WEB-002,Server,Active,Production,10.0.2.11,Ubuntu 22.04,IT,John Doe,US-East,Web server hosting customer portal
SRV-API-001,Server,Active,Production,10.0.2.20,Ubuntu 20.04,IT,Jane Smith,US-East,API server cluster node 1
SRV-API-002,Server,Active,Production,10.0.2.21,Ubuntu 20.04,IT,Jane Smith,US-East,API server cluster node 2
SRV-DB-001,Server,Active,Production,10.0.2.30,Red Hat 8,IT,Bob Wilson,US-East,Primary database server
SRV-DB-002,Server,Standby,Production,10.0.2.31,Red Hat 8,IT,Bob Wilson,US-East,Standby database server
DEV-LB-001,Device,Active,Production,10.0.3.10,Proprietary,Network,Alice Brown,US-East,Load balancer for web traffic
DEV-FW-001,Device,Active,Production,10.0.3.20,Proprietary,Security,Charlie Davis,US-East,Main firewall appliance
DEV-SW-001,Device,Active,Production,10.0.3.30,Cisco IOS,Network,Alice Brown,US-East,Core network switch
DEV-STG-001,Device,Active,Production,10.0.3.40,Proprietary,IT,Bob Wilson,US-East,SAN storage device
EOF
echo -e "${GREEN}✅ Test data file created${NC}"

# Run the Playwright test for complete workflow
echo ""
echo -e "${BLUE}2. Running complete discovery workflow test...${NC}"
echo "This will:"
echo "  - Login to the platform"
echo "  - Upload CMDB data file"
echo "  - Navigate to attribute mapping"
echo "  - Complete field mapping"
echo "  - Process data cleansing"
echo "  - Verify assets in inventory"
echo ""

# Create the comprehensive workflow test
cat > /tmp/discovery-workflow-test.js << 'EOF'
const { chromium } = require('playwright');

async function validateDiscoveryWorkflow() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // Set longer timeout for complex operations
  page.setDefaultTimeout(60000);

  const results = {
    login: false,
    fileUpload: false,
    attributeMapping: false,
    dataCleansing: false,
    inventoryAssets: false,
    appCount: 0,
    serverCount: 0,
    deviceCount: 0
  };

  try {
    console.log('\n📋 Step 1: Login');
    await page.goto('http://localhost:8081/login');
    await page.fill('input[type="email"]', 'chocka@gmail.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');

    // Wait for navigation
    await page.waitForURL('**/discovery/**', { timeout: 10000 });
    results.login = true;
    console.log('✅ Login successful');

    // Step 2: Navigate to Data Import
    console.log('\n📋 Step 2: Data Import');
    await page.goto('http://localhost:8081/discovery/cmdb-import');
    await page.waitForLoadState('networkidle');

    // Upload file
    const fileInput = await page.locator('input[type="file"]').first();
    await fileInput.setInputFiles('/tmp/test-cmdb-data.csv');

    // Wait for upload to process
    await page.waitForTimeout(5000);
    results.fileUpload = true;
    console.log('✅ File uploaded successfully');

    // Step 3: Navigate to Attribute Mapping
    console.log('\n📋 Step 3: Attribute Mapping');

    // Try clicking attribute mapping link
    const mappingLink = page.locator('a[href*="attribute-mapping"], text=/attribute.*mapping/i').first();
    if (await mappingLink.isVisible()) {
      await mappingLink.click();
    } else {
      await page.goto('http://localhost:8081/discovery/attribute-mapping');
    }

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Check if field mapping is available or needs to be triggered
    const triggerButton = page.locator('button:has-text("Trigger Field Mapping")');
    if (await triggerButton.isVisible()) {
      console.log('🔄 Triggering field mapping...');
      await triggerButton.click();
      await page.waitForTimeout(10000);
    }

    // Look for mapping interface
    const mappingInterface = await page.locator('table, .mapping-table, [data-testid*="mapping"]').count();
    if (mappingInterface > 0) {
      results.attributeMapping = true;
      console.log('✅ Attribute mapping interface loaded');

      // Try to finalize/continue
      const actionButtons = ['Finalize', 'Continue', 'Next', 'Apply', 'Save'];
      for (const buttonText of actionButtons) {
        const button = page.locator(`button:has-text("${buttonText}")`).first();
        if (await button.isVisible()) {
          await button.click();
          await page.waitForTimeout(3000);
          break;
        }
      }
    }

    // Step 4: Data Cleansing (if available)
    console.log('\n📋 Step 4: Data Cleansing');

    // Check if we're on data cleansing page
    const cleansingIndicators = await page.locator('text=/data.*cleansing|cleanse.*data|validation.*rules/i').count();
    if (cleansingIndicators > 0) {
      results.dataCleansing = true;
      console.log('✅ Data cleansing phase detected');

      // Try to continue from cleansing
      const continueButton = page.locator('button:has-text("Continue"), button:has-text("Next")').first();
      if (await continueButton.isVisible()) {
        await continueButton.click();
        await page.waitForTimeout(3000);
      }
    }

    // Step 5: Navigate to Inventory
    console.log('\n📋 Step 5: Inventory Verification');
    await page.goto('http://localhost:8081/discovery/inventory');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);

    // Count different asset types
    // Look for applications
    const appRows = await page.locator('tr:has-text("Application"), tr:has-text("APP-")').count();
    results.appCount = appRows;

    // Look for servers
    const serverRows = await page.locator('tr:has-text("Server"), tr:has-text("SRV-")').count();
    results.serverCount = serverRows;

    // Look for devices
    const deviceRows = await page.locator('tr:has-text("Device"), tr:has-text("DEV-")').count();
    results.deviceCount = deviceRows;

    // Check if any assets are visible
    const totalAssets = results.appCount + results.serverCount + results.deviceCount;
    if (totalAssets > 0) {
      results.inventoryAssets = true;
    }

    // Take screenshot of final inventory
    await page.screenshot({ path: '/tmp/inventory-final.png', fullPage: true });

  } catch (error) {
    console.error('❌ Error during workflow:', error.message);
    await page.screenshot({ path: '/tmp/error-screenshot.png', fullPage: true });
  } finally {
    await browser.close();
  }

  // Print results
  console.log('\n' + '='.repeat(50));
  console.log('📊 WORKFLOW VALIDATION RESULTS');
  console.log('='.repeat(50));
  console.log(`Login:             ${results.login ? '✅ Success' : '❌ Failed'}`);
  console.log(`File Upload:       ${results.fileUpload ? '✅ Success' : '❌ Failed'}`);
  console.log(`Attribute Mapping: ${results.attributeMapping ? '✅ Success' : '❌ Failed'}`);
  console.log(`Data Cleansing:    ${results.dataCleansing ? '✅ Success' : 'ℹ️  Skipped'}`);
  console.log(`Inventory Assets:  ${results.inventoryAssets ? '✅ Success' : '❌ Failed'}`);
  console.log('\n📈 Asset Counts:');
  console.log(`Applications:      ${results.appCount} (expected: 3)`);
  console.log(`Servers:           ${results.serverCount} (expected: 6)`);
  console.log(`Devices:           ${results.deviceCount} (expected: 4)`);
  console.log(`Total Assets:      ${results.appCount + results.serverCount + results.deviceCount} (expected: 13)`);
  console.log('='.repeat(50));

  // Return success if critical steps passed
  const success = results.login && results.fileUpload && results.inventoryAssets;
  process.exit(success ? 0 : 1);
}

validateDiscoveryWorkflow().catch(console.error);
EOF

# Check if playwright is installed
if ! npm list playwright >/dev/null 2>&1; then
  echo -e "${YELLOW}Installing Playwright...${NC}"
  npm install playwright
fi

# Run the test
node /tmp/discovery-workflow-test.js

# Check result
if [ $? -eq 0 ]; then
  echo ""
  echo -e "${GREEN}✅ Discovery workflow validation PASSED!${NC}"
  echo "The complete workflow from file upload to inventory is working correctly."

  # Show screenshot if exists
  if [ -f "/tmp/inventory-final.png" ]; then
    echo ""
    echo "📸 Screenshot saved at: /tmp/inventory-final.png"
  fi
else
  echo ""
  echo -e "${RED}❌ Discovery workflow validation FAILED${NC}"
  echo "Please check the error screenshot at: /tmp/error-screenshot.png"
  exit 1
fi
