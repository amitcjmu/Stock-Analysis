/**
 * TypeScript types for API client utilities.
 * Provides type safety for API operations and configurations.
 */

// Import shared types
import type {
  ApiResponse as SharedApiResponse,
  ApiError as SharedApiError,
  ResponseMetadata
} from '../../types/shared/api-types';
import type { AuditableMetadata } from '../../types/shared/metadata-types';

// API Response Types - Use shared types
export type ApiResponse<T = unknown> = SharedApiResponse<T, ApiError>;

// Legacy compatibility - keeping old structure for backward compatibility
export interface LegacyApiResponse<T = unknown> {
  status: 'success' | 'error' | 'warning' | 'info';
  message: string;
  data?: T;
  errors?: ApiError[];
  meta?: Record<string, unknown>;
  timestamp: string;
}

export interface PaginatedResponse<T = unknown> extends ApiResponse<T[]> {
  data: T[];
  meta: ResponseMetadata & {
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
  };
}

// API Error Types - Enhanced with shared structure
export interface ApiError extends SharedApiError {
  field?: string;
  value?: string | number | boolean | null;
  constraint?: string;
  additional_info?: Record<string, unknown>;
}

// Request Configuration Types
export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  params?: Record<string, unknown>;
  data?: unknown;
  timeout?: number;
  retries?: number;
  cache?: boolean;
  cacheKey?: string;
  cacheTtl?: number;
  url?: string;
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

// Specialized Error Types - Built on shared ApiError
export interface NetworkError extends ApiError {
  type: 'network';
  url: string;
  method: string;
  status?: number;
  response?: unknown;
}

export interface ValidationError extends ApiError {
  type: 'validation';
  field?: string;
  value?: string | number | boolean | null;
  errors: ApiError[];
}

export interface AuthenticationError extends ApiError {
  type: 'authentication';
  reason: 'token_expired' | 'invalid_credentials' | 'missing_token';
}

export interface AuthorizationError extends ApiError {
  type: 'authorization';
  requiredPermissions?: string[];
  userPermissions?: string[];
  resource?: string;
}

export interface ServerError extends ApiError {
  type: 'server';
  status: number;
  errorId?: string;
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
  onError?: (error: ApiErrorType) => Promise<ApiErrorType> | ApiErrorType;
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

export interface FlowApiResponse<T = unknown> extends ApiResponse<T> {
  meta?: ResponseMetadata & {
    flowContext?: FlowContext;
    flowStatus?: string;
    flowProgress?: number;
  };
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
  fieldName?: string;
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

export interface WebSocketMessage<T = unknown> {
  type: string;
  data: T;
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

export interface BatchResponse<T = unknown> {
  id: string;
  status: number;
  data: T;
  error?: ApiErrorType;
}

// Health Check Types
export interface HealthCheckResult {
  service: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  latency: number;
  timestamp: string;
  details?: Record<string, unknown>;
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
  filters?: Record<string, unknown>;
  search?: string;
  fields?: string[];
  include?: string[];
  exclude?: string[];
}

export interface QueryBuilder {
  page(page: number): QueryBuilder;
  pageSize(size: number): QueryBuilder;
  sort(field: string, order?: 'asc' | 'desc'): QueryBuilder;
  filter(field: string, value: string | number | boolean | null): QueryBuilder;
  filters(filters: Record<string, string | number | boolean | null>): QueryBuilder;
  search(query: string): QueryBuilder;
  fields(fields: string[]): QueryBuilder;
  include(fields: string[]): QueryBuilder;
  exclude(fields: string[]): QueryBuilder;
  build(): QueryParams;
  toString(): string;
}

// Client Instance Types
export interface ApiClient {
  get<T = unknown>(url: string, config?: RequestConfig): Promise<ApiResponse<T>>;
  post<T = unknown>(url: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>>;
  put<T = unknown>(url: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>>;
  delete<T = unknown>(url: string, config?: RequestConfig): Promise<ApiResponse<T>>;
  patch<T = unknown>(url: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>>;
  upload<T = unknown>(url: string, config: UploadConfig): Promise<ApiResponse<T>>;
  batch<T = unknown>(requests: BatchRequest[]): Promise<Array<BatchResponse<T>>>;
  poll<T = unknown>(url: string, config: PollingConfig): Promise<ApiResponse<T>>;
  healthCheck(): Promise<HealthCheckResult[]>;
  getMetrics(): ApiMetrics;
  clearCache(pattern?: string): void;
  setDefaultHeaders(headers: Record<string, string>): void;
  setMultiTenantContext(context: MultiTenantContext): void;
  addRequestInterceptor(interceptor: RequestInterceptor): void;
  addResponseInterceptor(interceptor: ResponseInterceptor): void;
  removeInterceptor(name: string): void;
}
