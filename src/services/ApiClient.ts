/**
 * API Client for Master Flow Orchestrator
 * Unified API client with authentication and error handling
 */

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

export class ApiClient {
  private static instance: ApiClient;
  private config: ApiClientConfig;

  private constructor() {
    this.config = {
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: 30000,
      retries: 3,
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
    data?: any,
    config?: RequestConfig
  ): Promise<T> {
    const url = `${this.config.baseURL}${endpoint}`;
    const headers = {
      ...this.config.defaultHeaders,
      ...config?.headers
    };

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

  async post<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>('POST', endpoint, data, config);
  }

  async put<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>('PUT', endpoint, data, config);
  }

  async patch<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>('PATCH', endpoint, data, config);
  }

  async delete<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>('DELETE', endpoint, data, config);
  }
}