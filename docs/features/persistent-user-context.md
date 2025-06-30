# Persistent User Context Management

## Overview

This feature ensures that when users switch context (client and engagement) via the breadcrumbs navbar, their selections are persisted to their user profile. This prevents the application from reverting to demo account context or default values when users refresh the page or navigate between pages.

## Problem Solved

**Before**: When users selected a different client/engagement via breadcrumbs:
1. Changes were only stored in localStorage
2. After page refresh, the system would revert to:
   - Demo account context (hardcoded fallback)
   - First available client/engagement (for platform admins)
   - User's original defaults (which were never updated)

**After**: User context selections are now persisted to their profile in the database, ensuring consistent context across sessions.

## Implementation

### Backend Changes

#### 1. New API Endpoint: `PUT /api/v1/context/me/defaults`

**File**: `/backend/app/api/v1/endpoints/context.py`

**Purpose**: Updates user's default client and engagement preferences in the database.

**Request Body**:
```json
{
  "client_id": "uuid-string",
  "engagement_id": "uuid-string"
}
```

**Response**:
```json
{
  "success": true,
  "message": "User defaults updated successfully",
  "updated_defaults": {
    "default_client_id": "uuid-string",
    "default_engagement_id": "uuid-string"
  }
}
```

**Security Features**:
- Validates user has access to specified client (RBAC enforcement)
- Platform admins can access any client
- Regular users must have explicit `ClientAccess` permission
- Special handling for demo user accessing demo client
- Validates that engagement belongs to specified client

#### 2. Database Schema

**File**: `/backend/app/models/client_account.py`

The `User` model already included the necessary fields:
```python
class User(Base):
    # Default Context (for faster context establishment)
    default_client_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    default_engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Relationships
    default_client = relationship("ClientAccount", foreign_keys=[default_client_id])
    default_engagement = relationship("Engagement", foreign_keys=[default_engagement_id])
```

#### 3. Context Resolution Logic

**File**: `/backend/app/api/v1/endpoints/context.py` (existing `GET /me` endpoint)

The existing context establishment logic already prioritizes user defaults:
```python
# Try to use user's default client if set
if current_user.default_client_id:
    default_client_query = select(ClientAccount).where(
        and_(
            ClientAccount.id == current_user.default_client_id,
            ClientAccount.is_active == True
        )
    )
    target_client = default_client_result.scalar_one_or_none()
```

### Frontend Changes

#### 1. Context API Helper

**File**: `/src/lib/api/context.ts`

**Purpose**: Clean API interface for context management.

**Key Functions**:
```typescript
export const updateUserDefaults = async (request: UpdateUserDefaultsRequest): Promise<UpdateUserDefaultsResponse>
export const getUserContext = async ()
export const getUserClients = async () 
export const getClientEngagements = async (clientId: string)
```

#### 2. AuthContext Integration

**File**: `/src/contexts/AuthContext.tsx`

**Changes Made**:

1. **Import the context API helper**:
```typescript
import { updateUserDefaults } from '@/lib/api/context';
```

2. **Update `switchClient` function** to persist client selection:
```typescript
// Update user defaults with just the client
try {
  await updateUserDefaults({ client_id: clientId });
  console.log('✅ Updated user default client:', clientId);
} catch (defaultError) {
  console.warn('⚠️ Failed to update user default client:', defaultError);
}
```

3. **Update `switchEngagement` function** to persist full context:
```typescript
// Update user defaults in the backend
try {
  await updateUserDefaults({
    client_id: client?.id,
    engagement_id: engagementId
  });
  console.log('✅ Updated user defaults - client:', client?.id, 'engagement:', engagementId);
} catch (defaultError) {
  console.warn('⚠️ Failed to update user defaults:', defaultError);
}
```

## User Experience Flow

### Context Selection Flow
1. **User selects new client** via breadcrumbs dropdown
2. **Frontend calls** `switchClient(clientId)`
3. **AuthContext updates** local state and localStorage
4. **Backend call** to `PUT /api/v1/context/me/defaults` with `client_id`
5. **User's profile updated** in database
6. **First engagement selected** automatically for the client
7. **Backend call** to `PUT /api/v1/context/me/defaults` with both `client_id` and `engagement_id`

### Context Restoration Flow
1. **User refreshes page** or navigates
2. **AuthContext initialization** calls `GET /api/v1/context/me`
3. **Backend resolves context** using user's `default_client_id` and `default_engagement_id`
4. **Context restored** to user's last selections
5. **No reversion** to demo account or random defaults

## Security Considerations

### Access Control
- **RBAC Enforcement**: Users can only set defaults for clients they have access to
- **Platform Admin Access**: Platform admins can access any client/engagement
- **Demo User Handling**: Special case for demo user accessing demo client
- **Validation**: Engagement must belong to the specified client

### Error Handling
- **Graceful Degradation**: If defaults update fails, context switching still works via localStorage
- **Fallback Logic**: If default client/engagement no longer exists, falls back to first available
- **Warning Logs**: Non-blocking warnings logged when defaults update fails

## Testing

### Backend Testing
```bash
# Test endpoint availability
docker exec migration_backend python -c "
from app.api.v1.endpoints.context import update_user_defaults
print('✅ Backend endpoint function imported successfully')
"

# Verify router registration
docker exec migration_backend python -c "
from app.api.v1.endpoints.context import router
print('Available endpoints:')
for route in router.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f'  {list(route.methods)[0]} {route.path}')
"
```

### Frontend Testing
```bash
# Test build with new context API integration
docker exec migration_frontend npm run build
```

## Benefits

### For Users
- **Consistent Experience**: Context persists across sessions and page refreshes
- **No Confusion**: No unexpected context switches to demo account
- **Productivity**: Users don't need to re-select their working context repeatedly

### For Platform Admins
- **Preference Persistence**: Their client/engagement selections are remembered
- **Efficient Workflow**: Can work across multiple clients without losing context

### For Regular Users
- **Secure Access**: Can only set defaults for clients they have permission to access
- **Automatic Restoration**: Last working context is restored on login

## Configuration

### Environment Variables
No new environment variables required. Uses existing:
- Database connection for user profile updates
- RBAC configuration for access validation

### Database Migrations
No new migrations required. Uses existing `default_client_id` and `default_engagement_id` fields in the `users` table.

## Monitoring

### Console Logging
- **Success**: `✅ Updated user defaults - client: {id}, engagement: {id}`
- **Warning**: `⚠️ Failed to update user defaults: {error}`
- **Debug**: Context resolution logs in backend

### Error Handling
- Non-blocking: Context switching works even if defaults update fails
- Graceful fallback to localStorage-only persistence
- Backend validation errors return proper HTTP status codes

## Future Enhancements

### Possible Improvements
1. **User Preferences Dashboard**: Allow users to manage their default context via UI
2. **Multiple Context Sets**: Allow users to save multiple "favorite" context combinations
3. **Team Defaults**: Organization-level default contexts
4. **Session Defaults**: Remember last session within each engagement
5. **Audit Trail**: Track context change history for compliance

### API Extensions
1. **GET /api/v1/context/me/defaults**: Get current user defaults
2. **DELETE /api/v1/context/me/defaults**: Clear user defaults
3. **POST /api/v1/context/me/favorites**: Save favorite context combinations