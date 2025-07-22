/**
 * TypeScript types for API client utilities.
 * Provides type safety for API operations and configurations.
 */

// API Response Types
export interface ApiResponse<T = any> {
  status: 'success' | 'error' | 'warning' | 'info';
  message: string;
  data?: T;
  errors?: ApiError[];
  meta?: Record<string, any>;
  timestamp: string;
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  data: T[];
  pagination: {
    total_items: number;
    page: number;
    page_size: number;
    total_pages: number;
    has_previous: boolean;
    has_next: boolean;
    previous_page?: number;
    next_page?: number;
  };
}

export interface ApiError {
  code: string;
  message: string;
  field?: string;
  value?: unknown;
  constraint?: string;
  additional_info?: Record<string, any>;
}

// Request Configuration Types
export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  params?: Record<string, any>;
  data?: unknown;
  timeout?: number;
  retries?: number;
  cache?: boolean;
  cacheKey?: string;
  cacheTtl?: number;
}

export interface ApiClientConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  retryDelay: number;
  headers: Record<string, string>;
  enableLogging: boolean;
  enableCache: boolean;
  cachePrefix: string;
  defaultCacheTtl: number;
}

// Multi-tenant Context Types
export interface MultiTenantContext {
  clientAccountId?: string;
  engagementId?: string;
  userId?: string;
  userRole?: string;
  permissions?: string[];
}

export interface MultiTenantHeaders {
  'X-Client-Account-ID'?: string;
  'X-Engagement-ID'?: string;
  'X-User-ID'?: string;
  'X-User-Role'?: string;
  'Authorization'?: string;
}

// Error Types
export interface NetworkError {
  type: 'network';
  message: string;
  code: string;
  url: string;
  method: string;
  status?: number;
  response?: unknown;
  timestamp: string;
}

export interface ValidationError {
  type: 'validation';
  message: string;
  code: string;
  field?: string;
  value?: unknown;
  errors: ApiError[];
  timestamp: string;
}

export interface AuthenticationError {
  type: 'authentication';
  message: string;
  code: string;
  reason: 'token_expired' | 'invalid_credentials' | 'missing_token';
  timestamp: string;
}

export interface AuthorizationError {
  type: 'authorization';
  message: string;
  code: string;
  requiredPermissions?: string[];
  userPermissions?: string[];
  resource?: string;
  timestamp: string;
}

export interface ServerError {
  type: 'server';
  message: string;
  code: string;
  status: number;
  errorId?: string;
  timestamp: string;
}

export type ApiErrorType = NetworkError | ValidationError | AuthenticationError | AuthorizationError | ServerError;

// Retry Configuration
export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffFactor: number;
  retryCondition: (error: ApiErrorType) => boolean;
}

// Cache Configuration
export interface CacheConfig {
  enabled: boolean;
  keyPrefix: string;
  defaultTtl: number;
  maxSize: number;
  cleanupInterval: number;
}

// Request/Response Interceptor Types
export interface RequestInterceptor {
  name: string;
  priority: number;
  onRequest: (config: RequestConfig) => Promise<RequestConfig> | RequestConfig;
  onError?: (error: unknown) => Promise<any> | any;
}

export interface ResponseInterceptor {
  name: string;
  priority: number;
  onResponse: (response: ApiResponse) => Promise<ApiResponse> | ApiResponse;
  onError?: (error: ApiErrorType) => Promise<ApiErrorType> | ApiErrorType;
}

// Flow-specific Types
export interface FlowContext {
  flowId: string;
  flowType: string;
  phase?: string;
  userId?: string;
  sessionId?: string;
}

export interface FlowApiResponse<T = any> extends ApiResponse<T> {
  flowContext?: FlowContext;
  flowStatus?: string;
  flowProgress?: number;
}

// Upload Types
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  speed: number;
  timeRemaining: number;
}

export interface UploadConfig extends RequestConfig {
  file: File;
  fieldName: string;
  onProgress?: (progress: UploadProgress) => void;
  chunkSize?: number;
  resumable?: boolean;
}

// WebSocket Types
export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnectAttempts: number;
  reconnectDelay: number;
  heartbeatInterval: number;
  headers?: Record<string, string>;
}

export interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: string;
  id?: string;
}

// Polling Types
export interface PollingConfig {
  interval: number;
  maxAttempts: number;
  stopCondition: (response: ApiResponse) => boolean;
  onProgress?: (attempt: number, response: ApiResponse) => void;
}

// Batch Request Types
export interface BatchRequest {
  id: string;
  method: string;
  url: string;
  data?: unknown;
  headers?: Record<string, string>;
}

export interface BatchResponse {
  id: string;
  status: number;
  data: unknown;
  error?: ApiErrorType;
}

// Health Check Types
export interface HealthCheckResult {
  service: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  latency: number;
  timestamp: string;
  details?: Record<string, any>;
}

// Metrics Types
export interface ApiMetrics {
  requestCount: number;
  errorCount: number;
  averageLatency: number;
  errorRate: number;
  successRate: number;
  cacheHitRate: number;
  lastUpdated: string;
}

// Query Builder Types
export interface QueryParams {
  page?: number;
  page_size?: number;
  sort?: string;
  order?: 'asc' | 'desc';
  filters?: Record<string, any>;
  search?: string;
  fields?: string[];
  include?: string[];
  exclude?: string[];
}

export interface QueryBuilder {
  page(page: number): QueryBuilder;
  pageSize(size: number): QueryBuilder;
  sort(field: string, order?: 'asc' | 'desc'): QueryBuilder;
  filter(field: string, value: unknown): QueryBuilder;
  filters(filters: Record<string, any>): QueryBuilder;
  search(query: string): QueryBuilder;
  fields(fields: string[]): QueryBuilder;
  include(fields: string[]): QueryBuilder;
  exclude(fields: string[]): QueryBuilder;
  build(): QueryParams;
  toString(): string;
}

// Client Instance Types
export interface ApiClient {
  get<T = any>(url: string, config?: RequestConfig): Promise<ApiResponse<T>>;
  post<T = any>(url: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>>;
  put<T = any>(url: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>>;
  delete<T = any>(url: string, config?: RequestConfig): Promise<ApiResponse<T>>;
  patch<T = any>(url: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>>;
  upload<T = any>(url: string, config: UploadConfig): Promise<ApiResponse<T>>;
  batch(requests: BatchRequest[]): Promise<BatchResponse[]>;
  poll<T = any>(url: string, config: PollingConfig): Promise<ApiResponse<T>>;
  healthCheck(): Promise<HealthCheckResult[]>;
  getMetrics(): ApiMetrics;
  clearCache(pattern?: string): void;
  setDefaultHeaders(headers: Record<string, string>): void;
  setMultiTenantContext(context: MultiTenantContext): void;
  addRequestInterceptor(interceptor: RequestInterceptor): void;
  addResponseInterceptor(interceptor: ResponseInterceptor): void;
  removeInterceptor(name: string): void;
}