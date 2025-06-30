# API v3 Migration Guide

This guide helps you migrate from the existing API (v1/v2) to the new unified v3 API for the AI Force Migration Platform.

## Overview

The v3 API consolidates all discovery flow operations into a clean, well-documented, and type-safe interface. It provides:

- **Unified Interface**: Single API for all discovery operations
- **Type Safety**: Full TypeScript support with generated types
- **Better Error Handling**: Comprehensive error types and handling
- **Real-time Updates**: Server-Sent Events for live status updates
- **File Upload Support**: Built-in file upload with progress tracking
- **Retry Logic**: Automatic retries with exponential backoff
- **Request/Response Logging**: Debug-friendly logging

## Breaking Changes

### URL Structure Changes

| Old Endpoint | New Endpoint |
|--------------|--------------|
| `/api/v1/unified-discovery/flow/initialize` | `/api/v3/discovery-flow/flows` (POST) |
| `/api/v1/discovery/session/{id}/status` | `/api/v3/discovery-flow/flows/{id}/status` |
| `/api/v2/discovery-flows/flows/active` | `/api/v3/discovery-flow/flows?status=active` |
| `/api/v1/data-import/store-import` | `/api/v3/data-import/imports` |
| `/api/v1/field-mapping/*` | `/api/v3/field-mapping/mappings/*` |

### Response Format Changes

**Old Response Format:**
```json
{
  "session_id": "uuid",
  "status": "running",
  "data": {...}
}
```

**New Response Format:**
```json
{
  "flow_id": "uuid",
  "status": "in_progress",
  "current_phase": "field_mapping",
  "progress_percentage": 45.5,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:30:00Z",
  ...
}
```

### Key Changes:
- `session_id` → `flow_id`
- More detailed status information
- Standardized timestamp format (ISO 8601)
- Consistent field naming (snake_case)

## Migration Steps

### 1. Install the v3 Client

The v3 API client is included in the existing codebase. Import it:

```typescript
import { createApiV3Client, FlowPhase, FlowStatus } from '@/api/v3';
```

### 2. Initialize the Client

**Old Way:**
```typescript
import { apiCall } from '@/config/api';

const response = await apiCall('/unified-discovery/flow/initialize', {
  method: 'POST',
  body: JSON.stringify(data)
});
```

**New Way:**
```typescript
import { createAutoConfiguredClient } from '@/api/v3';

const api = createAutoConfiguredClient({
  enableLogging: process.env.NODE_ENV === 'development'
});

const flow = await api.discoveryFlow.createFlow(data);
```

### 3. Update Discovery Flow Operations

#### Creating a Flow

**Old:**
```typescript
const response = await apiCall('/unified-discovery/flow/initialize', {
  method: 'POST',
  body: JSON.stringify({
    client_account_id: clientId,
    engagement_id: engagementId,
    raw_data: data
  })
});
```

**New:**
```typescript
const flow = await api.discoveryFlow.createFlow({
  name: 'Q4 2024 Migration',
  description: 'Quarterly migration assessment',
  client_account_id: clientId,
  engagement_id: engagementId,
  raw_data: data,
  execution_mode: ExecutionMode.HYBRID
});
```

#### Getting Flow Status

**Old:**
```typescript
const status = await apiCall(`/discovery/session/${sessionId}/status`);
```

**New:**
```typescript
const status = await api.discoveryFlow.getFlowStatus(flowId);
```

#### Real-time Updates

**Old:** (No built-in support)

**New:**
```typescript
const subscription = api.discoveryFlow.subscribeToFlowUpdates(
  flowId,
  (update) => {
    console.log('Flow status:', update.status);
    console.log('Progress:', update.progress_percentage);
  }
);

// Clean up when done
subscription.close();
```

### 4. Update Field Mapping Operations

**Old:**
```typescript
const mappings = await apiCall('/field-mapping/create', {
  method: 'POST',
  body: JSON.stringify({ flow_id: flowId, mappings: data })
});
```

**New:**
```typescript
const mappings = await api.fieldMapping.createFieldMapping({
  flow_id: flowId,
  source_fields: ['hostname', 'ip_address', 'os'],
  target_schema: 'asset_inventory',
  auto_map: true
});

// Get suggestions
const suggestions = await api.fieldMapping.getMappingSuggestions(
  flowId,
  'hostname'
);

// Validate mappings
const validation = await api.fieldMapping.validateFieldMapping(flowId, {
  mappings: { 'hostname': 'asset_name' },
  sample_data: sampleRecords
});
```

### 5. Update Data Import Operations

**Old:**
```typescript
const formData = new FormData();
formData.append('file', file);

const response = await fetch('/api/v1/data-import/store-import', {
  method: 'POST',
  body: formData
});
```

**New:**
```typescript
const importResult = await api.dataImport.uploadDataFile(
  file,
  {
    name: 'Monthly Asset Inventory',
    description: 'December 2024 inventory data',
    auto_create_flow: true
  },
  {
    onProgress: (progress) => {
      console.log(`Upload: ${progress.percentage}%`);
    },
    onComplete: (result) => {
      console.log('Upload complete:', result);
    }
  }
);
```

### 6. Error Handling

**Old:**
```typescript
try {
  const response = await apiCall('/some-endpoint');
} catch (error) {
  console.error('API error:', error);
  // Generic error handling
}
```

**New:**
```typescript
import { 
  isApiError, 
  isValidationApiError, 
  isNotFoundApiError,
  createUserFriendlyError 
} from '@/api/v3';

try {
  const result = await api.discoveryFlow.createFlow(data);
} catch (error) {
  if (isValidationApiError(error)) {
    // Handle validation errors
    error.validationErrors.forEach(ve => {
      console.error(`Field ${ve.field}: ${ve.message}`);
    });
  } else if (isNotFoundApiError(error)) {
    // Handle not found errors
    console.error(`Resource not found: ${error.resourceType}`);
  } else if (isApiError(error)) {
    // Handle general API errors
    console.error(`API Error ${error.statusCode}: ${error.message}`);
  }

  // Show user-friendly message
  const userMessage = createUserFriendlyError(error);
  showNotification(userMessage, 'error');
}
```

## New Features

### 1. Server-Sent Events for Real-time Updates

```typescript
// Subscribe to a specific flow
const flowSubscription = api.discoveryFlow.subscribeToFlowUpdates(
  flowId,
  (update) => {
    setFlowStatus(update.status);
    setProgress(update.progress_percentage);
    setCurrentPhase(update.current_phase);
  },
  {
    includePhaseUpdates: true,
    includeAgentInsights: true
  }
);

// Subscribe to all flows
const allFlowsSubscription = api.discoveryFlow.subscribeToAllFlowUpdates(
  (update) => {
    updateFlowInList(update.flow_id, update);
  }
);
```

### 2. Advanced File Upload with Progress

```typescript
const uploadFile = async (file: File) => {
  try {
    const result = await api.dataImport.uploadDataFile(
      file,
      {
        name: file.name,
        auto_create_flow: true
      },
      {
        onProgress: (progress) => {
          setUploadProgress(progress.percentage);
          setUploadSpeed(progress.speed);
        },
        onError: (error) => {
          setUploadError(error.message);
        },
        maxSize: 100 * 1024 * 1024, // 100MB
        allowedTypes: ['csv', 'xlsx', 'json']
      }
    );
    
    console.log('Upload successful:', result);
  } catch (error) {
    handleUploadError(error);
  }
};
```

### 3. Enhanced Flow Control

```typescript
// Execute specific phases
await api.discoveryFlow.executePhase(
  flowId, 
  FlowPhase.FIELD_MAPPING,
  {
    data: { auto_approve_high_confidence: true },
    human_input: { reviewer_notes: 'Approved by John Doe' }
  }
);

// Pause and resume flows
await api.discoveryFlow.pauseFlow(flowId, {
  reason: 'Waiting for stakeholder approval'
});

await api.discoveryFlow.resumeFlow(flowId, {
  target_phase: FlowPhase.DATA_CLEANSING,
  human_input: { approval_received: true }
});

// Asset promotion
const promotion = await api.discoveryFlow.promoteAssets(flowId);
console.log(`Promoted ${promotion.assets_promoted} assets`);
```

### 4. Advanced Field Mapping

```typescript
// Auto-mapping with confidence threshold
const autoMapping = await api.fieldMapping.autoMapFields(
  flowId,
  sourceFields,
  'asset_inventory',
  0.8 // 80% confidence threshold
);

// Bulk suggestions
const bulkSuggestions = await api.fieldMapping.getBulkMappingSuggestions(
  flowId,
  ['hostname', 'ip_addr', 'operating_system', 'memory_size']
);

// Mapping analytics
const analytics = await api.fieldMapping.getMappingAnalytics(flowId);
console.log('Mapping quality:', analytics.mapping_quality.overall_score);
```

## React Hook Integration

Create a custom hook for easy integration:

```typescript
// hooks/useDiscoveryFlow.ts
import { useState, useEffect } from 'react';
import { getGlobalApiClient, FlowResponse, FlowStatusUpdate } from '@/api/v3';

export function useDiscoveryFlow(flowId: string) {
  const [flow, setFlow] = useState<FlowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const api = getGlobalApiClient();

  useEffect(() => {
    const loadFlow = async () => {
      try {
        setLoading(true);
        const flowData = await api.discoveryFlow.getFlow(flowId);
        setFlow(flowData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    loadFlow();

    // Subscribe to real-time updates
    const subscription = api.discoveryFlow.subscribeToFlowUpdates(
      flowId,
      (update: FlowStatusUpdate) => {
        setFlow(prev => prev ? { ...prev, ...update } : null);
      }
    );

    return () => {
      subscription.close();
    };
  }, [flowId]);

  return { flow, loading, error };
}

// Usage in component
function FlowDashboard({ flowId }: { flowId: string }) {
  const { flow, loading, error } = useDiscoveryFlow(flowId);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!flow) return <div>Flow not found</div>;

  return (
    <div>
      <h1>{flow.name}</h1>
      <p>Status: {flow.status}</p>
      <p>Progress: {flow.progress_percentage}%</p>
      <p>Phase: {flow.current_phase}</p>
    </div>
  );
}
```

## Performance Optimizations

### 1. Request Caching

```typescript
// Enable caching for GET requests
const api = createApiV3Client({
  baseURL: process.env.REACT_APP_API_URL,
  enableLogging: false, // Disable in production
  defaultHeaders: {
    'Cache-Control': 'max-age=300' // 5 minutes
  }
});
```

### 2. Batch Operations

```typescript
// Batch upload multiple files
const files = [file1, file2, file3];
const results = await api.dataImport.batchUploadFiles(
  files,
  { auto_create_flow: false },
  { 
    onProgress: (progress) => console.log('Batch progress:', progress)
  }
);
```

### 3. Concurrent Requests

```typescript
// Process multiple flows concurrently
const flowIds = ['flow1', 'flow2', 'flow3'];
const flowStatuses = await Promise.all(
  flowIds.map(id => api.discoveryFlow.getFlowStatus(id))
);
```

## Testing

### Unit Testing

```typescript
// __tests__/api/v3/discoveryFlow.test.ts
import { createApiV3Client } from '@/api/v3';

describe('Discovery Flow API', () => {
  const api = createApiV3Client({
    baseURL: 'http://localhost:8000/api/v3'
  });

  test('creates flow successfully', async () => {
    const flow = await api.discoveryFlow.createFlow({
      name: 'Test Flow',
      client_account_id: 'test-client',
      engagement_id: 'test-engagement',
      raw_data: [{ hostname: 'server1' }]
    });

    expect(flow.flow_id).toBeDefined();
    expect(flow.status).toBe('initializing');
  });
});
```

### Integration Testing

```typescript
// __tests__/integration/flowWorkflow.test.ts
describe('Complete Flow Workflow', () => {
  test('end-to-end flow creation and execution', async () => {
    // 1. Upload data
    const importResult = await api.dataImport.uploadDataFile(testFile);
    
    // 2. Create flow
    const flow = await api.discoveryFlow.createFlow({
      name: 'E2E Test Flow',
      // ... other props
    });
    
    // 3. Execute phases
    await api.discoveryFlow.executePhase(flow.flow_id, FlowPhase.FIELD_MAPPING);
    
    // 4. Verify results
    const status = await api.discoveryFlow.getFlowStatus(flow.flow_id);
    expect(status.current_phase).toBe(FlowPhase.DATA_CLEANSING);
  });
});
```

## Common Patterns

### 1. Loading States with Error Handling

```typescript
const [state, setState] = useState({
  data: null,
  loading: false,
  error: null
});

const loadData = async () => {
  setState(prev => ({ ...prev, loading: true, error: null }));
  
  try {
    const data = await api.discoveryFlow.listFlows();
    setState({ data, loading: false, error: null });
  } catch (error) {
    setState(prev => ({ 
      ...prev, 
      loading: false, 
      error: createUserFriendlyError(error) 
    }));
  }
};
```

### 2. Form Validation with API Validation

```typescript
const validateForm = async (formData: FlowCreate) => {
  try {
    const validation = await api.discoveryFlow.validateFlowConfig(formData);
    
    if (!validation.is_valid) {
      const errors = validation.issues.reduce((acc, issue) => {
        acc[issue.field] = issue.message;
        return acc;
      }, {} as Record<string, string>);
      
      setFormErrors(errors);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Validation failed:', error);
    return false;
  }
};
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure the backend allows requests from your frontend domain
2. **Authentication**: Verify the auth token is properly set
3. **Type Errors**: Check that your TypeScript configuration includes the v3 types
4. **Network Timeouts**: Increase timeout for large file uploads

### Debug Mode

Enable debug logging:

```typescript
const api = createApiV3Client({
  baseURL: process.env.REACT_APP_API_URL,
  enableLogging: true, // Enable detailed logging
  retryAttempts: 1 // Reduce retries for debugging
});
```

### Health Checks

Monitor API health:

```typescript
const health = await api.healthCheck();
console.log('API Health:', health.overall_status);
console.log('Service Status:', health.services);
```

## Support

For questions or issues with the v3 API migration:

1. Check the [API Documentation](./v3-api-reference.md)
2. Review error logs with detailed error information
3. Use the built-in health check endpoints
4. Enable debug logging for troubleshooting

The v3 API provides significant improvements in type safety, error handling, and developer experience. Take advantage of the new features to build more robust applications.