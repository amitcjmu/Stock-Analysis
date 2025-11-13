# Debug Test Suite

These are **debugging helpers**, not production tests. They are excluded from CI/CD.

## Running Debug Tests
```bash
# Run all debug tests
npx playwright test tests/debug/

# Run specific debug test
npx playwright test tests/debug/migration-debug.spec.ts --headed
```

## When to Use

- Investigating test failures
- Debugging new page implementations
- Capturing API responses
- Understanding page structure

## NOT for CI/CD

These tests are intentionally excluded from the main test suite.
