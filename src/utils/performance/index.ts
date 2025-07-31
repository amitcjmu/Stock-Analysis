// Performance monitoring
export {
  performanceMonitor,
  useRenderPerformance,
  measurePerformance,
  measureAsync,
  measureSync,
  type PerformanceEvent,
  type RenderPerformance,
  type PerformanceConfig
} from './monitoring';

// Performance hooks
export {
  useApiPerformance,
  useCachePerformance,
  useBundlePerformance,
  useMemoryMonitoring,
  useRoutePerformance,
  useFormPerformance,
  usePerformanceTracker
} from './hooks';

// Memoization utilities
export {
  performantMemo,
  smartMemo,
  stableMemo,
  useStableCallback,
  useExpensiveMemo,
  useDebouncedValue,
  useThrottledCallback,
  withLazyRendering,
  VirtualList,
  useContextSelector,
  performanceToolkit,
  isEqual,
  shallowEqual
} from './memoization';

// Feature flags
export {
  featureFlagsManager,
  useFeatureFlags,
  useFeatureFlag,
  withFeatureFlag,
  FeatureGate,
  canaryUtils
} from './featureFlags';

// Combined exports for convenience
export const performance = {
  monitor: performanceMonitor,
  toolkit: performanceToolkit,
  featureFlags: featureFlagsManager,
  canary: canaryUtils,
};

// Performance configuration
export interface PerformanceOptions {
  enableMonitoring?: boolean;
  enableMemoization?: boolean;
  enableFeatureFlags?: boolean;
  sampleRate?: number;
  reportInterval?: number;
}

/**
 * Initialize performance monitoring for the entire application
 */
export const initializePerformance = (options: PerformanceOptions = {}) => {
  const {
    enableMonitoring = process.env.NODE_ENV === 'development',
    enableFeatureFlags = true,
    sampleRate = 0.1,
    reportInterval = 10000,
  } = options;

  if (enableMonitoring) {
    performanceMonitor.updateConfig({
      enabled: true,
      sampleRate,
      reportInterval,
      maxMetricsHistory: 100,
    });
  }

  if (enableFeatureFlags) {
    // Load remote feature flags if available
    const apiEndpoint = process.env.VITE_FEATURE_FLAGS_ENDPOINT;
    if (apiEndpoint) {
      featureFlagsManager.loadRemoteFlags(apiEndpoint).catch(console.warn);
    }
  }

  // Set up global error tracking for performance issues
  if (typeof window !== 'undefined') {
    window.addEventListener('error', (event) => {
      if (enableMonitoring) {
        performanceMonitor.recordEvent({
          name: 'javascript-error',
          duration: 0,
          timestamp: performance.now(),
          metadata: {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
          },
        });
      }
    });

    window.addEventListener('unhandledrejection', (event) => {
      if (enableMonitoring) {
        performanceMonitor.recordEvent({
          name: 'unhandled-promise-rejection',
          duration: 0,
          timestamp: performance.now(),
          metadata: {
            reason: event.reason?.toString() || 'Unknown rejection',
          },
        });
      }
    });
  }

  return {
    monitor: performanceMonitor,
    featureFlags: featureFlagsManager,
    toolkit: performanceToolkit,
  };
};
