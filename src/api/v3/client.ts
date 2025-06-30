/**
 * Base API Client for v3
 * Core client class with interceptors and configuration
 */

import type {
  ApiClientConfig,
  RequestConfig,
  RequestContext,
  StreamResponse,
  FileUploadConfig,
  FileUploadProgress
} from './types/common';

import {
  buildHeaders,
  buildRequestOptions,
  getAuthToken,
  getRequestContext,
  validateApiConfig,
  normalizeBaseUrl,
  buildFullUrl,
  mergeRequestConfig
} from './utils/requestConfig';

import { buildQueryString, buildFormData } from './utils/queryBuilder';
import { createAuthInterceptor } from './interceptors/auth';
import { createRetryInterceptor } from './interceptors/retry';
import { createLoggingInterceptor } from './interceptors/logging';
import { createErrorInterceptor, handleFetchError } from './interceptors/error';
import { ApiError, NetworkError, TimeoutError } from './types/responses';

/**
 * Base API Client class
 */
export class ApiClient {
  private readonly config: Required<ApiClientConfig>;
  private readonly authInterceptor: ReturnType<typeof createAuthInterceptor>;
  private readonly retryInterceptor: ReturnType<typeof createRetryInterceptor>;
  private readonly loggingInterceptor: ReturnType<typeof createLoggingInterceptor>;
  private readonly errorInterceptor: ReturnType<typeof createErrorInterceptor>;

  constructor(config: ApiClientConfig) {
    // Validate and normalize configuration
    validateApiConfig(config);
    
    this.config = {
      baseURL: normalizeBaseUrl(config.baseURL),
      timeout: config.timeout ?? 30000,
      retryAttempts: config.retryAttempts ?? 3,
      retryDelay: config.retryDelay ?? 1000,
      enableLogging: config.enableLogging ?? (process.env.NODE_ENV === 'development'),
      authToken: config.authToken ?? getAuthToken() ?? undefined,
      defaultHeaders: {
        'Content-Type': 'application/json',
        'X-API-Version': 'v3',
        ...config.defaultHeaders
      }
    };

    // Initialize interceptors
    this.authInterceptor = createAuthInterceptor({
      onTokenExpired: () => {
        console.warn('Auth token expired');
        // Could trigger token refresh or redirect to login
      }
    });

    this.retryInterceptor = createRetryInterceptor({
      maxAttempts: this.config.retryAttempts,
      baseDelay: this.config.retryDelay
    });

    this.loggingInterceptor = createLoggingInterceptor({
      enabled: this.config.enableLogging
    });

    this.errorInterceptor = createErrorInterceptor({
      logErrors: this.config.enableLogging
    });
  }

  /**
   * Generic request method
   */
  private async request<T>(
    method: string,
    endpoint: string,
    requestConfig: RequestConfig = {},
    body?: any,
    customHeaders: Record<string, string> = {}
  ): Promise<T> {
    const config = mergeRequestConfig(requestConfig);
    const context = getRequestContext();
    const url = buildFullUrl(this.config.baseURL, endpoint);

    // Build request
    const requestOptions = buildRequestOptions(
      method,
      config,
      context,
      this.config.authToken,
      body,
      { ...this.config.defaultHeaders, ...customHeaders }
    );

    let request = new Request(url, requestOptions);

    // Apply request interceptors
    request = this.authInterceptor.request(request);
    
    if (this.config.enableLogging) {
      this.loggingInterceptor.request(request);
    }

    // Execute request with retry logic
    const fetchWithRetry = () => fetch(request);
    
    try {
      const response = await this.retryInterceptor(fetchWithRetry, request);

      // Apply response interceptors
      const processedResponse = await this.errorInterceptor(response, request);
      
      if (this.config.enableLogging) {
        await this.loggingInterceptor.response(processedResponse, request);
      }

      // Apply auth response interceptor
      this.authInterceptor.response(processedResponse);

      // Parse response
      return await this.parseResponse<T>(processedResponse);

    } catch (error) {
      // Handle fetch errors
      const handledError = handleFetchError(error, request);
      
      if (this.config.enableLogging) {
        this.loggingInterceptor.error(handledError, request);
      }

      throw handledError;
    }
  }

  /**
   * Parse response based on content type
   */
  private async parseResponse<T>(response: Response): Promise<T> {
    if (response.status === 204) {
      return undefined as T; // No content
    }

    const contentType = response.headers.get('content-type');
    
    if (contentType?.includes('application/json')) {
      return await response.json();
    }
    
    if (contentType?.includes('text/')) {
      return await response.text() as T;
    }
    
    // Return response as-is for other content types
    return response as T;
  }

  /**
   * GET request
   */
  async get<T>(
    endpoint: string,
    params?: Record<string, any>,
    config: RequestConfig = {}
  ): Promise<T> {
    const url = params ? `${endpoint}${buildQueryString(params)}` : endpoint;
    return this.request<T>('GET', url, config);
  }

  /**
   * POST request
   */
  async post<T>(
    endpoint: string,
    body?: any,
    config: RequestConfig = {}
  ): Promise<T> {
    return this.request<T>('POST', endpoint, config, body);
  }

  /**
   * PUT request
   */
  async put<T>(
    endpoint: string,
    body?: any,
    config: RequestConfig = {}
  ): Promise<T> {
    return this.request<T>('PUT', endpoint, config, body);
  }

  /**
   * PATCH request
   */
  async patch<T>(
    endpoint: string,
    body?: any,
    config: RequestConfig = {}
  ): Promise<T> {
    return this.request<T>('PATCH', endpoint, config, body);
  }

  /**
   * DELETE request
   */
  async delete<T>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<T> {
    return this.request<T>('DELETE', endpoint, config);
  }

  /**
   * Upload file with progress tracking
   */
  async upload<T>(
    endpoint: string,
    file: File,
    additionalData: Record<string, any> = {},
    uploadConfig: FileUploadConfig = {}
  ): Promise<T> {
    const formData = buildFormData({
      file,
      ...additionalData
    });

    // Create custom headers (don't set Content-Type for FormData)
    const customHeaders: Record<string, string> = {};
    if (this.config.authToken) {
      customHeaders['Authorization'] = `Bearer ${this.config.authToken}`;
    }

    // Build request configuration
    const config: RequestConfig = {
      includeAuth: false, // We're manually adding auth header
      timeout: uploadConfig.timeout || 120000, // 2 minutes for uploads
      retryAttempts: 1 // Fewer retries for uploads
    };

    // Create XMLHttpRequest for progress tracking if callback is provided
    if (uploadConfig.onProgress) {
      return this.uploadWithProgress<T>(endpoint, formData, customHeaders, uploadConfig);
    }

    // Use regular fetch for uploads without progress tracking
    return this.request<T>('POST', endpoint, config, formData, customHeaders);
  }

  /**
   * Upload with progress tracking using XMLHttpRequest
   */
  private uploadWithProgress<T>(
    endpoint: string,
    formData: FormData,
    headers: Record<string, string>,
    config: FileUploadConfig
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const url = buildFullUrl(this.config.baseURL, endpoint);

      // Set up progress tracking
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && config.onProgress) {
          const progress: FileUploadProgress = {
            loaded: event.loaded,
            total: event.total,
            percentage: Math.round((event.loaded / event.total) * 100)
          };
          config.onProgress(progress);
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            if (config.onComplete) {
              config.onComplete(response);
            }
            resolve(response);
          } catch (error) {
            reject(new Error('Failed to parse upload response'));
          }
        } else {
          const error = new ApiError(
            xhr.status,
            'UPLOAD_FAILED',
            xhr.statusText || `Upload failed with status ${xhr.status}`
          );
          if (config.onError) {
            config.onError(error);
          }
          reject(error);
        }
      });

      // Handle errors
      xhr.addEventListener('error', () => {
        const error = new NetworkError('Upload failed due to network error');
        if (config.onError) {
          config.onError(error);
        }
        reject(error);
      });

      // Handle timeout
      xhr.addEventListener('timeout', () => {
        const error = new TimeoutError(config.timeout || 120000, 'Upload timed out');
        if (config.onError) {
          config.onError(error);
        }
        reject(error);
      });

      // Configure request
      xhr.open('POST', url);
      
      // Set headers
      Object.entries(headers).forEach(([key, value]) => {
        xhr.setRequestHeader(key, value);
      });

      // Set timeout
      if (config.timeout) {
        xhr.timeout = config.timeout;
      }

      // Send request
      xhr.send(formData);
    });
  }

  /**
   * Create Server-Sent Events connection
   */
  createEventSource(
    endpoint: string,
    params?: Record<string, any>
  ): StreamResponse {
    const url = params ? 
      buildFullUrl(this.config.baseURL, `${endpoint}${buildQueryString(params)}`) :
      buildFullUrl(this.config.baseURL, endpoint);

    const eventSource = new EventSource(url);
    
    const streamResponse: StreamResponse = {
      eventSource,
      close: () => eventSource.close(),
      onMessage: (callback) => {
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            callback(data);
          } catch (error) {
            console.error('Failed to parse SSE data:', error);
          }
        };
      },
      onError: (callback) => {
        eventSource.onerror = callback;
      },
      onClose: (callback) => {
        eventSource.addEventListener('close', callback);
      }
    };

    return streamResponse;
  }

  /**
   * Update auth token
   */
  setAuthToken(token: string): void {
    (this.config as any).authToken = token;
  }

  /**
   * Get current configuration
   */
  getConfig(): Readonly<Required<ApiClientConfig>> {
    return this.config;
  }

  /**
   * Create a new client instance with different configuration
   */
  withConfig(config: Partial<ApiClientConfig>): ApiClient {
    return new ApiClient({
      ...this.config,
      ...config
    });
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.get('/health');
  }
}