/**
 * useLazyComponent Hook - Advanced lazy loading with error boundaries and retries
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { LoadingPriority, LazyComponentOptions, LoadingState } from '@/types/lazy';
import { loadingManager } from '@/utils/lazy/loadingManager';

interface UseLazyComponentOptions extends LazyComponentOptions {
  immediate?: boolean;
  preload?: boolean;
  triggerDistance?: number;
}

interface UseLazyComponentReturn {
  Component: React.ComponentType | null;
  loading: boolean;
  error: Error | null;
  retry: () => void;
  loadComponent: () => void;
  loadingState: LoadingState | null;
}

export const useLazyComponent = (
  componentId: string,
  importFn: () => Promise<{ default: React.ComponentType<any> }>,
  options: UseLazyComponentOptions = {}
): UseLazyComponentReturn => {
  const {
    immediate = false,
    preload = false,
    priority = LoadingPriority.NORMAL,
    retryAttempts = 3,
    timeout = 30000,
    ...restOptions
  } = options;

  const [Component, setComponent] = useState<React.ComponentType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const loadingRef = useRef(false);

  const loadComponent = useCallback(async () => {
    if (loadingRef.current || Component) return;

    loadingRef.current = true;
    setLoading(true);
    setError(null);

    try {
      const loadedComponent = await loadingManager.loadComponent(
        componentId,
        importFn,
        { priority, retryAttempts, timeout, ...restOptions }
      );
      setComponent(() => loadedComponent);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [componentId, importFn, priority, retryAttempts, timeout, restOptions, Component]);

  const retry = useCallback(() => {
    setError(null);
    setComponent(null);
    loadingRef.current = false;
    loadComponent();
  }, [loadComponent]);

  // Get current loading state from manager
  const loadingState = loadingManager.getLoadingState(componentId);

  // Handle immediate loading
  useEffect(() => {
    if (immediate && !Component && !loading && !error) {
      loadComponent();
    }
  }, [immediate, Component, loading, error, loadComponent]);

  // Handle preloading
  useEffect(() => {
    if (preload && !Component && !loading) {
      loadingManager.preloadComponent(componentId, importFn, {
        priority: LoadingPriority.LOW,
        ...restOptions
      });
    }
  }, [preload, Component, loading, componentId, importFn, restOptions]);

  return {
    Component,
    loading,
    error,
    retry,
    loadComponent,
    loadingState
  };
};

/**
 * Hook for viewport-based lazy loading
 */
export const useViewportLazyComponent = (
  componentId: string,
  importFn: () => Promise<{ default: React.ComponentType<any> }>,
  targetRef: React.RefObject<HTMLElement>,
  options: UseLazyComponentOptions = {}
): UseLazyComponentReturn => {
  const { triggerDistance = 100, ...restOptions } = options;
  const result = useLazyComponent(componentId, importFn, { immediate: false, ...restOptions });

  useEffect(() => {
    if (!targetRef.current || result.Component) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            result.loadComponent();
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: `${triggerDistance}px`,
        threshold: 0.1
      }
    );

    observer.observe(targetRef.current);

    return () => observer.disconnect();
  }, [targetRef, result.Component, result.loadComponent, triggerDistance]);

  return result;
};

/**
 * Hook for hover-based preloading
 */
export const useHoverPreload = (
  componentId: string,
  importFn: () => Promise<{ default: React.ComponentType<any> }>,
  options: LazyComponentOptions = {}
): void => {
  const preloaded = useRef(false);

  const handleMouseEnter = useCallback(() => {
    if (!preloaded.current) {
      loadingManager.preloadComponent(componentId, importFn, {
        priority: LoadingPriority.HIGH,
        ...options
      });
      preloaded.current = true;
    }
  }, [componentId, importFn, options]);

  useEffect(() => {
    return () => {
      preloaded.current = false;
    };
  }, []);

  // Return the event handler for the component to use
  (handleMouseEnter as any).componentId = componentId;
  return handleMouseEnter as any;
};