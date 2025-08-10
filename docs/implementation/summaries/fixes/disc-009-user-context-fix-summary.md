# DISC-009: User Context Service Fixes

## Issue
Users were encountering the error: "Failed to get active flows for user: 'engagement_id'" which prevented them from seeing their flows in the UI.

## Root Cause
The error was caused by multiple issues in the user context handling:

1. **KeyError in UserService**: The code was trying to access `flow["engagement_id"]` without checking if the key exists
2. **Missing context validation**: The discovery flow query endpoints were not handling cases where engagement_id might be None
3. **Syntax error in base_flow.py**: A positional argument was following a keyword argument

## Fixes Implemented

### 1. Created User Context Service (`app/services/user_context_service.py`)
- Properly loads user relationships with `selectinload`
- Handles missing engagement context gracefully
- Provides fallback logic when engagement is None
- Validates user context and permissions

### 2. Updated Discovery Flow Query Endpoints (`app/api/v1/endpoints/discovery_flows/query_endpoints.py`)
- Added proper context validation
- Handles cases where engagement_id is None
- Attempts to resolve engagement_id from user context if missing
- Provides better error messages for context issues

### 3. Fixed UserService Flow Handling (`app/api/v1/endpoints/context/services/user_service.py`)
- Used `.get()` method instead of direct dictionary access for flow fields
- Added fallbacks for missing keys (id/flow_id, name/flow_name, engagement_id)
- Added specific error handlers for AttributeError and KeyError
- Improved error logging to capture context state

### 4. Fixed Syntax Error (`app/services/crewai_flows/unified_discovery_flow/base_flow.py`)
- Added missing parameter name `previous_result=` to function call

## API Changes
No breaking API changes. The endpoints now handle missing context more gracefully:
- `/api/v1/discovery/flows/active` - Returns flows even without engagement_id
- `/api/v1/discovery/flows/summary` - Handles missing engagement context

## Testing Recommendations
1. Test with users who have no engagement assigned
2. Test with missing context headers
3. Verify flows are visible for users with proper context
4. Check error messages are user-friendly

## Error Handling Improvements
- Specific error messages for missing context
- Graceful fallbacks when engagement is not available
- Better logging for debugging context issues
- User-friendly error messages that don't expose internal errors
