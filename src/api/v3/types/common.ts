/**
 * Common Types for API v3
 * Shared interfaces and types used across all v3 API clients
 */

// === Pagination Types ===

export interface PaginationParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

// === Error Types ===

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
  request_id: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface ValidationErrorResponse {
  error: string;
  message: string;
  validation_errors: ValidationError[];
  request_id: string;
}

// === Common Request/Response Types ===

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version: string;
  timestamp: string;
  components: Record<string, boolean>;
  uptime_seconds?: number;
}

export interface MetricsResponse {
  active_flows: number;
  total_flows: number;
  completed_flows: number;
  failed_flows: number;
  avg_completion_time_seconds?: number;
  avg_response_time_ms?: number;
  success_rate_percentage?: number;
  timestamp: string;
}

// === API Client Configuration ===

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  enableLogging?: boolean;
  authToken?: string;
  defaultHeaders?: Record<string, string>;
}

export interface RequestConfig {
  includeAuth?: boolean;
  includeContext?: boolean;
  timeout?: number;
  retryAttempts?: number;
  cache?: boolean;
}

// === Context Types ===

export interface RequestContext {
  client_account_id?: string;
  engagement_id?: string;
  user_id?: string;
  session_id?: string;
  flow_id?: string;
}

// === Query Builder Types ===

export interface QueryParams {
  [key: string]: string | number | boolean | string[] | undefined;
}

export interface FilterParams {
  search?: string;
  status?: string;
  created_after?: string;
  created_before?: string;
  updated_after?: string;
  updated_before?: string;
}

// === Response Helpers ===

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  request_id: string;
  timestamp: string;
}

export interface StreamResponse {
  eventSource: EventSource;
  close: () => void;
  onMessage: (callback: (data: any) => void) => void;
  onError: (callback: (error: Event) => void) => void;
  onClose: (callback: () => void) => void;
}

// === File Upload Types ===

export interface FileUploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface FileUploadConfig {
  onProgress?: (progress: FileUploadProgress) => void;
  onComplete?: (response: any) => void;
  onError?: (error: Error) => void;
  maxSize?: number;
  allowedTypes?: string[];
  timeout?: number;
}