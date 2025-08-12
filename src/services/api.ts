/**
 * API Service - Re-exports the api functions from config
 */

import type { ExternalApiRequestPayload, ExternalApiResponse } from '../config/api';

// Import apiCall first so it's available for the api object
import { apiCall, apiCallWithFallback, API_CONFIG, updateApiContext } from '../config/api';

// Re-export the functions
export { apiCall as get, apiCall as post, apiCall as put, apiCall as patch, apiCall as del } from '../config/api';

// Re-export the main functions
export { apiCall, apiCallWithFallback, API_CONFIG, updateApiContext };

// Create a default api object for convenience
export const api = {
  get: (endpoint: string, options?: RequestInit): Promise<ExternalApiResponse> => apiCall(endpoint, { ...options, method: 'GET' }),
  post: (endpoint: string, data?: ExternalApiRequestPayload, options?: RequestInit): Promise<ExternalApiResponse> => {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    return apiCall(endpoint, { ...options, method: 'POST', body });
  },
  put: (endpoint: string, data?: ExternalApiRequestPayload, options?: RequestInit): Promise<ExternalApiResponse> => {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    return apiCall(endpoint, { ...options, method: 'PUT', body });
  },
  patch: (endpoint: string, data?: ExternalApiRequestPayload, options?: RequestInit): Promise<ExternalApiResponse> => {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    return apiCall(endpoint, { ...options, method: 'PATCH', body });
  },
  delete: (endpoint: string, options?: RequestInit): Promise<ExternalApiResponse> => apiCall(endpoint, { ...options, method: 'DELETE' }),
};

export default api;
