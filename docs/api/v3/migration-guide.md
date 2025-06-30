# Migrating to API v3

This guide helps you migrate from v1/v2 APIs to the new consolidated v3 API introduced in Phase 1.

## Overview of Changes

### Major Architectural Changes
1. **Flow ID Primary**: All operations use `flow_id` instead of `session_id`
2. **Consolidated Endpoints**: Single v3 API replaces fragmented v1/v2 endpoints
3. **Standardized Responses**: Consistent success/error response format
4. **Multi-tenant Context**: Required headers for client account and engagement scoping
5. **Real-time Updates**: WebSocket support for live progress tracking
6. **Enhanced Features**: Better validation, error handling, and performance

### Breaking Changes
- **Identifier Change**: `session_id` → `flow_id` throughout all endpoints
- **Response Format**: Data now wrapped in standardized response structure
- **Required Headers**: Multi-tenant context headers now mandatory
- **Authentication**: Enhanced security requirements for v3 endpoints

## URL Structure Changes

### Discovery Flow Management
| v1/v2 Endpoint | v3 Endpoint | Method | Notes |
|----------------|-------------|--------|-------|
| `/api/v1/unified-discovery/flow/initialize` | `/api/v3/discovery-flow/flows` | POST | Flow creation with optional initial data |
| `/api/v1/discovery/session/{id}/status` | `/api/v3/discovery-flow/flows/{id}/status` | GET | Real-time flow status with detailed progress |
| `/api/v2/discovery-flows/flows/active` | `/api/v3/discovery-flow/flows?status=running` | GET | Query parameter filtering |
| `/api/v1/discovery/session/{id}/continue` | `/api/v3/discovery-flow/flows/{id}/execute/{phase}` | POST | Phase-specific execution |
| `/api/v2/discovery-flows/flows/{id}` | `/api/v3/discovery-flow/flows/{id}` | GET | Flow details with enhanced metadata |

### Data Import Management
| v1/v2 Endpoint | v3 Endpoint | Method | Notes |
|----------------|-------------|--------|-------|
| `/api/v1/data-import/store-import` | `/api/v3/data-import/imports` | POST | Enhanced validation and auto-mapping |
| `/api/v1/data-import/upload` | `/api/v3/data-import/imports/upload` | POST | Multi-format file support |
| `/api/v1/data-import/{id}/validate` | `/api/v3/data-import/imports/{id}/validate` | POST | Comprehensive validation rules |

### Field Mapping Management
| v1/v2 Endpoint | v3 Endpoint | Method | Notes |
|----------------|-------------|--------|-------|
| `/api/v1/field-mapping/{id}` | `/api/v3/field-mapping/mappings/{flow_id}` | GET | Flow-based mapping retrieval |
| `/api/v1/field-mapping/{id}/approve` | `/api/v3/field-mapping/mappings/{flow_id}` | PUT | Bulk mapping updates |
| No equivalent | `/api/v3/field-mapping/suggestions/{flow_id}` | GET | AI-powered mapping suggestions |

## Parameter Changes

### Identifier Migration
**Before (v1/v2):**
```javascript
// Session-based operations
const sessionId = "disc_session_20240120_123456";
await fetch(`/api/v1/discovery/session/${sessionId}/status`);
```

**After (v3):**
```javascript
// Flow-based operations
const flowId = "550e8400-e29b-41d4-a716-446655440000";
await fetch(`/api/v3/discovery-flow/flows/${flowId}/status`);
```

### Required Headers
**Before (v1/v2):**
```javascript
fetch('/api/v1/discovery/sessions', {
  headers: {
    'Authorization': 'Bearer token',
    'Content-Type': 'application/json'
  }
});
```

**After (v3):**
```javascript
fetch('/api/v3/discovery-flow/flows', {
  headers: {
    'Authorization': 'Bearer token',
    'Content-Type': 'application/json',
    'X-Client-Account-ID': 'client-uuid',
    'X-Engagement-ID': 'engagement-uuid'
  }
});
```

## Response Format Changes

### Success Response Format
**Before (v1/v2):**
```json
{
  "session_id": "disc_session_123",
  "status": "running",
  "progress": 45.5,
  "current_phase": "asset_inventory"
}
```

**After (v3):**
```json
{
  "success": true,
  "data": {
    "flow_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running",
    "progress_percentage": 45.5,
    "current_phase": "asset_inventory",
    "execution_mode": "hybrid",
    "estimated_completion": "2024-01-20T11:45:00Z"
  }
}
```

### Error Response Format
**Before (v1/v2):**
```json
{
  "error": "Session not found",
  "code": 404
}
```

**After (v3):**
```json
{
  "success": false,
  "error": {
    "code": "FLOW_NOT_FOUND",
    "message": "Flow not found",
    "details": {
      "flow_id": "invalid-flow-id",
      "reason": "Flow does not exist or access denied"
    },
    "timestamp": "2024-01-20T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Paginated Response Format
**Before (v1/v2):**
```json
{
  "sessions": [...],
  "total": 47,
  "page": 1,
  "limit": 20
}
```

**After (v3):**
```json
{
  "success": true,
  "data": {
    "flows": [...],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_items": 47,
      "items_per_page": 20,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

## Migration Examples

### Creating a Discovery Flow

#### Before (v1):
```javascript
const createSession = async () => {
  const response = await fetch('/api/v1/unified-discovery/flow/initialize', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer token',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      session_name: 'Q4 Migration Assessment',
      client_id: 'client-123',
      initial_data: [...] // Optional
    })
  });
  
  const result = await response.json();
  return result.session_id;
};
```

#### After (v3):
```javascript
const createFlow = async () => {
  const response = await fetch('/api/v3/discovery-flow/flows', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer token',
      'Content-Type': 'application/json',
      'X-Client-Account-ID': 'client-uuid',
      'X-Engagement-ID': 'engagement-uuid'
    },
    body: JSON.stringify({
      name: 'Q4 Migration Assessment',
      description: 'Quarterly migration planning discovery',
      execution_mode: 'hybrid',
      initial_data: [...] // Optional
    })
  });
  
  const result = await response.json();
  return result.success ? result.data.flow_id : null;
};
```

### Getting Flow Status

#### Before (v1):
```javascript
const getSessionStatus = async (sessionId) => {
  const response = await fetch(`/api/v1/discovery/session/${sessionId}/status`);
  const status = await response.json();
  
  return {
    id: status.session_id,
    state: status.status,
    progress: status.progress,
    phase: status.current_phase
  };
};
```

#### After (v3):
```javascript
const getFlowStatus = async (flowId) => {
  const response = await fetch(`/api/v3/discovery-flow/flows/${flowId}/status`, {
    headers: {
      'Authorization': 'Bearer token',
      'X-Client-Account-ID': 'client-uuid',
      'X-Engagement-ID': 'engagement-uuid'
    }
  });
  
  const result = await response.json();
  
  if (!result.success) {
    throw new Error(result.error.message);
  }
  
  return {
    id: result.data.flow_id,
    state: result.data.status,
    progress: result.data.progress_percentage,
    phase: result.data.current_phase,
    executionMode: result.data.execution_mode,
    estimatedCompletion: result.data.estimated_completion
  };
};
```

### Uploading Data

#### Before (v1):
```javascript
const uploadData = async (file, sessionId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  
  const response = await fetch('/api/v1/data-import/upload', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
};
```

#### After (v3):
```javascript
const uploadData = async (file, flowId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('flow_id', flowId);
  formData.append('auto_detect_fields', 'true');
  
  const response = await fetch('/api/v3/data-import/imports/upload', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer token',
      'X-Client-Account-ID': 'client-uuid',
      'X-Engagement-ID': 'engagement-uuid'
    },
    body: formData
  });
  
  const result = await response.json();
  return result.success ? result.data : null;
};
```

### Field Mapping Operations

#### Before (v1):
```javascript
const approveMapping = async (mappingId) => {
  const response = await fetch(`/api/v1/field-mapping/${mappingId}/approve`, {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer token',
      'Content-Type': 'application/json'
    }
  });
  
  return response.ok;
};
```

#### After (v3):
```javascript
const updateMappings = async (flowId, mappings) => {
  const response = await fetch(`/api/v3/field-mapping/mappings/${flowId}`, {
    method: 'PUT',
    headers: {
      'Authorization': 'Bearer token',
      'Content-Type': 'application/json',
      'X-Client-Account-ID': 'client-uuid',
      'X-Engagement-ID': 'engagement-uuid'
    },
    body: JSON.stringify({
      mappings: mappings.map(m => ({
        source_field: m.sourceField,
        target_field: m.targetField,
        status: 'approved',
        transformation: m.transformation
      }))
    })
  });
  
  const result = await response.json();
  return result.success;
};
```

## Frontend Migration Patterns

### React Hook Updates

#### Before (v1/v2):
```typescript
const useDiscoverySession = (sessionId: string) => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchSession = async () => {
      try {
        const response = await fetch(`/api/v1/discovery/session/${sessionId}`);
        const data = await response.json();
        setSession(data);
      } catch (error) {
        console.error('Failed to fetch session:', error);
      } finally {
        setLoading(false);
      }
    };
    
    if (sessionId) {
      fetchSession();
    }
  }, [sessionId]);
  
  return { session, loading };
};
```

#### After (v3):
```typescript
const useDiscoveryFlow = (flowId: string) => {
  const [flow, setFlow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchFlow = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch(`/api/v3/discovery-flow/flows/${flowId}`, {
          headers: {
            'Authorization': `Bearer ${getToken()}`,
            'X-Client-Account-ID': getClientAccountId(),
            'X-Engagement-ID': getEngagementId()
          }
        });
        
        const result = await response.json();
        
        if (result.success) {
          setFlow(result.data);
        } else {
          setError(result.error);
        }
      } catch (err) {
        setError({ message: 'Network error', code: 'NETWORK_ERROR' });
      } finally {
        setLoading(false);
      }
    };
    
    if (flowId) {
      fetchFlow();
    }
  }, [flowId]);
  
  return { flow, loading, error };
};
```

### API Client Updates

#### Before (v1/v2):
```typescript
class DiscoveryAPIClient {
  private baseUrl = '/api/v1';
  
  async createSession(data: any) {
    const response = await fetch(`${this.baseUrl}/unified-discovery/flow/initialize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await response.json();
  }
  
  async getSessionStatus(sessionId: string) {
    const response = await fetch(`${this.baseUrl}/discovery/session/${sessionId}/status`);
    return await response.json();
  }
}
```

#### After (v3):
```typescript
class DiscoveryAPIClient {
  private baseUrl = '/api/v3';
  private clientAccountId: string;
  private engagementId: string;
  
  constructor(clientAccountId: string, engagementId: string) {
    this.clientAccountId = clientAccountId;
    this.engagementId = engagementId;
  }
  
  private getHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`,
      'X-Client-Account-ID': this.clientAccountId,
      'X-Engagement-ID': this.engagementId
    };
  }
  
  private async handleResponse(response: Response) {
    const result = await response.json();
    if (!result.success) {
      throw new APIError(result.error);
    }
    return result.data;
  }
  
  async createFlow(data: any) {
    const response = await fetch(`${this.baseUrl}/discovery-flow/flows`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data)
    });
    return await this.handleResponse(response);
  }
  
  async getFlowStatus(flowId: string) {
    const response = await fetch(`${this.baseUrl}/discovery-flow/flows/${flowId}/status`, {
      headers: this.getHeaders()
    });
    return await this.handleResponse(response);
  }
}

class APIError extends Error {
  constructor(public errorData: any) {
    super(errorData.message);
    this.name = 'APIError';
  }
}
```

## Error Handling Updates

### Enhanced Error Handling

#### Before (v1/v2):
```javascript
try {
  const response = await fetch('/api/v1/discovery/sessions');
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }
  
  return data;
} catch (error) {
  console.error('API error:', error.message);
  throw error;
}
```

#### After (v3):
```javascript
try {
  const response = await fetch('/api/v3/discovery-flow/flows', {
    headers: getV3Headers()
  });
  
  const result = await response.json();
  
  if (!result.success) {
    const error = result.error;
    console.error(`API Error [${error.code}]:`, error.message);
    
    // Handle specific error codes
    switch (error.code) {
      case 'FLOW_NOT_FOUND':
        throw new NotFoundError(error.message);
      case 'VALIDATION_ERROR':
        throw new ValidationError(error.message, error.details);
      case 'UNAUTHORIZED':
        throw new AuthError(error.message);
      default:
        throw new APIError(error.message, error.code);
    }
  }
  
  return result.data;
} catch (error) {
  if (error instanceof APIError) {
    // Handle API-specific errors
    handleAPIError(error);
  } else {
    // Handle network or other errors
    console.error('Network error:', error);
  }
  throw error;
}
```

## WebSocket Migration

### Real-time Updates

#### Before (v1/v2):
```javascript
// Limited or no WebSocket support
const pollSessionStatus = (sessionId) => {
  setInterval(async () => {
    try {
      const status = await fetch(`/api/v1/discovery/session/${sessionId}/status`);
      const data = await status.json();
      updateUI(data);
    } catch (error) {
      console.error('Polling error:', error);
    }
  }, 5000); // Poll every 5 seconds
};
```

#### After (v3):
```javascript
// Native WebSocket support
const connectToFlowUpdates = (flowId) => {
  const wsUrl = `wss://api.platform.com/api/v3/ws/flows/${flowId}/status`;
  const ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    console.log('Connected to flow updates');
  };
  
  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    if (update.type === 'flow_status_update') {
      updateUI(update);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    // Fallback to polling
    pollFlowStatus(flowId);
  };
  
  return ws;
};
```

## Migration Utilities

### Backward Compatibility Helper

```typescript
// Utility for gradual migration
class APICompatibilityLayer {
  private useV3: boolean;
  
  constructor(useV3 = true) {
    this.useV3 = useV3;
  }
  
  async getFlowStatus(identifier: string) {
    if (this.useV3) {
      // Assume identifier is flow_id
      return await this.getV3FlowStatus(identifier);
    } else {
      // Assume identifier is session_id
      return await this.getV1SessionStatus(identifier);
    }
  }
  
  private async getV3FlowStatus(flowId: string) {
    const response = await fetch(`/api/v3/discovery-flow/flows/${flowId}/status`, {
      headers: getV3Headers()
    });
    const result = await response.json();
    return result.success ? result.data : null;
  }
  
  private async getV1SessionStatus(sessionId: string) {
    const response = await fetch(`/api/v1/discovery/session/${sessionId}/status`);
    return await response.json();
  }
}
```

### Identifier Migration Helper

```typescript
// Helper for converting session IDs to flow IDs
class IdentifierMigration {
  private sessionToFlowMapping = new Map<string, string>();
  
  async getFlowIdForSession(sessionId: string): Promise<string | null> {
    // Check cache first
    if (this.sessionToFlowMapping.has(sessionId)) {
      return this.sessionToFlowMapping.get(sessionId)!;
    }
    
    // Call migration endpoint
    try {
      const response = await fetch('/api/v3/migration/session-to-flow', {
        method: 'POST',
        headers: getV3Headers(),
        body: JSON.stringify({ session_id: sessionId })
      });
      
      const result = await response.json();
      if (result.success) {
        const flowId = result.data.flow_id;
        this.sessionToFlowMapping.set(sessionId, flowId);
        return flowId;
      }
    } catch (error) {
      console.error('Failed to migrate session ID:', error);
    }
    
    return null;
  }
}
```

## Testing Migration

### API Testing

```typescript
// Test v3 API endpoints
describe('API v3 Migration', () => {
  test('should create flow with v3 format', async () => {
    const response = await fetch('/api/v3/discovery-flow/flows', {
      method: 'POST',
      headers: getV3Headers(),
      body: JSON.stringify({
        name: 'Test Flow',
        execution_mode: 'hybrid'
      })
    });
    
    const result = await response.json();
    
    expect(result.success).toBe(true);
    expect(result.data.flow_id).toBeDefined();
    expect(result.data.name).toBe('Test Flow');
  });
  
  test('should handle v3 error format', async () => {
    const response = await fetch('/api/v3/discovery-flow/flows/invalid-id');
    const result = await response.json();
    
    expect(result.success).toBe(false);
    expect(result.error.code).toBe('FLOW_NOT_FOUND');
    expect(result.error.message).toBeDefined();
  });
});
```

## Migration Timeline

### Phase 1: Preparation (Week 1)
- [ ] Review API changes and plan migration
- [ ] Update development environment to support v3
- [ ] Create compatibility layer for gradual migration

### Phase 2: Backend Migration (Week 2)
- [ ] Update API client to support v3 endpoints
- [ ] Implement error handling for v3 format
- [ ] Add multi-tenant context headers

### Phase 3: Frontend Migration (Week 3)
- [ ] Update React hooks and components
- [ ] Migrate from session ID to flow ID
- [ ] Implement WebSocket connections for real-time updates

### Phase 4: Testing and Validation (Week 4)
- [ ] Comprehensive testing of migrated code
- [ ] Performance validation
- [ ] User acceptance testing

### Phase 5: Production Deployment (Week 5)
- [ ] Deploy with backward compatibility enabled
- [ ] Monitor API v3 usage and performance
- [ ] Gradually disable v1/v2 endpoints

## Support and Resources

### Documentation
- [API v3 Reference](./README.md) - Complete API documentation
- [WebSocket Guide](./websocket-guide.md) - Real-time updates implementation
- [Authentication Guide](./auth-guide.md) - Multi-tenant authentication

### Migration Tools
- [API Compatibility Checker](../tools/compatibility-checker.js) - Validate v3 compatibility
- [Session to Flow ID Migrator](../tools/id-migrator.js) - Bulk identifier migration
- [Response Format Converter](../tools/response-converter.js) - Handle response format changes

### Getting Help
- **Migration Support**: api-migration@company.com
- **Technical Questions**: api-support@company.com
- **Issues and Bugs**: Create issue in project repository
- **Emergency Support**: +1-555-API-HELP