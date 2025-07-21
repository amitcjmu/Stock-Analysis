/**
 * Shared Types for API Hooks
 * 
 * Common types and interfaces used across multiple API hook modules.
 */

// API response interface
export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  config: RequestConfig;
}

// Retry configuration
export interface RetryConfig {
  attempts: number;
  delay: number | ((attempt: number) => number);
  condition?: (error: Error) => boolean;
  onRetry?: (attempt: number, error: Error) => void;
}

// Cache configuration
export interface CacheConfig {
  enabled: boolean;
  ttl?: number;
  key?: string;
  storage?: 'memory' | 'localStorage' | 'sessionStorage';
  invalidateOn?: string[];
  tags?: string[];
}

// API interceptors
export interface ApiInterceptors {
  request?: RequestInterceptor[];
  response?: ResponseInterceptor[];
}

export interface RequestInterceptor {
  id?: string;
  onFulfilled?: (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
  onRejected?: (error: unknown) => unknown | Promise<unknown>;
}

export interface ResponseInterceptor {
  id?: string;
  onFulfilled?: (response: ApiResponse) => ApiResponse | Promise<ApiResponse>;
  onRejected?: (error: unknown) => unknown | Promise<unknown>;
}

// Authentication configuration
export interface AuthConfig {
  type: 'bearer' | 'basic' | 'apikey' | 'custom';
  token?: string;
  refreshToken?: string;
  refreshEndpoint?: string;
  header?: string;
  tokenPrefix?: string;
  onTokenExpired?: () => void;
  onRefreshSuccess?: (token: string) => void;
  onRefreshFailure?: (error: Error) => void;
}

// API client interface
export interface ApiClient {
  defaults: RequestConfig;
  interceptors: ApiInterceptors;
  request: <T = unknown>(config: RequestConfig) => Promise<T>;
  get: <T = unknown>(url: string, config?: RequestConfig) => Promise<T>;
  post: <T = unknown>(url: string, data?: unknown, config?: RequestConfig) => Promise<T>;
  put: <T = unknown>(url: string, data?: unknown, config?: RequestConfig) => Promise<T>;
  patch: <T = unknown>(url: string, data?: unknown, config?: RequestConfig) => Promise<T>;
  delete: <T = unknown>(url: string, config?: RequestConfig) => Promise<T>;
}

// Request configuration
export interface RequestConfig {
  url?: string;
  method?: HttpMethod;
  baseURL?: string;
  headers?: Record<string, string>;
  params?: unknown;
  data?: unknown;
  timeout?: number;
  withCredentials?: boolean;
  auth?: AuthCredentials;
  responseType?: ResponseType;
  signal?: AbortSignal;
  onUploadProgress?: (progressEvent: ProgressEvent) => void;
  onDownloadProgress?: (progressEvent: ProgressEvent) => void;
  transformRequest?: (data: unknown, headers: Record<string, string>) => unknown;
  transformResponse?: (data: unknown) => unknown;
  validateStatus?: (status: number) => boolean;
}

// API state
export interface ApiState {
  data?: unknown;
  error?: Error;
  loading: boolean;
  success: boolean;
  timestamp?: number;
}

// Interceptor type
export interface Interceptor {
  id: string;
  type: 'request' | 'response';
  handler: (value: unknown) => unknown | Promise<unknown>;
  errorHandler?: (error: unknown) => unknown | Promise<unknown>;
}

// Authentication credentials
export interface AuthCredentials {
  username?: string;
  password?: string;
  token?: string;
}

// Progress event
export interface ProgressEvent {
  loaded: number;
  total: number;
  lengthComputable: boolean;
}

// Type aliases
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS';
export type ResponseType = 'arraybuffer' | 'blob' | 'document' | 'json' | 'text' | 'stream';