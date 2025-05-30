/**
 * API Configuration
 * Manages backend API endpoints and configuration
 */

// Get the backend URL from environment variables with proper fallbacks
const getBackendUrl = (): string => {
  // First, check for environment-specific variables
  const backendUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_BASE_URL;
  
  if (backendUrl) {
    // Remove /api/v1 suffix if it exists to get the base URL
    return backendUrl.replace(/\/api\/v1$/, '');
  }
  
  // In development mode, use localhost
  if (import.meta.env.DEV || import.meta.env.MODE === 'development') {
    return 'http://localhost:8000';
  }
  
  // For production without explicit backend URL, use same origin
  // This is a fallback that should not be used with Vercel + Railway setup
  console.warn('No VITE_BACKEND_URL environment variable found. Using same origin as fallback.');
  return window.location.origin;
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
      ASSETS_BULK: '/api/v1/discovery/assets/bulk',
      ASSETS_CLEANUP: '/api/v1/discovery/assets/cleanup-duplicates',
      APPLICATIONS: '/api/v1/discovery/applications',
      APP_MAPPINGS: '/api/v1/discovery/app-server-mappings',
      FEEDBACK: '/api/v1/discovery/feedback',
      CHAT: '/api/v1/discovery/chat-test'
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