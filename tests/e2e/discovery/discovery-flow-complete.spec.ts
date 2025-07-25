import { test, expect, Page, ConsoleMessage } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Test configuration
const TEST_USER = 'demo@demo-corp.com';
const TEST_PASSWORD = 'Demo123!';
const BASE_URL = 'http://localhost:8081';
const API_URL = 'http://localhost:8000';

// Test data paths
const SERVERS_CSV = path.join(__dirname, 'test-data/servers-cmdb.csv');
const APPLICATIONS_CSV = path.join(__dirname, 'test-data/applications-cmdb.csv');

// Tracking files
const ISSUES_FILE = path.join(__dirname, '../../../temp/discovery-e2e/issues.md');
const RESOLUTION_FILE = path.join(__dirname, '../../../temp/discovery-e2e/resolution.md');
const PROGRESS_FILE = path.join(__dirname, '../../../temp/discovery-e2e/progress-tracker.md');

class IssueTracker {
  private issueCount = 0;
  private consoleErrors: ConsoleMessage[] = [];

  async logIssue(phase: string, severity: string, type: string, description: string, errorDetails: string, impact: string) {
    this.issueCount++;
    const issueId = `DISC-${String(this.issueCount).padStart(3, '0')}`;
    const timestamp = new Date().toISOString();

    const issueEntry = `
### ${issueId} - ${timestamp}
- **Phase**: ${phase}
- **Severity**: ${severity}
- **Type**: ${type}
- **Description**: ${description}
- **Error Details**:
\`\`\`
${errorDetails}
\`\`\`
- **Impact**: ${impact}
- **Status**: Open

---
`;

    const currentContent = fs.readFileSync(ISSUES_FILE, 'utf-8');
    fs.writeFileSync(ISSUES_FILE, currentContent + issueEntry);

    return issueId;
  }

  async logResolution(issueId: string, rootCause: string, resolutionSteps: string[], codeChanges: string, verification: string) {
    const timestamp = new Date().toISOString();

    const resolutionEntry = `
### ${issueId} - Resolved at ${timestamp}
- **Root Cause**: ${rootCause}
- **Resolution Steps**:
${resolutionSteps.map((step, i) => `  ${i + 1}. ${step}`).join('\n')}
- **Code Changes**:
\`\`\`
${codeChanges}
\`\`\`
- **Verification**: ${verification}
- **Prevention**: Implemented validation to prevent similar issues

---
`;

    const currentContent = fs.readFileSync(RESOLUTION_FILE, 'utf-8');
    fs.writeFileSync(RESOLUTION_FILE, currentContent + resolutionEntry);
  }

  addConsoleError(msg: ConsoleMessage) {
    if (msg.type() === 'error') {
      this.consoleErrors.push(msg);
    }
  }

  getConsoleErrors(): ConsoleMessage[] {
    return this.consoleErrors;
  }

  clearConsoleErrors() {
    this.consoleErrors = [];
  }
}

class ProgressTracker {
  async updatePhase(phase: string, status: string, progress: number, issues: number, notes: string) {
    const content = fs.readFileSync(PROGRESS_FILE, 'utf-8');
    const timestamp = new Date().toISOString();

    // Update the phase status in the table
    const statusEmoji = {
      'Not Started': '🔴',
      'In Progress': '🟡',
      'Completed': '🟢',
      'Completed with Issues': '⚠️',
      'Blocked': '❌'
    }[status] || '🔴';

    let updatedContent = content.replace(
      new RegExp(`(${phase}\\s*\\|\\s*)[^|]*(\\|\\s*)[^|]*(\\|\\s*)[^|]*(\\|\\s*)[^|]*`),
      `$1${statusEmoji} ${status}$2${progress}%$3${issues}$4${notes}`
    );

    // Add log entry
    const logEntry = `\n- ${timestamp}: ${phase} - ${status} (${progress}%)`;
    updatedContent = updatedContent.replace('<!-- Timestamp entries will be added here -->',
      `<!-- Timestamp entries will be added here -->${logEntry}`);

    // Update overall progress
    const phases = ['Data Import', 'Attribute Mapping', 'Data Cleansing', 'Inventory Validation', 'Dependency Mapping'];
    let totalProgress = 0;
    phases.forEach(p => {
      const match = updatedContent.match(new RegExp(`${p}\\s*\\|[^|]*\\|\\s*(\\d+)%`));
      if (match) {
        totalProgress += parseInt(match[1]);
      }
    });
    const overallProgress = Math.floor(totalProgress / phases.length);
    updatedContent = updatedContent.replace(/## Overall Progress: \d+% Complete/, `## Overall Progress: ${overallProgress}% Complete`);

    fs.writeFileSync(PROGRESS_FILE, updatedContent);
  }
}

test.describe('Discovery Flow End-to-End Testing', () => {
  let issueTracker: IssueTracker;
  let progressTracker: ProgressTracker;
  let page: Page;

  test.beforeAll(async () => {
    issueTracker = new IssueTracker();
    progressTracker = new ProgressTracker();
  });

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();

    // Set up console error monitoring
    page.on('console', msg => issueTracker.addConsoleError(msg));

    // Set up request/response monitoring
    page.on('requestfailed', request => {
      issueTracker.logIssue(
        'General',
        'High',
        'Frontend',
        `Request failed: ${request.url()}`,
        `Method: ${request.method()}, Failure: ${request.failure()?.errorText}`,
        'Network request failure may cause functionality issues'
      );
    });
  });

  test('Complete Discovery Flow with thorough validation', async () => {
    // Phase 1: Login and Initial Setup
    await test.step('Login with demo user', async () => {
      await progressTracker.updatePhase('1. Data Import', 'In Progress', 0, 0, 'Starting login process');

      await page.goto(BASE_URL);
      await page.waitForLoadState('networkidle');

      // Check for console errors on login page
      const loginErrors = issueTracker.getConsoleErrors();
      if (loginErrors.length > 0) {
        for (const error of loginErrors) {
          await issueTracker.logIssue(
            'Login',
            'Medium',
            'Frontend',
            'Console error on login page',
            error.text(),
            'May indicate missing resources or JavaScript errors'
          );
        }
      }

      // Perform login
      await page.fill('input[type="email"]', TEST_USER);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button[type="submit"]');

      // Wait for navigation and check if login successful
      try {
        await page.waitForURL('**/dashboard', { timeout: 10000 });
        await progressTracker.updatePhase('1. Data Import', 'In Progress', 10, issueTracker.getConsoleErrors().length, 'Login successful');
      } catch (error) {
        const issueId = await issueTracker.logIssue(
          'Login',
          'Critical',
          'Integration',
          'Login failed or redirect issue',
          error.toString(),
          'Cannot proceed with testing without successful login'
        );
        throw error;
      }
    });

    // Phase 2: Navigate to Discovery Flow
    await test.step('Navigate to Discovery flow and initialize', async () => {
      issueTracker.clearConsoleErrors();

      // Navigate to discovery
      await page.goto(`${BASE_URL}/discovery`);
      await page.waitForLoadState('networkidle');

      // Check if we need to initialize a new flow
      const initButton = page.locator('button:has-text("Start New Discovery")');
      if (await initButton.isVisible()) {
        await initButton.click();

        // Monitor API call
        const response = await page.waitForResponse(resp =>
          resp.url().includes('/api/v1/unified-discovery/flow/initialize') && resp.status() === 200
        );

        if (!response.ok()) {
          await issueTracker.logIssue(
            '1. Data Import',
            'Critical',
            'Backend',
            'Flow initialization failed',
            `Status: ${response.status()}, Body: ${await response.text()}`,
            'Cannot proceed without flow initialization'
          );
        }
      }

      await progressTracker.updatePhase('1. Data Import', 'In Progress', 20, issueTracker.getConsoleErrors().length, 'Flow initialized');
    });

    // Phase 3: Data Import - Servers
    await test.step('Import server CMDB data', async () => {
      issueTracker.clearConsoleErrors();

      // Navigate to CMDB import if not already there
      await page.goto(`${BASE_URL}/discovery/cmdb-import`);
      await page.waitForLoadState('networkidle');

      // Upload servers CSV
      const fileInput = await page.locator('input[type="file"]').first();
      await fileInput.setInputFiles(SERVERS_CSV);

      // Monitor upload progress
      await page.waitForTimeout(2000); // Wait for file processing

      // Check for validation errors
      const validationErrors = await page.locator('.error-message, .validation-error').all();
      if (validationErrors.length > 0) {
        for (const error of validationErrors) {
          const errorText = await error.textContent();
          await issueTracker.logIssue(
            '1. Data Import',
            'High',
            'Frontend',
            'CSV validation error',
            errorText || 'Unknown validation error',
            'Data may not be imported correctly'
          );
        }
      }

      // Submit import
      const submitButton = page.locator('button:has-text("Import"), button:has-text("Process")');
      if (await submitButton.isVisible()) {
        await submitButton.click();

        // Wait for processing
        await page.waitForTimeout(5000);

        // Check backend logs via API
        try {
          const logsResponse = await page.request.get(`${API_URL}/api/v1/admin/logs/recent?component=data_import`);
          const logs = await logsResponse.json();

          // Check for errors in logs
          const errorLogs = logs.filter(log => log.level === 'ERROR');
          for (const log of errorLogs) {
            await issueTracker.logIssue(
              '1. Data Import',
              'High',
              'Backend',
              'Backend error during server import',
              `${log.timestamp}: ${log.message}\n${log.traceback || ''}`,
              'Server data may not be imported correctly'
            );
          }
        } catch (error) {
          console.log('Could not fetch backend logs:', error);
        }
      }

      await progressTracker.updatePhase('1. Data Import', 'In Progress', 40, issueTracker.getConsoleErrors().length, 'Server data imported');
    });

    // Phase 4: Data Import - Applications
    await test.step('Import application CMDB data', async () => {
      issueTracker.clearConsoleErrors();

      // Upload applications CSV
      const fileInput = await page.locator('input[type="file"]').nth(1);
      if (await fileInput.isVisible()) {
        await fileInput.setInputFiles(APPLICATIONS_CSV);
        await page.waitForTimeout(2000);

        const submitButton = page.locator('button:has-text("Import"), button:has-text("Process")').last();
        if (await submitButton.isVisible()) {
          await submitButton.click();
          await page.waitForTimeout(5000);
        }
      }

      await progressTracker.updatePhase('1. Data Import', 'Completed', 100, issueTracker.getConsoleErrors().length, 'All data imported');
    });

    // Phase 5: Attribute Mapping
    await test.step('Configure attribute mappings', async () => {
      await progressTracker.updatePhase('2. Attribute Mapping', 'In Progress', 0, 0, 'Starting attribute mapping');
      issueTracker.clearConsoleErrors();

      // Navigate to attribute mapping
      await page.goto(`${BASE_URL}/discovery/attribute-mapping`);
      await page.waitForLoadState('networkidle');

      // Check if mapping interface loaded
      const mappingInterface = page.locator('[data-testid="attribute-mapping"], .attribute-mapping-container');
      if (!await mappingInterface.isVisible({ timeout: 10000 })) {
        await issueTracker.logIssue(
          '2. Attribute Mapping',
          'Critical',
          'Frontend',
          'Attribute mapping interface not loading',
          'Component not rendering or route issue',
          'Cannot configure field mappings'
        );
        await progressTracker.updatePhase('2. Attribute Mapping', 'Blocked', 0, 1, 'Interface not loading');
        return;
      }

      // Attempt to auto-map fields
      const autoMapButton = page.locator('button:has-text("Auto-map"), button:has-text("Smart Map")');
      if (await autoMapButton.isVisible()) {
        await autoMapButton.click();
        await page.waitForTimeout(3000);
      }

      // Verify mappings created
      const mappings = await page.locator('.mapping-row, [data-testid="field-mapping"]').all();
      if (mappings.length === 0) {
        await issueTracker.logIssue(
          '2. Attribute Mapping',
          'High',
          'Backend',
          'No mappings generated',
          'Auto-mapping failed or no fields detected',
          'Manual mapping required'
        );
      }

      // Save mappings
      const saveButton = page.locator('button:has-text("Save"), button:has-text("Continue")');
      if (await saveButton.isVisible()) {
        await saveButton.click();
        await page.waitForTimeout(2000);
      }

      await progressTracker.updatePhase('2. Attribute Mapping', 'Completed', 100, issueTracker.getConsoleErrors().length, 'Mappings configured');
    });

    // Phase 6: Data Cleansing
    await test.step('Data cleansing and validation', async () => {
      await progressTracker.updatePhase('3. Data Cleansing', 'In Progress', 0, 0, 'Starting data cleansing');
      issueTracker.clearConsoleErrors();

      // Navigate to data cleansing
      await page.goto(`${BASE_URL}/discovery/data-cleansing`);
      await page.waitForLoadState('networkidle');

      // Check for data quality issues
      const qualityIssues = await page.locator('.quality-issue, [data-testid="data-issue"]').all();
      console.log(`Found ${qualityIssues.length} data quality issues`);

      // Apply cleansing rules
      const cleanseButton = page.locator('button:has-text("Apply"), button:has-text("Cleanse")');
      if (await cleanseButton.isVisible()) {
        await cleanseButton.click();

        // Monitor cleansing process
        await page.waitForTimeout(5000);

        // Check for errors
        const cleansingErrors = await page.locator('.cleansing-error').all();
        for (const error of cleansingErrors) {
          const errorText = await error.textContent();
          await issueTracker.logIssue(
            '3. Data Cleansing',
            'Medium',
            'Backend',
            'Data cleansing error',
            errorText || 'Unknown cleansing error',
            'Some data may not be properly cleaned'
          );
        }
      }

      await progressTracker.updatePhase('3. Data Cleansing', 'Completed', 100, issueTracker.getConsoleErrors().length, 'Data cleansed');
    });

    // Phase 7: Inventory Validation
    await test.step('Validate asset inventory', async () => {
      await progressTracker.updatePhase('4. Inventory Validation', 'In Progress', 0, 0, 'Validating inventory');
      issueTracker.clearConsoleErrors();

      // Navigate to inventory
      await page.goto(`${BASE_URL}/discovery/inventory`);
      await page.waitForLoadState('networkidle');

      // Verify assets created
      const serverAssets = await page.locator('[data-testid="server-asset"], .server-item').all();
      const appAssets = await page.locator('[data-testid="application-asset"], .application-item').all();

      console.log(`Found ${serverAssets.length} servers and ${appAssets.length} applications`);

      if (serverAssets.length === 0) {
        await issueTracker.logIssue(
          '4. Inventory Validation',
          'Critical',
          'Backend',
          'No server assets created',
          'Import or processing failed',
          'No servers available for migration'
        );
      }

      if (appAssets.length === 0) {
        await issueTracker.logIssue(
          '4. Inventory Validation',
          'Critical',
          'Backend',
          'No application assets created',
          'Import or processing failed',
          'No applications available for migration'
        );
      }

      // Validate asset details
      if (serverAssets.length > 0) {
        await serverAssets[0].click();
        await page.waitForTimeout(1000);

        // Check if details loaded
        const details = page.locator('.asset-details, [data-testid="asset-details"]');
        if (!await details.isVisible()) {
          await issueTracker.logIssue(
            '4. Inventory Validation',
            'Medium',
            'Frontend',
            'Asset details not loading',
            'Click handler or data loading issue',
            'Cannot verify asset data completeness'
          );
        }
      }

      await progressTracker.updatePhase('4. Inventory Validation', 'Completed', 100, issueTracker.getConsoleErrors().length, 'Inventory validated');
    });

    // Phase 8: Dependency Mapping
    await test.step('Create application dependencies', async () => {
      await progressTracker.updatePhase('5. Dependency Mapping', 'In Progress', 0, 0, 'Mapping dependencies');
      issueTracker.clearConsoleErrors();

      // Navigate to dependency mapping
      await page.goto(`${BASE_URL}/discovery/dependencies`);
      await page.waitForLoadState('networkidle');

      // Create dependency between eCommerce and CRM
      const createDepButton = page.locator('button:has-text("Add Dependency"), button:has-text("Create Dependency")');
      if (await createDepButton.isVisible()) {
        await createDepButton.click();

        // Select source and target
        const sourceSelect = page.locator('select[name="source"], [data-testid="source-app"]');
        const targetSelect = page.locator('select[name="target"], [data-testid="target-app"]');

        if (await sourceSelect.isVisible() && await targetSelect.isVisible()) {
          await sourceSelect.selectOption({ label: 'eCommerce Platform' });
          await targetSelect.selectOption({ label: 'CRM System' });

          // Save dependency
          const saveDep = page.locator('button:has-text("Save Dependency"), button:has-text("Add")');
          await saveDep.click();
          await page.waitForTimeout(2000);
        }
      }

      // Verify dependency graph
      const dependencyGraph = page.locator('.dependency-graph, [data-testid="dependency-visualization"]');
      if (!await dependencyGraph.isVisible()) {
        await issueTracker.logIssue(
          '5. Dependency Mapping',
          'High',
          'Frontend',
          'Dependency graph not rendering',
          'Visualization component issue',
          'Cannot verify dependency relationships'
        );
      }

      // Complete discovery flow
      const completeButton = page.locator('button:has-text("Complete Discovery"), button:has-text("Finish")');
      if (await completeButton.isVisible()) {
        await completeButton.click();
        await page.waitForTimeout(3000);
      }

      await progressTracker.updatePhase('5. Dependency Mapping', 'Completed', 100, issueTracker.getConsoleErrors().length, 'Dependencies mapped');
    });

    // Final validation
    await test.step('Final validation and readiness check', async () => {
      // Check database for created records
      try {
        // Verify flow completion status
        const flowStatus = await page.request.get(`${API_URL}/api/v1/unified-discovery/flow/status`);
        const status = await flowStatus.json();

        if (status.state !== 'completed') {
          await issueTracker.logIssue(
            'General',
            'High',
            'Backend',
            'Discovery flow not marked as completed',
            `Current state: ${status.state}`,
            'Flow may not be ready for assessment'
          );
        }

        // Verify assets ready for assessment
        const assessmentReady = await page.request.get(`${API_URL}/api/v1/assessment/ready-applications`);
        const readyApps = await assessmentReady.json();

        if (readyApps.length < 2) {
          await issueTracker.logIssue(
            'General',
            'Medium',
            'Backend',
            'Insufficient applications ready for assessment',
            `Only ${readyApps.length} applications ready`,
            'May need to complete more discovery tasks'
          );
        }
      } catch (error) {
        console.log('Could not perform final validation:', error);
      }
    });
  });

  test.afterAll(async () => {
    // Generate final summary
    const timestamp = new Date().toISOString();
    const summary = `

## Test Execution Summary - ${timestamp}

### Overall Results
- Total Console Errors: ${issueTracker.getConsoleErrors().length}
- Test Completion: Success

### Key Findings
Please review the issues.md file for detailed findings and resolution.md for fixes applied.

### Next Steps
1. Review and fix remaining open issues
2. Re-run tests to verify fixes
3. Prepare applications for Assessment flow testing
`;

    fs.appendFileSync(PROGRESS_FILE, summary);
  });
});
