/**
 * TypeScript Module Boundaries - Main Entry Point
 * 
 * This is the main barrel export file that provides access to all type definitions
 * across the application. It enforces clear module boundaries and provides a
 * structured approach to importing types.
 * 
 * Usage:
 * ```typescript
 * // Import specific module namespaces
 * import { DiscoveryFlow, FlowOrchestration, SharedUtilities } from '@/types';
 * 
 * // Import component types
 * import { NavigationComponents, DiscoveryComponents, SharedComponents } from '@/types';
 * 
 * // Import hook types
 * import { DiscoveryHooks, SharedHooks, APIHooks } from '@/types';
 * 
 * // Import API types
 * import { DiscoveryAPI, AssessmentAPI, SharedAPI } from '@/types';
 * ```
 */

// Module Namespace Declarations
export * from './modules';

// Component Type Libraries
export type * from './components';

// Hook Type Definitions
export type * from './hooks';

// API Type Boundaries
export * from './api';

// Type Guards and Utilities
export * from './guards';

// Global Type Declarations
export * from './global';

// Re-export namespaces for convenience
export { 
  type DiscoveryFlow,
  type FlowOrchestration,
  type SharedUtilities 
} from './modules';

// Re-export component type groups
export type NavigationComponents = typeof import('./components/navigation');
export type DiscoveryComponents = typeof import('./components/discovery');
export type SharedComponents = typeof import('./components/shared');
export type FormComponents = typeof import('./components/forms');
export type LayoutComponents = typeof import('./components/layout');
export type DataDisplayComponents = typeof import('./components/data-display');
export type FeedbackComponents = typeof import('./components/feedback');
export type AdminComponents = typeof import('./components/admin');

// Re-export hook type groups
export type DiscoveryHooks = typeof import('./hooks/discovery');
export type SharedHooks = typeof import('./hooks/shared');
export type APIHooks = typeof import('./hooks/api');
export type StateManagementHooks = typeof import('./hooks/state-management');
export type FlowOrchestrationHooks = typeof import('./hooks/flow-orchestration');
export type AdminHooks = typeof import('./hooks/admin');

// Re-export API type groups
export type DiscoveryAPI = typeof import('./api/discovery');
export type AssessmentAPI = typeof import('./api/assessment');
export type PlanningAPI = typeof import('./api/planning');
export type ExecutionAPI = typeof import('./api/execution');
export type ModernizeAPI = typeof import('./api/modernize');
export type FinOpsAPI = typeof import('./api/finops');
export type ObservabilityAPI = typeof import('./api/observability');
export type DecommissionAPI = typeof import('./api/decommission');
export type AdminAPI = typeof import('./api/admin');
export type AuthAPI = typeof import('./api/auth');
export type SharedAPI = typeof import('./api/shared');

// Module boundary enforcement
export const MODULE_BOUNDARIES = {
  MODULES: [
    'DiscoveryFlow',
    'FlowOrchestration', 
    'SharedUtilities'
  ] as const,
  COMPONENTS: [
    'navigation',
    'discovery',
    'shared',
    'forms',
    'layout',
    'data-display',
    'feedback',
    'admin'
  ] as const,
  HOOKS: [
    'discovery',
    'shared',
    'api',
    'state-management',
    'flow-orchestration',
    'admin'
  ] as const,
  API: [
    'discovery',
    'assessment',
    'planning',
    'execution',
    'modernize',
    'finops',
    'observability',
    'decommission',
    'admin',
    'auth',
    'shared'
  ] as const
} as const;

// Type checking utilities
export type ModuleBoundaryType = keyof typeof MODULE_BOUNDARIES;
export type ModuleName<T extends ModuleBoundaryType> = typeof MODULE_BOUNDARIES[T][number];

// Validation functions for module boundaries
export const validateModuleBoundary = <T extends ModuleBoundaryType>(
  boundaryType: T,
  moduleName: string
): moduleName is ModuleName<T> => {
  return (MODULE_BOUNDARIES[boundaryType] as readonly string[]).includes(moduleName);
};

export const getAvailableModules = <T extends ModuleBoundaryType>(
  boundaryType: T
): ReadonlyArray<ModuleName<T>> => {
  return MODULE_BOUNDARIES[boundaryType];
};

// Type-safe module import utilities
export const createModuleImporter = <T extends ModuleBoundaryType>(
  boundaryType: T
) => {
  return {
    validate: (moduleName: string): moduleName is ModuleName<T> => 
      validateModuleBoundary(boundaryType, moduleName),
    getAvailable: (): ReadonlyArray<ModuleName<T>> => 
      getAvailableModules(boundaryType),
    importModule: async (moduleName: ModuleName<T>) => {
      switch (boundaryType) {
        case 'MODULES':
          return import(`./modules/${moduleName.toLowerCase()}`);
        case 'COMPONENTS':
          return import(`./components/${moduleName}`);
        case 'HOOKS':
          return import(`./hooks/${moduleName}`);
        case 'API':
          return import(`./api/${moduleName}`);
        default:
          throw new Error(`Unknown boundary type: ${boundaryType}`);
      }
    }
  };
};

// Pre-configured importers
export const ModuleImporter = createModuleImporter('MODULES');
export const ComponentImporter = createModuleImporter('COMPONENTS');
export const HookImporter = createModuleImporter('HOOKS');
export const APIImporter = createModuleImporter('API');

// Development helpers
export const DEV_HELPERS = {
  listAllTypes: () => {
    console.group('Available Type Modules');
    console.log('Modules:', MODULE_BOUNDARIES.MODULES);
    console.log('Components:', MODULE_BOUNDARIES.COMPONENTS);
    console.log('Hooks:', MODULE_BOUNDARIES.HOOKS);
    console.log('API:', MODULE_BOUNDARIES.API);
    console.groupEnd();
  },
  validateImport: (category: string, module: string) => {
    const isValid = Object.entries(MODULE_BOUNDARIES).some(([key, modules]) => 
      key.toLowerCase() === category.toLowerCase() && (modules as readonly string[]).includes(module)
    );
    if (!isValid) {
      console.warn(
        `Invalid import: ${category}/${module}. ` +
        `Available options: ${Object.entries(MODULE_BOUNDARIES)
          .map(([key, mods]) => `${key}: [${mods.join(', ')}]`)
          .join(', ')}`
      );
    }
    return isValid;
  }
} as const;

// TypeScript utility types for better developer experience
export type TypeImport<
  TBoundary extends ModuleBoundaryType,
  TModule extends ModuleName<TBoundary>
> = TBoundary extends 'MODULES'
  ? typeof import(`./modules/${Lowercase<TModule>}`)
  : TBoundary extends 'COMPONENTS'
  ? typeof import(`./components/${TModule}`)
  : TBoundary extends 'HOOKS'
  ? typeof import(`./hooks/${TModule}`)
  : TBoundary extends 'API'
  ? typeof import(`./api/${TModule}`)
  : never;

// Strict type imports (compile-time enforcement)
export type StrictModuleImport<T extends ModuleName<'MODULES'>> = TypeImport<'MODULES', T>;
export type StrictComponentImport<T extends ModuleName<'COMPONENTS'>> = TypeImport<'COMPONENTS', T>;
export type StrictHookImport<T extends ModuleName<'HOOKS'>> = TypeImport<'HOOKS', T>;
export type StrictAPIImport<T extends ModuleName<'API'>> = TypeImport<'API', T>;

// Version information
export const TYPE_SYSTEM_VERSION = '1.0.0';
export const TYPE_SYSTEM_BUILD = new Date().toISOString();

// Metadata for the type system
export const TYPE_SYSTEM_METADATA = {
  version: TYPE_SYSTEM_VERSION,
  build: TYPE_SYSTEM_BUILD,
  boundaries: MODULE_BOUNDARIES,
  description: 'TypeScript module boundaries and namespace organization system',
  features: [
    'Module namespace declarations',
    'Component type libraries', 
    'Hook type definitions',
    'API type boundaries',
    'Barrel exports',
    'Module boundary enforcement',
    'Type-safe imports',
    'Development helpers'
  ] as const
} as const;
