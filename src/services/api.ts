/**
 * API Service - Re-exports the api functions from config
 */

export { apiCall as get, apiCall as post, apiCall as put, apiCall as patch, apiCall as del } from '../config/api';

// Re-export the main apiCall function
export { apiCall, apiCallWithFallback, API_CONFIG, updateApiContext } from '../config/api';

// Create a default api object for convenience
export const api = {
  get: (endpoint: string, options?: RequestInit) => apiCall(endpoint, { ...options, method: 'GET' }),
  post: (endpoint: string, data?: any, options?: RequestInit) => apiCall(endpoint, { ...options, method: 'POST', body: JSON.stringify(data) }),
  put: (endpoint: string, data?: any, options?: RequestInit) => apiCall(endpoint, { ...options, method: 'PUT', body: JSON.stringify(data) }),
  patch: (endpoint: string, data?: any, options?: RequestInit) => apiCall(endpoint, { ...options, method: 'PATCH', body: JSON.stringify(data) }),
  delete: (endpoint: string, options?: RequestInit) => apiCall(endpoint, { ...options, method: 'DELETE' }),
};

export default api;