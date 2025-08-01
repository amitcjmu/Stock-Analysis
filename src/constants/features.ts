/**
 * Feature flag constants for controlling feature availability
 */

export const FEATURES = {
  // Core features
  DISCOVERY: {
    ENABLED: true,
    ASSET_SCANNING: true,
    APPLICATION_DETECTION: true,
    DEPENDENCY_MAPPING: true,
    TECH_DEBT_ANALYSIS: true,
    READINESS_ASSESSMENT: true,
    AI_ANALYSIS: true,
    BULK_OPERATIONS: true,
    EXPORT_FUNCTIONALITY: true
  },

  // Collection features
  COLLECTION: {
    ENABLED: true,
    ADAPTIVE_FORMS: true,
    BULK_UPLOAD: true,
    DATA_VALIDATION: true,
    FIELD_MAPPING: true,
    AI_SUGGESTIONS: true,
    WORKFLOW_AUTOMATION: true,
    PROGRESS_MONITORING: true
  },

  // Assessment features
  ASSESSMENT: {
    ENABLED: true,
    SIXR_ANALYSIS: true,
    CUSTOM_ASSESSMENTS: true,
    REPORT_GENERATION: true,
    COLLABORATIVE_REVIEW: true,
    AI_RECOMMENDATIONS: true
  },

  // Agent features
  AGENTS: {
    ENABLED: true,
    LEARNING_MODE: true,
    PARALLEL_EXECUTION: true,
    CUSTOM_AGENTS: true,
    AGENT_MONITORING: true,
    PERFORMANCE_TRACKING: true
  },

  // Monitoring features
  MONITORING: {
    ENABLED: true,
    REAL_TIME_UPDATES: true,
    METRICS_DASHBOARD: true,
    ALERTING: true,
    HISTORICAL_DATA: true,
    EXPORT_METRICS: true
  },

  // Admin features
  ADMIN: {
    ENABLED: true,
    USER_MANAGEMENT: true,
    CLIENT_MANAGEMENT: true,
    ENGAGEMENT_MANAGEMENT: true,
    ROLE_BASED_ACCESS: true,
    AUDIT_LOGGING: true,
    SYSTEM_SETTINGS: true
  },

  // UI features
  UI: {
    DARK_MODE: true,
    RESPONSIVE_DESIGN: true,
    KEYBOARD_SHORTCUTS: true,
    TOOLTIPS: true,
    GUIDED_TOURS: true,
    CUSTOMIZABLE_DASHBOARD: true,
    ADVANCED_FILTERS: true,
    BULK_ACTIONS: true
  },

  // Integration features
  INTEGRATIONS: {
    API_ACCESS: true,
    WEBHOOKS: true,
    SSO: true,
    LDAP: true,
    EXTERNAL_STORAGE: true,
    THIRD_PARTY_TOOLS: true
  },

  // Cache and Performance features
  CACHE: {
    USE_GLOBAL_CONTEXT: false,
    DISABLE_CUSTOM_CACHE: false,
    ENABLE_WEBSOCKET_CACHE: false,
    ENABLE_CACHE_HEADERS: false,
    REACT_QUERY_OPTIMIZATIONS: false
  },

  // Experimental features
  EXPERIMENTAL: {
    BETA_FEATURES: false,
    AI_COPILOT: false,
    VOICE_COMMANDS: false,
    AR_VISUALIZATION: false,
    BLOCKCHAIN_AUDIT: false,
    QUANTUM_ANALYSIS: false
  },

  // Security features
  SECURITY: {
    TWO_FACTOR_AUTH: true,
    SESSION_MANAGEMENT: true,
    IP_WHITELISTING: true,
    ENCRYPTION_AT_REST: true,
    AUDIT_TRAIL: true,
    COMPLIANCE_MODE: true
  }
} as const;

// Feature availability by environment
export const FEATURE_ENVIRONMENTS = {
  DEVELOPMENT: {
    ...FEATURES,
    CACHE: {
      ...FEATURES.CACHE,
      DISABLE_CUSTOM_CACHE: true,  // Use new API client with Redis backend caching
      ENABLE_WEBSOCKET_CACHE: true,
      ENABLE_CACHE_HEADERS: true,
      REACT_QUERY_OPTIMIZATIONS: true
    },
    EXPERIMENTAL: {
      ...FEATURES.EXPERIMENTAL,
      BETA_FEATURES: true
    }
  },

  STAGING: {
    ...FEATURES,
    CACHE: {
      ...FEATURES.CACHE,
      ENABLE_WEBSOCKET_CACHE: true,
      ENABLE_CACHE_HEADERS: true
    },
    EXPERIMENTAL: {
      ...FEATURES.EXPERIMENTAL,
      BETA_FEATURES: true
    }
  },

  PRODUCTION: {
    ...FEATURES,
    EXPERIMENTAL: {
      ...FEATURES.EXPERIMENTAL,
      BETA_FEATURES: false
    }
  }
} as const;

// Feature dependencies
export const FEATURE_DEPENDENCIES = {
  'DISCOVERY.AI_ANALYSIS': ['AGENTS.ENABLED'],
  'COLLECTION.AI_SUGGESTIONS': ['AGENTS.ENABLED', 'AGENTS.LEARNING_MODE'],
  'ASSESSMENT.AI_RECOMMENDATIONS': ['AGENTS.ENABLED'],
  'MONITORING.REAL_TIME_UPDATES': ['MONITORING.ENABLED'],
  'ADMIN.AUDIT_LOGGING': ['SECURITY.AUDIT_TRAIL'],
  'UI.DARK_MODE': ['UI.RESPONSIVE_DESIGN']
} as const;

// Helper function to check if a feature is enabled
export const isFeatureEnabled = (featurePath: string): boolean => {
  const keys = featurePath.split('.');
  let current: unknown = FEATURES;

  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = (current as Record<string, unknown>)[key];
    } else {
      return false;
    }
  }

  return current === true;
};

// Helper function to get features for current environment
export const getFeaturesForEnvironment = (env: 'DEVELOPMENT' | 'STAGING' | 'PRODUCTION' = 'PRODUCTION'): unknown => {
  return FEATURE_ENVIRONMENTS[env];
};

// Helper function to get current environment features
export const getCurrentFeatures = (): unknown => {
  const env = import.meta.env.MODE === 'development' ? 'DEVELOPMENT' :
             import.meta.env.MODE === 'staging' ? 'STAGING' : 'PRODUCTION';
  return getFeaturesForEnvironment(env);
};

// Helper function to check cache features specifically
export const isCacheFeatureEnabled = (featureName: keyof typeof FEATURES.CACHE): boolean => {
  const currentFeatures = getCurrentFeatures() as typeof FEATURES;
  return currentFeatures.CACHE[featureName];
};
