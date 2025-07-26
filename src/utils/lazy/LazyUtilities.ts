/**
 * Lazy Utilities - Utility-level code splitting for heavy utility modules
 */

import type { LazyUtilityModule } from '@/types/lazy'
import { LoadingPriority } from '@/types/lazy'
import type { loadingManager } from './loadingManager';

interface LazyUtilityOptions {
  priority?: LoadingPriority;
  timeout?: number;
  cache?: boolean;
  retryAttempts?: number;
}

class LazyUtilityManager {
  private static instance: LazyUtilityManager;
  private utilityCache = new Map<string, unknown>();
  private loadingPromises = new Map<string, Promise<unknown>>();

  private constructor() {}

  static getInstance(): LazyUtilityManager {
    if (!LazyUtilityManager.instance) {
      LazyUtilityManager.instance = new LazyUtilityManager();
    }
    return LazyUtilityManager.instance;
  }

  async loadUtility<T = unknown>(
    utilityId: string,
    importFn: () => Promise<LazyUtilityModule<T>>,
    options: LazyUtilityOptions = {}
  ): Promise<T> {
    const {
      priority = LoadingPriority.NORMAL,
      timeout = 10000,
      cache = true,
      retryAttempts = 2
    } = options;

    // Check cache first
    if (cache && this.utilityCache.has(utilityId)) {
      return this.utilityCache.get(utilityId);
    }

    // Check if already loading
    if (this.loadingPromises.has(utilityId)) {
      return this.loadingPromises.get(utilityId);
    }

    // Create loading promise
    const loadingPromise = this.loadWithRetry(
      utilityId,
      importFn,
      retryAttempts,
      timeout,
      cache
    );

    this.loadingPromises.set(utilityId, loadingPromise);

    try {
      const utility = await loadingPromise;
      return utility;
    } finally {
      this.loadingPromises.delete(utilityId);
    }
  }

  private async loadWithRetry<T>(
    utilityId: string,
    importFn: () => Promise<LazyUtilityModule<T>>,
    maxRetries: number,
    timeout: number,
    cache: boolean
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const startTime = performance.now();

        const utilityModule = await Promise.race([
          importFn(),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Utility load timeout')), timeout)
          )
        ]);

        const endTime = performance.now();
        console.debug(`Utility ${utilityId} loaded in ${endTime - startTime}ms`);

        const utility = utilityModule as T;

        // Cache if enabled
        if (cache) {
          this.utilityCache.set(utilityId, utility);
        }

        return utility;
      } catch (error) {
        lastError = error as Error;

        // Exponential backoff for retries
        if (attempt < maxRetries) {
          await this.delay(Math.pow(2, attempt) * 500);
        }
      }
    }

    throw lastError;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  clearCache(): void {
    this.utilityCache.clear();
  }

  getCacheSize(): number {
    return this.utilityCache.size;
  }
}

const lazyUtilityManager = LazyUtilityManager.getInstance();

/**
 * Utility loading functions for different categories
 */

// API Utilities
export const loadAPIUtils = (): Promise<unknown> =>
  lazyUtilityManager.loadUtility(
    'api-utils',
    () => import('@/utils/api'),
    { priority: LoadingPriority.HIGH, cache: true }
  );

export const loadHTTPClient = (): Promise<unknown> =>
  lazyUtilityManager.loadUtility(
    'http-client',
    () => import('@/utils/api/httpClient'),
    { priority: LoadingPriority.HIGH, cache: true }
  );

// Data Processing Utilities
export const loadDataCleansingUtils = (): Promise<unknown> =>
  lazyUtilityManager.loadUtility(
    'data-cleansing-utils',
    () => import('@/utils/dataCleansingUtils'),
    { priority: LoadingPriority.NORMAL, cache: true }
  );

// Data Processing Utilities - Currently not implemented
// export const loadCSVProcessor = () =>
//   lazyUtilityManager.loadUtility(
//     'csv-processor',
//     () => import('@/utils/data/csvProcessor'),
//     { priority: LoadingPriority.NORMAL, cache: true }
//   );

// export const loadDataValidator = () =>
//   lazyUtilityManager.loadUtility(
//     'data-validator',
//     () => import('@/utils/validation/dataValidator'),
//     { priority: LoadingPriority.NORMAL, cache: true }
//   );

// File Processing Utilities - Currently not implemented
// export const loadFileProcessor = () =>
//   lazyUtilityManager.loadUtility(
//     'file-processor',
//     () => import('@/utils/file/fileProcessor'),
//     { priority: LoadingPriority.NORMAL, cache: true }
//   );

// export const loadExcelProcessor = () =>
//   lazyUtilityManager.loadUtility(
//     'excel-processor',
//     () => import('@/utils/file/excelProcessor'),
//     { priority: LoadingPriority.NORMAL, cache: true }
//   );

// Formatting and Display Utilities
export const loadMarkdownUtils = (): Promise<unknown> =>
  lazyUtilityManager.loadUtility(
    'markdown-utils',
    () => import('@/utils/markdown'),
    { priority: LoadingPriority.LOW, cache: true }
  );

// Date and Formatting Utilities - Currently not implemented
// export const loadDateUtils = () =>
//   lazyUtilityManager.loadUtility(
//     'date-utils',
//     () => import('@/utils/date/dateUtils'),
//     { priority: LoadingPriority.NORMAL, cache: true }
//   );

// export const loadNumberFormatter = () =>
//   lazyUtilityManager.loadUtility(
//     'number-formatter',
//     () => import('@/utils/formatting/numberFormatter'),
//     { priority: LoadingPriority.NORMAL, cache: true }
//   );

// Chart and Visualization Utilities - Currently not implemented
// export const loadChartUtils = () =>
//   lazyUtilityManager.loadUtility(
//     'chart-utils',
//     () => import('@/utils/charts/chartUtils'),
//     { priority: LoadingPriority.LOW, cache: true }
//   );

// Visualization Utilities - Currently not implemented
// export const loadVisualizationHelpers = () =>
//   lazyUtilityManager.loadUtility(
//     'visualization-helpers',
//     () => import('@/utils/visualization/helpers'),
//     { priority: LoadingPriority.LOW, cache: true }
//   );

// Analytics and Tracking Utilities - Currently not implemented
// export const loadAnalyticsUtils = () =>
//   lazyUtilityManager.loadUtility(
//     'analytics-utils',
//     () => import('@/utils/analytics/analyticsUtils'),
//     { priority: LoadingPriority.LOW, cache: true }
//   );

// export const loadPerformanceTracker = () =>
//   lazyUtilityManager.loadUtility(
//     'performance-tracker',
//     () => import('@/utils/performance/performanceTracker'),
//     { priority: LoadingPriority.LOW, cache: true }
//   );

// Security and Validation Utilities - Currently not implemented
// export const loadSecurityUtils = () =>
//   lazyUtilityManager.loadUtility(
//     'security-utils',
//     () => import('@/utils/security/securityUtils'),
//     { priority: LoadingPriority.HIGH, cache: true }
//   );

// export const loadInputSanitizer = () =>
//   lazyUtilityManager.loadUtility(
//     'input-sanitizer',
//     () => import('@/utils/security/inputSanitizer'),
//     { priority: LoadingPriority.HIGH, cache: true }
//   );

// Migration and Transform Utilities - Currently not implemented
// export const loadSessionToFlowMigration = () =>
//   lazyUtilityManager.loadUtility(
//     'session-to-flow-migration',
//     () => import('@/utils/migration/sessionToFlow'),
//     { priority: LoadingPriority.NORMAL, cache: true }
//   );

// export const loadDataTransformers = () =>
//   lazyUtilityManager.loadUtility(
//     'data-transformers',
//     () => import('@/utils/transform/dataTransformers'),
//     { priority: LoadingPriority.NORMAL, cache: true }
//   );

// Version and Compatibility Utilities
export const loadVersionUtils = (): Promise<unknown> =>
  lazyUtilityManager.loadUtility(
    'version-utils',
    () => import('@/utils/version'),
    { priority: LoadingPriority.LOW, cache: true }
  );

// export const loadBrowserCompatibility = () =>
//   lazyUtilityManager.loadUtility(
//     'browser-compatibility',
//     () => import('@/utils/compatibility/browserCheck'),
//     { priority: LoadingPriority.LOW, cache: true }
//   );

/**
 * Conditional utility loading based on environment or feature flags - Currently not implemented
 */
// export const loadDevUtilities = (): JSX.Element => {
//   if (process.env.NODE_ENV === 'development') {
//     return lazyUtilityManager.loadUtility(
//       'dev-utilities',
//       () => import('@/utils/dev/devUtils'),
//       { priority: LoadingPriority.LOW, cache: true }
//     );
//   }
//   return Promise.resolve(null);
// };

// export const loadTestUtilities = (): JSX.Element => {
//   if (process.env.NODE_ENV === 'test') {
//     return lazyUtilityManager.loadUtility(
//       'test-utilities',
//       () => import('@/utils/test/testUtils'),
//       { priority: LoadingPriority.LOW, cache: true }
//     );
//   }
//   return Promise.resolve(null);
// };

/**
 * Batch utility loading for related functionality - Using available utilities only
 */
export const loadDiscoveryUtilities = async (): Promise<unknown[]> => {
  return Promise.all([
    loadDataCleansingUtils(),
    // loadCSVProcessor(), // Not implemented
    // loadDataValidator(), // Not implemented
    // loadFileProcessor() // Not implemented
  ]);
};

export const loadAssessmentUtilities = async (): Promise<unknown[]> => {
  return Promise.all([
    // loadDataTransformers(), // Not implemented
    // loadAnalyticsUtils(), // Not implemented
    // loadNumberFormatter() // Not implemented
    loadMarkdownUtils()
  ]);
};

export const loadAdminUtilities = async (): Promise<unknown[]> => {
  return Promise.all([
    // loadSecurityUtils(), // Not implemented
    // loadInputSanitizer(), // Not implemented
    // loadAnalyticsUtils(), // Not implemented
    // loadPerformanceTracker() // Not implemented
    loadVersionUtils()
  ]);
};

/**
 * Utility cache management
 */
export const clearUtilityCache = (): void => {
  lazyUtilityManager.clearCache();
};

export const getUtilityCacheSize = (): number => {
  return lazyUtilityManager.getCacheSize();
};

export const getUtilityCacheStats = (): {
  cacheSize: number;
  memoryUsage: { used: number; total: number; } | null;
} => {
  return {
    cacheSize: lazyUtilityManager.getCacheSize(),
    memoryUsage: (performance as Performance & { memory?: { usedJSHeapSize: number; totalJSHeapSize: number } }).memory ? {
      used: Math.round((performance as Performance & { memory: { usedJSHeapSize: number; totalJSHeapSize: number } }).memory.usedJSHeapSize / 1024 / 1024),
      total: Math.round((performance as Performance & { memory: { usedJSHeapSize: number; totalJSHeapSize: number } }).memory.totalJSHeapSize / 1024 / 1024)
    } : null
  };
};
