# Fix for useRealTimeProcessing Hook

The useRealTimeProcessing hook has 5 direct discovery API calls that need to be updated to use the masterFlowServiceExtended. However, since this hook is used by multiple components for real-time status updates, we need to be careful with the migration.

## Current Issues:
1. Line 331: `/api/v1/discovery/flow/${data.flow_id}/validate`
2. Line 343: `/api/v1/discovery/flow/${data.flow_id}/retry`
3. Line 358: `/api/v1/discovery/flow/${data.flow_id}/pause`
4. Line 370: `/api/v1/discovery/flow/${data.flow_id}/resume`
5. Line 538: `/api/v1/discovery/flow/${flow_id}/validation-status`

## Recommended Approach:
Since this hook is actively used and working (just using legacy endpoints), we should:

1. **Phase 1**: Update the backend to support these endpoints through the unified flow API
2. **Phase 2**: Update the hook to use masterFlowServiceExtended
3. **Phase 3**: Test thoroughly with the components that use it

For now, the hook continues to work with the legacy endpoints. When the backend team adds these endpoints to the unified flow API, we can update this hook to use masterFlowServiceExtended.

## Components using this hook:
- UniversalProcessingStatus.tsx
- CMDBValidationPanel.tsx

Both are critical for the CMDB import flow, so we should not break them while the legacy endpoints still work.