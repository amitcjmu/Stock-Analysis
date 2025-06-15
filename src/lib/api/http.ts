// API Configuration
const getApiBaseUrl = (): string => {
  // Priority 1: Explicit VITE_BACKEND_URL (for production deployments)
  if (import.meta.env.VITE_BACKEND_URL) {
    const backendUrl = import.meta.env.VITE_BACKEND_URL;
    // Remove /api/v1 suffix if it exists to get the base URL
    return backendUrl.endsWith('/api/v1') ? backendUrl : `${backendUrl}/api/v1`;
  }
  
  // Priority 2: Legacy VITE_API_BASE_URL
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // Priority 3: Check if we're in production mode with Vercel
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // If running on Vercel (vercel.app domain), use Railway backend
    if (hostname.includes('.vercel.app')) {
      // This should be set as VITE_BACKEND_URL in Vercel environment variables
      // pointing to your Railway.com backend URL
      console.warn('Production deployment detected. Ensure VITE_BACKEND_URL is set to your Railway backend URL.');
      // Fallback to same origin (not recommended for Vercel + Railway setup)
      return window.location.origin;
    }
  }
  
  // Priority 4: Development mode - use localhost
  if (import.meta.env.DEV || import.meta.env.MODE === 'development') {
    return 'http://localhost:8000/api/v1';
  }
  
  // Priority 5: Final fallback - same origin
  if (typeof window !== 'undefined') {
    console.warn('No VITE_BACKEND_URL environment variable found. Using same origin as fallback.');
    return window.location.origin;
  }
  
  // Fallback for SSR or build time
  return 'http://localhost:8000/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

// Helper function to normalize endpoint path
const normalizeEndpoint = (endpoint: string): string => {
  // Remove any leading /api/v1 to prevent duplication
  const normalizedEndpoint = endpoint.replace(/^\/api\/v1/, '');
  // Ensure endpoint starts with /
  return normalizedEndpoint.startsWith('/') ? normalizedEndpoint : `/${normalizedEndpoint}`;
};

// Default client for fallback
const DEFAULT_CLIENT = {
  id: "demo",
  name: "Pujyam Corp",
  status: "active",
  type: "enterprise",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  metadata: {
    industry: "Technology",
    size: "Enterprise",
    location: "Global"
  }
};

// Cache Management
class ApiCache {
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  
  set(key: string, data: any, ttl: number = 300000): void { // 5 minutes default
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }
  
  get(key: string): any | null {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }
  
  delete(key: string): void {
    this.cache.delete(key);
  }
  
  clear(): void {
    this.cache.clear();
  }
  
  invalidatePattern(pattern: string): void {
    const regex = new RegExp(pattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }
}

// Error Classes
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public type: 'network' | 'server' | 'client' | 'unknown',
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Base HTTP Client
export class HttpClient {
  private cache = new ApiCache();
  private maxRetries = 3;

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    retries: number = this.maxRetries,
    useCache: boolean = false,
    cacheTtl?: number
  ): Promise<T> {
    // Check cache first for GET requests
    if (options.method === 'GET' && useCache) {
      const cached = this.cache.get(endpoint);
      if (cached) return cached;
    }
    
    // Remove any leading /api/v1 since it's already in the base URL
    const cleanEndpoint = endpoint.replace(/^\/api\/v1/, '');
    const url = `${API_BASE_URL}${cleanEndpoint.startsWith('/') ? cleanEndpoint : `/${cleanEndpoint}`}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`,
        ...options.headers,
      },
      ...options,
    };

    // If body is a string, use it directly, otherwise stringify it
    if (defaultOptions.body && typeof defaultOptions.body !== 'string') {
      defaultOptions.body = JSON.stringify(defaultOptions.body);
    }

    let lastError: Error;
    
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await fetch(url, defaultOptions);
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new APIError(
            errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            'server',
            errorData
          );
        }
        
        const data = await response.json();
        
        // Cache successful GET responses
        if (options.method === 'GET' && useCache) {
          this.cache.set(endpoint, data, cacheTtl);
        }
        
        return data;
        
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        // Don't retry on client errors (4xx)
        if (error instanceof APIError && error.status >= 400 && error.status < 500) {
          throw error;
        }
        
        // Wait before retry (exponential backoff)
        if (attempt < retries - 1) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    throw lastError;
  }

  protected getAuthToken(): string {
    // Get token from localStorage
    return localStorage.getItem('auth_token') || '';
  }

  async get<T>(url: string, useCache: boolean = true, cacheTtl?: number): Promise<T> {
    return this.makeRequest<T>(url, { method: 'GET' }, this.maxRetries, useCache, cacheTtl);
  }
  
  async post<T>(url: string, data?: any): Promise<T> {
    return this.makeRequest<T>(url, {
      method: 'POST',
      body: data
    });
  }
  
  async put<T>(url: string, data?: any): Promise<T> {
    return this.makeRequest<T>(url, {
      method: 'PUT',
      body: data
    });
  }
  
  async delete<T>(url: string): Promise<T> {
    return this.makeRequest<T>(url, { method: 'DELETE' });
  }

  clearCache(): void {
    this.cache.clear();
  }

  invalidateCache(pattern: string): void {
    this.cache.invalidatePattern(pattern);
  }
} 

interface ApiCallOptions extends RequestInit {
  headers?: HeadersInit;
}

export const apiCall = async <T = any>(
  endpoint: string,
  options: ApiCallOptions = {}
): Promise<T> => {
  const client = new HttpClient();
  
  if (options.method === 'GET' || !options.method) {
    return client.get(endpoint);
  } else if (options.method === 'POST') {
    return client.post(endpoint, options.body);
  } else if (options.method === 'PUT') {
    return client.put(endpoint, options.body);
  } else if (options.method === 'DELETE') {
    return client.delete(endpoint);
  }
  
  throw new Error(`Unsupported HTTP method: ${options.method}`);
}; 