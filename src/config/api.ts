/**
 * API Configuration
 * Manages backend API endpoints and configuration
 * Supports local development, Vercel frontend + Railway backend deployment
 */

// Get the backend URL from environment variables with proper fallbacks
const getBackendUrl = (): string => {
  // Priority 1: Explicit VITE_BACKEND_URL (for production deployments)
  if (import.meta.env.VITE_BACKEND_URL) {
    const backendUrl = import.meta.env.VITE_BACKEND_URL;
    // Remove /api/v1 suffix if it exists to get the base URL
    return backendUrl.replace(/\/api\/v1$/, '');
  }
  
  // Priority 2: Legacy VITE_API_BASE_URL
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL.replace(/\/api\/v1$/, '');
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
    return 'http://localhost:8000';
  }
  
  // Priority 5: Final fallback - same origin
  if (typeof window !== 'undefined') {
    console.warn('No VITE_BACKEND_URL environment variable found. Using same origin as fallback.');
    return window.location.origin;
  }
  
  // Fallback for SSR or build time
  return 'http://localhost:8000';
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
      CHAT: '/api/v1/discovery/chat-test',
      // New discovery dashboard endpoints
      DISCOVERY_METRICS: '/api/v1/discovery/assets/discovery-metrics',
      APPLICATION_LANDSCAPE: '/api/v1/discovery/assets/application-landscape',
      INFRASTRUCTURE_LANDSCAPE: '/api/v1/discovery/assets/infrastructure-landscape'
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
  
  // Log API calls in development for debugging
  if (import.meta.env.DEV) {
    console.log(`API Call: ${options.method || 'GET'} ${url}`);
  }
  
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