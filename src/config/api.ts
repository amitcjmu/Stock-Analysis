/**
 * API Configuration
 * Manages backend API endpoints and configuration
 */

// Get the backend URL from environment or use default
const getBackendUrl = (): string => {
  // In development, use localhost:8000
  if (import.meta.env.DEV) {
    return 'http://localhost:8000';
  }
  
  // In production, use the same origin or environment variable
  return import.meta.env.VITE_BACKEND_URL || window.location.origin;
};

export const API_CONFIG = {
  BASE_URL: getBackendUrl(),
  ENDPOINTS: {
    DISCOVERY: {
      ANALYZE_CMDB: '/api/v1/discovery/analyze-cmdb',
      PROCESS_CMDB: '/api/v1/discovery/process-cmdb',
      CMDB_TEMPLATES: '/api/v1/discovery/cmdb-templates'
    }
  }
};

/**
 * Helper function to make API calls with proper error handling
 */
export const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_CONFIG.BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
  }

  return response.json();
}; 