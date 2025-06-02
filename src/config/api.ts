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
      INFRASTRUCTURE_LANDSCAPE: '/api/v1/discovery/assets/infrastructure-landscape',
      // Agent endpoints
      AGENT_ANALYSIS: '/api/v1/discovery/agents/agent-analysis',
      AGENT_CLARIFICATION: '/api/v1/discovery/agents/agent-clarification',
      AGENT_STATUS: '/api/v1/discovery/agents/agent-status',
      AGENT_LEARNING: '/api/v1/discovery/agents/agent-learning',
      APPLICATION_PORTFOLIO: '/api/v1/discovery/agents/application-portfolio',
      APPLICATION_VALIDATION: '/api/v1/discovery/agents/application-validation',
      READINESS_ASSESSMENT: '/api/v1/discovery/agents/readiness-assessment',
      // Assessment Readiness Orchestrator endpoints
      ASSESSMENT_READINESS: '/api/v1/discovery/agents/assessment-readiness',
      STAKEHOLDER_SIGNOFF_PACKAGE: '/api/v1/discovery/agents/stakeholder-signoff-package',
      STAKEHOLDER_SIGNOFF_FEEDBACK: '/api/v1/discovery/agents/stakeholder-signoff-feedback',
      // Tech Debt Analysis endpoints
      TECH_DEBT_ANALYSIS: '/api/v1/discovery/agents/tech-debt-analysis',
      TECH_DEBT_FEEDBACK: '/api/v1/discovery/agents/tech-debt-feedback',
      // Dependency Analysis endpoints
      DEPENDENCY_ANALYSIS: '/api/v1/discovery/agents/dependency-analysis',
      DEPENDENCY_FEEDBACK: '/api/v1/discovery/agents/dependency-feedback',
      // Data cleanup endpoints  
      DATA_CLEANUP_ANALYZE: '/api/v1/discovery/data-cleanup/agent-analyze',
      DATA_CLEANUP_PROCESS: '/api/v1/discovery/data-cleanup/agent-process',
      // Data import persistence endpoints
      STORE_IMPORT: '/api/v1/data-import/store-import',
      LATEST_IMPORT: '/api/v1/data-import/latest-import',
      GET_IMPORT: '/api/v1/data-import/import',
      LIST_IMPORTS: '/api/v1/data-import/imports',
      AVAILABLE_TARGET_FIELDS: '/api/v1/data-import/available-target-fields'
    },
    MONITORING: {
      STATUS: '/api/v1/monitoring/status',
      TASKS: '/api/v1/monitoring/tasks',
      AGENTS: '/api/v1/monitoring/agents',
      HEALTH: '/api/v1/monitoring/health',
      METRICS: '/api/v1/monitoring/metrics',
      CANCEL_TASK: '/api/v1/monitoring/tasks'
    },
    ADMIN: {
      CLIENTS: '/api/v1/admin/clients',
      ENGAGEMENTS: '/api/v1/admin/engagements',
      USERS: '/api/v1/admin/users',
      USER_PROFILES: '/api/v1/admin/user-profiles',
      CLIENT_ACCESS: '/api/v1/admin/client-access',
      ENGAGEMENT_ACCESS: '/api/v1/admin/engagement-access'
    },
    HEALTH: '/health'
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