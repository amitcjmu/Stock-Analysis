/**
 * API Client for Master Flow Orchestrator
 * Unified API client with authentication and error handling
 */

import type { ApiResponse, ApiError } from '../types/shared/api-types';

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
      const token = localStorage.getItem('auth_token');
      if (token && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    } catch (e) {
      // Ignore localStorage errors
    }

    console.log(`🔍 MasterFlowService.request - ${method} ${url}`, { headers });

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
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
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
