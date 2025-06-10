# Test info

- Name: Data Import to Attribute Mapping Flow >> should successfully upload a file and navigate to attribute mapping
- Location: /Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/data-import-flow.spec.ts:4:3

# Error details

```
Error: page.waitForEvent: Test timeout of 30000ms exceeded.
=========================== logs ===========================
waiting for event "filechooser"
============================================================
    at /Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/data-import-flow.spec.ts:12:36
```

# Page snapshot

```yaml
- region "Notifications (F8)":
  - list
- img
- heading "AI Force" [level=1]
- paragraph: Migration Platform
- navigation:
  - list:
    - listitem:
      - link "Dashboard":
        - /url: /
        - img
        - text: Dashboard
    - listitem:
      - img
      - text: Discovery
      - img
      - list:
        - listitem:
          - link "Overview":
            - /url: /discovery/overview
            - img
            - text: Overview
        - listitem:
          - link "Data Import":
            - /url: /discovery/data-import
            - img
            - text: Data Import
        - listitem:
          - link "Attribute Mapping":
            - /url: /discovery/attribute-mapping
            - img
            - text: Attribute Mapping
        - listitem:
          - link "Data Cleansing":
            - /url: /discovery/data-cleansing
            - img
            - text: Data Cleansing
        - listitem:
          - link "Inventory":
            - /url: /discovery/inventory
            - img
            - text: Inventory
        - listitem:
          - link "Dependencies":
            - /url: /discovery/dependencies
            - img
            - text: Dependencies
        - listitem:
          - link "Tech Debt":
            - /url: /discovery/tech-debt-analysis
            - img
            - text: Tech Debt
    - listitem:
      - img
      - text: Assess
      - img
    - listitem:
      - img
      - text: Plan
      - img
    - listitem:
      - img
      - text: Execute
      - img
    - listitem:
      - img
      - text: Modernize
      - img
    - listitem:
      - img
      - text: Decommission
      - img
    - listitem:
      - img
      - text: FinOps
      - img
    - listitem:
      - img
      - text: Observability
      - img
    - listitem:
      - img
      - text: Admin
      - img
- text: AI Force v0.4.9 Click for feedback
- main:
  - navigation "Context breadcrumb":
    - button:
      - img
    - img
    - button "Acme Corporation Demo":
      - img
      - text: Acme Corporation Demo
    - img
    - button "Cloud Migration Initiative 2024" [disabled]:
      - img
      - text: Cloud Migration Initiative 2024
    - img
    - img
    - text: Engagement View
  - heading "Intelligent Data Analysis" [level=1]
  - paragraph: Upload any data file and let our AI crew intelligently determine its type, value, and processing requirements
  - img
  - paragraph:
    - strong: "Smart AI Analysis:"
    - text: Our intelligent agents analyze any uploaded data to determine actual content type, assess quality and relevance, then recommend the optimal processing workflow for your migration journey.
  - heading "Upload Your Data (AI Will Determine Actual Type)" [level=2]
  - paragraph:
    - text: Choose the category that best represents what you
    - emphasis: intended
    - text: to upload. Our AI crew will analyze the actual content and determine its true type and value.
  - img
  - heading "CMDB Data" [level=3]
  - paragraph: Configuration Management Database exports with asset information
  - strong: "Accepted formats:"
  - text: .csv, .xlsx, .json
  - strong: "Examples:"
  - text: ServiceNow exports, BMC Remedy data, Custom CMDB files
  - img
  - text: Click to upload files
  - img
  - heading "Application Scan Data" [level=3]
  - paragraph: Application discovery and dependency scan results
  - strong: "Accepted formats:"
  - text: .csv, .json, .xml
  - strong: "Examples:"
  - text: Appdynamics exports, Dynatrace data, New Relic reports
  - img
  - text: Click to upload files
  - img
  - heading "Migration Discovery Data" [level=3]
  - paragraph: Migration readiness assessments and infrastructure details
  - strong: "Accepted formats:"
  - text: .csv, .xlsx, .json
  - strong: "Examples:"
  - text: AWS Migration Hub, Azure Migrate data, Migration assessments
  - img
  - text: Click to upload files
  - img
  - heading "Documentation" [level=3]
  - paragraph: Technical documentation, architecture diagrams, and runbooks
  - strong: "Accepted formats:"
  - text: .pdf, .doc, .docx, .md
  - strong: "Examples:"
  - text: Architecture docs, Runbooks, Technical specifications
  - img
  - text: Click to upload files
  - img
  - heading "Application Monitoring Data" [level=3]
  - paragraph: Performance metrics, logs, and monitoring tool exports
  - strong: "Accepted formats:"
  - text: .csv, .json, .log
  - strong: "Examples:"
  - text: Splunk exports, Prometheus data, CloudWatch logs
  - img
  - text: Click to upload files
  - heading "How Intelligent Analysis Works" [level=2]
  - heading "🤖 AI-Powered Content Detection" [level=3]
  - list:
    - listitem: • AI crew analyzes actual file content and structure
    - listitem: • Determines true data type regardless of upload category
    - listitem: • Assesses data quality and migration relevance
    - listitem: • Scores information value for your migration project
  - heading "📊 Intelligent Recommendations" [level=3]
  - list:
    - listitem: • Tailored processing workflow based on actual content
    - listitem: • Context-aware next steps for optimal migration planning
    - listitem: • Quality-based confidence scoring and issue identification
    - listitem: • Application-focused insights from any data type
  - img
  - paragraph:
    - strong: "Pro Tip:"
    - text: Don't worry about choosing the "perfect" category - our AI crew is designed to understand your data regardless of how you categorize it. Just pick the closest match and let the intelligence do the rest!
  - img
  - heading "Agent Clarifications" [level=3]
  - button "Refresh questions":
    - img
  - img
  - paragraph: No agent questions yet
  - paragraph: Agents will ask clarifications as they analyze your data
  - img
  - heading "Data Classification" [level=3]
  - text: by AI Agents
  - button "0 Good Data":
    - img
    - text: 0 Good Data
  - button "0 Needs Clarification":
    - img
    - text: 0 Needs Clarification
  - button "0 Unusable":
    - img
    - text: 0 Unusable
  - img
  - paragraph: No data classifications yet
  - paragraph: Agents will classify data as it's processed
  - img
  - heading "Agent Insights" [level=3]
  - text: 0 discoveries
  - button "Refresh insights":
    - img
  - button "All Insights 0"
  - button "Actionable 0"
  - button "High Confidence 0"
  - img
  - paragraph: No agent insights yet
  - paragraph: Agents will provide insights as they analyze your data
- button "Open AI Assistant and Feedback":
  - img
```

# Test source

```ts
   1 | import { test, expect } from '@playwright/test';
   2 |
   3 | test.describe('Data Import to Attribute Mapping Flow', () => {
   4 |   test('should successfully upload a file and navigate to attribute mapping', async ({ page }) => {
   5 |     // 1. Navigate to the Data Import page
   6 |     await page.goto('http://localhost:8081/discovery/data-import');
   7 |
   8 |     // Wait for the page to load and the upload zones to be visible
   9 |     await expect(page.locator('text=Upload Your Data')).toBeVisible();
  10 |
  11 |     // 2. Upload a sample CSV file
> 12 |     const fileUploadPromise = page.waitForEvent('filechooser');
     |                                    ^ Error: page.waitForEvent: Test timeout of 30000ms exceeded.
  13 |     await page.locator('text=CMDB Data').first().click();
  14 |     const fileChooser = await fileUploadPromise;
  15 |     
  16 |     // Create a dummy CSV file
  17 |     const csvContent = 'asset_name,ip_address,os\nserver1,192.168.1.1,Linux\nserver2,192.168.1.2,Windows';
  18 |     await fileChooser.setFiles({
  19 |       name: 'test_cmdb_import.csv',
  20 |       mimeType: 'text/csv',
  21 |       buffer: Buffer.from(csvContent),
  22 |     });
  23 |
  24 |     // 3. Wait for the analysis to complete
  25 |     // The analysis triggers a navigation, so we wait for the new page to load
  26 |     await page.waitForURL('**/discovery/attribute-mapping', { timeout: 15000 });
  27 |
  28 |     // 4. Verify that the application successfully navigates to the attribute mapping page
  29 |     await expect(page).toHaveURL(/.*attribute-mapping/);
  30 |     await expect(page.locator('h1:has-text("Attribute Mapping")')).toBeVisible();
  31 |     
  32 |     console.log('Successfully navigated to Attribute Mapping page.');
  33 |   });
  34 | }); 
```