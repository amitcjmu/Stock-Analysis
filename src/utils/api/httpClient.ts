/**
 * HTTP client implementation with comprehensive error handling and features.
 * Provides a robust API client with retry, caching, and multi-tenant support.
 */

import type {
  ApiClient,
  ApiClientConfig,
  ApiResponse,
  ApiErrorType,
  RequestConfig,
  MultiTenantContext,
  MultiTenantHeaders,
  UploadConfig,
  UploadProgress,
  BatchRequest,
  BatchResponse,
  PollingConfig,
  HealthCheckResult,
  ApiMetrics,
  RequestInterceptor,
  ResponseInterceptor,
  QueryParams
} from './apiTypes';
import type { handleApiError, createApiError } from './errorHandling';
import { applyRetryPolicy } from './retryPolicies';
import { CacheManager } from './cacheStrategies';
import { createMultiTenantHeaders } from './multiTenantHeaders';

// Get base URL with proper Docker development handling
const getDefaultBaseUrl = (): string => {
  // Force proxy usage for development - Docker container on port 8081
  if (typeof window !== 'undefined' && window.location.port === '8081') {
    return '';
  }

  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

// Default configuration
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: getDefaultBaseUrl(),
  timeout: 30000,
  retries: 3,
  retryDelay: 1000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  enableLogging: process.env.NODE_ENV === 'development',
  enableCache: true,
  cachePrefix: 'api_cache_',
  defaultCacheTtl: 5 * 60 * 1000 // 5 minutes
};

class HttpClient implements ApiClient {
  private config: ApiClientConfig;
  private cache: CacheManager;
  private multiTenantContext?: MultiTenantContext;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private metrics: ApiMetrics = {
    requestCount: 0,
    errorCount: 0,
    averageLatency: 0,
    errorRate: 0,
    successRate: 0,
    cacheHitRate: 0,
    lastUpdated: new Date().toISOString()
  };

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.cache = new CacheManager({
      keyPrefix: this.config.cachePrefix,
      defaultTtl: this.config.defaultCacheTtl
    });

    // Add default interceptors
    this.addDefaultInterceptors();
  }

  private addDefaultInterceptors(): unknown {
    // Request logging interceptor
    if (this.config.enableLogging) {
      this.addRequestInterceptor({
        name: 'logging',
        priority: 1000,
        onRequest: (config) => {
          console.log(`[API] ${config.method || 'GET'} ${config.url || ''}`, config);
          return config;
        }
      });
    }

    // Multi-tenant headers interceptor
    this.addRequestInterceptor({
      name: 'multiTenant',
      priority: 900,
      onRequest: (config) => {
        if (this.multiTenantContext) {
          const tenantHeaders = createMultiTenantHeaders(this.multiTenantContext);
          config.headers = { ...config.headers, ...tenantHeaders };
        }
        return config;
      }
    });

    // Response logging interceptor
    if (this.config.enableLogging) {
      this.addResponseInterceptor({
        name: 'logging',
        priority: 1000,
        onResponse: (response) => {
          console.log('[API] Response:', response);
          return response;
        },
        onError: (error) => {
          console.error('[API] Error:', error);
          return error;
        }
      });
    }
  }

  private async executeRequest<T>(
    method: string,
    url: string,
    data?: unknown,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const startTime = Date.now();
    const fullUrl = this.buildUrl(url);

    // Apply request interceptors
    let requestConfig: RequestConfig = {
      method: method as 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
      url: fullUrl,
      data,
      headers: { ...this.config.headers, ...config.headers },
      timeout: config.timeout || this.config.timeout,
      ...config
    };

    for (const interceptor of this.getSortedInterceptors(this.requestInterceptors)) {
      try {
        requestConfig = await interceptor.onRequest(requestConfig);
      } catch (error) {
        if (interceptor.onError) {
          await interceptor.onError(error);
        }
      }
    }

    // Check cache for GET requests
    if (method === 'GET' && this.config.enableCache && config.cache !== false) {
      const cacheKey = this.buildCacheKey(fullUrl, config.params);
      const cached = await this.cache.get(cacheKey) as ApiResponse<T> | null;
      if (cached) {
        this.updateMetrics(Date.now() - startTime, true, true);
        return cached;
      }
    }

    try {
      // Make the actual request
      const response = await this.makeRequest<T>(requestConfig);

      // Apply response interceptors
      let processedResponse = response;
      for (const interceptor of this.getSortedInterceptors(this.responseInterceptors)) {
        try {
          processedResponse = await interceptor.onResponse(processedResponse) as ApiResponse<T>;
        } catch (error) {
          if (interceptor.onError) {
            await interceptor.onError(error as ApiErrorType);
          }
        }
      }

      // Cache successful GET responses
      if (method === 'GET' && this.config.enableCache && config.cache !== false) {
        const cacheKey = this.buildCacheKey(fullUrl, config.params);
        const ttl = config.cacheTtl || this.config.defaultCacheTtl;
        await this.cache.set(cacheKey, processedResponse, ttl);
      }

      this.updateMetrics(Date.now() - startTime, true, false);
      return processedResponse;

    } catch (error) {
      this.updateMetrics(Date.now() - startTime, false, false);

      // Apply error interceptors
      let processedError = error;
      for (const interceptor of this.getSortedInterceptors(this.responseInterceptors)) {
        if (interceptor.onError) {
          try {
            processedError = await interceptor.onError(processedError);
          } catch (interceptorError) {
            // Log interceptor error but continue
            console.error('Response interceptor error:', interceptorError);
          }
        }
      }

      throw processedError;
    }
  }

  private async makeRequest<T>(config: RequestConfig): Promise<ApiResponse<T>> {
    const { method = 'GET', url, data, headers, timeout, params } = config;

    if (!url) {
      throw new Error('URL is required for request');
    }

    // Build query string for GET requests
    const queryString = params ? this.buildQueryString(params) : '';
    const fullUrl = queryString ? `${url}?${queryString}` : url;

    const requestInit: RequestInit = {
      method,
      headers: new Headers(headers),
      signal: timeout ? AbortSignal.timeout(timeout) : undefined,
    };

    if (data && method !== 'GET') {
      if (data instanceof FormData) {
        requestInit.body = data;
        // Remove Content-Type header for FormData (browser will set it with boundary)
        (requestInit.headers as Headers).delete('Content-Type');
      } else {
        requestInit.body = JSON.stringify(data);
      }
    }

    const response = await fetch(fullUrl, requestInit);

    // Handle different response types
    let responseData: unknown;
    const contentType = response.headers.get('Content-Type');

    if (contentType?.includes('application/json')) {
      responseData = await response.json();
    } else if (contentType?.includes('text/')) {
      responseData = await response.text();
    } else {
      responseData = await response.blob();
    }

    // Handle non-2xx responses
    if (!response.ok) {
      const error = createApiError(response.status, responseData, {
        url: fullUrl,
        method,
        response: responseData
      });
      throw error;
    }

    // Transform response data to match SharedApiResponse structure
    return {
      data: responseData as T,
      success: true,
      meta: {
        timestamp: new Date().toISOString(),
        duration: 0,
        version: '1.0.0'
      }
    } as ApiResponse<T>;
  }

  private buildUrl(url: string): string {
    if (url.startsWith('http')) {
      return url;
    }
    return `${this.config.baseURL}${url.startsWith('/') ? '' : '/'}${url}`;
  }

  private buildQueryString(params: Record<string, unknown>): string {
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, String(v)));
        } else {
          searchParams.append(key, String(value));
        }
      }
    });

    return searchParams.toString();
  }

  private buildCacheKey(url: string, params?: Record<string, unknown>): string {
    const baseKey = url;
    const paramKey = params ? JSON.stringify(params) : '';
    return `${baseKey}${paramKey}`;
  }

  private getSortedInterceptors<T extends { priority: number }>(interceptors: T[]): T[] {
    return [...interceptors].sort((a, b) => b.priority - a.priority);
  }

  private updateMetrics(latency: number, success: boolean, cacheHit: boolean): void {
    this.metrics.requestCount++;

    if (success) {
      // Update average latency
      const totalLatency = this.metrics.averageLatency * (this.metrics.requestCount - 1) + latency;
      this.metrics.averageLatency = totalLatency / this.metrics.requestCount;
    } else {
      this.metrics.errorCount++;
    }

    if (cacheHit) {
      // Update cache hit rate
      const totalRequests = this.metrics.requestCount;
      const cacheHits = this.metrics.cacheHitRate * totalRequests + 1;
      this.metrics.cacheHitRate = cacheHits / totalRequests;
    }

    this.metrics.errorRate = this.metrics.errorCount / this.metrics.requestCount;
    this.metrics.successRate = 1 - this.metrics.errorRate;
    this.metrics.lastUpdated = new Date().toISOString();
  }

  // Public API methods
  async get<T = unknown>(url: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return applyRetryPolicy(
      () => this.executeRequest<T>('GET', url, undefined, config),
      { maxRetries: this.config.retries }
    );
  }

  async post<T = unknown>(url: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return applyRetryPolicy(
      () => this.executeRequest<T>('POST', url, data, config),
      { maxRetries: this.config.retries }
    );
  }

  async put<T = unknown>(url: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return applyRetryPolicy(
      () => this.executeRequest<T>('PUT', url, data, config),
      { maxRetries: this.config.retries }
    );
  }

  async delete<T = unknown>(url: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return applyRetryPolicy(
      () => this.executeRequest<T>('DELETE', url, undefined, config),
      { maxRetries: this.config.retries }
    );
  }

  async patch<T = unknown>(url: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return applyRetryPolicy(
      () => this.executeRequest<T>('PATCH', url, data, config),
      { maxRetries: this.config.retries }
    );
  }

  async upload<T = unknown>(url: string, config: UploadConfig): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append(config.fieldName || 'file', config.file);

    // Add additional data if provided
    if (config.data) {
      Object.entries(config.data).forEach(([key, value]) => {
        formData.append(key, String(value));
      });
    }

    return this.executeRequest<T>('POST', url, formData, {
      ...config,
      headers: {
        ...config.headers,
        // Don't set Content-Type for FormData
      }
    });
  }

  async batch<T = unknown>(requests: BatchRequest[]): Promise<Array<BatchResponse<T>>> {
    const batchPromises = requests.map(async (request) => {
      try {
        const response = await this.executeRequest<T>(
          request.method,
          request.url,
          request.data,
          { headers: request.headers }
        );
        return {
          id: request.id,
          status: 200,
          data: response.data
        } as BatchResponse<T>;
      } catch (error) {
        return {
          id: request.id,
          status: 500,
          data: null as T,
          error: error as ApiErrorType
        } as BatchResponse<T>;
      }
    });

    return Promise.all(batchPromises);
  }

  async poll<T = unknown>(url: string, config: PollingConfig): Promise<ApiResponse<T>> {
    let attempt = 0;

    while (attempt < config.maxAttempts) {
      try {
        const response = await this.get<T>(url);

        if (config.onProgress) {
          config.onProgress(attempt + 1, response);
        }

        if (config.stopCondition(response)) {
          return response;
        }

        attempt++;

        if (attempt < config.maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, config.interval));
        }
      } catch (error) {
        if (attempt === config.maxAttempts - 1) {
          throw error;
        }
        attempt++;
        await new Promise(resolve => setTimeout(resolve, config.interval));
      }
    }

    throw new Error(`Polling failed after ${config.maxAttempts} attempts`);
  }

  async healthCheck(): Promise<HealthCheckResult[]> {
    const healthUrl = '/api/v1/health';
    const startTime = Date.now();

    try {
      const response = await this.get(healthUrl);
      const latency = Date.now() - startTime;

      return [{
        service: 'api',
        status: 'healthy',
        latency,
        timestamp: new Date().toISOString(),
        details: response.data as Record<string, unknown>
      }];
    } catch (error) {
      const latency = Date.now() - startTime;
      return [{
        service: 'api',
        status: 'unhealthy',
        latency,
        timestamp: new Date().toISOString(),
        details: { error: (error as Error).message }
      }];
    }
  }

  getMetrics(): ApiMetrics {
    return { ...this.metrics };
  }

  clearCache(pattern?: string): void {
    this.cache.clear(pattern);
  }

  setDefaultHeaders(headers: Record<string, string>): void {
    this.config.headers = { ...this.config.headers, ...headers };
  }

  setMultiTenantContext(context: MultiTenantContext): void {
    this.multiTenantContext = context;
  }

  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor);
  }

  removeInterceptor(name: string): void {
    this.requestInterceptors = this.requestInterceptors.filter(i => i.name !== name);
    this.responseInterceptors = this.responseInterceptors.filter(i => i.name !== name);
  }
}

// Global client instance
let globalClient: HttpClient | null = null;

export function createApiClient(config?: Partial<ApiClientConfig>): HttpClient {
  return new HttpClient(config);
}

export function configureApiClient(config: Partial<ApiClientConfig>): HttpClient {
  globalClient = new HttpClient(config);
  return globalClient;
}

export function getApiClient(): HttpClient {
  if (!globalClient) {
    globalClient = new HttpClient();
  }
  return globalClient;
}

// Convenience functions
// handleApiError is already exported from errorHandling.ts
export const setDefaultHeaders = (headers: Record<string, string>): void => getApiClient().setDefaultHeaders(headers);
export const setMultiTenantHeaders = (context: MultiTenantContext): void => getApiClient().setMultiTenantContext(context);
export const retryRequest = <T>(fn: () => Promise<T>, retries: number = 3): Promise<T> => applyRetryPolicy(fn, { maxRetries: retries });
export const clearApiCache = (pattern?: string): void => getApiClient().clearCache(pattern);

// Default export
export default HttpClient;
