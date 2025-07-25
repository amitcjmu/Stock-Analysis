# One-Time Fix Scripts

⚠️ **ARCHIVED - DO NOT RUN WITHOUT UNDERSTANDING CONTEXT**

These scripts were created during the platform remediation phase to fix specific issues. They are kept for historical reference only.

## Scripts

### add_client_context.py
- **Purpose**: Added client context to JSON data files during multi-tenant implementation
- **Created**: During Phase 5 flow-based architecture implementation
- **Status**: Completed - functionality now built into the platform

### fix_field_mappings_context.py
- **Purpose**: Fixed field mappings context by updating to demo context values
- **Created**: During field mapping UI issues remediation
- **Status**: Completed - field mapping context now properly handled

### complete_active_flows.py
- **Purpose**: Manually completed active discovery flows to stop polling
- **Created**: During session_id → flow_id migration
- **Status**: Completed - flow completion now handled automatically

### promote_assets.py
- **Purpose**: Promoted discovery assets to main assets table
- **Created**: During database consolidation (ADR-005)
- **Status**: Completed - asset promotion now automatic

## Warning

These scripts directly modify database state and were designed for specific migration scenarios. Do not run them without:
1. Understanding the original issue they addressed
2. Verifying the issue still exists
3. Testing in a non-production environment first
