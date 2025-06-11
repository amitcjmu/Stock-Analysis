/**
 * API Configuration
 * Manages backend API endpoints and configuration
 * Supports local development, Vercel frontend + Railway backend deployment
 */

// Define types for the API context
interface AppContextType {
  client: { id: string } | null;
  engagement: { id: string } | null;
  session: { id: string } | null;
}

// Create a variable to store the current context
let currentContext: AppContextType = {
  client: null,
  engagement: null,
  session: null
};

// Export a function to update the context
// This will be called by the AppContextProvider when the context changes
export const updateApiContext = (context: AppContextType) => {
  currentContext = { ...context };
};

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
      AGENT_ANALYSIS: '/api/v1/discovery/agents/agent-analysis',
      ANALYZE_CMDB: '/api/v1/discovery/analyze-cmdb',
      PROCESS_CMDB: '/api/v1/discovery/process-cmdb',
      CMDB_TEMPLATES: '/api/v1/discovery/cmdb-templates',
      CMDB_FEEDBACK: '/api/v1/discovery/cmdb-feedback',
      ASSETS: '/api/v1/assets/list/paginated',
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
      DEPENDENCIES: '/api/v1/discovery/dependencies',
      EXPORT_VISUALIZATION: '/api/v1/discovery/dependencies/export-visualization',
      // Data cleanup endpoints  
      DATA_CLEANUP_ANALYZE: '/api/v1/discovery/data-cleanup/agent-analyze',
      DATA_CLEANUP_PROCESS: '/api/v1/discovery/data-cleanup/agent-process',
      // Data import persistence endpoints
      STORE_IMPORT: '/api/v1/assets/bulk-create',
      STORE_IMPORT_TEMP: '/api/v1/data-import/store-import-temp',
      LATEST_IMPORT: '/api/v1/data-import/latest-import',
      LATEST_IMPORT_TEMP: '/api/v1/data-import/latest-import-temp',
      GET_IMPORT: '/api/v1/data-import/import',
      LIST_IMPORTS: '/api/v1/data-import/imports',
      AVAILABLE_TARGET_FIELDS: '/api/v1/data-import/available-target-fields',
      CRITICAL_ATTRIBUTES_STATUS: '/api/v1/data-import/critical-attributes-status'
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
    AGENT_LEARNING: {
      LEARNING_STATISTICS: '/api/v1/agent-learning/learning/stats',
      FIELD_MAPPING_LEARN: '/api/v1/agent-learning/learning/field-mapping',
      FIELD_MAPPING_SUGGEST: '/api/v1/agent-learning/learning/field-mapping/suggest',
      DATA_SOURCE_PATTERN: '/api/v1/agent-learning/learning/data-source-pattern',
      QUALITY_ASSESSMENT: '/api/v1/agent-learning/learning/quality-assessment',
      USER_PREFERENCES: '/api/v1/agent-learning/learning/user-preferences',
      AGENT_PERFORMANCE: '/api/v1/agent-learning/learning/agent-performance',
      HEALTH: '/api/v1/agent-learning/health'
    },
    HEALTH: '/health',
    // SIXR Endpoints
    SIXR_ANALYSIS: '/api/v1/sixr/analyze'
  }
};

// Track in-flight requests to prevent duplicates
const pendingRequests = new Map<string, Promise<any>>();

interface ApiError extends Error {
  status?: number;
  statusText?: string;
  response?: any;
  requestId?: string;
  isApiError: boolean;
}

/**
 * Helper function to make API calls with proper error handling and authentication
 * @param endpoint The API endpoint to call
 * @param options Fetch options
 * @param includeContext Whether to include the current context in the request headers
 */
export const apiCall = async (
  endpoint: string, 
  options: RequestInit = {}, 
  includeContext: boolean = true
): Promise<any> => {
  const requestId = Math.random().toString(36).substring(2, 8);
  const startTime = performance.now();
  const url = `${API_CONFIG.BASE_URL}${endpoint}`;
  const method = (options.method || 'GET').toUpperCase();
  
  // Create a unique key for this request to prevent duplicates
  const requestKey = `${method}:${endpoint}`;
  
  // If we already have a request with the same key, return that instead
  if (pendingRequests.has(requestKey)) {
    console.log(`[${requestId}] Request already in flight: ${requestKey}`);
    return pendingRequests.get(requestKey);
  }

  // Log the API call
  console.group(`API Call [${requestId}]`);
  console.log('Method:', method);
  console.log('URL:', url);
  console.log('Current Context:', currentContext);
  
  // Create the request promise and store it
  const requestPromise = (async () => {
    try {
      // Add headers
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId,
        ...options.headers,
      };
      
      // Add auth token if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      } else {
        console.warn('No auth token found in localStorage');
      }
      
      // Add context headers if needed
      if (includeContext) {
        if (currentContext.client?.id) {
          headers['X-Client-Account-ID'] = currentContext.client.id;
        }
        if (currentContext.engagement?.id) {
          headers['X-Engagement-ID'] = currentContext.engagement.id;
        }
        if (currentContext.session?.id) {
          headers['X-Session-ID'] = currentContext.session.id;
        }
      }
      
      // Make the request
      const response = await fetch(url, {
        ...options,
        method, // Ensure method is uppercase
        headers,
        credentials: 'include',
      });
      
      const endTime = performance.now();
      const duration = (endTime - startTime).toFixed(2);
      
      // Parse response as JSON if possible
      let data;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        try {
          data = await response.json();
        } catch (e) {
          console.error('Failed to parse JSON response:', e);
          throw new Error('Invalid JSON response from server');
        }
      } else {
        data = await response.text();
      }
      
      // Log the response
      console.log('Status:', response.status, response.statusText);
      console.log('Duration:', `${duration}ms`);
      console.log('Response:', data);
      
      if (!response.ok) {
        const error = new Error(data?.message || response.statusText || 'Request failed') as ApiError;
        error.status = response.status;
        error.statusText = response.statusText;
        error.response = data;
        error.requestId = requestId;
        error.isApiError = true;
        
        // Special handling for 404s
        if (response.status === 404) {
          console.warn(`[${requestId}] Resource not found: ${url}`);
        }
        
        throw error;
      }
      
      return data;
    } catch (error) {
      const endTime = performance.now();
      const duration = (endTime - startTime).toFixed(2);
      
      let apiError: ApiError;
      if (error instanceof Error) {
        apiError = error as ApiError;
        apiError.isApiError = true;
      } else {
        apiError = new Error('Unknown API error') as ApiError;
        apiError.isApiError = true;
      }
      
      apiError.requestId = requestId;
      
      console.error(`API Call [${requestId}] failed after ${duration}ms:`, apiError);
      
      // Re-throw the enhanced error
      throw apiError;
    } finally {
      // Clean up the pending request
      pendingRequests.delete(requestKey);
      console.groupEnd();
    }
  })();
  
  // Store the promise for deduplication
  pendingRequests.set(requestKey, requestPromise);
  
  return requestPromise;
};