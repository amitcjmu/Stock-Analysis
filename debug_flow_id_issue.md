# Flow ID Display Issue Analysis

## Problem
The actual flow ID in the database is: `23678d88-f4bd-49f4-bca8-b93c7b2b9ef2`
But the URL in the monitor popup shows: `23b76d88-f4bd-49f4-bca8-b93c7b2b9ef2`

Character "6" at position 2 is being changed to "b".

## Potential Root Causes

### 1. Frontend Display Issue
- **File**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/pages/discovery/EnhancedDiscoveryDashboard/components/FlowsOverview.tsx`
- **Line 149**: `Flow ID: {flow.flow_id.slice(0, 8)}...`
- **Issue**: This only shows the first 8 characters for display, but the full flow ID is passed to the monitor function

### 2. Data Transformation Issue
- **File**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/pages/discovery/EnhancedDiscoveryDashboard/services/dashboardService.ts`
- **Lines 130-147**: Where flow data is processed and transformed
- **Potential Issue**: Some data transformation might be corrupting the flow ID

### 3. URL Parameter Encoding
- **File**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/services/flowProcessingService.ts`
- **Line 96**: `const response = await apiCall(\`\${this.baseUrl}/continue/\${flowId}\`, ...)`
- **Issue**: The flowId is directly embedded in the URL path

### 4. Font Rendering Issue
- Could be a font rendering issue where "6" appears as "b"
- Less likely since user specifically mentions URL shows "b"

## Files to Check

1. **FlowsOverview.tsx** - Line 149 (flow ID display)
2. **dashboardService.ts** - Lines 130-147 (flow data processing)
3. **FlowStatusWidget.tsx** - Lines 104-108 (API call with flow ID)
4. **flowProcessingService.ts** - Line 96 (URL construction)

## Investigation Steps

1. **Check actual flow ID in database**: `23678d88-f4bd-49f4-bca8-b93c7b2b9ef2`
2. **Check flow ID in dashboard service response** 
3. **Check flow ID passed to FlowStatusWidget**
4. **Check URL construction in flowProcessingService**
5. **Check browser network requests to see actual API call**

## Likely Issue
The problem is likely in one of these areas:
- Flow ID being corrupted during data processing in dashboardService
- URL encoding/decoding issue 
- String manipulation somewhere that's converting "6" to "b"

## Next Steps
1. Add debugging logs to track flow ID at each step
2. Check browser network tab to see actual API requests
3. Verify database contains correct flow ID
4. Check if there's any hex/base64 encoding happening