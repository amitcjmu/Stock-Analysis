# Collection Flow E2E Tests

This directory contains end-to-end tests for the Collection Flow functionality using Playwright.

## Overview

The collection flow tests validate:
- Collection overview page functionality
- Adaptive forms creation and management
- Collection flow lifecycle (create, continue, delete)
- Authentication error handling (401 redirects)
- Bulk upload functionality
- Progress tracking
- Flow management operations

## Prerequisites

1. **Frontend**: Must be running on `http://localhost:5173`
   ```bash
   npm run dev
   ```

2. **Backend**: Must be running on `http://localhost:8000`
   ```bash
   cd backend && uvicorn app.main:app --reload
   ```

3. **Demo Account**: Tests use the demo account credentials:
   - Email: `demo@demo-corp.com`
   - Password: `Demo123!`

## Running the Tests

### Using the Test Runner Script (Recommended)
```bash
./tests/e2e/run-collection-tests.sh
```

This script will:
- Check that required services are running
- Run all collection flow tests
- Generate an HTML report
- Provide a summary of results

### Using Playwright Directly
```bash
# Run all collection tests
npx playwright test tests/e2e/collection-flow.spec.ts

# Run in headed mode (see browser)
npx playwright test tests/e2e/collection-flow.spec.ts --headed

# Run a specific test
npx playwright test tests/e2e/collection-flow.spec.ts -g "should create a new collection flow"

# Debug mode
npx playwright test tests/e2e/collection-flow.spec.ts --debug
```

### Using Playwright MCP Server

The tests are designed to work with the Playwright MCP server. Agents can run these tests by:

1. Navigating to the test directory
2. Using the MCP browser tools to execute the test scenarios
3. Validating the collection flow functionality

## Test Structure

### Main Test Suite: Collection Flow E2E Tests
1. **Overview Page Tests**
   - Validates page layout and main sections
   - Checks for collection options visibility

2. **Adaptive Forms Tests**
   - Navigation to adaptive forms
   - Form validation
   - Flow creation process

3. **Flow Management Tests**
   - Incomplete flow handling
   - Flow deletion
   - Flow continuation

4. **Error Handling Tests**
   - 401 authentication error handling
   - Network error resilience

### Secondary Suite: Collection Flow Management
- Flow management page access
- Batch operations
- Advanced flow controls

## Test Configuration

Tests are configured with:
- **Timeout**: 120 seconds per test
- **Retries**: 1 retry on failure
- **Mode**: Can run in headed or headless mode

## Debugging Failed Tests

1. **View Screenshots**: Playwright captures screenshots on failure
   ```bash
   ls test-results/
   ```

2. **View Traces**: Enable trace recording for detailed debugging
   ```bash
   npx playwright test --trace on
   ```

3. **Interactive Debugging**:
   ```bash
   npx playwright test --debug
   ```

## Common Issues

### Services Not Running
- Ensure both frontend and backend are running before tests
- The test runner script checks this automatically

### Authentication Failures
- Verify the demo account exists in the database
- Check that authentication endpoints are working

### Timeout Errors
- Increase timeout in test configuration if needed
- Check for slow API responses

## Adding New Tests

To add new collection flow tests:

1. Add test cases to `collection-flow.spec.ts`
2. Follow the existing pattern:
   ```typescript
   test('should [action description]', async ({ page }) => {
     // Test implementation
   });
   ```

3. Use descriptive test names
4. Include proper assertions
5. Handle edge cases gracefully

## CI Integration

For CI pipelines:
```bash
# Run in headless mode with CI reporter
PLAYWRIGHT_HEADLESS=true npx playwright test tests/e2e/collection-flow.spec.ts --reporter=junit
```

## Maintenance

- Update tests when UI changes
- Keep selectors up to date
- Add data-testid attributes to UI components for stable selectors
- Review and update demo data as needed