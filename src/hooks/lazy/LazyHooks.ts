/**
 * Lazy Hooks - Specific lazy-loaded hooks for the application
 */

import { useLazyHook, useConditionalLazyHook } from './useLazyHook';
import { LoadingPriority } from '@/types/lazy';

/**
 * Discovery-related lazy hooks
 */

// Lazy load attribute mapping logic
export const useLazyAttributeMappingLogic = (immediate = false) => {
  return useLazyHook(
    'attribute-mapping-logic',
    () => import('@/hooks/discovery/attribute-mapping/useAttributeMappingLogic'),
    {
      priority: LoadingPriority.HIGH,
      immediate,
      timeout: 20000
    }
  );
};

// Lazy load data cleansing logic
export const useLazyDataCleansingLogic = (immediate = false) => {
  return useLazyHook(
    'data-cleansing-logic',
    () => import('@/hooks/discovery/data-cleansing/useDataCleansingLogic'),
    {
      priority: LoadingPriority.NORMAL,
      immediate,
      timeout: 15000
    }
  );
};

// Lazy load discovery flow management
export const useLazyUnifiedDiscoveryFlow = (immediate = false) => {
  return useLazyHook(
    'unified-discovery-flow',
    () => import('@/hooks/useUnifiedDiscoveryFlow'),
    {
      priority: LoadingPriority.HIGH,
      immediate,
      timeout: 25000
    }
  );
};

/**
 * Assessment-related lazy hooks
 */

// Lazy load 6R analysis logic
export const useLazySixRAnalysis = (immediate = false) => {
  return useLazyHook(
    'sixr-analysis',
    () => import('@/hooks/useSixRAnalysis'),
    {
      priority: LoadingPriority.NORMAL,
      immediate,
      timeout: 20000
    }
  );
};

// Lazy load assessment flow logic
export const useLazyAssessmentFlow = (immediate = false) => {
  return useLazyHook(
    'assessment-flow',
    () => import('@/hooks/assessment/useAssessmentFlow'),
    {
      priority: LoadingPriority.HIGH,
      immediate,
      timeout: 20000
    }
  );
};

/**
 * Admin-related lazy hooks (LOW priority)
 */

// Lazy load admin management hooks
export const useLazyAdminManagement = (userIsAdmin: boolean, immediate = false) => {
  return useConditionalLazyHook(
    'admin-management',
    () => import('@/hooks/admin/useAdminManagement'),
    userIsAdmin,
    {
      priority: LoadingPriority.LOW,
      immediate: immediate && userIsAdmin,
      timeout: 15000
    }
  );
};

// Lazy load user management hooks
export const useLazyUserManagement = (userIsAdmin: boolean, immediate = false) => {
  return useConditionalLazyHook(
    'user-management',
    () => import('@/hooks/admin/useUserManagement'),
    userIsAdmin,
    {
      priority: LoadingPriority.LOW,
      immediate: immediate && userIsAdmin,
      timeout: 15000
    }
  );
};

/**
 * Utility and integration hooks
 */

// Lazy load API hooks
export const useLazyAPIHooks = (immediate = false) => {
  return useLazyHook(
    'api-hooks',
    () => import('@/hooks/api/useApiHooks'),
    {
      priority: LoadingPriority.NORMAL,
      immediate,
      timeout: 10000
    }
  );
};

// Lazy load form validation hooks
export const useLazyFormValidation = (immediate = false) => {
  return useLazyHook(
    'form-validation',
    () => import('@/hooks/validation/useFormValidation'),
    {
      priority: LoadingPriority.NORMAL,
      immediate,
      timeout: 10000
    }
  );
};

// Lazy load performance monitoring hooks
export const useLazyPerformanceMonitoring = (immediate = false) => {
  return useLazyHook(
    'performance-monitoring',
    () => import('@/hooks/monitoring/usePerformanceMonitoring'),
    {
      priority: LoadingPriority.LOW,
      immediate,
      timeout: 10000
    }
  );
};

/**
 * Advanced lazy hook patterns
 */

// Progressive hook loading - load basic functionality first, then enhanced features
export const useProgressiveLazyHook = <T extends Record<string, any>>(
  baseHookId: string,
  baseImport: () => Promise<{ default: T }>,
  enhancedHookId: string,
  enhancedImport: () => Promise<{ default: T }>,
  shouldLoadEnhanced: boolean,
  immediate = false
) => {
  const baseHook = useLazyHook(baseHookId, baseImport, {
    priority: LoadingPriority.HIGH,
    immediate
  });

  const enhancedHook = useConditionalLazyHook(
    enhancedHookId,
    enhancedImport,
    shouldLoadEnhanced && !!baseHook.hookModule,
    {
      priority: LoadingPriority.NORMAL,
      immediate: shouldLoadEnhanced && !!baseHook.hookModule
    }
  );

  return {
    hookModule: enhancedHook.hookModule || baseHook.hookModule,
    loading: baseHook.loading || enhancedHook.loading,
    error: enhancedHook.error || baseHook.error,
    isEnhanced: !!enhancedHook.hookModule,
    retry: () => {
      baseHook.retry();
      if (shouldLoadEnhanced) {
        enhancedHook.retry();
      }
    }
  };
};

// Batch hook loading for related functionality
export const useBatchLazyHooks = (
  hooks: Array<{
    id: string;
    import: () => Promise<any>;
    priority?: LoadingPriority;
  }>,
  immediate = false
) => {
  const hookResults = hooks.map(hook => 
    useLazyHook(hook.id, hook.import, {
      priority: hook.priority || LoadingPriority.NORMAL,
      immediate
    })
  );

  const allLoaded = hookResults.every(result => !!result.hookModule);
  const anyLoading = hookResults.some(result => result.loading);
  const anyError = hookResults.find(result => result.error);

  return {
    hooks: hookResults.map(result => result.hookModule),
    allLoaded,
    loading: anyLoading,
    error: anyError?.error || null,
    retryAll: () => hookResults.forEach(result => result.retry())
  };
};