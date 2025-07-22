/**
 * Global Type Declarations
 * 
 * Global TypeScript declarations and ambient module definitions
 * that extend the application's type system.
 */

// Global interface merging for module boundaries
declare global {
  interface MigrationPlatform {
    Types: typeof import('./platform-types');
    Utilities: {
      TypeGuards: typeof import('./guards');
      ModuleBoundaries: typeof import('./index').MODULE_BOUNDARIES;
    };
  }
  
  // Global type utilities interface
  interface TypeUtils {
    // Re-export from type-utils module
    Brand: typeof import('./type-utils').Brand;
    FlowId: typeof import('./type-utils').FlowId;
    UserId: typeof import('./type-utils').UserId;
    ClientAccountId: typeof import('./type-utils').ClientAccountId;
    EngagementId: typeof import('./type-utils').EngagementId;
    Nullable: typeof import('./type-utils').Nullable;
    Optional: typeof import('./type-utils').Optional;
    Maybe: typeof import('./type-utils').Maybe;
    DeepPartial: typeof import('./type-utils').DeepPartial;
    DeepReadonly: typeof import('./type-utils').DeepReadonly;
    Exact: typeof import('./type-utils').Exact;
    Parameters: typeof import('./type-utils').Parameters;
    ReturnType: typeof import('./type-utils').ReturnType;
    PromiseType: typeof import('./type-utils').PromiseType;
    ArrayElement: typeof import('./type-utils').ArrayElement;
    ValueOf: typeof import('./type-utils').ValueOf;
    KeyOf: typeof import('./type-utils').KeyOf;
    NonNullable: typeof import('./type-utils').NonNullable;
    RequireFields: typeof import('./type-utils').RequireFields;
    OptionalFields: typeof import('./type-utils').OptionalFields;
    Mutable: typeof import('./type-utils').Mutable;
    DeepMutable: typeof import('./type-utils').DeepMutable;
  }
  
  // Environment-specific types
  interface Environment {
    ProcessEnv: {
      NODE_ENV: 'development' | 'production' | 'test';
      NEXT_PUBLIC_API_URL: string;
      NEXT_PUBLIC_API_V1_ONLY: string;
      DATABASE_URL: string;
      DEEPINFRA_API_KEY: string;
      CREWAI_ENABLED: string;
      ALLOWED_ORIGINS: string;
    };
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
      module?: string;
      feature?: string;
      version?: string;
    };
    mutationMeta: {
      module?: string;
      feature?: string;
      optimistic?: boolean;
    };
  }
}

// Export global types for use in other files
export type {
  FlowId,
  UserId,
  ClientAccountId,
  EngagementId,
  Nullable,
  Optional,
  Maybe,
  DeepPartial,
  DeepReadonly,
  Exact,
  PromiseType,
  ArrayElement,
  ValueOf,
  RequireFields,
  OptionalFields,
  Mutable,
  DeepMutable
} from './type-utils';

// Brand type creators
import type { FlowId, UserId, ClientAccountId, EngagementId } from './type-utils';

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
  };
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
