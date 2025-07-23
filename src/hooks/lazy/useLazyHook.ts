/**
 * useLazyHook - Hook-level code splitting for complex hooks
 */

import { useState, useRef } from 'react'
import { useEffect, useCallback } from 'react'
import type { LazyHookModule } from '@/types/lazy'
import { LoadingPriority } from '@/types/lazy'
import type { loadingManager } from '@/utils/lazy/loadingManager';

interface UseLazyHookOptions {
  priority?: LoadingPriority;
  immediate?: boolean;
  timeout?: number;
  retryAttempts?: number;
}

interface UseLazyHookReturn<T> {
  hookModule: T | null;
  loading: boolean;
  error: Error | null;
  loadHook: () => Promise<T>;
  retry: () => void;
}

/**
 * Core lazy hook loader
 */
export const useLazyHook = <T = unknown>(
  hookId: string,
  importFn: () => Promise<LazyHookModule<T>>,
  options: UseLazyHookOptions = {}
): UseLazyHookReturn<T> => {
  const {
    priority = LoadingPriority.NORMAL,
    immediate = false,
    timeout = 15000,
    retryAttempts = 2
  } = options;

  const [hookModule, setHookModule] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const loadingRef = useRef(false);
  const cacheRef = useRef<Map<string, T>>(new Map());

  const loadHook = useCallback(async (): Promise<T> => {
    if (loadingRef.current) {
      throw new Error('Hook is already loading');
    }

    // Check cache first
    const cached = cacheRef.current.get(hookId);
    if (cached) {
      setHookModule(cached);
      return cached;
    }

    loadingRef.current = true;
    setLoading(true);
    setError(null);

    try {
      const startTime = performance.now();
      
      const modulePromise = importFn();
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Hook load timeout')), timeout)
      );

      const module = await Promise.race([modulePromise, timeoutPromise]);
      
      const endTime = performance.now();
      console.debug(`Hook ${hookId} loaded in ${endTime - startTime}ms`);

      // Cache the module
      cacheRef.current.set(hookId, module as T);
      setHookModule(module as T);
      
      return module as T;
    } catch (err) {
      const error = err as Error;
      setError(error);
      console.error(`Failed to load hook ${hookId}:`, error);
      throw error;
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [hookId, importFn, timeout]);

  const retry = useCallback(() => {
    setError(null);
    setHookModule(null);
    loadingRef.current = false;
    loadHook().catch(() => {}); // Error is handled in loadHook
  }, [loadHook]);

  useEffect(() => {
    if (immediate && !hookModule && !loading && !error) {
      loadHook().catch(() => {}); // Error is handled in loadHook
    }
  }, [immediate, hookModule, loading, error, loadHook]);

  return {
    hookModule,
    loading,
    error,
    loadHook,
    retry
  };
};

/**
 * Lazy hook with automatic dependency resolution
 */
export const useLazyHookWithDependencies = <T = unknown>(
  hookId: string,
  importFn: () => Promise<LazyHookModule<T>>,
  dependencies: string[],
  options: UseLazyHookOptions = {}
): UseLazyHookReturn<T> => {
  const [dependenciesLoaded, setDependenciesLoaded] = useState(false);
  const mainHook = useLazyHook(hookId, importFn, { 
    ...options, 
    immediate: options.immediate && dependenciesLoaded 
  });

  useEffect(() => {
    // Load dependencies first
    Promise.all(
      dependencies.map(dep => 
        import(/* webpackChunkName: "hook-dependency" */ dep)
      )
    ).then(() => {
      setDependenciesLoaded(true);
    }).catch(error => {
      console.error('Failed to load hook dependencies:', error);
    });
  }, [dependencies]);

  return mainHook;
};

/**
 * Conditional lazy hook loading based on feature flags or user permissions
 */
export const useConditionalLazyHook = <T = unknown>(
  hookId: string,
  importFn: () => Promise<LazyHookModule<T>>,
  condition: boolean | (() => boolean),
  options: UseLazyHookOptions = {}
): UseLazyHookReturn<T> => {
  const [shouldLoad, setShouldLoad] = useState(false);

  useEffect(() => {
    const conditionResult = typeof condition === 'function' ? condition() : condition;
    setShouldLoad(conditionResult);
  }, [condition]);

  return useLazyHook(hookId, importFn, {
    ...options,
    immediate: options.immediate && shouldLoad
  });
};

/**
 * Lazy hook with cache invalidation
 */
export const useLazyHookWithCache = <T = unknown>(
  hookId: string,
  importFn: () => Promise<LazyHookModule<T>>,
  cacheKey: string,
  options: UseLazyHookOptions & { 
    cacheTimeout?: number;
    invalidateOn?: string[];
  } = {}
): UseLazyHookReturn<T> & { clearCache: () => void } => {
  const { cacheTimeout = 300000, invalidateOn = [], ...hookOptions } = options; // 5 minutes default
  const [cacheInvalidated, setCacheInvalidated] = useState(false);
  const cacheTimeRef = useRef<number>(0);

  const hook = useLazyHook(hookId, importFn, hookOptions);

  const clearCache = useCallback(() => {
    setCacheInvalidated(true);
    cacheTimeRef.current = 0;
  }, []);

  // Cache timeout check
  useEffect(() => {
    if (hook.hookModule && cacheTimeRef.current === 0) {
      cacheTimeRef.current = Date.now();
    }

    const timer = setInterval(() => {
      if (cacheTimeRef.current > 0 && Date.now() - cacheTimeRef.current > cacheTimeout) {
        clearCache();
      }
    }, 60000); // Check every minute

    return () => clearInterval(timer);
  }, [hook.hookModule, cacheTimeout, clearCache]);

  // Invalidate cache on specified events
  useEffect(() => {
    const handleEvent = () => clearCache();
    
    invalidateOn.forEach(event => {
      window.addEventListener(event, handleEvent);
    });

    return () => {
      invalidateOn.forEach(event => {
        window.removeEventListener(event, handleEvent);
      });
    };
  }, [invalidateOn, clearCache]);

  return {
    ...hook,
    clearCache
  };
};