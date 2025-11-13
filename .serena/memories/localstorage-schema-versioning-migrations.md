# localStorage Schema Versioning for Migrations

## Purpose
Track localStorage data format changes across migrations (e.g., INTEGER → UUID tenant IDs) to prevent stale data corruption.

## Pattern
```typescript
// storage.ts
const STORAGE_SCHEMA_VERSION = 2;  // Increment on breaking changes
const SCHEMA_VERSION_KEY = 'auth_storage_schema_version';

export const validateAndClearStaleData = (): boolean => {
  const storedVersion = localStorage.getItem(SCHEMA_VERSION_KEY);
  const currentVersion = STORAGE_SCHEMA_VERSION.toString();

  if (storedVersion !== currentVersion) {
    console.log(`📦 Schema mismatch: stored=${storedVersion}, current=${currentVersion}`);
    clearInvalidContextData();  // Clear stale data, preserve auth token
    localStorage.setItem(SCHEMA_VERSION_KEY, currentVersion);
    return true;  // Cleared
  }
  return false;  // Valid
};

export const clearInvalidContextData = (): void => {
  // Clear context but preserve auth token and schema version
  localStorage.removeItem('auth_client');
  localStorage.removeItem('auth_engagement');
  localStorage.removeItem('auth_client_id');
  localStorage.removeItem('user_context_selection');
  // DO NOT remove: auth_token, auth_storage_schema_version
};
```

## Critical: Logout Must Preserve Schema Version
```typescript
// WRONG - Breaks schema versioning
const logout = () => {
  clearAllStoredData();  // Removes schema version ❌
  navigate('/login');
};

// CORRECT - Preserves schema version
const logout = () => {
  // Explicit cleanup
  tokenStorage.removeToken();
  tokenStorage.removeRefreshToken();
  tokenStorage.removeUser();
  contextStorage.clearContext();

  // Clear context keys
  localStorage.removeItem('auth_client');
  localStorage.removeItem('auth_engagement');
  localStorage.removeItem('auth_flow');

  // PRESERVE: auth_storage_schema_version ✅
  navigate('/login');
};
```

## Why Schema Version Persists Across Sessions
- It's about **data format**, not user session
- Tells app if localStorage data is compatible with current code
- Cleared only when code explicitly updates version
- NOT tied to login/logout cycle

## When to Increment Version
```typescript
// migration 115: client_account_id INTEGER → UUID
const STORAGE_SCHEMA_VERSION = 1;  // Before migration

// After migration deployed
const STORAGE_SCHEMA_VERSION = 2;  // Triggers cleanup of old INTEGER IDs
```

## App Initialization
```typescript
// appInitializer.ts
const wasCleared = validateAndClearStaleData();
if (wasCleared) {
  console.log('📦 localStorage schema updated - user will re-fetch fresh data');
}
```

## Testing
1. Set version to 1 in localStorage
2. Refresh app (code has version 2)
3. Verify: context cleared, schema version set to 2
4. Logout and login
5. Verify: context persists, version still 2

## Common Bug
**Symptom**: Context resets after every login
**Cause**: Logout clears schema version
**Fix**: Preserve `auth_storage_schema_version` during logout

## Related
- PR #867: Original schema versioning implementation
- Migration 115: INTEGER → UUID conversion
