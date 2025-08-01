/**
 * Memoization hooks and utilities
 * Separated to avoid React Fast Refresh warnings
 */

import React, { useMemo, useCallback, useRef } from 'react';
import { memo } from 'react';
import { useRenderPerformance } from './hooks';
import { isEqual, shallowEqual, type AnyFunction } from './memoizationHelpers';

/**
 * Enhanced memo with performance tracking
 */
export const performantMemo = <P extends object>(
  Component: React.ComponentType<P>,
  propsAreEqual?: (prevProps: P, nextProps: P) => boolean,
  displayName?: string
): React.FC<P> => {
  const componentName = displayName || Component.displayName || Component.name || 'Anonymous';

  const MemoizedComponent = memo(Component, propsAreEqual);
  MemoizedComponent.displayName = `PerformantMemo(${componentName})`;

  return (props: P): React.ReactElement => {
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
    ignoreKeys?: Array<keyof P>;
    displayName?: string;
  } = {}
): React.FC<P> => {
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
  stableKeys: Array<keyof P> = [],
  displayName?: string
): React.FC<P> => {
  const componentName = displayName || Component.displayName || Component.name || 'Anonymous';

  const propsAreEqual = (prevProps: P, nextProps: P): boolean => {
    const prevEntries = Object.entries(prevProps) as Array<[keyof P, unknown]>;
    const nextEntries = Object.entries(nextProps) as Array<[keyof P, unknown]>;

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
export const useStableCallback = <T extends AnyFunction>(
  callback: T,
  deps: React.DependencyList
): T => {
  const callbackRef = useRef<T>(callback);
  callbackRef.current = callback;

  return useCallback(
    ((...args: Parameters<T>) => callbackRef.current(...args)) as T,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    deps
  );
};

/**
 * Hook for expensive computations with memoization
 */
export const useExpensiveMemo = <T,>(
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
};

/**
 * Hook for debounced values
 */
export const useDebouncedValue = <T,>(value: T, delay: number): T => {
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
export const useThrottledCallback = <T extends AnyFunction>(
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
 * Context selector hook for avoiding unnecessary re-renders
 */
export const useContextSelector = <T, S>(
  context: React.Context<T>,
  selector: (value: T) => S
): S => {
  const value = React.useContext(context);
  return useMemo(() => selector(value), [value, selector]);
};
