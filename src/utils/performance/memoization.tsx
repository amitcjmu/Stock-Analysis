import React, { memo, useMemo, useCallback, useRef } from 'react';
import { useRenderPerformance } from './hooks';

// Deep comparison utilities
const isEqual = (a: any, b: any): boolean => {
  if (a === b) return true;

  if (a == null || b == null) return a === b;

  if (typeof a !== typeof b) return false;

  if (typeof a !== 'object') return a === b;

  if (Array.isArray(a) !== Array.isArray(b)) return false;

  if (Array.isArray(a)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (!isEqual(a[i], b[i])) return false;
    }
    return true;
  }

  const keysA = Object.keys(a);
  const keysB = Object.keys(b);

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (!keysB.includes(key)) return false;
    if (!isEqual(a[key], b[key])) return false;
  }

  return true;
};

// Shallow comparison for props
const shallowEqual = (a: any, b: any): boolean => {
  if (a === b) return true;

  if (typeof a !== 'object' || typeof b !== 'object' || a == null || b == null) {
    return false;
  }

  const keysA = Object.keys(a);
  const keysB = Object.keys(b);

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (a[key] !== b[key]) return false;
  }

  return true;
};

/**
 * Enhanced memo with performance tracking
 */
export const performantMemo = <P extends object>(
  Component: React.ComponentType<P>,
  propsAreEqual?: (prevProps: P, nextProps: P) => boolean,
  displayName?: string
) => {
  const componentName = displayName || Component.displayName || Component.name || 'Anonymous';

  const MemoizedComponent = memo(Component, propsAreEqual);
  MemoizedComponent.displayName = `PerformantMemo(${componentName})`;

  return (props: P) => {
    useRenderPerformance(componentName);
    return <MemoizedComponent {...props} />;
  };
};

/**
 * Smart memo that automatically determines comparison strategy
 */
export const smartMemo = <P extends object>(
  Component: React.ComponentType<P>,
  options: {
    deep?: boolean;
    ignoreKeys?: (keyof P)[];
    displayName?: string;
  } = {}
) => {
  const { deep = false, ignoreKeys = [], displayName } = options;
  const componentName = displayName || Component.displayName || Component.name || 'Anonymous';

  const propsAreEqual = (prevProps: P, nextProps: P): boolean => {
    // Create filtered props objects
    const filteredPrev = { ...prevProps };
    const filteredNext = { ...nextProps };

    ignoreKeys.forEach(key => {
      delete filteredPrev[key];
      delete filteredNext[key];
    });

    return deep ? isEqual(filteredPrev, filteredNext) : shallowEqual(filteredPrev, filteredNext);
  };

  return performantMemo(Component, propsAreEqual, `SmartMemo(${componentName})`);
};

/**
 * Memo specifically for components with function props
 */
export const stableMemo = <P extends object>(
  Component: React.ComponentType<P>,
  stableKeys: (keyof P)[] = [],
  displayName?: string
) => {
  const componentName = displayName || Component.displayName || Component.name || 'Anonymous';

  const propsAreEqual = (prevProps: P, nextProps: P): boolean => {
    const prevEntries = Object.entries(prevProps) as [keyof P, any][];
    const nextEntries = Object.entries(nextProps) as [keyof P, any][];

    if (prevEntries.length !== nextEntries.length) return false;

    for (const [key, value] of prevEntries) {
      const nextValue = nextProps[key];

      if (stableKeys.includes(key)) {
        // For stable keys, do reference equality check
        if (value !== nextValue) return false;
      } else {
        // For other keys, do shallow equality check
        if (typeof value === 'function' && typeof nextValue === 'function') {
          // Functions are considered equal if they have the same string representation
          // This is not perfect but better than always re-rendering
          if (value.toString() !== nextValue.toString()) return false;
        } else if (value !== nextValue) {
          return false;
        }
      }
    }

    return true;
  };

  return performantMemo(Component, propsAreEqual, `StableMemo(${componentName})`);
};

/**
 * Hook for stable callbacks
 */
export const useStableCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList
): T => {
  const callbackRef = useRef<T>(callback);
  callbackRef.current = callback;

  return useCallback(
    ((...args: Parameters<T>) => callbackRef.current(...args)) as T,
    deps
  );
};

/**
 * Hook for expensive computations with memoization
 */
export const useExpensiveMemo = <T>(
  factory: () => T,
  deps: React.DependencyList,
  options: {
    debugLabel?: string;
    perfThreshold?: number; // milliseconds
  } = {}
): T => {
  const { debugLabel = 'expensive-computation', perfThreshold = 1 } = options;

  return useMemo(() => {
    const start = performance.now();
    const result = factory();
    const duration = performance.now() - start;

    if (duration > perfThreshold && process.env.NODE_ENV === 'development') {
      console.warn(`Expensive computation "${debugLabel}" took ${duration.toFixed(2)}ms`);
    }

    return result;
  }, deps);
};

/**
 * Hook for debounced values
 */
export const useDebouncedValue = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value);

  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Hook for throttled callbacks
 */
export const useThrottledCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const lastRun = useRef<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  return useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now();

      if (now - lastRun.current >= delay) {
        callback(...args);
        lastRun.current = now;
      } else {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(() => {
          callback(...args);
          lastRun.current = Date.now();
        }, delay - (now - lastRun.current));
      }
    }) as T,
    [callback, delay]
  );
};

/**
 * Higher-order component for lazy rendering
 */
export const withLazyRendering = <P extends object>(
  Component: React.ComponentType<P>,
  options: {
    threshold?: number; // Intersection threshold
    rootMargin?: string;
    displayName?: string;
  } = {}
) => {
  const { threshold = 0.1, rootMargin = '100px', displayName } = options;
  const componentName = displayName || Component.displayName || Component.name || 'Anonymous';

  const LazyComponent: React.FC<P> = (props) => {
    const [isVisible, setIsVisible] = React.useState(false);
    const [hasRendered, setHasRendered] = React.useState(false);
    const ref = useRef<HTMLDivElement>(null);

    React.useEffect(() => {
      const element = ref.current;
      if (!element) return;

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting && !hasRendered) {
            setIsVisible(true);
            setHasRendered(true);
          }
        },
        { threshold, rootMargin }
      );

      observer.observe(element);

      return () => observer.disconnect();
    }, [hasRendered]);

    return (
      <div ref={ref}>
        {isVisible ? <Component {...props} /> : (
          <div className="h-32 flex items-center justify-center bg-gray-50">
            <div className="text-sm text-gray-500">Loading...</div>
          </div>
        )}
      </div>
    );
  };

  LazyComponent.displayName = `LazyRendering(${componentName})`;
  return LazyComponent;
};

/**
 * Virtual list component for large datasets
 */
interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
}

export const VirtualList = <T,>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 3
}: VirtualListProps<T>) => {
  const [scrollTop, setScrollTop] = React.useState(0);

  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );

  const visibleItems = items.slice(startIndex, endIndex + 1);

  const handleScroll = useThrottledCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, 16); // ~60fps

  return (
    <div
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      <div style={{ height: items.length * itemHeight, position: 'relative' }}>
        {visibleItems.map((item, index) => (
          <div
            key={startIndex + index}
            style={{
              position: 'absolute',
              top: (startIndex + index) * itemHeight,
              height: itemHeight,
            }}
          >
            {renderItem(item, startIndex + index)}
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Context selector hook for avoiding unnecessary re-renders
 */
export const useContextSelector = <T, S>(
  context: React.Context<T>,
  selector: (value: T) => S
): S => {
  const value = React.useContext(context);
  return useMemo(() => selector(value), [value, selector]);
};

// Export all utilities as a performance toolkit
export const performanceToolkit = {
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
  isEqual,
  shallowEqual,
};
