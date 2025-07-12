/**
 * Global Type Declarations
 * 
 * Global TypeScript declarations and ambient module definitions
 * that extend the application's type system.
 */

// Global namespace declarations for module boundaries
declare global {
  namespace MigrationPlatform {
    namespace Types {
      // Module namespace references
      type DiscoveryFlow = import('./modules/discovery').DiscoveryFlow;
      type FlowOrchestration = import('./modules/flow-orchestration').FlowOrchestration;
      type SharedUtilities = import('./modules/shared-utilities').SharedUtilities;
      
      // Component type references
      type NavigationComponents = typeof import('./components/navigation');
      type DiscoveryComponents = typeof import('./components/discovery');
      type SharedComponents = typeof import('./components/shared');
      type FormComponents = typeof import('./components/forms');
      type LayoutComponents = typeof import('./components/layout');
      type DataDisplayComponents = typeof import('./components/data-display');
      type FeedbackComponents = typeof import('./components/feedback');
      type AdminComponents = typeof import('./components/admin');
      
      // Hook type references
      type DiscoveryHooks = typeof import('./hooks/discovery');
      type SharedHooks = typeof import('./hooks/shared');
      type APIHooks = typeof import('./hooks/api');
      type StateManagementHooks = typeof import('./hooks/state-management');
      type FlowOrchestrationHooks = typeof import('./hooks/flow-orchestration');
      type AdminHooks = typeof import('./hooks/admin');
      
      // API type references
      type DiscoveryAPI = typeof import('./api/discovery');
      type AssessmentAPI = typeof import('./api/assessment');
      type PlanningAPI = typeof import('./api/planning');
      type ExecutionAPI = typeof import('./api/execution');
      type ModernizeAPI = typeof import('./api/modernize');
      type FinOpsAPI = typeof import('./api/finops');
      type ObservabilityAPI = typeof import('./api/observability');
      type DecommissionAPI = typeof import('./api/decommission');
      type AdminAPI = typeof import('./api/admin');
      type AuthAPI = typeof import('./api/auth');
      type SharedAPI = typeof import('./api/shared');
    }
    
    namespace Utilities {
      type TypeGuards = typeof import('./guards');
      type ModuleBoundaries = typeof import('./index').MODULE_BOUNDARIES;
    }
  }
  
  // Global type utilities
  namespace TypeUtils {
    // Utility for creating branded types
    type Brand<T, B> = T & { __brand: B };
    
    // Flow ID branded type
    type FlowId = Brand<string, 'FlowId'>;
    type UserId = Brand<string, 'UserId'>;
    type ClientAccountId = Brand<string, 'ClientAccountId'>;
    type EngagementId = Brand<string, 'EngagementId'>;
    
    // Common utility types
    type Nullable<T> = T | null;
    type Optional<T> = T | undefined;
    type Maybe<T> = T | null | undefined;
    
    // Deep partial type
    type DeepPartial<T> = {
      [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
    };
    
    // Deep readonly type
    type DeepReadonly<T> = {
      readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P];
    };
    
    // Exact type (prevents excess properties)
    type Exact<T, U> = T & Record<Exclude<keyof U, keyof T>, never>;
    
    // Extract function parameter types
    type Parameters<T> = T extends (...args: infer P) => any ? P : never;
    
    // Extract function return type
    type ReturnType<T> = T extends (...args: any[]) => infer R ? R : any;
    
    // Extract promise type
    type PromiseType<T> = T extends Promise<infer P> ? P : T;
    
    // Extract array element type
    type ArrayElement<T> = T extends (infer U)[] ? U : never;
    
    // Create union from object values
    type ValueOf<T> = T[keyof T];
    
    // Create union from object keys
    type KeyOf<T> = keyof T;
    
    // Non-nullable version of a type
    type NonNullable<T> = T extends null | undefined ? never : T;
    
    // Required version of optional properties
    type RequireFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
    
    // Optional version of required properties
    type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
    
    // Mutable version of readonly type
    type Mutable<T> = {
      -readonly [P in keyof T]: T[P];
    };
    
    // Deep mutable version
    type DeepMutable<T> = {
      -readonly [P in keyof T]: T[P] extends object ? DeepMutable<T[P]> : T[P];
    };
  }
  
  // Environment-specific types
  namespace Environment {
    interface ProcessEnv {
      NODE_ENV: 'development' | 'production' | 'test';
      NEXT_PUBLIC_API_URL: string;
      NEXT_PUBLIC_API_V1_ONLY: string;
      DATABASE_URL: string;
      DEEPINFRA_API_KEY: string;
      CREWAI_ENABLED: string;
      ALLOWED_ORIGINS: string;
    }
  }
  
  // Window object extensions
  interface Window {
    __MIGRATION_PLATFORM_DEV__?: {
      typeGuards: typeof import('./guards').DEV_TYPE_GUARDS;
      moduleHelpers: typeof import('./index').DEV_HELPERS;
      typeSystem: typeof import('./index').TYPE_SYSTEM_METADATA;
    };
  }
}

// Ambient module declarations for external libraries
declare module 'react' {
  interface FunctionComponent<P = {}> {
    displayName?: string;
  }
}

// Custom module declarations
declare module '*.svg' {
  const content: string;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

declare module '*.webp' {
  const content: string;
  export default content;
}

declare module '*.css' {
  const classes: Record<string, string>;
  export default classes;
}

declare module '*.module.css' {
  const classes: Record<string, string>;
  export default classes;
}

declare module '*.scss' {
  const classes: Record<string, string>;
  export default classes;
}

declare module '*.module.scss' {
  const classes: Record<string, string>;
  export default classes;
}

// Type augmentations for popular libraries
declare module '@tanstack/react-query' {
  interface Register {
    defaultError: Error;
    queryMeta: {
      module?: keyof MigrationPlatform.Types;
      feature?: string;
      version?: string;
    };
    mutationMeta: {
      module?: keyof MigrationPlatform.Types;
      feature?: string;
      optimistic?: boolean;
    };
  }
}

// Export global types for use in other files
export type FlowId = TypeUtils.FlowId;
export type UserId = TypeUtils.UserId;
export type ClientAccountId = TypeUtils.ClientAccountId;
export type EngagementId = TypeUtils.EngagementId;

export type Nullable<T> = TypeUtils.Nullable<T>;
export type Optional<T> = TypeUtils.Optional<T>;
export type Maybe<T> = TypeUtils.Maybe<T>;
export type DeepPartial<T> = TypeUtils.DeepPartial<T>;
export type DeepReadonly<T> = TypeUtils.DeepReadonly<T>;
export type Exact<T, U> = TypeUtils.Exact<T, U>;
export type PromiseType<T> = TypeUtils.PromiseType<T>;
export type ArrayElement<T> = TypeUtils.ArrayElement<T>;
export type ValueOf<T> = TypeUtils.ValueOf<T>;
export type RequireFields<T, K extends keyof T> = TypeUtils.RequireFields<T, K>;
export type OptionalFields<T, K extends keyof T> = TypeUtils.OptionalFields<T, K>;
export type Mutable<T> = TypeUtils.Mutable<T>;
export type DeepMutable<T> = TypeUtils.DeepMutable<T>;

// Brand type creators
export const createFlowId = (id: string): FlowId => id as FlowId;
export const createUserId = (id: string): UserId => id as UserId;
export const createClientAccountId = (id: string): ClientAccountId => id as ClientAccountId;
export const createEngagementId = (id: string): EngagementId => id as EngagementId;

// Type assertion utilities
export const assertIsFlowId = (value: string): asserts value is FlowId => {
  if (!value || typeof value !== 'string') {
    throw new Error('Invalid FlowId');
  }
};

export const assertIsUserId = (value: string): asserts value is UserId => {
  if (!value || typeof value !== 'string') {
    throw new Error('Invalid UserId');
  }
};

export const assertIsClientAccountId = (value: string): asserts value is ClientAccountId => {
  if (!value || typeof value !== 'string') {
    throw new Error('Invalid ClientAccountId');
  }
};

export const assertIsEngagementId = (value: string): asserts value is EngagementId => {
  if (!value || typeof value !== 'string') {
    throw new Error('Invalid EngagementId');
  }
};

// Development mode type helpers
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  // Expose type system utilities in development
  window.__MIGRATION_PLATFORM_DEV__ = {
    get typeGuards() {
      return import('./guards').then(m => m.DEV_TYPE_GUARDS);
    },
    get moduleHelpers() {
      return import('./index').then(m => m.DEV_HELPERS);
    },
    get typeSystem() {
      return import('./index').then(m => m.TYPE_SYSTEM_METADATA);
    }
  } as any;
}

// Type system constants
export const TYPE_SYSTEM_CONSTANTS = {
  BOUNDARIES: {
    MODULES: ['DiscoveryFlow', 'FlowOrchestration', 'SharedUtilities'],
    COMPONENTS: ['navigation', 'discovery', 'shared', 'forms', 'layout', 'data-display', 'feedback', 'admin'],
    HOOKS: ['discovery', 'shared', 'api', 'state-management', 'flow-orchestration', 'admin'],
    API: ['discovery', 'assessment', 'planning', 'execution', 'modernize', 'finops', 'observability', 'decommission', 'admin', 'auth', 'shared']
  },
  PATTERNS: {
    FLOW_ID: /^[a-zA-Z0-9-_]+$/,
    USER_ID: /^[a-zA-Z0-9-_]+$/,
    CLIENT_ACCOUNT_ID: /^[a-zA-Z0-9-_]+$/,
    ENGAGEMENT_ID: /^[a-zA-Z0-9-_]+$/
  },
  VALIDATION: {
    MAX_STRING_LENGTH: 255,
    MAX_ARRAY_LENGTH: 1000,
    MAX_OBJECT_DEPTH: 10
  }
} as const;

// Export type for external use
export type TypeSystemConstants = typeof TYPE_SYSTEM_CONSTANTS;
