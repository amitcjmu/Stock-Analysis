# Test Data Validation Patterns - Real vs Mock Data

## Critical Discovery: Tests Using Invalid UUIDs
Tests were using placeholder UUIDs like 'demo-client-id' causing foreign key violations.

## Correct Test Data Approach

### Use Real Database UUIDs
```typescript
// WRONG - Invalid placeholder
const TEST_TENANT_ID = 'demo-client-id';

// CORRECT - Real demo tenant from database
const TEST_TENANT_ID = '11111111-1111-1111-1111-111111111111';
```

### Query Real Data for Tests
```typescript
// Instead of hardcoding, query actual test data
const demoUser = await db.query(
  "SELECT * FROM users WHERE email = 'demo@demo-corp.com'"
);
const realTenantId = demoUser.client_account_id;
```

## Validation Principles
1. **Use Real Database Data** - Not mock UUIDs
2. **Respect Foreign Keys** - All IDs must exist in parent tables
3. **Follow Data Relationships** - tenant → engagement → flow
4. **Validate Cascade Effects** - Deletes/updates should cascade properly

## Common UUID Patterns in This Codebase
- Demo Tenant: `11111111-1111-1111-1111-111111111111`
- Demo Engagement: Usually created dynamically
- Demo User: Query by email `demo@demo-corp.com`
