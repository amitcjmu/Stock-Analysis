/**
 * API client utilities module for HTTP client configuration and error handling.
 * Provides consistent API patterns and request/response handling.
 */

export * from './httpClient';
// export * from './apiConfig'; // File doesn't exist
export * from './errorHandling';
// export * from './requestInterceptors'; // File doesn't exist
// export * from './responseInterceptors'; // File doesn't exist
export * from './multiTenantHeaders';
export * from './retryPolicies';
export * from './cacheStrategies';
export * from './apiTypes';

// Re-export commonly used functions
export {
  createApiClient,
  configureApiClient,
  setDefaultHeaders,
  setMultiTenantHeaders,
  retryRequest,
  clearApiCache
} from './httpClient';

// Export handleApiError from errorHandling
export { handleApiError } from './errorHandling';

export type {
  ApiClientConfig,
  ApiResponse,
  ApiError,
  RequestConfig,
  RetryConfig,
  CacheConfig,
  MultiTenantContext
} from './apiTypes';