/**
 * API Service - Re-exports the api functions from config
 */

import type { ExternalApiRequestPayload } from '../config/api';

export { apiCall as get, apiCall as post, apiCall as put, apiCall as patch, apiCall as del } from '../config/api';

// Re-export the main apiCall function
export { apiCall, apiCallWithFallback, API_CONFIG, updateApiContext } from '../config/api';

// Create a default api object for convenience
export const api = {
  get: (endpoint: string, options?: RequestInit) => apiCall(endpoint, { ...options, method: 'GET' }),
  post: (endpoint: string, data?: ExternalApiRequestPayload, options?: RequestInit) => {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    return apiCall(endpoint, { ...options, method: 'POST', body });
  },
  put: (endpoint: string, data?: ExternalApiRequestPayload, options?: RequestInit) => {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    return apiCall(endpoint, { ...options, method: 'PUT', body });
  },
  patch: (endpoint: string, data?: ExternalApiRequestPayload, options?: RequestInit) => {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    return apiCall(endpoint, { ...options, method: 'PATCH', body });
  },
  delete: (endpoint: string, options?: RequestInit) => apiCall(endpoint, { ...options, method: 'DELETE' }),
};

export default api;