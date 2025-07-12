/**
 * API Hook Types
 * 
 * Type definitions for API-related hooks including data fetching,
 * mutation hooks, and API client configuration patterns.
 */

import {
  BaseAsyncHookParams,
  BaseAsyncHookReturn,
  BaseMutationHookParams,
  BaseMutationHookReturn
} from './shared';

// Base API Hook Types
export interface UseApiParams<TParams = any> extends BaseAsyncHookParams {
  endpoint: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  params?: TParams;
  headers?: Record<string, string>;
  baseURL?: string;
  timeout?: number;
  withCredentials?: boolean;
  validateStatus?: (status: number) => boolean;
  transformRequest?: (data: any) => any;
  transformResponse?: (data: any) => any;
  cancelOnUnmount?: boolean;
  retryConfig?: RetryConfig;
  cacheConfig?: CacheConfig;
}

export interface UseApiReturn<TData = any, TError = Error> extends BaseAsyncHookReturn<TData, TError> {
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

// Query Hook Types
export interface UseQueryParams<TParams = any> extends UseApiParams<TParams> {
  queryKey: string | string[];
  dependencies?: any[];
  enabled?: boolean;
  retryOnMount?: boolean;
  backgroundRefetch?: boolean;
  pollingInterval?: number;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
  onSettled?: (data: any | undefined, error: Error | null) => void;
  select?: (data: any) => any;
  keepPreviousData?: boolean;
  suspense?: boolean;
}

export interface UseQueryReturn<TData = any, TError = Error> extends UseApiReturn<TData, TError> {
  data: TData | undefined;
  error: TError | null;
  isLoading: boolean;
  isFetching: boolean;
  isError: boolean;
  isSuccess: boolean;
  isIdle: boolean;
  isStale: boolean;
  isPlaceholderData: boolean;
  isPreviousData: boolean;
  dataUpdatedAt: number;
  errorUpdatedAt: number;
  failureCount: number;
  refetch: (options?: RefetchOptions) => Promise<any>;
  remove: () => void;
  cancel: () => void;
}

// Mutation Hook Types
export interface UseMutationParams<TData = any, TError = Error, TVariables = any, TContext = any> 
  extends BaseMutationHookParams<TData, TError, TVariables, TContext> {
  endpoint: string;
  method: 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  baseURL?: string;
  timeout?: number;
  withCredentials?: boolean;
  optimisticUpdate?: OptimisticUpdateConfig<TData, TVariables>;
  invalidateQueries?: string[];
  updateQueries?: QueryUpdateConfig<TData, TVariables>[];
  onMutate?: (variables: TVariables) => Promise<TContext | void> | TContext | void;
  onSuccess?: (data: TData, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
  onError?: (error: TError, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
  onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
}

export interface UseMutationReturn<TData = any, TError = Error, TVariables = any, TContext = any> 
  extends BaseMutationHookReturn<TData, TError, TVariables, TContext> {
  data: TData | undefined;
  error: TError | null;
  isIdle: boolean;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  isPaused: boolean;
  status: 'idle' | 'loading' | 'error' | 'success';
  failureCount: number;
  failureReason: TError | null;
  mutate: (variables: TVariables, options?: MutateOptions<TData, TError, TVariables, TContext>) => void;
  mutateAsync: (variables: TVariables, options?: MutateOptions<TData, TError, TVariables, TContext>) => Promise<TData>;
  reset: () => void;
  context: TContext | undefined;
  variables: TVariables | undefined;
}

// Infinite Query Hook Types
export interface UseInfiniteQueryParams<TParams = any> extends UseQueryParams<TParams> {
  getNextPageParam: (lastPage: any, allPages: any[]) => any;
  getPreviousPageParam?: (firstPage: any, allPages: any[]) => any;
  maxPages?: number;
  initialPageParam?: any;
}

export interface UseInfiniteQueryReturn<TData = any, TError = Error> extends Omit<UseQueryReturn<TData, TError>, 'data'> {
  data: InfiniteData<TData> | undefined;
  fetchNextPage: (options?: FetchNextPageOptions) => Promise<any>;
  fetchPreviousPage: (options?: FetchPreviousPageOptions) => Promise<any>;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  isFetchingNextPage: boolean;
  isFetchingPreviousPage: boolean;
}

// Subscription Hook Types
export interface UseSubscriptionParams<TData = any> {
  endpoint: string;
  protocol?: 'websocket' | 'sse' | 'polling';
  options?: SubscriptionOptions;
  enabled?: boolean;
  onData?: (data: TData) => void;
  onError?: (error: Error) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onReconnect?: () => void;
  transformData?: (rawData: any) => TData;
  filterData?: (data: TData) => boolean;
  bufferSize?: number;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export interface UseSubscriptionReturn<TData = any> {
  data: TData | undefined;
  error: Error | null;
  isConnected: boolean;
  isConnecting: boolean;
  isReconnecting: boolean;
  connectionState: ConnectionState;
  lastMessage?: TData;
  messageCount: number;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
  send: (message: any) => void;
  subscribe: (event: string, handler: (data: any) => void) => () => void;
  unsubscribe: (event: string) => void;
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
  get: <T = any>(endpoint: string, config?: RequestConfig) => Promise<T>;
  post: <T = any>(endpoint: string, data?: any, config?: RequestConfig) => Promise<T>;
  put: <T = any>(endpoint: string, data?: any, config?: RequestConfig) => Promise<T>;
  patch: <T = any>(endpoint: string, data?: any, config?: RequestConfig) => Promise<T>;
  delete: <T = any>(endpoint: string, config?: RequestConfig) => Promise<T>;
  upload: (endpoint: string, file: File, config?: UploadConfig) => Promise<any>;
  download: (endpoint: string, config?: DownloadConfig) => Promise<Blob>;
  setAuthToken: (token: string) => void;
  clearAuth: () => void;
  addInterceptor: (interceptor: Interceptor) => () => void;
  removeInterceptor: (id: string) => void;
}

// Request Hook Types
export interface UseRequestParams<TData = any, TParams = any> {
  url: string;
  method?: HttpMethod;
  data?: any;
  params?: TParams;
  headers?: Record<string, string>;
  timeout?: number;
  retryConfig?: RetryConfig;
  cacheConfig?: CacheConfig;
  onUploadProgress?: (progress: ProgressEvent) => void;
  onDownloadProgress?: (progress: ProgressEvent) => void;
  transformRequest?: (data: any) => any;
  transformResponse?: (data: any) => TData;
  validateStatus?: (status: number) => boolean;
  signal?: AbortSignal;
}

export interface UseRequestReturn<TData = any> {
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

// Batch Request Hook Types
export interface UseBatchRequestParams {
  requests: BatchRequest[];
  concurrent?: boolean;
  maxConcurrency?: number;
  stopOnError?: boolean;
  retryFailedRequests?: boolean;
  onProgress?: (completed: number, total: number) => void;
  onRequestComplete?: (result: BatchRequestResult, index: number) => void;
  onRequestError?: (error: Error, request: BatchRequest, index: number) => void;
}

export interface UseBatchRequestReturn {
  results: BatchRequestResult[];
  loading: boolean;
  completed: number;
  total: number;
  progress: number;
  errors: BatchError[];
  execute: () => Promise<BatchRequestResult[]>;
  abort: () => void;
  retry: (indices?: number[]) => Promise<BatchRequestResult[]>;
  reset: () => void;
}

// File Upload Hook Types
export interface UseFileUploadParams {
  endpoint: string;
  method?: 'POST' | 'PUT' | 'PATCH';
  headers?: Record<string, string>;
  maxFileSize?: number;
  allowedTypes?: string[];
  multiple?: boolean;
  autoUpload?: boolean;
  chunkSize?: number;
  resumable?: boolean;
  validateFile?: (file: File) => ValidationResult;
  transformFile?: (file: File) => File | Promise<File>;
  onProgress?: (progress: UploadProgress) => void;
  onSuccess?: (response: any, file: File) => void;
  onError?: (error: Error, file: File) => void;
  onComplete?: (results: UploadResult[]) => void;
}

export interface UseFileUploadReturn {
  files: UploadFile[];
  uploading: boolean;
  progress: number;
  completed: number;
  total: number;
  errors: UploadError[];
  addFiles: (files: File[] | FileList) => void;
  removeFile: (id: string) => void;
  clearFiles: () => void;
  upload: (files?: File[]) => Promise<UploadResult[]>;
  uploadFile: (file: File) => Promise<UploadResult>;
  pauseUpload: (id: string) => void;
  resumeUpload: (id: string) => void;
  cancelUpload: (id: string) => void;
  retryUpload: (id: string) => Promise<UploadResult>;
}

// Cache Hook Types
export interface UseCacheParams<T = any> {
  key: string;
  defaultValue?: T;
  ttl?: number;
  storage?: 'memory' | 'localStorage' | 'sessionStorage' | 'indexedDB';
  serializer?: CacheSerializer<T>;
  validator?: (value: T) => boolean;
  onExpire?: (key: string, value: T) => void;
  onSet?: (key: string, value: T) => void;
  onGet?: (key: string, value: T) => void;
  onDelete?: (key: string) => void;
}

export interface UseCacheReturn<T = any> {
  value: T | undefined;
  exists: boolean;
  expired: boolean;
  lastModified?: number;
  ttl?: number;
  set: (value: T, ttl?: number) => void;
  get: () => T | undefined;
  delete: () => void;
  clear: () => void;
  refresh: () => void;
  extend: (ttl: number) => void;
  touch: () => void;
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
  setSuccess: (data?: any) => void;
  setError: (error: Error) => void;
  setIdle: () => void;
  reset: () => void;
  setState: (state: Partial<ApiState>) => void;
}

// Supporting Types
export interface RetryConfig {
  attempts: number;
  delay: number | ((attempt: number) => number);
  condition?: (error: Error) => boolean;
  onRetry?: (attempt: number, error: Error) => void;
}

export interface CacheConfig {
  enabled: boolean;
  ttl?: number;
  key?: string;
  storage?: 'memory' | 'localStorage' | 'sessionStorage';
  invalidateOn?: string[];
  tags?: string[];
}

export interface ApiInterceptors {
  request?: RequestInterceptor[];
  response?: ResponseInterceptor[];
}

export interface RequestInterceptor {
  id?: string;
  onFulfilled?: (config: any) => any | Promise<any>;
  onRejected?: (error: any) => any | Promise<any>;
}

export interface ResponseInterceptor {
  id?: string;
  onFulfilled?: (response: any) => any | Promise<any>;
  onRejected?: (error: any) => any | Promise<any>;
}

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

export interface OptimisticUpdateConfig<TData, TVariables> {
  updater: (variables: TVariables) => TData;
  rollback?: (previous: TData, error: Error) => TData;
}

export interface QueryUpdateConfig<TData, TVariables> {
  queryKey: string;
  updater: (previous: any, variables: TVariables, response: TData) => any;
}

export interface RefetchOptions {
  throwOnError?: boolean;
  cancelRefetch?: boolean;
}

export interface MutateOptions<TData, TError, TVariables, TContext> {
  onSuccess?: (data: TData, variables: TVariables, context: TContext | undefined) => void;
  onError?: (error: TError, variables: TVariables, context: TContext | undefined) => void;
  onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables, context: TContext | undefined) => void;
}

export interface InfiniteData<TData> {
  pages: TData[];
  pageParams: any[];
}

export interface FetchNextPageOptions {
  pageParam?: any;
  throwOnError?: boolean;
}

export interface FetchPreviousPageOptions {
  pageParam?: any;
  throwOnError?: boolean;
}

export interface SubscriptionOptions {
  protocols?: string[];
  headers?: Record<string, string>;
  query?: Record<string, string>;
  timeout?: number;
  heartbeat?: boolean;
  heartbeatInterval?: number;
  compression?: boolean;
}

export interface ApiClient {
  defaults: RequestConfig;
  interceptors: ApiInterceptors;
  request: <T = any>(config: RequestConfig) => Promise<T>;
  get: <T = any>(url: string, config?: RequestConfig) => Promise<T>;
  post: <T = any>(url: string, data?: any, config?: RequestConfig) => Promise<T>;
  put: <T = any>(url: string, data?: any, config?: RequestConfig) => Promise<T>;
  patch: <T = any>(url: string, data?: any, config?: RequestConfig) => Promise<T>;
  delete: <T = any>(url: string, config?: RequestConfig) => Promise<T>;
}

export interface RequestConfig {
  url?: string;
  method?: HttpMethod;
  baseURL?: string;
  headers?: Record<string, string>;
  params?: any;
  data?: any;
  timeout?: number;
  withCredentials?: boolean;
  auth?: AuthCredentials;
  responseType?: ResponseType;
  signal?: AbortSignal;
  onUploadProgress?: (progressEvent: ProgressEvent) => void;
  onDownloadProgress?: (progressEvent: ProgressEvent) => void;
  transformRequest?: (data: any, headers: Record<string, string>) => any;
  transformResponse?: (data: any) => any;
  validateStatus?: (status: number) => boolean;
}

export interface UploadConfig extends RequestConfig {
  onProgress?: (progress: UploadProgress) => void;
  chunkSize?: number;
  resumable?: boolean;
}

export interface DownloadConfig extends RequestConfig {
  onProgress?: (progress: DownloadProgress) => void;
  filename?: string;
}

export interface BatchRequest {
  id?: string;
  url: string;
  method?: HttpMethod;
  data?: any;
  headers?: Record<string, string>;
  params?: any;
}

export interface BatchRequestResult {
  id?: string;
  success: boolean;
  data?: any;
  error?: Error;
  status?: number;
  headers?: Record<string, string>;
}

export interface BatchError {
  index: number;
  request: BatchRequest;
  error: Error;
}

export interface UploadFile {
  id: string;
  file: File;
  status: UploadStatus;
  progress: number;
  error?: Error;
  result?: any;
  url?: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  rate: number;
  estimated: number;
}

export interface UploadResult {
  id: string;
  success: boolean;
  data?: any;
  error?: Error;
  url?: string;
}

export interface UploadError {
  id: string;
  file: File;
  error: Error;
}

export interface DownloadProgress {
  loaded: number;
  total: number;
  percentage: number;
  rate: number;
  estimated: number;
}

export interface CacheSerializer<T> {
  serialize: (value: T) => string;
  deserialize: (value: string) => T;
}

export interface ApiState {
  data?: any;
  error?: Error;
  loading: boolean;
  success: boolean;
  timestamp?: number;
}

export interface Interceptor {
  id: string;
  type: 'request' | 'response';
  handler: (value: any) => any | Promise<any>;
  errorHandler?: (error: any) => any | Promise<any>;
}

export interface AuthCredentials {
  username?: string;
  password?: string;
  token?: string;
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS';
export type ResponseType = 'arraybuffer' | 'blob' | 'document' | 'json' | 'text' | 'stream';
export type ConnectionState = 'connecting' | 'connected' | 'disconnecting' | 'disconnected' | 'reconnecting' | 'error';
export type UploadStatus = 'pending' | 'uploading' | 'paused' | 'completed' | 'failed' | 'cancelled';
export type ValidationResult = { valid: boolean; errors?: string[] };
