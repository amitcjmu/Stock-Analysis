import React, { Suspense, lazy, ComponentType, LazyExoticComponent } from 'react';
import { ErrorBoundary } from '../ErrorBoundary';
import { useBundlePerformance, useRoutePerformance } from '../../utils/performance/hooks';
import { FeatureGate } from '../../utils/performance/featureFlags';

// Enhanced loading fallback with performance tracking
const LoadingFallbackWithPerformance: React.FC<{
  message?: string;
  bundleName?: string;
}> = ({ message = 'Loading...', bundleName }) => {
  const { loadingStats } = useBundlePerformance();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">{message}</p>
        {process.env.NODE_ENV === 'development' && bundleName && (
          <div className="text-xs text-gray-400 mt-2">
            Bundle: {bundleName} | Loaded: {loadingStats.loadedBundles}/{loadingStats.totalBundles}
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced error fallback
const ErrorFallback: React.FC<{
  error: Error;
  resetErrorBoundary: () => void;
  bundleName?: string;
}> = ({ error, resetErrorBoundary, bundleName }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center max-w-md">
      <div className="text-red-500 text-6xl mb-4">⚠️</div>
      <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
      <p className="text-gray-600 mb-4">
        Failed to load the requested component.
      </p>
      {process.env.NODE_ENV === 'development' && (
        <details className="text-left bg-gray-100 p-3 rounded mb-4 text-sm">
          <summary className="cursor-pointer font-medium">Error Details</summary>
          <pre className="mt-2 text-xs overflow-auto">
            Bundle: {bundleName || 'Unknown'}
            {'\n'}
            {error.message}
            {'\n'}
            {error.stack}
          </pre>
        </details>
      )}
      <button
        onClick={resetErrorBoundary}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
      >
        Try again
      </button>
    </div>
  </div>
);

// HOC for enhanced lazy loading with performance tracking
export const createEnhancedLazy = <P extends object>(
  importFn: () => Promise<{ default: ComponentType<P> }>,
  options: {
    bundleName: string;
    fallbackMessage?: string;
    enablePerformanceTracking?: boolean;
    featureFlag?: string;
    retryAttempts?: number;
  }
) => {
  const {
    bundleName,
    fallbackMessage,
    enablePerformanceTracking = true,
    featureFlag,
    retryAttempts = 3
  } = options;

  // Create lazy component with retry logic
  const LazyComponent = lazy(async () => {
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= retryAttempts; attempt++) {
      try {
        if (enablePerformanceTracking) {
          const start = performance.now();
          const module = await importFn();
          const duration = performance.now() - start;

          // Log performance metrics
          if (duration > 1000) { // Warn if bundle takes more than 1 second
            console.warn(`Bundle "${bundleName}" took ${duration.toFixed(2)}ms to load`);
          }

          return module;
        } else {
          return await importFn();
        }
      } catch (error) {
        lastError = error as Error;

        if (attempt < retryAttempts) {
          // Wait before retrying (exponential backoff)
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
          console.warn(`Bundle "${bundleName}" failed to load (attempt ${attempt}/${retryAttempts}), retrying...`);
        }
      }
    }

    throw lastError || new Error(`Failed to load bundle "${bundleName}" after ${retryAttempts} attempts`);
  });

  const EnhancedLazyComponent: React.FC<P> = (props) => {
    const { trackBundleLoad } = useBundlePerformance();
    const { startRouteTransition, endRouteTransition } = useRoutePerformance();

    React.useEffect(() => {
      startRouteTransition(bundleName);
      return () => {
        endRouteTransition(bundleName, { bundleName });
      };
    }, []);

    const ComponentWithFeatureFlag = featureFlag ? (
      <FeatureGate flag={featureFlag as any} fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">Feature Not Available</h2>
            <p className="text-gray-600">This feature is currently disabled.</p>
          </div>
        </div>
      }>
        <LazyComponent {...props} />
      </FeatureGate>
    ) : (
      <LazyComponent {...props} />
    );

    return (
      <ErrorBoundary
        fallback={({ error, resetErrorBoundary }) => (
          <ErrorFallback
            error={error}
            resetErrorBoundary={resetErrorBoundary}
            bundleName={bundleName}
          />
        )}
      >
        <Suspense
          fallback={
            <LoadingFallbackWithPerformance
              message={fallbackMessage}
              bundleName={bundleName}
            />
          }
        >
          {ComponentWithFeatureFlag}
        </Suspense>
      </ErrorBoundary>
    );
  };

  EnhancedLazyComponent.displayName = `EnhancedLazy(${bundleName})`;
  return EnhancedLazyComponent;
};

// Progressive loading components with priority levels
export enum LoadingPriority {
  CRITICAL = 0,   // Load immediately
  HIGH = 1,       // Load when visible or on hover
  NORMAL = 2,     // Load when visible
  LOW = 3,        // Load when idle
}

// Progressive lazy loading with intersection observer
export const createProgressiveLazy = <P extends object>(
  importFn: () => Promise<{ default: ComponentType<P> }>,
  options: {
    bundleName: string;
    priority: LoadingPriority;
    threshold?: number;
    rootMargin?: string;
  }
) => {
  const { bundleName, priority, threshold = 0.1, rootMargin = '100px' } = options;

  const ProgressiveLazyComponent: React.FC<P> = (props) => {
    const [shouldLoad, setShouldLoad] = React.useState(priority === LoadingPriority.CRITICAL);
    const [isVisible, setIsVisible] = React.useState(false);
    const [Component, setComponent] = React.useState<ComponentType<P> | null>(null);
    const ref = React.useRef<HTMLDivElement>(null);

    // Load based on priority
    React.useEffect(() => {
      if (priority === LoadingPriority.CRITICAL) {
        setShouldLoad(true);
        return;
      }

      const element = ref.current;
      if (!element) return;

      let observer: IntersectionObserver;

      if (priority === LoadingPriority.HIGH || priority === LoadingPriority.NORMAL) {
        observer = new IntersectionObserver(
          ([entry]) => {
            if (entry.isIntersecting) {
              setIsVisible(true);
              setShouldLoad(true);
              observer.disconnect();
            }
          },
          { threshold, rootMargin }
        );
        observer.observe(element);
      }

      if (priority === LoadingPriority.LOW) {
        // Load when browser is idle
        if ('requestIdleCallback' in window) {
          const idleCallback = window.requestIdleCallback(() => {
            setShouldLoad(true);
          });
          return () => window.cancelIdleCallback(idleCallback);
        } else {
          // Fallback for browsers without requestIdleCallback
          const timeout = setTimeout(() => setShouldLoad(true), 5000);
          return () => clearTimeout(timeout);
        }
      }

      return () => {
        if (observer) observer.disconnect();
      };
    }, [priority, threshold, rootMargin]);

    // Load component when needed
    React.useEffect(() => {
      if (shouldLoad && !Component) {
        importFn().then(module => {
          setComponent(() => module.default);
        }).catch(error => {
          console.error(`Failed to load bundle "${bundleName}":`, error);
        });
      }
    }, [shouldLoad, Component]);

    // Hover preloading for high priority components
    const handleMouseEnter = React.useCallback(() => {
      if (priority === LoadingPriority.HIGH && !shouldLoad) {
        setShouldLoad(true);
      }
    }, [priority, shouldLoad]);

    if (!shouldLoad) {
      return (
        <div
          ref={ref}
          onMouseEnter={handleMouseEnter}
          className="min-h-32 flex items-center justify-center"
        >
          <div className="text-gray-400 text-sm">Loading...</div>
        </div>
      );
    }

    if (!Component) {
      return (
        <div className="min-h-32 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    return <Component {...props} />;
  };

  ProgressiveLazyComponent.displayName = `ProgressiveLazy(${bundleName})`;
  return ProgressiveLazyComponent;
};

// Bundle analyzer component (development only)
export const BundleAnalyzer: React.FC = () => {
  const { loadingStats } = useBundlePerformance();
  const [isVisible, setIsVisible] = React.useState(false);

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <>
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="fixed bottom-4 left-4 bg-purple-600 text-white p-2 rounded-full shadow-lg z-50"
        title="Toggle Bundle Analyzer"
      >
        📦
      </button>

      {isVisible && (
        <div className="fixed bottom-16 left-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-sm z-50">
          <h3 className="font-semibold mb-2">Bundle Loading Stats</h3>
          <div className="text-sm space-y-1">
            <div>Total Bundles: {loadingStats.totalBundles}</div>
            <div>Loaded: {loadingStats.loadedBundles}</div>
            <div>Failed: {loadingStats.failedBundles}</div>
            <div>Avg Load Time: {loadingStats.averageLoadTime.toFixed(2)}ms</div>
            <div className="mt-2 pt-2 border-t">
              Success Rate: {loadingStats.totalBundles > 0
                ? ((loadingStats.loadedBundles / loadingStats.totalBundles) * 100).toFixed(1)
                : 0}%
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Route preloader utility
export const RoutePreloader: React.FC<{
  routes: Array<{
    path: string;
    importFn: () => Promise<any>;
    priority: LoadingPriority;
  }>;
}> = ({ routes }) => {
  const { trackBundleLoad } = useBundlePerformance();

  React.useEffect(() => {
    // Preload critical routes immediately
    const criticalRoutes = routes.filter(route => route.priority === LoadingPriority.CRITICAL);
    criticalRoutes.forEach(route => {
      trackBundleLoad(route.path, route.importFn);
    });

    // Preload high priority routes when browser is idle
    const highPriorityRoutes = routes.filter(route => route.priority === LoadingPriority.HIGH);
    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(() => {
        highPriorityRoutes.forEach(route => {
          trackBundleLoad(route.path, route.importFn);
        });
      });
    }
  }, [routes, trackBundleLoad]);

  return null; // This component doesn't render anything
};

// Export enhanced lazy loading utilities
export const enhancedLazy = {
  create: createEnhancedLazy,
  progressive: createProgressiveLazy,
  LoadingPriority,
  BundleAnalyzer,
  RoutePreloader,
};
