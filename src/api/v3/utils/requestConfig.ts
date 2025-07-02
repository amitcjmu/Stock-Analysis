/**
 * Request Configuration Utilities for API v3
 * Helper functions for configuring API requests
 */

import type { RequestConfig, RequestContext, ApiClientConfig } from '../types/common';

/**
 * Default request configuration
 */
export const DEFAULT_REQUEST_CONFIG: Required<RequestConfig> = {
  includeAuth: true,
  includeContext: true,
  timeout: 30000,
  retryAttempts: 3,
  cache: false
};

/**
 * Default API client configuration
 */
export const DEFAULT_API_CONFIG: Partial<ApiClientConfig> = {
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  enableLogging: process.env.NODE_ENV === 'development',
  defaultHeaders: {
    'Content-Type': 'application/json',
    'X-API-Version': 'v3'
  }
};

/**
 * Merge request config with defaults
 */
export function mergeRequestConfig(config: RequestConfig = {}): Required<RequestConfig> {
  return {
    ...DEFAULT_REQUEST_CONFIG,
    ...config
  };
}

/**
 * Build headers for API requests
 */
export function buildHeaders(
  config: Required<RequestConfig>,
  context?: RequestContext,
  authToken?: string,
  customHeaders: Record<string, string> = {}
): HeadersInit {
  const headers: Record<string, string> = {
    ...DEFAULT_API_CONFIG.defaultHeaders,
    ...customHeaders
  };

  // Add request ID for tracing
  headers['X-Request-ID'] = generateRequestId();

  // Add authentication header
  if (config.includeAuth && authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  // Add context headers
  if (config.includeContext && context) {
    if (context.client_account_id) {
      headers['X-Client-Account-ID'] = context.client_account_id;
    }
    if (context.engagement_id) {
      headers['X-Engagement-ID'] = context.engagement_id;
    }
    if (context.user_id) {
      headers['X-User-ID'] = context.user_id;
    }
    if (context.flow_id) {
      headers['X-Flow-ID'] = context.flow_id;
    }
  }

  return headers;
}

/**
 * Generate unique request ID
 */
export function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * Build request options for fetch
 */
export function buildRequestOptions(
  method: string,
  config: Required<RequestConfig>,
  context?: RequestContext,
  authToken?: string,
  body?: any,
  customHeaders: Record<string, string> = {}
): RequestInit {
  const headers = buildHeaders(config, context, authToken, customHeaders);

  const options: RequestInit = {
    method: method.toUpperCase(),
    headers,
    credentials: 'include'
  };

  // Add body if provided and method supports it
  if (body && !['GET', 'HEAD'].includes(method.toUpperCase())) {
    if (body instanceof FormData) {
      // Don't set Content-Type for FormData - browser will set it with boundary
      delete (headers as any)['Content-Type'];
      options.body = body;
    } else if (typeof body === 'object') {
      options.body = JSON.stringify(body);
    } else {
      options.body = body;
    }
  }

  // Add timeout using AbortController
  if (config.timeout > 0) {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), config.timeout);
    options.signal = controller.signal;
  }

  return options;
}

/**
 * Get auth token from storage
 */
export function getAuthToken(): string | null {
  try {
    return localStorage.getItem('auth_token');
  } catch (error) {
    console.warn('Failed to get auth token from localStorage:', error);
    return null;
  }
}

/**
 * Set auth token in storage
 */
export function setAuthToken(token: string): void {
  try {
    localStorage.setItem('auth_token', token);
  } catch (error) {
    console.warn('Failed to set auth token in localStorage:', error);
  }
}

/**
 * Remove auth token from storage
 */
export function removeAuthToken(): void {
  try {
    localStorage.removeItem('auth_token');
  } catch (error) {
    console.warn('Failed to remove auth token from localStorage:', error);
  }
}

/**
 * Get request context from various sources
 */
export function getRequestContext(): RequestContext {
  const context: RequestContext = {};

  try {
    // Try to get context from localStorage
    const storedContext = localStorage.getItem('app_context');
    if (storedContext) {
      const parsed = JSON.parse(storedContext);
      Object.assign(context, parsed);
    }

    // Try to get context from URL parameters (fallback)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('client_id')) {
      context.client_account_id = urlParams.get('client_id') || undefined;
    }
    if (urlParams.get('engagement_id')) {
      context.engagement_id = urlParams.get('engagement_id') || undefined;
    }
  } catch (error) {
    console.warn('Failed to get request context:', error);
  }

  return context;
}

/**
 * Set request context
 */
export function setRequestContext(context: RequestContext): void {
  try {
    localStorage.setItem('app_context', JSON.stringify(context));
  } catch (error) {
    console.warn('Failed to set request context:', error);
  }
}

/**
 * Check if request should be retried
 */
export function shouldRetryRequest(error: any, attempt: number, maxAttempts: number): boolean {
  if (attempt >= maxAttempts) {
    return false;
  }

  // Don't retry on client errors (4xx)
  if (error.status && error.status >= 400 && error.status < 500) {
    return false;
  }

  // Retry on network errors, timeouts, and server errors (5xx)
  return (
    !error.status || // Network error
    error.status >= 500 || // Server error
    error.name === 'AbortError' || // Timeout
    error.name === 'TimeoutError'
  );
}

/**
 * Calculate retry delay with exponential backoff
 */
export function calculateRetryDelay(attempt: number, baseDelay: number = 1000): number {
  const exponentialDelay = baseDelay * Math.pow(2, attempt - 1);
  const jitter = Math.random() * 1000; // Add up to 1 second of jitter
  return Math.min(exponentialDelay + jitter, 30000); // Cap at 30 seconds
}

/**
 * Validate API client configuration
 */
export function validateApiConfig(config: ApiClientConfig): void {
  if (!config.baseURL) {
    throw new Error('API base URL is required');
  }

  if (!config.baseURL.startsWith('http://') && !config.baseURL.startsWith('https://')) {
    throw new Error('API base URL must start with http:// or https://');
  }

  if (config.timeout && (config.timeout < 1000 || config.timeout > 300000)) {
    throw new Error('Timeout must be between 1000ms and 300000ms');
  }

  if (config.retryAttempts && (config.retryAttempts < 0 || config.retryAttempts > 10)) {
    throw new Error('Retry attempts must be between 0 and 10');
  }

  if (config.retryDelay && (config.retryDelay < 100 || config.retryDelay > 10000)) {
    throw new Error('Retry delay must be between 100ms and 10000ms');
  }
}

/**
 * Normalize base URL
 */
export function normalizeBaseUrl(baseUrl: string): string {
  // Remove trailing slash
  let normalized = baseUrl.replace(/\/+$/, '');
  
  // Ensure it has a protocol
  if (!normalized.startsWith('http://') && !normalized.startsWith('https://')) {
    normalized = `https://${normalized}`;
  }
  
  return normalized;
}

/**
 * Build full URL from base URL and endpoint
 */
export function buildFullUrl(baseUrl: string, endpoint: string): string {
  const normalizedBase = normalizeBaseUrl(baseUrl);
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  return `${normalizedBase}${normalizedEndpoint}`;
}