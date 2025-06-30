# Field Mapping Approval Fix Summary

## Problem
The field mapping approval/reject functionality was failing with a foreign key constraint error because the `data_import_id` was not being stored in the `discovery_flows` table.

## Root Cause
1. The `DiscoveryFlow` model has a `data_import_id` field, but it was not being populated when creating flows
2. The field mapping approval endpoints require `data_import_id` to create field mapping records
3. When `flow.data_import_id` was null, the API calls failed

## Solution

### 1. Fixed DiscoveryFlowRepository (app/repositories/discovery_flow_repository.py)
- Added `data_import_id` parameter to `create_discovery_flow` method
- Updated the flow creation to store `data_import_id` in addition to `import_session_id`

### 2. Fixed DiscoveryFlowService (app/services/discovery_flow_service.py)
- Updated the service to pass both `import_session_id` and `data_import_id` when creating flows
- This ensures backward compatibility while properly storing the data import reference

### 3. Created Migration Script (scripts/fix_discovery_flow_data_import_id.py)
- Fixed 13 existing discovery flows that had `import_session_id` but no `data_import_id`
- The script copies `import_session_id` to `data_import_id` for all affected flows

## Testing
After the fix:
- Existing flows now have `data_import_id` populated
- New flows created through the data import process will have `data_import_id` set correctly
- Field mapping approval/reject should now work without foreign key errors

## Next Steps
1. Test the field mapping approval functionality in the UI
2. Monitor for any new flows to ensure they have `data_import_id` populated
3. Consider adding a database constraint to ensure `data_import_id` is always set when `import_session_id` is present