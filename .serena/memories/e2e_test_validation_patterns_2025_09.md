# E2E Test Validation Patterns - Critical Learnings

## The Problem: Tests Pass Despite Real Issues
Tests were passing with API 200 status even when:
- No field mappings existed
- Users were blocked from proceeding
- Required actions were incomplete

## Critical Validation Patterns

### 1. Blocking Flow Detection
```typescript
// After login, check for blocking flows
const blockingBanner = page.locator('[data-testid="blocking-flow"]');
const hasBlockingFlow = await blockingBanner.isVisible({ timeout: 5000 });

if (hasBlockingFlow) {
  const blockingText = await blockingBanner.textContent();
  // Validate with backend API
  const statusResponse = await apiContext.get('/api/v1/unified-discovery/flows/current/status');
  const status = await statusResponse.json();
  if (status.blocked || status.requires_action) {
    // Test should FAIL - user is blocked
  }
}
```

### 2. Field Mapping Validation
```typescript
// Don't just check API status - validate data
const mappings = await mappingsResponse.json();
const mappingArray = Array.isArray(mappings) ? mappings : (mappings.mappings || []);

// CRITICAL: Fail if no mappings
if (mappingArray.length === 0) {
  throw new Error('No field mappings - user blocked');
}

// Check for unmapped fields
const unmappedFields = mappingArray.filter(m => !m.target_field || m.status === 'pending');
if (unmappedFields.length > 0) {
  // User cannot proceed
}
```

### 3. User Journey Validation
```typescript
// Check if user can actually proceed
const continueButton = page.locator('button:has-text("Continue"), [data-testid="continue-flow"]');
const canProceed = await continueButton.isEnabled();

if (!canProceed) {
  // Test MUST fail - user is blocked
}
```

### 4. Retry Logic for Async Operations
```typescript
// Wait for async data generation
let retryCount = 0;
const maxRetries = 10;

while (retryCount < maxRetries) {
  const response = await apiContext.get('/api/v1/flows/{id}/field-mappings');
  const data = await response.json();

  if (data.length > 0 || retryCount >= maxRetries - 1) {
    break;
  }

  await page.waitForTimeout(3000);
  retryCount++;
}
```

### 5. Layer-Specific Error Reporting
```typescript
interface LayeredError {
  layer: 'frontend' | 'middleware' | 'backend' | 'database';
  type: string;
  message: string;
  page: string;  // Which page error occurred
  timestamp: string;
}

// Report errors by layer
if (status >= 500) {
  addLayeredError('backend', 'HTTP 500', url);
} else if (status >= 400) {
  addLayeredError('middleware', 'HTTP 4xx', url);
}
```

## Key Principles
1. **Test Business Logic, Not Just API Status** - 200 OK doesn't mean success
2. **Follow User Journey** - Don't navigate directly to pages
3. **Validate UI State** - Check if buttons are enabled/disabled
4. **Verify Database Persistence** - Ensure data is actually saved
5. **Use Stable Selectors** - Prefer data-testid over CSS classes
6. **Add Retry Logic** - Handle async operations with polling
7. **Continue on Error** - Gather all issues, don't stop at first failure

## Common Mistakes to Avoid
- ❌ Passing test if API returns 200 with empty data
- ❌ Direct navigation instead of following user flow
- ❌ Not checking if user can proceed
- ❌ Using fragile array indexing for steps
- ❌ Throwing errors that stop test execution
- ❌ Short timeouts for async operations
