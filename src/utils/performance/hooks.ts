import { useEffect, useRef, useState, useCallback } from 'react';
import type { RenderPerformance } from './monitoring';
import { performanceMonitor } from './monitoring';
import { useGlobalPerformance } from '../../contexts/GlobalContext';

/**
 * Hook for tracking component render performance
 */
export const useRenderPerformance = (componentName: string) => {
  const { enabled, updateMetrics } = useGlobalPerformance();
  const renderStartTime = useRef<number>(0);
  const renderCount = useRef<number>(0);
  const lastPropsRef = useRef<Record<string, unknown> | null>(null);
  const lastStateRef = useRef<Record<string, unknown> | null>(null);

  // Start timing on each render
  if (enabled) {
    renderStartTime.current = performance.now();
    renderCount.current += 1;
  }

  useEffect(() => {
    if (!enabled) return;

    const endTime = performance.now();
    const renderTime = endTime - renderStartTime.current;

    const renderPerformance: RenderPerformance = {
      componentName,
      renderTime,
      propsChanged: false, // Would need deep comparison
      stateChanged: false, // Would need state tracking
      timestamp: renderStartTime.current,
    };

    performanceMonitor.recordRender(renderPerformance);

    // Update global metrics
    updateMetrics({
      lastRenderTime: renderTime,
      renderCount: renderCount.current,
    });
  });

  return {
    renderCount: renderCount.current,
    markStart: useCallback((label: string) => {
      if (enabled) {
        performanceMonitor.markStart(`${componentName}-${label}`);
      }
    }, [componentName, enabled]),

    markEnd: useCallback((label: string) => {
      if (enabled) {
        return performanceMonitor.markEnd(`${componentName}-${label}`);
      }
      return null;
    }, [componentName, enabled]),
  };
};

/**
 * Hook for tracking API call performance
 */
export const useApiPerformance = () => {
  const { enabled, updateMetrics } = useGlobalPerformance();
  const apiCallCount = useRef<number>(0);

  const trackApiCall = useCallback(async <T>(
    label: string,
    apiCall: () => Promise<T>,
    metadata?: Record<string, unknown>
  ): Promise<T> => {
    if (!enabled) {
      return apiCall();
    }

    performanceMonitor.markStart(`api-${label}`);
    apiCallCount.current += 1;

    try {
      const result = await apiCall();

      performanceMonitor.markEnd(`api-${label}`, {
        ...metadata,
        success: true,
        apiCallCount: apiCallCount.current,
      });

      updateMetrics({
        apiCallCount: apiCallCount.current,
      });

      return result;
    } catch (error) {
      performanceMonitor.markEnd(`api-${label}`, {
        ...metadata,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        apiCallCount: apiCallCount.current,
      });

      updateMetrics({
        apiCallCount: apiCallCount.current,
      });

      throw error;
    }
  }, [enabled, updateMetrics]);

  return {
    trackApiCall,
    apiCallCount: apiCallCount.current,
  };
};

/**
 * Hook for tracking cache performance
 */
export const useCachePerformance = () => {
  const { enabled, updateMetrics } = useGlobalPerformance();
  const cacheHits = useRef<number>(0);
  const cacheMisses = useRef<number>(0);

  const trackCacheHit = useCallback((key: string, metadata?: Record<string, unknown>) => {
    if (!enabled) return;

    cacheHits.current += 1;

    performanceMonitor.recordEvent({
      name: 'cache-hit',
      duration: 0,
      timestamp: performance.now(),
      metadata: {
        key,
        hit: true,
        ...metadata,
      },
    });

    const hitRate = cacheHits.current / (cacheHits.current + cacheMisses.current);
    updateMetrics({ cacheHitRate: hitRate });
  }, [enabled, updateMetrics]);

  const trackCacheMiss = useCallback((key: string, metadata?: Record<string, unknown>) => {
    if (!enabled) return;

    cacheMisses.current += 1;

    performanceMonitor.recordEvent({
      name: 'cache-miss',
      duration: 0,
      timestamp: performance.now(),
      metadata: {
        key,
        hit: false,
        ...metadata,
      },
    });

    const hitRate = cacheHits.current / (cacheHits.current + cacheMisses.current);
    updateMetrics({ cacheHitRate: hitRate });
  }, [enabled, updateMetrics]);

  return {
    trackCacheHit,
    trackCacheMiss,
    cacheHits: cacheHits.current,
    cacheMisses: cacheMisses.current,
    hitRate: cacheHits.current / (cacheHits.current + cacheMisses.current) || 0,
  };
};

/**
 * Hook for tracking bundle loading performance
 */
export const useBundlePerformance = () => {
  const { enabled } = useGlobalPerformance();
  const [loadingStats, setLoadingStats] = useState<{
    totalBundles: number;
    loadedBundles: number;
    failedBundles: number;
    averageLoadTime: number;
  }>({
    totalBundles: 0,
    loadedBundles: 0,
    failedBundles: 0,
    averageLoadTime: 0,
  });

  const trackBundleLoad = useCallback(async <T>(
    bundleName: string,
    importFn: () => Promise<T>
  ): Promise<T> => {
    if (!enabled) {
      return importFn();
    }

    const startTime = performance.now();

    setLoadingStats(prev => ({
      ...prev,
      totalBundles: prev.totalBundles + 1,
    }));

    try {
      const result = await importFn();
      const loadTime = performance.now() - startTime;

      performanceMonitor.recordEvent({
        name: 'bundle-load',
        duration: loadTime,
        timestamp: startTime,
        metadata: {
          bundleName,
          success: true,
        },
      });

      setLoadingStats(prev => {
        const newLoadedCount = prev.loadedBundles + 1;
        const newAverageLoadTime =
          (prev.averageLoadTime * prev.loadedBundles + loadTime) / newLoadedCount;

        return {
          ...prev,
          loadedBundles: newLoadedCount,
          averageLoadTime: newAverageLoadTime,
        };
      });

      return result;
    } catch (error) {
      const loadTime = performance.now() - startTime;

      performanceMonitor.recordEvent({
        name: 'bundle-load',
        duration: loadTime,
        timestamp: startTime,
        metadata: {
          bundleName,
          success: false,
          error: error instanceof Error ? error.message : 'Bundle load failed',
        },
      });

      setLoadingStats(prev => ({
        ...prev,
        failedBundles: prev.failedBundles + 1,
      }));

      throw error;
    }
  }, [enabled]);

  return {
    trackBundleLoad,
    loadingStats,
  };
};

/**
 * Hook for monitoring memory usage
 */
export const useMemoryMonitoring = (intervalMs: number = 30000) => {
  const { enabled } = useGlobalPerformance();
  const [memoryStats, setMemoryStats] = useState<{
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
    timestamp: number;
  } | null>(null);

  useEffect(() => {
    if (!enabled || !('memory' in performance)) return;

    const checkMemory = () => {
      const memory = (performance as { memory?: { usedJSHeapSize: number; totalJSHeapSize: number; jsHeapSizeLimit: number } }).memory;
      if (memory) {
        const stats = {
          usedJSHeapSize: memory.usedJSHeapSize,
          totalJSHeapSize: memory.totalJSHeapSize,
          jsHeapSizeLimit: memory.jsHeapSizeLimit,
          timestamp: Date.now(),
        };

        setMemoryStats(stats);

        performanceMonitor.recordEvent({
          name: 'memory-usage',
          duration: 0,
          timestamp: performance.now(),
          metadata: stats,
        });
      }
    };

    checkMemory(); // Initial check
    const interval = setInterval(checkMemory, intervalMs);

    return () => clearInterval(interval);
  }, [enabled, intervalMs]);

  return memoryStats;
};

/**
 * Hook for tracking route transitions
 */
export const useRoutePerformance = () => {
  const { enabled } = useGlobalPerformance();
  const routeStartTime = useRef<number>(0);

  const startRouteTransition = useCallback((routeName: string) => {
    if (!enabled) return;

    routeStartTime.current = performance.now();
    performanceMonitor.markStart(`route-${routeName}`);
  }, [enabled]);

  const endRouteTransition = useCallback((routeName: string, metadata?: Record<string, unknown>) => {
    if (!enabled) return null;

    const duration = performanceMonitor.markEnd(`route-${routeName}`, metadata);

    if (duration !== null) {
      performanceMonitor.recordEvent({
        name: 'route-transition',
        duration,
        timestamp: routeStartTime.current,
        metadata: {
          routeName,
          ...metadata,
        },
      });
    }

    return duration;
  }, [enabled]);

  return {
    startRouteTransition,
    endRouteTransition,
  };
};

/**
 * Hook for tracking form performance
 */
export const useFormPerformance = (formName: string) => {
  const { enabled } = useGlobalPerformance();
  const formStartTime = useRef<number>(0);
  const fieldInteractions = useRef<number>(0);

  const startForm = useCallback(() => {
    if (!enabled) return;

    formStartTime.current = performance.now();
    fieldInteractions.current = 0;
  }, [enabled]);

  const trackFieldInteraction = useCallback((fieldName: string) => {
    if (!enabled) return;

    fieldInteractions.current += 1;

    performanceMonitor.recordEvent({
      name: 'form-field-interaction',
      duration: 0,
      timestamp: performance.now(),
      metadata: {
        formName,
        fieldName,
        interactionCount: fieldInteractions.current,
      },
    });
  }, [enabled, formName]);

  const completeForm = useCallback((success: boolean, metadata?: Record<string, unknown>) => {
    if (!enabled) return null;

    const completionTime = performance.now() - formStartTime.current;

    performanceMonitor.recordEvent({
      name: 'form-completion',
      duration: completionTime,
      timestamp: formStartTime.current,
      metadata: {
        formName,
        success,
        fieldInteractions: fieldInteractions.current,
        ...metadata,
      },
    });

    return completionTime;
  }, [enabled, formName]);

  return {
    startForm,
    trackFieldInteraction,
    completeForm,
    interactionCount: fieldInteractions.current,
  };
};

/**
 * Hook for general performance tracking
 */
export const usePerformanceTracker = () => {
  const { enabled } = useGlobalPerformance();

  const track = useCallback(<T>(
    label: string,
    operation: () => T | Promise<T>,
    metadata?: Record<string, unknown>
  ): T | Promise<T> => {
    if (!enabled) {
      return operation();
    }

    if (operation instanceof Promise || (operation as { then?: unknown })?.then) {
      // Async operation
      performanceMonitor.markStart(label);
      return Promise.resolve(operation()).then(
        (result) => {
          performanceMonitor.markEnd(label, { ...metadata, success: true });
          return result;
        },
        (error) => {
          performanceMonitor.markEnd(label, {
            ...metadata,
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
          });
          throw error;
        }
      ) as T;
    } else {
      // Sync operation
      performanceMonitor.markStart(label);
      try {
        const result = operation();
        performanceMonitor.markEnd(label, { ...metadata, success: true });
        return result;
      } catch (error) {
        performanceMonitor.markEnd(label, {
          ...metadata,
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
        throw error;
      }
    }
  }, [enabled]);

  return { track };
};
