# Frontend Legacy Patterns Analysis Report

## Executive Summary
This report identifies all legacy patterns in the frontend codebase that bypass the Master Flow Orchestrator or use deprecated APIs. These patterns need to be updated to use the unified master flow service.

## 1. Direct Discovery API Usage (Bypassing Master Flow Orchestrator)

### Files using `/api/v1/discovery/*` endpoints directly:

#### 1.1 Components with Direct API Calls
- **File**: `/src/components/discovery/PlanVisualization.tsx`
  - Line 89: `fetch(\`/api/v1/discovery/flow/planning/intelligence/${flowId}\`)`
  - Line 283: `fetch(\`/api/v1/discovery/flow/planning/optimize/${flowId}\`)`
  - **Should use**: `masterFlowService.getFlowStatus()` or appropriate master flow methods

- **File**: `/src/components/discovery/UploadBlocker.tsx`
  - Line 226: `fetch(\`/api/v1/discovery/flow/${flow.flowId}/complete\`)`
  - **Should use**: `masterFlowService.completeFlow()` or similar

- **File**: `/src/components/discovery/AgentCommunicationPanel.tsx`
  - Line 92: `fetch(\`/api/v1/discovery/flow/communication/messages/${flowId}\`)`
  - Line 101: `fetch(\`/api/v1/discovery/flow/communication/events/${flowId}\`)`
  - Line 110: `fetch(\`/api/v1/discovery/flow/communication/stats/${flowId}\`)`
  - **Should use**: Master flow service communication methods

- **File**: `/src/components/discovery/MemoryKnowledgePanel.tsx`
  - Line 91: `fetch(\`/api/v1/discovery/flow/memory/analytics/${flowId}\`)`
  - Line 132: `fetch(\`/api/v1/discovery/flow/knowledge/status/${flowId}\`)`
  - Line 169: `fetch(\`/api/v1/discovery/flow/memory/optimize/${flowId}\`)`
  - **Should use**: Master flow service memory/knowledge methods

- **File**: `/src/components/FlowCrewAgentMonitor/hooks/useAgentMonitor.ts`
  - Line 92, 131: `fetch(\`/api/v1/discovery/flow/crews/monitoring/${flow.flow_id}\`)`
  - **Should use**: `masterFlowService.getCrewStatus()` or similar

#### 1.2 Hooks with Direct API Calls
- **File**: `/src/hooks/useRealTimeProcessing.ts`
  - Line 98: `/api/v1/discovery/flow/status/${flow_id}`
  - Line 138: `/api/v1/discovery/flow/${flow_id}/processing-status`
  - Lines 331, 343, 358, 370: Various discovery flow control endpoints
  - Line 421: `/api/v1/discovery/flow/${flow_id}/agent-insights`
  - Line 538: `/api/v1/discovery/flow/${flow_id}/validation-status`
  - **Should use**: Master flow service methods for all operations

- **File**: `/src/hooks/discovery/useAttributeMappingNavigation.ts`
  - Line 38: `apiCall(\`/api/v1/discovery/flow/${flowId}/resume\`)`
  - **Should use**: `masterFlowService.resumeFlow()`

- **File**: `/src/hooks/useDiscoveryDashboard.ts`
  - Line 66: `/api/v1/discovery/metrics`
  - Line 87: `/api/v1/discovery/application-landscape`
  - Line 108: `/api/v1/discovery/infrastructure-landscape`
  - **Note**: Missing import for `apiCall` function
  - **Should use**: Master flow service dashboard methods

- **File**: `/src/pages/discovery/CMDBImport/index.tsx`
  - Line 70: `apiCall(\`/api/v1/discovery/flow/status/${file.flow_id}\`)`
  - Line 156: `apiCall(\`/api/v1/discovery/flow/${file.flow_id}/processing-status\`)`
  - **Should use**: `masterFlowService.getFlowStatus()`

## 2. Session ID References (Legacy Pattern)

### Files still using session_id/sessionId:

- **File**: `/src/services/dataImportV2Service.ts`
  - Line 56: `importSessionId?: string` parameter
  - Line 69: Uses `importSessionId` in request
  - **Should use**: `flow_id` throughout

- **File**: `/src/pages/discovery/CMDBImport/hooks/useCMDBImport.ts`
  - Line 90: `getStoredImportData(importSessionId: string)`
  - Line 197: Checks `uploadedFile.importSessionId`
  - Line 202: Uses `uploadedFile.importSessionId`
  - **Should use**: `flow_id` instead of `importSessionId`

- **File**: `/src/pages/discovery/CMDBImport/CMDBImport.types.ts`
  - Contains `importSessionId` field in type definitions
  - **Should use**: `flow_id` field

- **File**: `/src/contexts/AuthContext/types.ts`
  - May contain session-related types
  - **Should review**: Ensure no session_id references

- **File**: `/src/components/admin/session-comparison/SessionComparisonMain.tsx`
  - Component name suggests session usage
  - **Should review**: Update to flow-based comparison

## 3. V2/V3 API References

### Files importing from v2 services:
- **File**: `/src/services/dataImportV2Service.ts`
  - Service marked as `@deprecated`
  - Still being used by some components
  - **Should migrate**: All consumers to use master flow service

- **Archive folder references** (22 files found):
  - These are in `/src/archive/` and should not be used
  - Any imports from archive should be removed

## 4. Mixed API Pattern Usage

### Files using both legacy and new patterns:

- **File**: `/src/hooks/useUnifiedDiscoveryFlow.ts`
  - Uses `masterFlowService` (good)
  - But throws error for phase execution (line 57)
  - **Should implement**: Complete phase execution via master flow

- **File**: `/src/components/discovery/UploadBlocker.tsx`
  - Imports `masterFlowService` (good)
  - But also uses direct fetch calls (bad)
  - **Should use**: Consistent master flow service usage

## 5. Missing Master Flow Integration

### Files not using masterFlowService when they should:

1. **Discovery Dashboard Services**:
   - `/src/pages/discovery/EnhancedDiscoveryDashboard/services/dashboardService.ts`
   - Should integrate with master flow dashboard APIs

2. **Data Cleansing Analysis**:
   - `/src/hooks/useDataCleansingAnalysis.ts`
   - Should use master flow for data cleansing operations

3. **Tech Debt Queries**:
   - `/src/hooks/discovery/useTechDebtQueries.ts`
   - Should use master flow for tech debt analysis

4. **Application Hook**:
   - `/src/hooks/useApplication.ts`
   - Should use master flow for application data

## 6. Recommendations

### Priority 1 - Critical Updates (Blocking Master Flow):
1. Replace all direct `/api/v1/discovery/*` calls with `masterFlowService`
2. Update `importSessionId` to `flow_id` in all files
3. Remove dependencies on `dataImportV2Service`

### Priority 2 - Important Updates:
1. Implement missing methods in `masterFlowService`:
   - Communication/messaging endpoints
   - Memory/knowledge management
   - Crew monitoring
   - Dashboard metrics
   - Phase execution

2. Update hooks to use master flow service:
   - `useRealTimeProcessing`
   - `useDiscoveryDashboard`
   - `useDataCleansingAnalysis`

### Priority 3 - Cleanup:
1. Remove all archive folder imports
2. Update component names from "session" to "flow"
3. Add proper TypeScript types for master flow responses

## 7. Migration Checklist

For each file identified:
- [ ] Replace direct API calls with `masterFlowService` methods
- [ ] Update `session_id`/`sessionId` to `flow_id`
- [ ] Remove `importSessionId` references
- [ ] Update imports from deprecated services
- [ ] Test the updated functionality
- [ ] Update any related tests

## 8. Impact Analysis

- **High Risk Files** (Core functionality):
  - `useCMDBImport.ts` - Main import flow
  - `useRealTimeProcessing.ts` - Real-time updates
  - `useUnifiedDiscoveryFlow.ts` - Central flow hook

- **Medium Risk Files** (Feature-specific):
  - Communication panels
  - Memory/knowledge panels
  - Dashboard services

- **Low Risk Files** (Display only):
  - Visualization components
  - Status displays

This comprehensive update will ensure all frontend code properly uses the Master Flow Orchestrator system and eliminates legacy patterns.