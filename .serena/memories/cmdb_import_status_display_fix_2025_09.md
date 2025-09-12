# CMDB Import Status Display Fix - September 2025

## Problem: Incorrect "Analyzing..." Labels
**Issue**: CMDB import page showed "Analyzing..." for Security Status and Data Quality even when data was fully processed and ready for user action.

## Root Cause
The status detection logic didn't properly identify when uploaded data was available. The `isAnalysisComplete` check only looked for `completed` status or field mappings, missing the case where data exists but is waiting for user input.

## Solution Applied

### 1. Enhanced Data Detection
**File**: `src/pages/discovery/CMDBImport/components/CMDBDataTable.tsx`

```typescript
// Check if we have data uploaded and ready
const hasUploadedData = flowSummary.total_assets || flowState?.raw_data?.length;

// Override status if data is ready but waiting for user action
if (hasUploadedData && currentStatus === 'processing' && !isStartingFlow) {
  currentStatus = 'waiting_for_approval';
}
```

### 2. Fixed Analysis Complete Logic
```typescript
const isAnalysisComplete = flowState?.status === 'completed' ||
                          currentStatus === 'approved' ||
                          hasFieldMappings ||
                          currentStatus === 'waiting_for_approval' ||
                          hasUploadedData;  // Added this check
```

### 3. Updated Status Labels
```typescript
// Security Status
{securityStatus === false ? 'Issues Found' :
 securityStatus === true ? 'Secure' :
 hasUploadedData ? 'Validated' : 'Analyzing...'}

// Data Quality
{(flowState?.errors?.length || 0) > 0 ? `${flowState.errors.length} Errors` :
 (flowState?.warnings?.length || 0) > 0 ? `${flowState.warnings.length} Warnings` :
 qualityInsights.length > 0 ? 'Good Quality' :
 isAnalysisComplete ? 'Good Quality' : 'Analyzing...'}
```

## Key Patterns
1. **Always check for uploaded data** - Don't rely solely on flow status
2. **Override generic statuses** - When data exists, show appropriate user-facing status
3. **Use early data extraction** - Move data checks before status mapping to enable override logic

## Common Pitfall Avoided
Don't add temporary UI components (like SimplifiedFlowStatus) when the real issue is incorrect status detection logic. Fix the root cause in the data layer instead.

## Testing Approach
When fixing status displays:
1. Check actual API responses in browser console
2. Verify data presence (flowSummary.total_assets, raw_data)
3. Ensure status changes based on data availability, not just flow state
