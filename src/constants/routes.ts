/**
 * Application route constants
 */

export const ROUTES = {
  // Root routes
  ROOT: '/',
  HOME: '/home',
  DASHBOARD: '/dashboard',
  
  // Auth routes
  AUTH: {
    LOGIN: '/login',
    LOGOUT: '/logout',
    REGISTER: '/register',
    FORGOT_PASSWORD: '/forgot-password',
    RESET_PASSWORD: '/reset-password'
  },
  
  // Collection routes
  COLLECTION: {
    ROOT: '/collection',
    OVERVIEW: '/collection/overview',
    ADAPTIVE_FORMS: '/collection/adaptive-forms',
    BULK_UPLOAD: '/collection/bulk-upload',
    INTEGRATION: '/collection/integration',
    PROGRESS: '/collection/progress',
    FLOW_MANAGEMENT: '/collection/flow-management'
  },
  
  // Discovery routes
  DISCOVERY: {
    ROOT: '/discovery',
    ASSETS: '/discovery/assets',
    APPLICATIONS: '/discovery/applications',
    DEPENDENCIES: '/discovery/dependencies',
    ANALYSIS: '/discovery/analysis',
    TECH_DEBT: '/discovery/tech-debt',
    READINESS: '/discovery/readiness'
  },
  
  // Admin routes
  ADMIN: {
    ROOT: '/admin',
    USERS: '/admin/users',
    CLIENTS: '/admin/clients',
    ENGAGEMENTS: '/admin/engagements',
    SETTINGS: '/admin/settings',
    PERMISSIONS: '/admin/permissions'
  },
  
  // Monitoring routes
  MONITORING: {
    ROOT: '/monitoring',
    AGENTS: '/monitoring/agents',
    WORKFLOWS: '/monitoring/workflows',
    METRICS: '/monitoring/metrics',
    HEALTH: '/monitoring/health'
  },
  
  // Assessment routes
  ASSESSMENT: {
    ROOT: '/assessment',
    SIXR: '/assessment/sixr',
    REPORTS: '/assessment/reports'
  },
  
  // Profile routes
  PROFILE: {
    ROOT: '/profile',
    SETTINGS: '/profile/settings',
    PREFERENCES: '/profile/preferences'
  },
  
  // Error routes
  ERROR: {
    NOT_FOUND: '/404',
    UNAUTHORIZED: '/401',
    FORBIDDEN: '/403',
    SERVER_ERROR: '/500'
  }
} as const;

// Route parameters
export const ROUTE_PARAMS = {
  ID: ':id',
  CLIENT_ID: ':clientId',
  ENGAGEMENT_ID: ':engagementId',
  FLOW_ID: ':flowId',
  ASSET_ID: ':assetId',
  USER_ID: ':userId'
} as const;

// Route guards/permissions
export const ROUTE_PERMISSIONS = {
  PUBLIC: ['AUTH.LOGIN', 'AUTH.REGISTER', 'AUTH.FORGOT_PASSWORD'],
  AUTHENTICATED: ['HOME', 'DASHBOARD', 'PROFILE.ROOT'],
  ADMIN_ONLY: ['ADMIN.ROOT', 'ADMIN.USERS', 'ADMIN.PERMISSIONS'],
  CLIENT_ACCESS: ['DISCOVERY.ROOT', 'COLLECTION.ROOT', 'ASSESSMENT.ROOT']
} as const;