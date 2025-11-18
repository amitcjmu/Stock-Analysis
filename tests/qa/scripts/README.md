# QA Verification Scripts

This directory contains JavaScript-based QA verification scripts for manual testing and validation.

## Files

### qa-verification-script.js
Comprehensive QA verification script that tests multiple flows and features.

**Purpose**:
- Verifies discovery flow execution
- Tests collection flow phases
- Validates assessment flow functionality
- Checks UI state and data consistency

**Usage**:
```bash
node tests/qa/scripts/qa-verification-script.js
```

**Features**:
- Automated API endpoint testing
- Multi-flow validation
- Response structure verification
- Error scenario testing

### qa-verify-no-active-flow.js
Specific QA script to verify behavior when no active flows exist.

**Purpose**:
- Tests UI behavior with empty states
- Validates error handling for missing flows
- Checks default states and fallbacks

**Usage**:
```bash
node tests/qa/scripts/qa-verify-no-active-flow.js
```

**Use Cases**:
- Testing fresh installations
- Verifying cleanup operations
- Validating empty state UI

## Important Notes

- These are manual QA scripts (not part of automated test suites)
- Run from project root directory
- Require backend and frontend services to be running
- Check script headers for environment variables needed

## Relationship to E2E Tests

These scripts complement but don't replace:
- Playwright E2E tests in `/tests/e2e/`
- Backend integration tests in `/backend/tests/`
- Jest unit tests

Use these for:
- Manual exploratory testing
- Quick verification of bug fixes
- Ad-hoc testing scenarios

## Location
`/tests/qa/scripts/`
