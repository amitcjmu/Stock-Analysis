# Discovery Flow Synchronization Issues - Troubleshooting Guide

## Overview
This document summarizes the learnings from troubleshooting discovery flow synchronization issues in the AI Force Migration Platform. These issues manifested as flows showing as active on the overview page but displaying "flow not found" when viewing details, along with missing data and UI components.

## Architecture Understanding

### 1. Discovery Flow System
- **Primary Flow**: UnifiedDiscoveryFlow (CrewAI-based) located at `/backend/app/services/crewai_flows/unified_discovery_flow.py`
- **Flow ID Management**: The system uses `flow_id` (not `session_id`) as the primary identifier
- **Data Import Endpoint**: `/api/v1/data-import/store-import` is the correct agentic endpoint that triggers CrewAI flows
- **Frontend Route**: `/discovery/cmdb-import` is the correct page (despite the legacy naming)

### 2. Key Components
```
Frontend Flow:
CMDBImport.tsx → uploads data → /data-import/store-import API
                              ↓
                   Creates UnifiedDiscoveryFlow with CrewAI agents
                              ↓
                   Updates discovery_flows table in PostgreSQL
                              ↓
AttributeMapping.tsx → retrieves field mappings from flow state
```

### 3. Multi-Tenant Architecture
- All database queries are scoped by `client_account_id` and `engagement_id`
- Context is passed via headers: `X-Client-Account-Id`, `X-Engagement-Id`
- Default/placeholder UUIDs: `11111111-1111-1111-1111-111111111111` (often cause issues)

## Common Issues and Solutions

### Issue 1: Flows Not Appearing in Active List
**Symptom**: Flow created but not showing in active flows list
**Root Cause**: Flow created with status "initialized" but query only looked for ["active", "running", "paused"]
**Solution**: Added "initialized" to `valid_active_statuses` in `DiscoveryFlowRepository`

### Issue 2: Context Mismatch
**Symptom**: Flow status returns 404 even though flow exists
**Root Cause**: Flow created with actual client IDs but status requests use placeholder UUIDs
**Solution**: Implemented fallback to global search in `FlowManagementHandler.get_flow_status()`

### Issue 7: Attribute Mapping Page Shows 0 Active Flows (v0.9.1)
**Symptom**: Attribute mapping page displays "No Field Mapping Available" with 0 flows despite flows existing
**Root Cause**: Multiple context header issues:
1. Frontend sends inconsistent `X-Client-Account-Id` values across different API calls
2. Flows created with one context (e.g., `11111111-1111-1111-1111-111111111111`) not found when queried with different context (e.g., `dfea7406-1575-4348-a0b2-2770cbe2d9f9`)
3. `UnifiedDiscoveryService` was hardcoding demo context headers that overrode actual auth headers

**Solution**: 
- Enhanced `FlowManagementHandler.get_active_flows()` to fall back to global search if no flows found with current context
- Updated `get_flow_status()` to switch repository context when flow found globally
- Removed hardcoded headers from `UnifiedDiscoveryService.httpClient.request()`
- Added logging to track context switching for debugging

**Files Modified**:
- `backend/app/api/v1/discovery_handlers/flow_management.py`
- `src/services/discoveryUnifiedService.ts`

**Validation**: 
- Active flows API now returns flows properly (9 flows for demo context, 7 for real context)
- Flow status API successfully retrieves flow data with field mapping information

### Issue 3: Frontend Shows 0% Progress
**Symptom**: Flow completed but frontend stuck at "Waiting for processing to begin..."
**Root Cause**: Frontend didn't handle "active" status with 100% progress as completed
**Solution**: Updated `UniversalProcessingStatus` component status detection logic

### Issue 4: No Processing Statistics
**Symptom**: "0 Records Processed" despite successful upload
**Root Cause**: Processing statistics not tracked or returned in API responses
**Solution**: 
- Added `records_processed`, `records_total`, `records_valid` to API responses
- Updated UnifiedDiscoveryFlow to track these during data import
- Modified flow state persistence to store at root level

### Issue 5: Missing Field Mappings
**Symptom**: Attribute mapping page shows "No Field Mapping Available"
**Root Cause**: Frontend trying to fetch from empty `/data-import/mappings` endpoint instead of flow state
**Solution**: Modified `useAttributeMappingLogic` to retrieve mappings from flow state data

### Issue 6: Incorrect Routing
**Symptom**: 404 errors on `/upload-data` route
**Root Cause**: Multiple places had incorrect navigation paths
**Solution**: Updated all references to use `/discovery/cmdb-import`

## Key Files to Know

### Backend
1. **Flow Management**:
   - `/backend/app/api/v1/discovery_handlers/flow_management.py` - Main flow status API
   - `/backend/app/repositories/discovery_flow_repository.py` - Database queries for flows
   - `/backend/app/services/crewai_flows/unified_discovery_flow.py` - Main CrewAI flow

2. **Data Import**:
   - `/backend/app/api/v1/endpoints/data_import/handlers/import_storage_handler.py` - Handles data upload and triggers flow

3. **Flow State**:
   - `/backend/app/services/crewai_flows/flow_state_bridge.py` - Bridges CrewAI and PostgreSQL
   - `/backend/app/services/crewai_flows/postgresql_flow_persistence.py` - Persists flow state

### Frontend
1. **Hooks**:
   - `/src/hooks/useRealTimeProcessing.ts` - Polls for flow status updates
   - `/src/hooks/discovery/useAttributeMappingLogic.ts` - Loads field mappings
   - `/src/hooks/discovery/useDiscoveryFlowAutoDetection.ts` - Auto-detects active flows

2. **Components**:
   - `/src/components/discovery/UniversalProcessingStatus.tsx` - Shows flow progress
   - `/src/pages/discovery/AttributeMapping.tsx` - Field mapping page
   - `/src/pages/discovery/EnhancedDiscoveryDashboard.tsx` - Overview dashboard

## Debugging Tips

### 1. Check Flow Creation
```sql
-- Find flows by client
SELECT flow_id, status, current_phase, progress_percentage, created_at 
FROM discovery_flows 
WHERE client_account_id = 'YOUR_CLIENT_ID'
ORDER BY created_at DESC;

-- Check flow state data
SELECT flow_id, crewai_state_data->>'records_processed' as records
FROM discovery_flows
WHERE flow_id = 'YOUR_FLOW_ID';
```

### 2. Console Debugging
Look for these patterns in browser console:
- `🔍 Flow detection results:` - Shows if flows are found
- `📊 Processing flow data:` - Shows field mapping retrieval
- `UniversalProcessingStatus: Retrieved active flow` - Shows flow status updates
- `🔍 Getting active flows from PostgreSQL for context` - Backend context logging
- `✅ Found X active flows globally` - Global search fallback success

### 3. Context Header Debugging (v0.9.1)
Check backend logs for context switching:
- `🔍 Flow not found with current context` - Indicates context mismatch
- `✅ Flow found globally - client: X, engagement: Y` - Global search success
- `🔍 No flows found with current context, trying global search` - Fallback triggered

Monitor frontend auth headers:
- `🔍 getAuthHeaders Debug:` - Shows current context values
- `✅ Added X-Client-Account-ID header:` - Confirms header inclusion
- `⚠️ No client or client.id available` - Missing context warning

### 4. Common API Endpoints
- `GET /api/v1/discovery/flow/status/{flow_id}` - Get flow status (updated endpoint)
- `POST /api/v1/data-import/store-import` - Upload data and create flow
- `GET /api/v1/discovery/flows/active` - List active flows (context-aware with fallback)

### 5. Event Listener
The `discovery_flow_listener.py` tracks CrewAI events and updates database status. Check logs for:
- `🚀 Discovery Flow started`
- `✅ CrewAI flow phase completed`
- `🎯 Flow ID extracted from`

## Best Practices

1. **Always Include Context Headers**: Ensure X-Client-Account-Id and X-Engagement-Id are set
2. **Use Flow ID, Not Session ID**: The system migrated from session_id to flow_id
3. **Check Multiple Status Fields**: Flows can have status "initialized", "active", "running", "completed"
4. **Verify Data at Each Layer**: CrewAI state → PostgreSQL → API response → Frontend
5. **Look for Processing Statistics**: Ensure records_processed, records_total are tracked

## UI/UX Improvements (v0.9.1)

### Attribute Mapping Page Layout Reorganization
**Enhancement**: Moved Flow Detection Debug Info and Discovery Flow Crew Progress to bottom of page
**Rationale**: Focus on the 4 main tabs (imported data, field mapping, critical attributes, training progress)
**Implementation**:
- Debug info and crew progress moved to bottom section with border separator
- Main content grid now prominently displays the core functionality tabs
- Improved visual hierarchy for better user experience
**Files**: `src/pages/discovery/AttributeMapping.tsx`

## Remaining Known Issues

1. **Breadcrumbs/Agent Panels**: Sometimes don't render on certain pages
2. **Field Mapping Generation**: CrewAI agents might not always generate mappings
3. **Context Persistence**: Context headers sometimes reset to placeholders
4. **Real-time Updates**: WebSocket updates not implemented, using polling
5. **Context Header Consistency**: Frontend may still send mixed context values in complex scenarios

## Quick Fixes Checklist

- [ ] Flow not found? Check if status is "initialized" and context matches
- [ ] No progress? Check if frontend handles all status variations
- [ ] No data? Check if data is in flow state, not separate API
- [ ] 404 errors? Verify all routes use `/discovery/cmdb-import`
- [ ] Missing stats? Ensure processing fields are at root level of state data
- [ ] 0 active flows? Check for context header mismatches in browser network tab
- [ ] Attribute mapping empty? Verify UnifiedDiscoveryService doesn't have hardcoded headers
- [ ] Context switching issues? Look for global search fallback logs in backend
- [ ] Frontend auth headers missing? Check AuthContext client/engagement state