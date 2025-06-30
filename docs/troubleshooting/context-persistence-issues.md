# Context Persistence Troubleshooting Guide

## Issue: Context switching works but persistence may fail with 403/404 errors

Based on the browser console errors, the context switching appears to work in the UI, but the backend persistence may be failing. This document provides comprehensive troubleshooting steps.

## Current Implementation Status

### ✅ Backend Implementation
- **API Endpoint**: `PUT /api/v1/context/me/defaults` is properly registered and available
- **Router Integration**: Context router is included in main API at `/api/v1/context/*`
- **Authentication**: Endpoint requires valid authentication token
- **Authorization**: RBAC enforcement validates user access to specified client/engagement

### ✅ Frontend Implementation  
- **API Helper**: `/src/lib/api/context.ts` provides clean interface
- **AuthContext Integration**: Calls backend API when context switches occur
- **Error Handling**: Non-blocking - context switching works even if backend persistence fails
- **Debugging**: Enhanced logging for troubleshooting

## Troubleshooting Steps

### 1. Check Browser Console for Detailed Error Information

Look for these log messages:
```javascript
// Success case
"🔄 Updating user defaults: {client_id: 'uuid', engagement_id: 'uuid'}"
"✅ User defaults updated successfully: {success: true, ...}"

// Error case  
"❌ Failed to update user defaults: {error: 'details', status: 403, request: {...}}"
"⚠️ Continuing with localStorage-only context persistence"
```

### 2. Verify Authentication Token

Check in browser console:
```javascript
// Check if auth token exists
localStorage.getItem('auth_token')

// Check current user context
JSON.parse(localStorage.getItem('user_data') || '{}')
```

### 3. Verify API Endpoint Availability

Test the endpoint directly in browser DevTools Network tab:
1. Switch to Network tab
2. Filter by "context"
3. Switch client/engagement via breadcrumbs
4. Look for `PUT /api/v1/context/me/defaults` request
5. Check status code and response

### 4. Check Backend Logs

In Docker container:
```bash
docker logs migration_backend | grep -i "context\|defaults\|403\|404"
```

### 5. Test Context Endpoint Manually

```bash
# Test if endpoint is available
docker exec migration_backend python -c "
from app.api.v1.endpoints.context import router
for route in router.routes:
    if hasattr(route, 'path') and 'defaults' in route.path:
        print(f'Found: {list(route.methods)[0]} {route.path}')
"
```

## Common Issues and Solutions

### Issue 1: 403 Forbidden Error

**Cause**: User lacks permission to update defaults for the selected client

**Solutions**:
1. **For Regular Users**: Ensure user has `ClientAccess` record for the client
2. **For Platform Admins**: Verify user has `platform_admin` role in `UserRole` table
3. **For Demo User**: Ensure accessing demo client ID `11111111-1111-1111-1111-111111111111`

**Debug Query** (in database):
```sql
-- Check user roles
SELECT ur.role_type, ur.is_active 
FROM user_roles ur 
WHERE ur.user_id = 'your-user-id';

-- Check client access
SELECT ca.client_account_id, ca.access_level 
FROM client_access ca 
WHERE ca.user_profile_id = 'your-user-id';
```

### Issue 2: 404 Not Found Error

**Cause**: Endpoint not properly registered or client/engagement doesn't exist

**Solutions**:
1. **Verify Router Registration**: Ensure context router is included in main API
2. **Check Client Exists**: Verify client ID exists and is active
3. **Check Engagement Exists**: Verify engagement belongs to specified client

### Issue 3: 422 Validation Error

**Cause**: Invalid UUID format or missing required fields

**Solutions**:
1. **Check UUID Format**: Ensure IDs are valid UUIDs
2. **Verify Engagement-Client Relationship**: Engagement must belong to specified client

### Issue 4: Context Works but Doesn't Persist After Refresh

**Symptoms**: Context switching works immediately but reverts after page refresh

**Debugging**:
1. Check if API call succeeds: Look for success log messages
2. Verify user defaults in database:
   ```sql
   SELECT default_client_id, default_engagement_id 
   FROM users 
   WHERE id = 'your-user-id';
   ```
3. Check context resolution in `/context/me` endpoint

## Fallback Behavior

### LocalStorage-Only Persistence

If backend persistence fails, the system falls back to localStorage-only persistence:

**Advantages**:
- Context switching still works within the same browser session
- No blocking of user workflow
- Graceful degradation

**Limitations**:
- Context doesn't persist across different browsers/devices
- Reverts to defaults after cache clear

### Manual Testing

Test localStorage persistence:
```javascript
// Set context manually
localStorage.setItem('auth_client', JSON.stringify({
  id: 'client-uuid',
  name: 'Test Client'
}));

localStorage.setItem('auth_engagement', JSON.stringify({
  id: 'engagement-uuid', 
  name: 'Test Engagement'
}));

// Refresh page and check if context is restored
```

## Monitoring and Debugging

### Console Logging

The implementation includes comprehensive logging:

**Context Switching**:
```
🔄 Switching to client: {clientId}
🔄 Switching to engagement: {engagementId}
```

**Backend Persistence**:
```
✅ Updated user default client: {clientId}
✅ Updated user defaults - client: {clientId}, engagement: {engagementId}
```

**Error Handling**:
```
❌ Failed to update user defaults: {error details}
⚠️ Failed to update user defaults (non-blocking): {message}
```

### Performance Impact

- **Non-blocking**: Backend persistence failures don't interrupt user workflow
- **Async**: API calls are asynchronous and don't block UI updates
- **Cached**: Context resolution uses user defaults for faster loading

## Production Deployment Considerations

### Environment Variables

Ensure these are set correctly:
```env
# Backend
DATABASE_URL=postgresql://...
DEEPINFRA_API_KEY=your_key

# Frontend  
VITE_BACKEND_URL=https://your-railway-app.railway.app
```

### Database Health

Verify database connectivity and user/client data integrity:
```sql
-- Check users table has default columns
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name LIKE '%default%';

-- Verify demo data exists
SELECT id, name FROM client_accounts WHERE id = '11111111-1111-1111-1111-111111111111';
```

## Recovery Procedures

### Reset User Defaults

If user defaults become corrupted:
```sql
-- Clear user defaults
UPDATE users 
SET default_client_id = NULL, default_engagement_id = NULL 
WHERE id = 'user-id';

-- Set to first available client
UPDATE users 
SET default_client_id = (
  SELECT ca.client_account_id 
  FROM client_access ca 
  WHERE ca.user_profile_id = users.id 
  LIMIT 1
) 
WHERE id = 'user-id';
```

### Clear Browser State

If localStorage becomes corrupted:
```javascript
// Clear all auth-related localStorage
['auth_token', 'user_data', 'auth_client', 'auth_engagement', 'auth_session'].forEach(key => {
  localStorage.removeItem(key);
});

// Refresh page to trigger re-authentication
window.location.reload();
```

## Future Enhancements

### Enhanced Error Reporting
- Add error reporting to monitoring system
- Include detailed context information in error logs
- User-friendly error messages in UI

### Improved Fallback Strategies
- Retry logic for transient failures
- Multiple persistence backends (localStorage + IndexedDB)
- Offline-first approach with sync

### User Experience Improvements
- Loading indicators during context updates
- Success/failure toast notifications
- Context history and quick switching