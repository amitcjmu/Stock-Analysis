/**
 * API Configuration
 * Manages backend API endpoints and configuration
 * Supports local development, Vercel frontend + Railway backend deployment
 */

import type { ApiResponse, ApiError } from '../types/shared/api-types';
import { tokenStorage } from '../contexts/AuthContext/storage';

// Define types for the API context
interface AppContextType {
  user: { id: string } | null;
  client: { id: string } | null;
  engagement: { id: string } | null;
  flow: { id: string } | null;
}

// Create a variable to store the current context
let currentContext: AppContextType = {
  user: null,
  client: null,
  engagement: null,
  flow: null
};

// Export a function to update the context
// This will be called by the AppContextProvider when the context changes
export const updateApiContext = (context: AppContextType) => {
  currentContext = { ...context };
};

// Get the backend URL from environment variables with proper fallbacks
const getBackendUrl = (): string => {
  // Force proxy usage for development - Docker container on port 8081
  if (typeof window !== 'undefined' && window.location.port === '8081') {
    console.log('🔧 Docker development mode detected - using Vite proxy');
    return '';
  }
  
  // Priority 1: Explicit VITE_BACKEND_URL (for production deployments)
  if (import.meta.env.VITE_BACKEND_URL) {
    const backendUrl = import.meta.env.VITE_BACKEND_URL;
    console.log('🔧 Using VITE_BACKEND_URL:', backendUrl);
    return backendUrl;
  }
  
  // Priority 2: Legacy VITE_API_BASE_URL
  if (import.meta.env.VITE_API_BASE_URL) {
    console.log('🔧 Using VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // Priority 3: Check if we're in production mode with Vercel
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // If running on Vercel (vercel.app domain), use Railway backend
    if (hostname.includes('.vercel.app')) {
      console.warn('Production deployment detected. Ensure VITE_BACKEND_URL is set to your Railway backend URL.');
      return window.location.origin;
    }
  }
  
  // Priority 4: Development mode - use empty string to utilize Vite proxy
  if (import.meta.env.DEV || import.meta.env.MODE === 'development') {
    console.log('🔧 Vite development mode detected - using proxy');
    return '';  // Empty string means use same origin with proxy
  }
  
  // Priority 5: Final fallback - use proxy for development
  if (typeof window !== 'undefined') {
    // In development, always use proxy to avoid CORS issues
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      console.log('🔧 Localhost development detected - using proxy');
      return '';
    }
    console.warn('No VITE_BACKEND_URL environment variable found. Using same origin as fallback.');
    return window.location.origin;
  }
  
  // Fallback for SSR or build time - use empty string for proxy
  console.log('🔧 SSR/build fallback - using proxy');
  return '';
};

// Get backend URL dynamically at request time
const getBaseUrl = (): string => {
  const url = getBackendUrl();
  console.log('🔧 API_CONFIG.BASE_URL resolved to:', url);
  return url;
};

export const API_CONFIG = {
  get BASE_URL() {
    return getBaseUrl();
  },
  ENDPOINTS: {
    DISCOVERY: {
      AGENT_ANALYSIS: '/agents/discovery/analysis', // FIXED: Use actual agent analysis endpoint
      ANALYZE_CMDB: '/agents/discovery/analysis', // FIXED: Use actual agent analysis endpoint  
      PROCESS_CMDB: '/discovery/flow/run', // Discovery flow execution endpoint
      CMDB_TEMPLATES: '/discovery/cmdb-templates',
      CMDB_FEEDBACK: '/discovery/cmdb-feedback',
      ASSETS: '/discovery/assets',
      ASSETS_BULK: '/discovery/assets/bulk',
      ASSETS_CLEANUP: '/discovery/assets/cleanup-duplicates',
      APPLICATIONS: '/discovery/applications',
      APP_MAPPINGS: '/discovery/app-server-mappings',
      FEEDBACK: '/discovery/feedback',
      CHAT: '/discovery/chat-test',
      // New discovery dashboard endpoints
      DISCOVERY_METRICS: '/discovery/assets/discovery-metrics',
      APPLICATION_LANDSCAPE: '/discovery/assets/application-landscape',
      INFRASTRUCTURE_LANDSCAPE: '/discovery/assets/infrastructure-landscape',
      // Agent endpoints
      AGENT_CLARIFICATION: '/discovery/agents/agent-clarification',
      AGENT_STATUS: '/agents/discovery/agent-status',
      AGENTIC_ANALYSIS_STATUS: '/discovery/flow/agent/crew/analysis/status',
      AGENT_LEARNING: '/agents/discovery/learning/agent-learning',
      APPLICATION_PORTFOLIO: '/discovery/agents/application-portfolio',
      APPLICATION_VALIDATION: '/discovery/agents/application-validation',
      READINESS_ASSESSMENT: '/discovery/agents/readiness-assessment',
      // Assessment Readiness Orchestrator endpoints
      ASSESSMENT_READINESS: '/discovery/agents/assessment-readiness',
      STAKEHOLDER_SIGNOFF_PACKAGE: '/discovery/agents/stakeholder-signoff-package',
      STAKEHOLDER_SIGNOFF_FEEDBACK: '/discovery/agents/stakeholder-signoff-feedback',
      // Tech Debt Analysis endpoints
      TECH_DEBT_ANALYSIS: '/discovery/agents/tech-debt-analysis',
      TECH_DEBT_FEEDBACK: '/discovery/agents/tech-debt-feedback',
      // Dependency Analysis endpoints
      DEPENDENCY_ANALYSIS: '/discovery/dependency-analysis/execute',
      DEPENDENCY_FEEDBACK: '/discovery/agents/dependencies/dependency-feedback',
      DEPENDENCIES: '/discovery/dependencies',
      EXPORT_VISUALIZATION: '/discovery/dependencies/export-visualization',
      // Data cleanup endpoints  
      DATA_CLEANUP_ANALYZE: '/discovery/data-cleanup/agent-analyze',
      DATA_CLEANUP_PROCESS: '/discovery/data-cleanup/agent-process',
      // Data import persistence endpoints
      STORE_IMPORT: '/assets/bulk-create',
      STORE_IMPORT_TEMP: '/data-import/store-import-temp',
      LATEST_IMPORT: '/data-import/latest-import',
      LATEST_IMPORT_TEMP: '/data-import/latest-import-temp',
      GET_IMPORT: '/data-import/import',
      LIST_IMPORTS: '/data-import/imports',
      AVAILABLE_TARGET_FIELDS: '/data-import/field-mapping/suggestions/available-target-fields',
      CRITICAL_ATTRIBUTES_STATUS: '/data-import/critical-attributes-status',
      CONTEXT_FIELD_MAPPINGS: '/data-import/context-field-mappings',
      SIMPLE_FIELD_MAPPINGS: '/data-import/simple-field-mappings',
      AGENT_CLARIFICATIONS: '/data-import/agent-clarifications'
    },
    MONITORING: {
      STATUS: '/monitoring/status',
      TASKS: '/monitoring/tasks',
      AGENTS: '/monitoring/agents',
      HEALTH: '/monitoring/health',
      METRICS: '/monitoring/metrics',
      CANCEL_TASK: '/monitoring/tasks'
    },
    ADMIN: {
      CLIENTS: '/api/v1/admin/clients',
      DEFAULT_CLIENT: '/context-establishment/clients', // Changed from /default to get all clients
      ENGAGEMENTS: '/api/v1/admin/engagements',
      USERS: '/api/v1/admin/users',
      USER_PROFILES: '/api/v1/admin/user-profiles',
      CLIENT_ACCESS: '/api/v1/admin/client-access',
      ENGAGEMENT_ACCESS: '/api/v1/admin/engagement-access'
    },
    AGENT_LEARNING: {
      LEARNING_STATISTICS: '/agent-learning/learning/stats',
      FIELD_MAPPING_LEARN: '/agent-learning/learning/field-mapping',
      FIELD_MAPPING_SUGGEST: '/agent-learning/learning/field-mapping/suggest',
      DATA_SOURCE_PATTERN: '/agent-learning/learning/data-source-pattern',
      QUALITY_ASSESSMENT: '/agent-learning/learning/quality-assessment',
      USER_PREFERENCES: '/agent-learning/learning/user-preferences',
      AGENT_PERFORMANCE: '/agent-learning/learning/agent-performance',
      HEALTH: '/agent-learning/health'
    },
    HEALTH: '/health',
    // SIXR Endpoints
    SIXR_ANALYSIS: '/sixr/analyze'
  }
};

// CC: External API request payload types for integration layer
export type ExternalApiRequestPayload = 
  | Record<string, unknown>
  | FormData
  | string
  | number
  | boolean
  | null
  | undefined;

/**
 * Enhanced API response for external integrations 
 */
export type ExternalApiResponse<TData = unknown> = ApiResponse<TData, ApiError>;

// Track in-flight requests to prevent duplicates
const pendingRequests = new Map<string, Promise<ExternalApiResponse>>();

// Enhanced rate limiting and caching system
interface CacheEntry<T = unknown> {
  data: T;
  timestamp: number;
  expiry: number;
}

interface RateLimitEntry {
  count: number;
  resetTime: number;
}

// Cache for API responses (5 minute default expiry)
const responseCache = new Map<string, CacheEntry<ExternalApiResponse>>();
// Rate limiting tracker per endpoint
const rateLimitTracker = new Map<string, RateLimitEntry>();

// Rate limit configuration
const RATE_LIMITS = {
  // Removed available-target-fields as it's now deprecated (using hardcoded list)
  'GET:/api/v1/data-import/field-mapping': { maxRequests: 5, windowMs: 30000 }, // 5 requests per 30s
  'GET:/api/v1/data-import/latest': { maxRequests: 10, windowMs: 60000 }, // 10 requests per minute
  'default': { maxRequests: 30, windowMs: 60000 } // Default: 30 requests per minute
};

// Cache configuration per endpoint
const CACHE_CONFIG = {
  // Removed available-target-fields as it's now deprecated (using hardcoded list)
  'GET:/api/v1/data-import/field-mapping': 60000, // 1 minute
  'GET:/api/v1/data-import/latest': 30000, // 30 seconds
  'default': 120000 // 2 minutes default
};

function isRateLimited(method: string, normalizedEndpoint: string): boolean {
  const key = `${method}:${normalizedEndpoint}`;
  const config = RATE_LIMITS[key] || RATE_LIMITS.default;
  const now = Date.now();
  
  let entry = rateLimitTracker.get(key);
  
  if (!entry || now > entry.resetTime) {
    // Reset or create new entry
    entry = { count: 0, resetTime: now + config.windowMs };
    rateLimitTracker.set(key, entry);
  }
  
  if (entry.count >= config.maxRequests) {
    console.warn(`Rate limit exceeded for ${key}. Reset at ${new Date(entry.resetTime).toISOString()}`);
    return true;
  }
  
  entry.count++;
  return false;
}

function getCachedResponse<T = unknown>(method: string, normalizedEndpoint: string): T | null {
  const key = `${method}:${normalizedEndpoint}`;
  const entry = responseCache.get(key);
  
  if (!entry) return null;
  
  const now = Date.now();
  if (now > entry.expiry) {
    responseCache.delete(key);
    return null;
  }
  
  console.log(`📋 Cache hit for ${key}, expires in ${Math.round((entry.expiry - now) / 1000)}s`);
  return entry.data;
}

function setCachedResponse<T = unknown>(method: string, normalizedEndpoint: string, data: T): void {
  const key = `${method}:${normalizedEndpoint}`;
  const config = CACHE_CONFIG[key] || CACHE_CONFIG.default;
  const expiry = Date.now() + config;
  
  responseCache.set(key, { data, timestamp: Date.now(), expiry });
  console.log(`💾 Cached response for ${key}, expires at ${new Date(expiry).toISOString()}`);
}

interface EnhancedApiError extends ApiError {
  status?: number;
  statusText?: string;
  response?: ExternalApiResponse;
  requestId?: string;
  isApiError: boolean;
  isRateLimited?: boolean;
  retryAfter?: number;
  isAuthError?: boolean;
  isForbidden?: boolean;
  isTimeout?: boolean;
}

// Extend RequestInit to include timeout and typed body
interface ApiRequestInit extends RequestInit {
  timeout?: number;
  body?: ExternalApiRequestPayload | string;
}

/**
 * Helper function to make API calls with proper error handling and authentication
 * @param endpoint The API endpoint to call
 * @param options Fetch options
 * @param includeContext Whether to include the current context in the request headers
 */
export const apiCall = async (
  endpoint: string, 
  options: ApiRequestInit = {}, 
  includeContext: boolean = true
): Promise<ExternalApiResponse> => {
  const requestId = Math.random().toString(36).substring(2, 8);
  const startTime = performance.now();
  
  // Log API call parameters for debugging
  console.log(`🔍 API Call [${requestId}] - endpoint="${endpoint}", includeContext=${includeContext}`);
  
  // Normalize endpoint - NO double prefixes
  let normalizedEndpoint: string;
  if (endpoint.startsWith('/api/v1') || endpoint.startsWith('/api/v2')) {
    // Endpoint already has version prefix - use as is
    normalizedEndpoint = endpoint;
  } else {
    // Add V1 prefix for legacy endpoints  
    normalizedEndpoint = `/api/v1${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  }
  
  const baseUrl = API_CONFIG.BASE_URL;
  const url = `${baseUrl}${normalizedEndpoint}`;
  const method = (options.method || 'GET').toUpperCase();
  
  // Debug: Log the URL being called
  console.log(`🔗 API Call [${requestId}] - baseUrl="${baseUrl}", url="${url}"`);
  
  // Safety check: If we're in development and the URL contains localhost:8000, force proxy
  if (typeof window !== 'undefined' && window.location.port === '8081' && url.includes('localhost:8000')) {
    console.warn(`⚠️ API Call [${requestId}] - Detected direct backend URL, forcing proxy`);
    const urlObj = new URL(url);
    const proxyUrl = urlObj.pathname + urlObj.search;
    console.log(`🔧 API Call [${requestId}] - Rewritten URL: ${proxyUrl}`);
    return apiCall(proxyUrl, options, includeContext);
  }
  
  // Create a unique key for this request to prevent duplicates
  // Exclude POST/PUT/PATCH/DELETE requests from deduplication as they can have side effects
  const requestKey = `${method}:${normalizedEndpoint}`;
  const shouldDeduplicate = ['GET', 'HEAD', 'OPTIONS'].includes(method);
  
  // Check cache first for GET requests
  if (shouldDeduplicate) {
    const cachedResponse = getCachedResponse(method, normalizedEndpoint);
    if (cachedResponse !== null) {
      return Promise.resolve(cachedResponse);
    }
    
    // Check rate limiting
    if (isRateLimited(method, normalizedEndpoint)) {
      const rateLimitError = new Error('Rate limit exceeded') as EnhancedApiError;
      rateLimitError.status = 429;
      rateLimitError.isRateLimited = true;
      rateLimitError.isApiError = true;
      rateLimitError.code = 'RATE_LIMIT_EXCEEDED';
      throw rateLimitError;
    }
  }
  
  // If we already have a request with the same key, return that instead (only for safe methods)
  if (shouldDeduplicate && pendingRequests.has(requestKey)) {
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
      // Add headers - start with defaults, then merge user headers
      const headers: HeadersInit = {
        'X-Request-ID': requestId,
      };
      
      // Only set default Content-Type for non-FormData requests
      // FormData uploads need the browser to set Content-Type with boundary
      if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
      }
      
      // Merge user headers last to allow overrides
      Object.assign(headers, options.headers);
      
      // Add auth token if available (don't override if user provided one)
      try {
        const token = localStorage.getItem('auth_token');
        if (token && !headers['Authorization']) {
          headers['Authorization'] = `Bearer ${token}`;
          console.log(`🔐 API Call [${requestId}] - Added auth token to headers`);
        } else if (!token) {
          console.warn(`⚠️ API Call [${requestId}] - No auth token found in localStorage`);
        } else {
          console.log(`🔐 API Call [${requestId}] - User provided Authorization header, not overriding`);
        }
      } catch (storageError) {
        console.warn(`⚠️ API Call [${requestId}] - Failed to access localStorage for auth token:`, storageError);
      }
      
      // Add context headers if needed
      if (includeContext) {
        try {
          console.log(`🏢 API Call [${requestId}] - Current context:`, currentContext);
          
          // Only add headers if the value exists and is not "null" string
          if (currentContext?.user?.id && currentContext.user.id !== 'null') {
            headers['X-User-ID'] = currentContext.user.id;
            console.log(`👤 API Call [${requestId}] - Added user ID: ${currentContext.user.id}`);
          } else {
            console.warn(`⚠️ API Call [${requestId}] - No user ID available for X-User-ID header`);
          }
          
          if (currentContext?.client?.id && currentContext.client.id !== 'null') {
            headers['X-Client-Account-ID'] = currentContext.client.id;
            console.log(`🏢 API Call [${requestId}] - Added client ID: ${currentContext.client.id}`);
          } else {
            console.warn(`⚠️ API Call [${requestId}] - No client or client_id available for X-Client-Account-ID header`);
          }
          
          if (currentContext?.engagement?.id && currentContext.engagement.id !== 'null') {
            headers['X-Engagement-ID'] = currentContext.engagement.id;
            console.log(`📋 API Call [${requestId}] - Added engagement ID: ${currentContext.engagement.id}`);
          } else {
            console.warn(`⚠️ API Call [${requestId}] - No engagement or engagement_id available for X-Engagement-ID header`);
          }
          
          if (currentContext?.flow?.id && currentContext.flow.id !== 'null') {
            headers['X-Flow-ID'] = currentContext.flow.id;
            console.log(`🔄 API Call [${requestId}] - Added flow ID: ${currentContext.flow.id}`);
          } else {
            console.log(`ℹ️ API Call [${requestId}] - No flow ID available, skipping X-Flow-ID header`);
          }
        } catch (contextError) {
          console.warn(`⚠️ API Call [${requestId}] - Failed to add context headers:`, contextError);
        }
      } else {
        console.log(`🚫 API Call [${requestId}] - Context headers skipped (includeContext=false)`);
      }
      
      // Log final headers being sent
      console.log(`🔗 API Call [${requestId}] - Final headers:`, headers);
      
      // Create abort controller for timeout
      const controller = new AbortController();
      
      // Determine timeout based on operation type
      // Agentic activities (classification, analysis, flow execution) have no timeout
      // UI interactions have reasonable timeouts
      const isAgenticActivity = (
        normalizedEndpoint.includes('/assets/list/paginated') ||
        normalizedEndpoint.includes('/discovery/flow/run') ||
        normalizedEndpoint.includes('/assets/analyze') ||
        normalizedEndpoint.includes('/asset_inventory') ||
        normalizedEndpoint.includes('/classification')
      );
      
      const timeoutMs = options.timeout || (
        isAgenticActivity ? null : // No timeout for agentic activities
        normalizedEndpoint.includes('/bulk') ? 180000 : // 3 minutes for bulk operations (UI-based)
        60000 // Default 1 minute for UI interactions
      );
      
      let timeoutId = null;
      if (timeoutMs !== null) {
        timeoutId = setTimeout(() => {
          controller.abort();
          console.error(`⏱️ API Call [${requestId}] - Timeout after ${timeoutMs}ms`);
        }, timeoutMs);
      } else {
        console.log(`🔄 API Call [${requestId}] - No timeout set for agentic activity`);
      }
      
      // Make the request with abort signal
      const response = await fetch(url, {
        ...options,
        method, // Ensure method is uppercase
        headers,
        credentials: 'include',
        signal: controller.signal,
      }).finally(() => {
        if (timeoutId !== null) {
          clearTimeout(timeoutId);
        }
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
        const error = new Error(data?.message || response.statusText || 'Request failed') as EnhancedApiError;
        error.status = response.status;
        error.statusText = response.statusText;
        error.response = data;
        error.requestId = requestId;
        error.isApiError = true;
        error.code = `HTTP_${response.status}`;
        error.message = data?.message || response.statusText || 'Request failed';
        
        // Special handling for different status codes
        if (response.status === 404) {
          console.warn(`[${requestId}] Resource not found: ${url}`);
        } else if (response.status === 429) {
          console.warn(`[${requestId}] Rate limited (429): ${url}`);
          error.isRateLimited = true;
          // Extract retry-after header if present
          const retryAfter = response.headers.get('Retry-After');
          if (retryAfter) {
            error.retryAfter = parseInt(retryAfter) * 1000; // Convert to ms
          } else {
            error.retryAfter = 2000; // Default 2s retry delay
          }
          console.log(`[${requestId}] Retry suggested after: ${error.retryAfter}ms`);
        } else if (response.status === 401) {
          console.warn(`[${requestId}] Authentication failed: ${url}`);
          error.isAuthError = true;
          
          // Handle token expiration by logging out
          console.warn('🔐 Token expired, logging out user');
          tokenStorage.removeToken();
          tokenStorage.setUser(null);
          localStorage.removeItem('auth_client');
          localStorage.removeItem('auth_engagement');
          localStorage.removeItem('auth_flow');
          sessionStorage.removeItem('auth_initialization_complete');
          
          // Redirect to login
          window.location.href = '/login';
        } else if (response.status === 403) {
          console.warn(`[${requestId}] Authorization failed: ${url}`);
          error.isForbidden = true;
        }
        
        throw error;
      }
      
      // Cache successful GET responses
      if (shouldDeduplicate && response.ok) {
        setCachedResponse(method, normalizedEndpoint, data);
      }
      
      return data;
    } catch (error) {
      const endTime = performance.now();
      const duration = (endTime - startTime).toFixed(2);
      
      let apiError: EnhancedApiError;
      
      // Handle timeout errors specifically
      if (error.name === 'AbortError') {
        apiError = new Error(`Request timed out after ${duration}ms. The server may be processing a large dataset.`) as EnhancedApiError;
        apiError.status = 408; // Request Timeout
        apiError.statusText = 'Request Timeout';
        apiError.requestId = requestId;
        apiError.isApiError = true;
        apiError.isTimeout = true;
        apiError.code = 'REQUEST_TIMEOUT';
        apiError.message = `Request timed out after ${duration}ms. The server may be processing a large dataset.`;
      } else if (error instanceof Error) {
        apiError = error as EnhancedApiError;
        apiError.isApiError = true;
        if (!apiError.code) {
          apiError.code = 'API_ERROR';
        }
      } else {
        apiError = new Error('Unknown API error') as EnhancedApiError;
        apiError.isApiError = true;
        apiError.code = 'UNKNOWN_ERROR';
        apiError.message = 'Unknown API error';
      }
      
      apiError.requestId = requestId;
      
      console.error(`API Call [${requestId}] failed after ${duration}ms:`, apiError);
      
      // Re-throw the enhanced error
      throw apiError;
    } finally {
      // Clean up the pending request (only if it was stored for deduplication)
      if (shouldDeduplicate) {
        pendingRequests.delete(requestKey);
      }
      console.groupEnd();
    }
  })();
  
  // Store the promise for deduplication (only for safe methods)
  if (shouldDeduplicate) {
    pendingRequests.set(requestKey, requestPromise);
  }
  
  return requestPromise;
};

/**
 * API call with fallback behavior - returns a structured response with success/error status
 * @param endpoint The API endpoint to call
 * @param options Fetch options
 * @param includeContext Whether to include the current context in the request headers
 */
export const apiCallWithFallback = async (
  endpoint: string, 
  options: ApiRequestInit = {}, 
  includeContext: boolean = true
): Promise<{ ok: boolean; status: string; data?: ExternalApiResponse; message?: string; json?: () => Promise<ExternalApiResponse> }> => {
  try {
    const data = await apiCall(endpoint, options, includeContext);
    
    // Return a structured response that mimics fetch Response object
    return {
      ok: true,
      status: 'success',
      data,
      json: async () => data
    };
  } catch (error) {
    console.error('API call failed, using fallback behavior:', error);
    
    const apiError = error as EnhancedApiError;
    return {
      ok: false,
      status: 'error',
      message: apiError.message || 'Request failed',
      json: async () => ({ 
        error: {
          code: apiError.code || 'UNKNOWN_ERROR',
          message: apiError.message || 'Request failed',
          details: apiError.details
        } as ApiError
      })
    };
  }
};