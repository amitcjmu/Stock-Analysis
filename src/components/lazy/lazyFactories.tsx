/**
 * Lazy Component Factories
 *
 * Factory functions for creating enhanced lazy components.
 * Separated from main component file to maintain react-refresh compatibility.
 */

import React, { Suspense, lazy } from 'react';
import type { ComponentType } from 'react';
import { ErrorBoundary } from '../ErrorBoundary';
import { useRoutePerformance } from '../../utils/performance/hooks';
import { FeatureGate } from '../../utils/performance/featureFlags';
import type { FeatureFlags } from '../../contexts/GlobalContext/types';
import { LoadingPriority } from './lazyUtils';
import { LoadingFallbackWithPerformance, ErrorFallback } from './lazyComponents';

// Enhanced loading and error components imported from ./lazyComponents

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
): React.FC<P> => {
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
    const { startRouteTransition, endRouteTransition } = useRoutePerformance();

    React.useEffect(() => {
      startRouteTransition(bundleName);
      return () => {
        endRouteTransition(bundleName, { bundleName });
      };
    }, [startRouteTransition, endRouteTransition]);

    const ComponentWithFeatureFlag = featureFlag ? (
      <FeatureGate flag={featureFlag as keyof FeatureFlags} fallback={
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

// Progressive lazy loading with intersection observer
export const createProgressiveLazy = <P extends object>(
  importFn: () => Promise<{ default: ComponentType<P> }>,
  options: {
    bundleName: string;
    priority: LoadingPriority;
    threshold?: number;
    rootMargin?: string;
  }
): React.FC<P> => {
  const { bundleName, priority, threshold = 0.1, rootMargin = '100px' } = options;

  const ProgressiveLazyComponent: React.FC<P> = (props) => {
    const [shouldLoad, setShouldLoad] = React.useState(priority === LoadingPriority.CRITICAL);
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
    }, []);

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
    const isHighPriority = priority === LoadingPriority.HIGH;
    const handleMouseEnter = React.useCallback(() => {
      if (isHighPriority && !shouldLoad) {
        setShouldLoad(true);
      }
    }, [isHighPriority, shouldLoad]);

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
