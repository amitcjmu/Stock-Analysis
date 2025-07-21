# Collection Flow RBAC Implementation

## Overview
This document describes the Role-Based Access Control (RBAC) implementation for collection flows, ensuring that users can only perform actions based on their assigned roles.

## Role Permissions

### Collection Flow Operations
- **View**: user, viewer, analyst, engagement_manager, admin (all roles)
- **Create**: analyst, engagement_manager, admin 
- **Edit**: analyst, engagement_manager, admin
- **Delete**: engagement_manager, admin

## Implementation Details

### Backend Changes

1. **Created RBAC utility module** (`backend/app/core/rbac_utils.py`):
   - `check_user_role()` - Checks if user has one of the allowed roles
   - `require_role()` - Enforces role requirements, raises 403 if unauthorized
   - Role constants for collection operations

2. **Updated collection API endpoints** (`backend/app/api/v1/endpoints/collection.py`):
   - Added `require_role()` check to `create_collection_flow` endpoint
   - Added `require_role()` check to `delete_flow` endpoint
   - Users without proper roles receive 403 Forbidden response

### Frontend Changes

1. **Created RBAC utility module** (`src/utils/rbac.ts`):
   - Permission checking functions: `canCreateCollectionFlow()`, `canDeleteCollectionFlow()`, etc.
   - Role name mapping: `getRoleName()`
   - Role constants matching backend

2. **Updated UI Components**:
   
   **AdaptiveForms.tsx**:
   - Added permission check before creating new flows
   - Shows error toast if user lacks create permission
   
   **CollectionUploadBlocker.tsx**:
   - Delete button only shown for users with delete permission
   - Uses `canDeleteCollectionFlow(user)` check
   
   **Index.tsx (Collection Overview)**:
   - Added role indicator showing current user role
   - Buttons disabled with tooltip for users without create permission
   - Shows "(View only)" label for users with read-only access

## User Experience

### For Users with View-Only Access (role: user/viewer)
- Can view all collection flows
- Cannot create new collection flows
- Cannot delete existing flows
- UI shows disabled buttons with explanatory tooltips
- Role badge shows their current role with "(View only)" indicator

### For Analysts (role: analyst)
- Can view all collection flows
- Can create new collection flows
- Can edit existing flows
- Cannot delete flows
- Delete button is hidden from UI

### For Managers and Admins (role: engagement_manager/admin)
- Full access to all operations
- Can create, view, edit, and delete collection flows
- All UI buttons are enabled

## Testing

To test the RBAC implementation:

1. Login as different users with different roles
2. Verify that:
   - Users with 'user' role see disabled create buttons
   - Users with 'user' role don't see delete buttons
   - Analysts can create but not delete flows
   - Managers can perform all operations

## Security Considerations

- Backend enforcement ensures security even if frontend checks are bypassed
- 403 Forbidden responses include clear error messages
- Role checks are performed on every API request
- Frontend checks provide immediate feedback to users

## Future Enhancements

1. Add audit logging for permission denied attempts
2. Implement more granular permissions (e.g., edit own flows only)
3. Add role-based filtering of flows (show only relevant flows)
4. Implement delegation of permissions