# Phase 1 - Agent B2: Frontend API Client v3

## Context
You are part of a parallel remediation effort to fix critical architectural issues in the AI Force Migration Platform. This is Track B (Frontend) of Phase 1, working with Agent B1 to create a TypeScript client for the new consolidated v3 API.

### Required Reading Before Starting
- `docs/planning/PHASE-1-REMEDIATION-PLAN.md` - Overall Phase 1 objectives
- `AGENT_B1_BACKEND_API_CONSOLIDATION.md` - Understanding the v3 API structure
- Review existing API calls in `src/services/` and `src/config/api.ts`

### Phase 1 Goal
Create a robust, type-safe TypeScript client for the new v3 API that provides excellent developer experience and handles all edge cases gracefully.

## Your Specific Tasks

### 1. Create TypeScript API Client Structure
**Files to create**:
```
src/api/v3/
├── index.ts                    # Main export file
├── client.ts                   # Base API client class
├── discoveryFlowClient.ts      # Discovery flow operations
├── fieldMappingClient.ts       # Field mapping operations
├── dataImportClient.ts         # Data import operations
├── types/
│   ├── index.ts
│   ├── discovery.ts            # TypeScript interfaces matching Pydantic schemas
│   ├── fieldMapping.ts
│   ├── common.ts              # Shared types (pagination, errors)
│   └── responses.ts
├── interceptors/
│   ├── auth.ts                # Authentication interceptor
│   ├── retry.ts               # Retry logic for failed requests
│   ├── logging.ts             # Request/response logging
│   └── error.ts               # Error transformation
└── utils/
    ├── queryBuilder.ts        # Build query parameters
    └── requestConfig.ts       # Request configuration helpers
```

### 2. Implement Base API Client
**File**: `src/api/v3/client.ts`

```typescript
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { authInterceptor } from './interceptors/auth';
import { retryInterceptor } from './interceptors/retry';
import { errorInterceptor } from './interceptors/error';
import { loggingInterceptor } from './interceptors/logging';

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  enableLogging?: boolean;
}

export class ApiClient {
  private client: AxiosInstance;
  
  constructor(config: ApiClientConfig) {
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Version': 'v3'
      }
    });
    
    // Apply interceptors
    this.setupInterceptors(config);
  }
  
  private setupInterceptors(config: ApiClientConfig) {
    // Request interceptors
    this.client.interceptors.request.use(authInterceptor);
    if (config.enableLogging) {
      this.client.interceptors.request.use(loggingInterceptor.request);
    }
    
    // Response interceptors
    this.client.interceptors.response.use(
      response => response,
      errorInterceptor
    );
    
    // Retry logic
    this.client.interceptors.response.use(
      response => response,
      retryInterceptor(config.retryAttempts || 3, config.retryDelay || 1000)
    );
  }
  
  // Generic request methods with proper typing
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }
  
  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }
  
  // ... other HTTP methods
}
```

### 3. Create Discovery Flow Client
**File**: `src/api/v3/discoveryFlowClient.ts`

```typescript
import { ApiClient } from './client';
import { 
  FlowCreate, 
  FlowResponse, 
  FlowPhase, 
  FlowStatus,
  PaginatedResponse,
  FlowListParams
} from './types/discovery';

export class DiscoveryFlowClient {
  constructor(private apiClient: ApiClient) {}
  
  /**
   * Create a new discovery flow
   */
  async createFlow(data: FlowCreate): Promise<FlowResponse> {
    return this.apiClient.post<FlowResponse>('/discovery-flow/flows', data);
  }
  
  /**
   * Get flow details with all sub-resources
   */
  async getFlow(flowId: string): Promise<FlowResponse> {
    return this.apiClient.get<FlowResponse>(`/discovery-flow/flows/${flowId}`);
  }
  
  /**
   * Get real-time flow execution status
   */
  async getFlowStatus(flowId: string): Promise<FlowStatus> {
    return this.apiClient.get<FlowStatus>(`/discovery-flow/flows/${flowId}/status`);
  }
  
  /**
   * Execute a specific flow phase
   */
  async executePhase(flowId: string, phase: FlowPhase): Promise<FlowResponse> {
    return this.apiClient.post<FlowResponse>(
      `/discovery-flow/flows/${flowId}/execute/${phase}`
    );
  }
  
  /**
   * List all flows with filtering and pagination
   */
  async listFlows(params?: FlowListParams): Promise<PaginatedResponse<FlowResponse>> {
    return this.apiClient.get<PaginatedResponse<FlowResponse>>(
      '/discovery-flow/flows',
      { params }
    );
  }
  
  /**
   * Delete a flow (soft delete)
   */
  async deleteFlow(flowId: string): Promise<void> {
    return this.apiClient.delete(`/discovery-flow/flows/${flowId}`);
  }
  
  /**
   * Subscribe to flow status updates (SSE)
   */
  subscribeToFlowUpdates(flowId: string, onUpdate: (status: FlowStatus) => void): EventSource {
    const eventSource = new EventSource(
      `${this.apiClient.baseURL}/discovery-flow/flows/${flowId}/subscribe`
    );
    
    eventSource.onmessage = (event) => {
      const status = JSON.parse(event.data) as FlowStatus;
      onUpdate(status);
    };
    
    return eventSource;
  }
}
```

### 4. Define TypeScript Types
**File**: `src/api/v3/types/discovery.ts`

```typescript
// Match the Pydantic schemas from backend exactly
export enum FlowPhase {
  FIELD_MAPPING = 'field_mapping',
  DATA_CLEANSING = 'data_cleansing',
  INVENTORY_BUILDING = 'inventory_building',
  APP_SERVER_DEPENDENCIES = 'app_server_dependencies',
  APP_APP_DEPENDENCIES = 'app_app_dependencies',
  TECHNICAL_DEBT = 'technical_debt'
}

export enum FlowStatus {
  INITIALIZING = 'initializing',
  IN_PROGRESS = 'in_progress',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface FlowCreate {
  name: string;
  description?: string;
  client_account_id: string;
  engagement_id: string;
  metadata?: Record<string, any>;
}

export interface FlowResponse {
  flow_id: string;
  name: string;
  status: FlowStatus;
  current_phase?: FlowPhase;
  progress_percentage: number;
  created_at: string;
  updated_at: string;
  phases_completed: FlowPhase[];
  metadata: Record<string, any>;
}

export interface FlowListParams {
  page?: number;
  page_size?: number;
  status?: FlowStatus;
  client_account_id?: string;
  engagement_id?: string;
  sort_by?: 'created_at' | 'updated_at' | 'name';
  sort_order?: 'asc' | 'desc';
}
```

### 5. Implement Retry Interceptor
**File**: `src/api/v3/interceptors/retry.ts`

```typescript
import { AxiosError, AxiosInstance } from 'axios';

interface RetryConfig {
  retries: number;
  retryDelay: number;
  retryCondition?: (error: AxiosError) => boolean;
}

const DEFAULT_RETRY_CONDITION = (error: AxiosError): boolean => {
  // Retry on network errors and 5xx errors
  return !error.response || (error.response.status >= 500 && error.response.status < 600);
};

export const retryInterceptor = (retries: number, retryDelay: number) => {
  return async (error: AxiosError) => {
    const config = error.config as any;
    
    // Initialize retry count
    config.__retryCount = config.__retryCount || 0;
    
    // Check if we should retry
    if (config.__retryCount >= retries || !DEFAULT_RETRY_CONDITION(error)) {
      return Promise.reject(error);
    }
    
    // Increment retry count
    config.__retryCount += 1;
    
    // Calculate delay with exponential backoff
    const delay = retryDelay * Math.pow(2, config.__retryCount - 1);
    
    // Log retry attempt
    console.warn(`Retrying request (${config.__retryCount}/${retries}) after ${delay}ms`);
    
    // Create promise to handle retry
    return new Promise((resolve) => {
      setTimeout(() => resolve(axios(config)), delay);
    });
  };
};
```

### 6. Create Migration Guide
**File**: `docs/api/v3-migration-guide.md`

Document:
- How to migrate from old API calls to v3
- Breaking changes (should be minimal)
- New features and improvements
- Code examples for common operations

## Success Criteria
- [ ] Complete TypeScript client with all v3 endpoints
- [ ] 100% type safety (no `any` types except where necessary)
- [ ] Automatic retry logic for transient failures
- [ ] Comprehensive error handling and transformation
- [ ] Request/response logging for debugging
- [ ] SSE support for real-time updates
- [ ] All interceptors properly implemented
- [ ] Migration guide completed

## Interfaces with Other Agents
- **Agent B1** provides the API specification
- **Agent A2** will use this client for flow operations
- **Agent D1** will use field mapping client
- Share types in `src/api/v3/types/index.ts`

## Implementation Guidelines

### 1. Type Safety First
- Generate types from OpenAPI spec if available
- No implicit `any` types
- Strict null checks enabled
- Exhaustive switch cases for enums

### 2. Error Handling
```typescript
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public errorCode: string,
    public details?: any
  ) {
    super(`API Error ${statusCode}: ${errorCode}`);
  }
}
```

### 3. Caching Strategy
- Cache GET requests where appropriate
- Invalidate cache on mutations
- Respect cache headers from server

### 4. Development Experience
- IntelliSense support for all methods
- JSDoc comments with examples
- Helpful error messages
- Debug mode with detailed logging

## Commands to Run
```bash
# Type checking
docker exec -it migration_frontend npm run type-check

# Generate types from OpenAPI (if available)
docker exec -it migration_frontend npm run generate-api-types

# Run tests
docker exec -it migration_frontend npm run test:api

# Build to verify
docker exec -it migration_frontend npm run build
```

## Definition of Done
- [ ] Complete v3 API client implementation
- [ ] All types match backend schemas exactly
- [ ] Interceptors working correctly
- [ ] Retry logic tested with various scenarios
- [ ] Error handling comprehensive
- [ ] SSE implementation tested
- [ ] Migration guide complete with examples
- [ ] PR created with title: "feat: [Phase1-B2] Frontend API v3 client"
- [ ] Zero TypeScript errors
- [ ] Integration tests passing

## Usage Example
```typescript
import { createApiV3Client } from '@/api/v3';

const api = createApiV3Client({
  baseURL: process.env.REACT_APP_API_URL,
  enableLogging: process.env.NODE_ENV === 'development'
});

// Create a new flow
const flow = await api.discoveryFlow.createFlow({
  name: 'Q4 2024 Migration',
  client_account_id: clientId,
  engagement_id: engagementId
});

// Subscribe to updates
const eventSource = api.discoveryFlow.subscribeToFlowUpdates(
  flow.flow_id,
  (status) => console.log('Flow status:', status)
);

// Execute a phase
await api.discoveryFlow.executePhase(flow.flow_id, FlowPhase.FIELD_MAPPING);
```

## Notes
- Coordinate with Agent B1 on API contract
- Test against both dev and staging environments
- Consider bundle size optimization
- Plan for offline support in future phases