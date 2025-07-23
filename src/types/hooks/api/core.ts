/**
 * Core API Hook Types
 * 
 * Base API hooks for general HTTP operations, request handling,
 * API client management, and state management.
 */

import type { BaseAsyncHookParams } from '../shared/base-patterns'
import type { BaseAsyncHookReturn } from '../shared/base-patterns'
import type { RetryConfig, CacheConfig, ApiResponse, RequestConfig, ApiInterceptors, AuthConfig, HttpMethod, ProgressEvent, ApiState, Interceptor } from './shared'
import type { ApiClient } from './shared'

// Base API Hook Types
export interface UseApiParams<TParams = unknown> extends BaseAsyncHookParams {
  endpoint: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  params?: TParams;
  headers?: Record<string, string>;
  baseURL?: string;
  timeout?: number;
  withCredentials?: boolean;
  validateStatus?: (status: number) => boolean;
  transformRequest?: (data: unknown) => unknown;
  transformResponse?: (data: unknown) => unknown;
  cancelOnUnmount?: boolean;
  retryConfig?: RetryConfig;
  cacheConfig?: CacheConfig;
}

export interface UseApiReturn<TData = unknown, TError = Error> extends BaseAsyncHookReturn<TData, TError> {
  data: TData | undefined;
  error: TError | null;
  loading: boolean;
  success: boolean;
  statusCode?: number;
  headers?: Record<string, string>;
  retryCount: number;
  lastFetchTime?: number;
  cacheHit: boolean;
  abort: () => void;
  retry: () => Promise<void>;
  invalidate: () => void;
}

// Request Hook Types
export interface UseRequestParams<TData = unknown, TParams = unknown> {
  url: string;
  method?: HttpMethod;
  data?: unknown;
  params?: TParams;
  headers?: Record<string, string>;
  timeout?: number;
  retryConfig?: RetryConfig;
  cacheConfig?: CacheConfig;
  onUploadProgress?: (progress: ProgressEvent) => void;
  onDownloadProgress?: (progress: ProgressEvent) => void;
  transformRequest?: (data: unknown) => unknown;
  transformResponse?: (data: unknown) => TData;
  validateStatus?: (status: number) => boolean;
  signal?: AbortSignal;
}

export interface UseRequestReturn<TData = unknown> {
  data: TData | undefined;
  error: Error | null;
  loading: boolean;
  success: boolean;
  progress: number;
  statusCode?: number;
  headers?: Record<string, string>;
  execute: (overrides?: Partial<UseRequestParams>) => Promise<TData>;
  abort: () => void;
  retry: () => Promise<TData>;
  reset: () => void;
}

// API Client Hook Types
export interface UseApiClientParams {
  baseURL: string;
  defaultHeaders?: Record<string, string>;
  timeout?: number;
  withCredentials?: boolean;
  interceptors?: ApiInterceptors;
  retryConfig?: RetryConfig;
  cacheConfig?: CacheConfig;
  authConfig?: AuthConfig;
}

export interface UseApiClientReturn {
  client: ApiClient;
  get: <T = unknown>(endpoint: string, config?: RequestConfig) => Promise<T>;
  post: <T = unknown>(endpoint: string, data?: unknown, config?: RequestConfig) => Promise<T>;
  put: <T = unknown>(endpoint: string, data?: unknown, config?: RequestConfig) => Promise<T>;
  patch: <T = unknown>(endpoint: string, data?: unknown, config?: RequestConfig) => Promise<T>;
  delete: <T = unknown>(endpoint: string, config?: RequestConfig) => Promise<T>;
  upload: (endpoint: string, file: File, config?: UploadConfig) => Promise<UploadResponse>;
  download: (endpoint: string, config?: DownloadConfig) => Promise<Blob>;
  setAuthToken: (token: string) => void;
  clearAuth: () => void;
  addInterceptor: (interceptor: Interceptor) => () => void;
  removeInterceptor: (id: string) => void;
}

// API State Hook Types
export interface UseApiStateParams {
  initialState?: ApiState;
  onStateChange?: (state: ApiState) => void;
  autoReset?: boolean;
  resetDelay?: number;
}

export interface UseApiStateReturn {
  state: ApiState;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  isIdle: boolean;
  hasData: boolean;
  hasError: boolean;
  setLoading: () => void;
  setSuccess: (data?: unknown) => void;
  setError: (error: Error) => void;
  setIdle: () => void;
  reset: () => void;
  setState: (state: Partial<ApiState>) => void;
}

// Import types from shared for re-export if needed
import type { UploadConfig, DownloadConfig, UploadResponse } from './file-operations';