/**
 * API Client for Master Flow Orchestrator
 * Unified API client with authentication and error handling
 */

import type { ApiResponse, ApiError } from '../types/shared/api-types';
import { tokenStorage } from '../contexts/AuthContext/storage';

export interface ApiClientConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  defaultHeaders: Record<string, string>;
}

export interface RequestConfig {
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
}

/**
 * Custom API error that preserves response body for detailed error handling
 * Issue #719: Needed to propagate backend error details (like apps_not_found) to frontend
 */
export class ApiError extends Error {
  status: number;
  statusText: string;
  response: {
    data: Record<string, unknown>;
    status: number;
    statusText: string;
  };

  constructor(status: number, statusText: string, data: Record<string, unknown>) {
    super(`HTTP ${status}: ${statusText}`);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.response = {
      data,
      status,
      statusText,
    };
  }
}

/**
 * Generic request payload type for external API data
 */
export type RequestPayload =
  | Record<string, unknown>
  | FormData
  | string
  | number
  | boolean
  | null
  | undefined;

export class ApiClient {
  private static instance: ApiClient;
  private config: ApiClientConfig;

  private constructor() {
    // Get backend URL from environment or window location
    const getBackendUrl = (): string => {
      // Use VITE environment variable if available
      if (import.meta.env?.VITE_BACKEND_URL) {
        return import.meta.env.VITE_BACKEND_URL;
      }
      // Fallback to process.env for Next.js compatibility
      if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL;
      }
      // Development mode - use empty string to utilize Vite proxy
      if (import.meta.env?.DEV || import.meta.env?.MODE === 'development') {
        return '';
      }
      // Default fallback
      return '';
    };

    const baseUrl = getBackendUrl();
    console.log('🔧 ApiClient initialized with baseURL:', `${baseUrl}/api/v1`);

    this.config = {
      baseURL: `${baseUrl}/api/v1`,
      timeout: 30000,
      retries: 0,  // CC FIX: Remove retries to prevent duplicate backend executions
      defaultHeaders: {
        'Content-Type': 'application/json',
      }
    };
  }

  public static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: RequestPayload,
    config?: RequestConfig
  ): Promise<T> {
    const url = `${this.config.baseURL}${endpoint}`;
    const headers = {
      ...this.config.defaultHeaders,
      ...config?.headers
    };

    // Add auth token if available
    try {
      const token = tokenStorage.getToken();
      if (token && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    } catch (e) {
      // Ignore tokenStorage errors
    }

    if (process.env.NODE_ENV !== 'production') {
      console.log(`🔍 MasterFlowService.request - ${method} ${url}`, { url: url, method: method });
    }

    const requestOptions: RequestInit = {
      method,
      headers,
      signal: AbortSignal.timeout(config?.timeout || this.config.timeout),
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      requestOptions.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, requestOptions);

      if (!response.ok) {
        // Issue #719: Parse response body to preserve error details (like apps_not_found)
        let errorData: Record<string, unknown> = {};
        try {
          errorData = await response.json();
        } catch {
          // Response may not be JSON, use empty object
          errorData = { message: response.statusText };
        }
        console.error(`API Error ${response.status}: ${method} ${endpoint}`, errorData);
        throw new ApiError(response.status, response.statusText, errorData);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      // Re-throw ApiErrors as-is to preserve response data
      if (error instanceof ApiError) {
        throw error;
      }
      console.error(`API Request failed: ${method} ${endpoint}`, error);
      throw error;
    }
  }

  async get<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>('GET', endpoint, undefined, config);
  }

  async post<T>(endpoint: string, data?: RequestPayload, config?: RequestConfig): Promise<T> {
    return this.request<T>('POST', endpoint, data, config);
  }

  async put<T>(endpoint: string, data?: RequestPayload, config?: RequestConfig): Promise<T> {
    return this.request<T>('PUT', endpoint, data, config);
  }

  async patch<T>(endpoint: string, data?: RequestPayload, config?: RequestConfig): Promise<T> {
    return this.request<T>('PATCH', endpoint, data, config);
  }

  async delete<T>(endpoint: string, data?: RequestPayload, config?: RequestConfig): Promise<T> {
    return this.request<T>('DELETE', endpoint, data, config);
  }
}
