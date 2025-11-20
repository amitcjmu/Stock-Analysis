/**
 * Simplified API Client - Redis Cache Migration
 *
 * This client removes custom caching and relies on backend Redis caching
 * while maintaining request deduplication for optimal performance.
 *
 * CC Generated API Client for AI Force Migration Platform
 */

import { isCacheFeatureEnabled } from '@/constants/features';
import { tokenStorage } from '@/contexts/AuthContext/storage';

// Auth utilities
interface AuthHeaders {
  Authorization?: string;
  'X-User-ID'?: string;
  'X-Client-Account-ID'?: string;
  'X-Engagement-ID'?: string;
  'X-Flow-ID'?: string;
}

const getAuthHeaders = (): AuthHeaders => {
  const headers: AuthHeaders = {};

  try {
    const token = tokenStorage.getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    } else {
      // CRITICAL: Log when token is missing to debug timing issues (dev only)
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ [apiClient] getAuthHeaders: No token available from tokenStorage');
      }
    }

    const user = tokenStorage.getUser();
    if (user?.id) {
      headers['X-User-ID'] = user.id;
    }

    const clientId = localStorage.getItem('auth_client');
    if (clientId && clientId !== 'null') {
      const client = JSON.parse(clientId);
      if (client?.id) {
        headers['X-Client-Account-ID'] = client.id;
      }
    }

    const engagementId = localStorage.getItem('auth_engagement');
    if (engagementId && engagementId !== 'null') {
      const engagement = JSON.parse(engagementId);
      if (engagement?.id) {
        headers['X-Engagement-ID'] = engagement.id;
      }
    }

    const flowId = localStorage.getItem('auth_flow');
    if (flowId && flowId !== 'null') {
      const flow = JSON.parse(flowId);
      if (flow?.id) {
        headers['X-Flow-ID'] = flow.id;
      }
    }
  } catch (error) {
    // Make token retrieval failures visible instead of silent (dev only)
    if (process.env.NODE_ENV === 'development') {
      console.error('❌ [apiClient] getAuthHeaders: Failed to retrieve auth headers:', error);
    }
    // Re-throw to make failures visible
    throw error;
  }

  return headers;
};

// API Error class
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public response?: any,
    public requestId?: string
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
  }
}

// Request options interface
export interface RequestOptions extends Omit<RequestInit, 'body'> {
  timeout?: number;
  body?: any;
}

// Base URL configuration
const getBaseUrl = (): string => {
  // Force proxy usage for development - Docker container on port 8081
  if (typeof window !== 'undefined' && window.location.port === '8081') {
    return '';
  }

  // Priority 1: Explicit VITE_BACKEND_URL (for production deployments)
  if (import.meta.env.VITE_BACKEND_URL) {
    return import.meta.env.VITE_BACKEND_URL;
  }

  // Priority 2: Legacy VITE_API_BASE_URL
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  // Priority 3: Check if we're in production mode with Vercel
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname.includes('.vercel.app')) {
      console.warn('Production deployment detected. Ensure VITE_BACKEND_URL is set to your Railway backend URL.');
      return window.location.origin;
    }
  }

  // Priority 4: Development mode - use empty string to utilize Vite proxy
  if (import.meta.env.DEV || import.meta.env.MODE === 'development') {
    return '';  // Empty string means use same origin with proxy
  }

  // Final fallback
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return '';
    }
    return window.location.origin;
  }

  return '';
};

/**
 * Simplified API Client with request deduplication only
 */
class ApiClient {
  private pendingRequests = new Map<string, Promise<any>>();
  private baseUrl: string;

  constructor() {
    this.baseUrl = getBaseUrl();
  }

  /**
   * GET request with deduplication
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const requestKey = `GET:${endpoint}`;

    // Request deduplication only (no caching)
    if (this.pendingRequests.has(requestKey)) {
      return this.pendingRequests.get(requestKey);
    }

    const request = this.executeRequest<T>(endpoint, {
      ...options,
      method: 'GET'
    }).finally(() => {
      this.pendingRequests.delete(requestKey);
    });

    this.pendingRequests.set(requestKey, request);
    return request;
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.executeRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.executeRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data
    });
  }

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.executeRequest<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.executeRequest<T>(endpoint, {
      ...options,
      method: 'DELETE'
    });
  }

  /**
   * Execute HTTP request
   */
  private async executeRequest<T>(
    endpoint: string,
    options: RequestInit & { timeout?: number; body?: any }
  ): Promise<T> {
    const requestId = Math.random().toString(36).substring(2, 8);
    const startTime = performance.now();

    // Normalize endpoint
    let normalizedEndpoint: string;
    if (endpoint.startsWith('/api/v1') || endpoint.startsWith('/api/v2')) {
      normalizedEndpoint = endpoint;
    } else {
      normalizedEndpoint = `/api/v1${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    }

    // CRITICAL FIX: Always use relative URLs when running on port 8081 (Docker development)
    // This prevents the browser from trying to access http://backend:8000 directly
    let url: string;
    if (typeof window !== 'undefined' && window.location.port === '8081') {
      // Force relative URL for Docker development
      url = normalizedEndpoint;
    } else {
      url = `${this.baseUrl}${normalizedEndpoint}`;
    }

    // CRITICAL FIX FOR ISSUE #306: Enforce Flow ID for all discovery endpoints
    // Check if this is a discovery endpoint that requires Flow ID
    const isDiscoveryEndpoint = (normalizedEndpoint.startsWith('/api/v1/unified-discovery/') ||
                                normalizedEndpoint.startsWith('/api/v1/discovery/')) &&
                                // Exempt endpoints that don't require Flow ID
                                !normalizedEndpoint.includes('/overview') &&
                                !normalizedEndpoint.includes('/flows') &&
                                !normalizedEndpoint.includes('/flow/create') &&
                                !normalizedEndpoint.includes('/flow/health') &&
                                !normalizedEndpoint.includes('/flow/status');

    if (isDiscoveryEndpoint) {
      // Merge auth headers with caller's headers to check for Flow ID
      const authHeaders = getAuthHeaders();
      const callerHeaders = (options.headers || {}) as Record<string, string>;
      const combinedHeaders = { ...authHeaders, ...callerHeaders };

      // Also check for flow_id in URL query parameters (for current_flow mode)
      const urlObj = new URL(url, window.location.origin);
      const queryFlowId = urlObj.searchParams.get('flow_id');

      // Only require Flow ID if this appears to be a flow-specific request
      // If no flow_id parameter is present, assume it's an "All Assets" type request
      const hasFlowIdInQuery = urlObj.searchParams.has('flow_id');
      const hasFlowIdInHeaders = !!combinedHeaders['X-Flow-ID'];

      // CRITICAL: Only enforce flow_id requirement for endpoints that explicitly request it
      // "All Assets" mode should work without flow_id, "Current Flow Only" mode should have flow_id
      if (hasFlowIdInQuery && !queryFlowId) {
        // Case: Request has flow_id parameter but it's empty/null
        console.warn(`🚫 Blocking discovery request with empty Flow ID: ${normalizedEndpoint}`);
        throw new ApiError(400, 'Flow ID required for discovery operations. Please ensure a discovery flow is selected.', {
          code: 'FLOW_ID_REQUIRED',
          endpoint: normalizedEndpoint,
          message: 'Discovery operations require an active discovery flow context'
        }, requestId);
      }

      // Log the flow context for debugging
      if (queryFlowId) {
        console.log(`✅ Discovery request allowed with flow_id query parameter: ${queryFlowId.substring(0, 8)}...`);
      } else if (combinedHeaders['X-Flow-ID']) {
        console.log(`✅ Discovery request allowed with X-Flow-ID header: ${combinedHeaders['X-Flow-ID'].substring(0, 8)}...`);
      } else {
        console.log(`✅ Discovery request allowed without flow_id (All Assets mode): ${normalizedEndpoint}`);
      }
      // Remove sensitive logging - just use debug if needed
      // console.debug('Discovery request allowed with Flow context');
    }

    const method = (options.method || 'GET').toUpperCase();

    try {
      // API Request logged

      // Prepare headers
      const authHeaders = getAuthHeaders();
      const headers: HeadersInit = {
        'X-Request-ID': requestId,
        ...authHeaders,
        ...options.headers,
      };

      // Add debug logging to track authorization header (dev only)
      if (!authHeaders.Authorization && process.env.NODE_ENV === 'development') {
        console.warn(`⚠️ [apiClient] Request [${requestId}] being sent WITHOUT Authorization header:`, {
          method,
          url: normalizedEndpoint,
          hasToken: !!tokenStorage.getToken()
        });
      }

      // Only set default Content-Type for non-FormData requests
      if (!(options.body instanceof FormData) && method !== 'GET') {
        headers['Content-Type'] = 'application/json';
      }

      // Prepare body
      let body: string | FormData | undefined;

      if (options.body !== undefined) {
        if (options.body instanceof FormData) {
          body = options.body;
        } else if (typeof options.body === 'string') {
          body = options.body;
        } else {
          body = JSON.stringify(options.body);
        }
      }

      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutMs = options.timeout || 120000; // Default 2 minutes (increased for agent processing)

      const timeoutId = setTimeout(() => {
        controller.abort();
      }, timeoutMs);

      // Make the request
      const response = await fetch(url, {
        ...options,
        method,
        headers,
        body,
        credentials: 'include',
        signal: controller.signal,
        // Honor backend cache headers if feature is enabled
        cache: isCacheFeatureEnabled('ENABLE_CACHE_HEADERS') ? 'default' : 'no-store',
      }).finally(() => {
        clearTimeout(timeoutId);
      });

      const endTime = performance.now();
      const duration = (endTime - startTime).toFixed(2);

      // Parse response
      let data: T;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text() as T;
      }

      // API Response logged

      if (!response.ok) {
        throw new ApiError(response.status, response.statusText, data, requestId);
      }

      return data;

    } catch (error) {
      const endTime = performance.now();
      const duration = (endTime - startTime).toFixed(2);

      if (error.name === 'AbortError') {
        console.error(`⏱️ API Timeout [${requestId}] after ${duration}ms`);
        throw new ApiError(408, 'Request Timeout', undefined, requestId);
      }

      if (error instanceof ApiError) {
        console.error(`❌ API Error [${requestId}] ${error.status} (${duration}ms):`, error.message);

        // Handle auth errors
        if (error.status === 401) {
          console.warn('🔐 Token expired, clearing auth data');
          tokenStorage.removeToken();
          tokenStorage.removeUser();
          localStorage.removeItem('auth_client');
          localStorage.removeItem('auth_engagement');
          localStorage.removeItem('auth_flow');
          sessionStorage.removeItem('auth_initialization_complete');

          // Redirect to login if in browser
          if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }

        throw error;
      }

      console.error(`❌ API Request Failed [${requestId}] (${duration}ms):`, error);
      throw new ApiError(500, 'Network Error', error, requestId);
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export the auth headers function
export { getAuthHeaders };

// Export backward compatibility function
export const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const method = (options.method || 'GET').toUpperCase();

  switch (method) {
    case 'GET':
      return apiClient.get(endpoint, options);
    case 'POST':
      return apiClient.post(endpoint, options.body, options);
    case 'PUT':
      return apiClient.put(endpoint, options.body, options);
    case 'PATCH':
      return apiClient.patch(endpoint, options.body, options);
    case 'DELETE':
      return apiClient.delete(endpoint, options);
    default:
      return apiClient.get(endpoint, options);
  }
};

export default apiClient;
