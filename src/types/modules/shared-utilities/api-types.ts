/**
 * API Utilities Types
 * 
 * Types for API clients, request handling, caching, and retry mechanisms.
 */

// API service interfaces
export interface ApiClientService {
  get: <T>(url: string, options?: RequestOptions) => Promise<ApiResponse<T>>;
  post: <T>(url: string, data?: unknown, options?: RequestOptions) => Promise<ApiResponse<T>>;
  put: <T>(url: string, data?: unknown, options?: RequestOptions) => Promise<ApiResponse<T>>;
  patch: <T>(url: string, data?: unknown, options?: RequestOptions) => Promise<ApiResponse<T>>;
  delete: <T>(url: string, options?: RequestOptions) => Promise<ApiResponse<T>>;
  upload: <T>(url: string, file: File, options?: UploadOptions) => Promise<ApiResponse<T>>;
  download: (url: string, options?: DownloadOptions) => Promise<Blob>;
}

export interface RequestInterceptorService {
  addRequestInterceptor: (interceptor: RequestInterceptor) => string;
  removeRequestInterceptor: (id: string) => void;
  addResponseInterceptor: (interceptor: ResponseInterceptor) => string;
  removeResponseInterceptor: (id: string) => void;
}

export interface CacheService {
  get: <T>(key: string) => Promise<T | null>;
  set: <T>(key: string, value: T, ttl?: number) => Promise<void>;
  delete: (key: string) => Promise<void>;
  clear: () => Promise<void>;
  has: (key: string) => Promise<boolean>;
  keys: (pattern?: string) => Promise<string[]>;
}

export interface RetryService {
  retry: <T>(fn: () => Promise<T>, options?: RetryOptions) => Promise<T>;
  withRetry: <T>(options: RetryOptions) => (fn: () => Promise<T>) => Promise<T>;
  isRetryable: (error: Error) => boolean;
  getBackoffDelay: (attempt: number, options: RetryOptions) => number;
}

// API model types
export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  message?: string;
  errors?: ApiError[];
  metadata?: ResponseMetadata;
  pagination?: PaginationInfo;
}

export interface ApiError {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, unknown>;
}

export interface ResponseMetadata {
  requestId: string;
  timestamp: string;
  version: string;
  processingTime: number;
  rateLimit?: RateLimitInfo;
}

export interface PaginationInfo {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface RequestOptions {
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
  cache?: boolean;
  cacheTtl?: number;
  validateStatus?: (status: number) => boolean;
  transformRequest?: (data: unknown) => unknown;
  transformResponse?: (data: unknown) => unknown;
}

export interface UploadOptions extends RequestOptions {
  onProgress?: (progress: ProgressEvent) => void;
  chunkSize?: number;
  resumable?: boolean;
}

export interface DownloadOptions extends RequestOptions {
  onProgress?: (progress: ProgressEvent) => void;
  fileName?: string;
  mimeType?: string;
}

export interface RequestInterceptor {
  onRequest: (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
  onRequestError: (error: Error) => Promise<Error>;
}

export interface ResponseInterceptor {
  onResponse: (response: Response) => Response | Promise<Response>;
  onResponseError: (error: Error) => Promise<Error>;
}

export interface RetryOptions {
  maxRetries: number;
  initialDelay: number;
  maxDelay: number;
  backoffFactor: number;
  jitter: boolean;
  retryableErrors: string[];
  onRetry?: (error: Error, attempt: number) => void;
}

export interface RequestConfig {
  url: string;
  method: string;
  headers: Record<string, string>;
  data?: unknown;
  params?: Record<string, unknown>;
  timeout: number;
  baseURL?: string;
}

export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: number;
  retryAfter?: number;
}

export interface Response {
  data: unknown;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  config: RequestConfig;
}