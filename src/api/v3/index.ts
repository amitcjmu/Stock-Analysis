/**
 * API v3 Client - Main Export
 * Unified client for all v3 API operations
 */

import { ApiClient } from './client';
import { DiscoveryFlowClient } from './discoveryFlowClient';
import { FieldMappingClient } from './fieldMappingClient';
import { DataImportClient } from './dataImportClient';

import type { 
  ApiClientConfig,
  RequestContext,
  HealthCheckResponse
} from './types/common';

// Re-export all types for easy access
export * from './types';

// Re-export client classes
export { ApiClient, DiscoveryFlowClient, FieldMappingClient, DataImportClient };

// Re-export utility functions
export { buildQueryString, buildFormData, buildUrl } from './utils/queryBuilder';
export { 
  getAuthToken, 
  setAuthToken, 
  removeAuthToken,
  getRequestContext,
  setRequestContext
} from './utils/requestConfig';

// Re-export error classes
export {
  ApiError,
  ValidationApiError,
  NotFoundApiError,
  NetworkError,
  TimeoutError,
  isApiError,
  isValidationApiError,
  isNotFoundApiError,
  isNetworkError,
  isTimeoutError,
  createUserFriendlyError,
  isRecoverableError
} from './types/responses';

/**
 * Unified API v3 Client
 * Combines all specialized clients into a single interface
 */
export class ApiV3Client {
  public readonly discoveryFlow: DiscoveryFlowClient;
  public readonly fieldMapping: FieldMappingClient;
  public readonly dataImport: DataImportClient;

  private readonly apiClient: ApiClient;

  constructor(config: ApiClientConfig) {
    this.apiClient = new ApiClient(config);
    
    // Initialize specialized clients
    this.discoveryFlow = new DiscoveryFlowClient(this.apiClient);
    this.fieldMapping = new FieldMappingClient(this.apiClient);
    this.dataImport = new DataImportClient(this.apiClient);
  }

  /**
   * Get the underlying API client for custom requests
   */
  getApiClient(): ApiClient {
    return this.apiClient;
  }

  /**
   * Update authentication token
   */
  setAuthToken(token: string): void {
    this.apiClient.setAuthToken(token);
  }

  /**
   * Get current client configuration
   */
  getConfig(): Readonly<Required<ApiClientConfig>> {
    return this.apiClient.getConfig();
  }

  /**
   * Create a new client instance with different configuration
   */
  withConfig(config: Partial<ApiClientConfig>): ApiV3Client {
    return new ApiV3Client({
      ...this.getConfig(),
      ...config
    });
  }

  /**
   * Comprehensive health check for all v3 services
   */
  async healthCheck(): Promise<{
    overall_status: 'healthy' | 'degraded' | 'unhealthy';
    services: {
      api: HealthCheckResponse;
      discovery_flow: HealthCheckResponse;
      field_mapping: HealthCheckResponse;
      data_import: HealthCheckResponse;
    };
    timestamp: string;
  }> {
    try {
      const [api, discoveryFlow, fieldMapping, dataImport] = await Promise.allSettled([
        this.apiClient.healthCheck(),
        this.discoveryFlow.getHealth(),
        this.fieldMapping.getHealth(),
        this.dataImport.getHealth()
      ]);

      const services = {
        api: api.status === 'fulfilled' ? api.value : { status: 'unhealthy' as const, timestamp: new Date().toISOString() },
        discovery_flow: discoveryFlow.status === 'fulfilled' ? discoveryFlow.value : { status: 'unhealthy' as const, timestamp: new Date().toISOString() },
        field_mapping: fieldMapping.status === 'fulfilled' ? fieldMapping.value : { status: 'unhealthy' as const, timestamp: new Date().toISOString() },
        data_import: dataImport.status === 'fulfilled' ? dataImport.value : { status: 'unhealthy' as const, timestamp: new Date().toISOString() }
      };

      // Determine overall status
      const statuses = Object.values(services).map(service => service.status);
      const healthyCount = statuses.filter(status => status === 'healthy').length;
      const totalCount = statuses.length;

      let overall_status: 'healthy' | 'degraded' | 'unhealthy';
      if (healthyCount === totalCount) {
        overall_status = 'healthy';
      } else if (healthyCount > 0) {
        overall_status = 'degraded';
      } else {
        overall_status = 'unhealthy';
      }

      return {
        overall_status,
        services,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      throw new Error(`Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

/**
 * Factory function to create a configured API v3 client
 */
export function createApiV3Client(config: ApiClientConfig): ApiV3Client {
  return new ApiV3Client(config);
}

/**
 * Default configuration factory
 */
export function createDefaultConfig(baseURL?: string): ApiClientConfig {
  return {
    baseURL: baseURL || process.env.REACT_APP_API_URL || '/api/v3',  // Use relative path for proxy
    timeout: 30000,
    retryAttempts: 3,
    retryDelay: 1000,
    enableLogging: process.env.NODE_ENV === 'development',
    defaultHeaders: {
      'Content-Type': 'application/json',
      'X-API-Version': 'v3',
      'X-Client': 'web-app'
    }
  };
}

/**
 * Create API client with automatic configuration detection
 */
export function createAutoConfiguredClient(overrides: Partial<ApiClientConfig> = {}): ApiV3Client {
  const defaultConfig = createDefaultConfig();
  
  // Auto-detect base URL from environment
  let baseURL = defaultConfig.baseURL;
  
  if (typeof window !== 'undefined') {
    // Browser environment - check for environment variables
    if (import.meta.env.VITE_API_URL) {
      baseURL = `${import.meta.env.VITE_API_URL}/api/v3`;
    } else if (import.meta.env.VITE_BACKEND_URL) {
      baseURL = `${import.meta.env.VITE_BACKEND_URL}/api/v3`;
    }
  }

  const config: ApiClientConfig = {
    ...defaultConfig,
    baseURL,
    ...overrides
  };

  return createApiV3Client(config);
}

/**
 * Singleton instance for global use
 */
let globalApiClient: ApiV3Client | null = null;

/**
 * Get or create global API client instance
 */
export function getGlobalApiClient(config?: ApiClientConfig): ApiV3Client {
  if (!globalApiClient) {
    globalApiClient = config ? createApiV3Client(config) : createAutoConfiguredClient();
  }
  return globalApiClient;
}

/**
 * Reset global API client instance
 */
export function resetGlobalApiClient(): void {
  globalApiClient = null;
}

/**
 * Hook for React components to easily access the API client
 */
export function useApiV3Client(config?: ApiClientConfig): ApiV3Client {
  return getGlobalApiClient(config);
}

// Default export for convenience
export default {
  createApiV3Client,
  createDefaultConfig,
  createAutoConfiguredClient,
  getGlobalApiClient,
  resetGlobalApiClient,
  useApiV3Client,
  ApiV3Client,
  ApiClient,
  DiscoveryFlowClient,
  FieldMappingClient,
  DataImportClient
};