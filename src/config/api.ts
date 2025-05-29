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
      CMDB_TEMPLATES: '/api/v1/discovery/cmdb-templates',
      CMDB_FEEDBACK: '/api/v1/discovery/cmdb-feedback',
      ASSETS: '/api/v1/discovery/assets',
      APPLICATIONS: '/api/v1/discovery/applications',
      APP_MAPPINGS: '/api/v1/discovery/app-server-mappings'
    },
    MONITORING: {
      STATUS: '/api/v1/monitoring/status',
      TASKS: '/api/v1/monitoring/tasks',
      AGENTS: '/api/v1/monitoring/agents',
      HEALTH: '/api/v1/monitoring/health',
      METRICS: '/api/v1/monitoring/metrics',
      CANCEL_TASK: '/api/v1/monitoring/tasks'
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