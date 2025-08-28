# Frontend Flow Detection and Query Parameter Fixes

## Query Parameter Support Issue (2025-01-19)
### Problem
Frontend attribute mapping page ignored query parameters `?flow_id=...` and only read route parameters `/:flowId`, causing different tabs to show data from different flows.

### Root Cause
`useDiscoveryFlowAutoDetection` hook used `useParams` which only reads route parameters, not query parameters.

### Solution
```typescript
// src/hooks/discovery/useDiscoveryFlowAutoDetection.ts
import { useParams, useLocation } from 'react-router-dom';

export const useDiscoveryFlowAutoDetection = (options: FlowAutoDetectionOptions = {}): FlowAutoDetectionResult => {
  // First try route params (e.g., /path/:flowId)
  const { flowId: routeFlowId } = useParams<{ flowId?: string }>();

  // Also check query params (e.g., ?flow_id=...)
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const queryFlowId = queryParams.get('flow_id');

  // Use route param first, then query param as fallback
  const urlFlowId = routeFlowId || queryFlowId || undefined;
  // ... rest of logic
}
```

### Result
- All tabs now use the same flow ID consistently
- Query parameter `?flow_id=...` is properly recognized
- Field count displays correctly (9 instead of 0)

## Field Mapping Data Structure Issue
### Problem
Field mappings showed correct count but 0 mapped items in UI columns despite backend returning 9 mappings.

### Root Cause
Data transformation mismatch between backend (snake_case) and frontend (camelCase) field names.

### Partial Fix Applied
```typescript
// src/hooks/discovery/attribute-mapping/useFieldMappings.ts
// Convert unified discovery format with consistent naming
return response.field_mappings.map(m => ({
  id: m.id || `${m.source_field}_${m.target_attribute}`,
  sourceField: m.source_field,  // Use camelCase for consistency
  source_field: m.source_field,  // Keep snake_case for backward compatibility
  targetAttribute: m.target_attribute,  // Use camelCase
  target_field: m.target_attribute,  // Keep snake_case
  confidence: m.confidence,
  is_approved: m.is_approved || false,
  status: m.status || 'suggested',
  mapping_type: m.mapping_type || 'auto',
  transformation_rule: m.transformation,
  validation_rule: m.validation_rules
}));
```

### Remaining Issue
ThreeColumnFieldMapper component still receives undefined values for sourceField/targetAttribute due to deeper transformation issues in the data pipeline.

## Critical Attributes Flow Awareness
### Problem
Critical attributes endpoint was not flow-aware, returning data from any flow in the engagement.

### Solution
```typescript
// src/hooks/discovery/attribute-mapping/useCriticalAttributes.ts
const endpoint = finalFlowId
  ? `${API_CONFIG.ENDPOINTS.DISCOVERY.CRITICAL_ATTRIBUTES_STATUS}?flow_id=${finalFlowId}`
  : API_CONFIG.ENDPOINTS.DISCOVERY.CRITICAL_ATTRIBUTES_STATUS;
```

## Key API Endpoints Discovered
- `/api/v1/unified-discovery/flows/{flowId}/field-mappings` - Returns field mappings for a flow
- `/api/v1/flows/{flowId}/status` - Returns flow status with import data
- `/data-import/critical-attributes-status` - Returns critical attributes (now flow-aware)

## Backend Response Structure
Field mappings from unified discovery endpoint:
```json
{
  "source_field": "App_Name",
  "target_attribute": "asset_name",
  "confidence": 0.5,
  "mapping_type": "auto",
  "transformation": null,
  "validation_rules": null
}
```
Note: Missing `status` and `is_approved` fields that frontend expects.
