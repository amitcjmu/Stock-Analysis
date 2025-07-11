/**
 * API client utilities module for HTTP client configuration and error handling.
 * Provides consistent API patterns and request/response handling.
 */

export * from './httpClient';
export * from './apiConfig';
export * from './errorHandling';
export * from './requestInterceptors';
export * from './responseInterceptors';
export * from './multiTenantHeaders';
export * from './retryPolicies';
export * from './cacheStrategies';
export * from './apiTypes';

// Re-export commonly used functions
export {
  createApiClient,
  configureApiClient,
  handleApiError,
  setDefaultHeaders,
  setMultiTenantHeaders,
  retryRequest,
  clearApiCache
} from './httpClient';

export type {
  ApiClientConfig,
  ApiResponse,
  ApiError,
  RequestConfig,
  RetryConfig,
  CacheConfig,
  MultiTenantContext
} from './apiTypes';