# Test Data UUID Requirements

## The Problem
Tests were using invalid placeholder UUIDs that caused database foreign key violations:
- Used: `'demo-client-id'`, `'demo-engagement-id'`
- These are strings, not valid UUIDs
- Database rejects them with FK constraint errors

## Actual Demo UUIDs in Database
From `backend/seeding/constants.py`:
```python
DEMO_CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
```

## Test Configuration
```typescript
// tests/e2e/regression/discovery/discovery-flow-full-e2e-regression.spec.ts
tenantHeaders = {
  'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',  // Real UUID
  'X-Engagement-ID': '22222222-2222-2222-2222-222222222222'       // Real UUID
};
```

## Getting IDs from LocalStorage
```typescript
// After login, get real IDs
const localStorage = await page.evaluate(() => {
  return {
    clientAccountId: localStorage.getItem('auth_client_id') || '11111111-1111-1111-1111-111111111111',
    engagementId: localStorage.getItem('engagementId') || '22222222-2222-2222-2222-222222222222'
  };
});
```

## Demo User Credentials
```typescript
TEST_USERS = {
  demo: {
    email: 'demo@demo-corp.com',
    password: 'Demo123!',
    role: 'user'
  }
}
```

## Key Principles
1. **Always use real database UUIDs** - No placeholders
2. **Check seeding/constants.py** - Source of truth for test data
3. **Verify with database** - Ensure records exist
4. **Use localStorage after login** - Get actual session IDs

## Common Demo User IDs
- Admin: `55555555-5555-5555-5555-555555555555`
- Demo User: `44444444-4444-4444-4444-444444444444`
- Test flows should use these existing records
