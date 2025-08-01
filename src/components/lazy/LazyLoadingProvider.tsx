/**
 * Lazy Loading Provider - React provider component for lazy loading
 */

import React from 'react'
import { useState, useCallback, useEffect } from 'react'
import type { LazyComponentOptions } from '@/types/lazy';
import { loadingManager } from '@/utils/lazy/loadingManager';
import { LazyLoadingContext, type LazyLoadingContextType } from './LazyLoadingContext';

interface LazyLoadingProviderProps {
  children: React.ReactNode;
  globalOptions?: LazyComponentOptions;
}

export const LazyLoadingProvider: React.FC<LazyLoadingProviderProps> = ({
  children,
  globalOptions = {}
}) => {
  const [, forceUpdate] = useState({});

  // Force re-render when loading states change
  const triggerUpdate = useCallback(() => {
    forceUpdate({});
  }, []);

  useEffect(() => {
    // Setup performance observer for bundle analysis
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.name.includes('chunk')) {
            console.debug('Chunk loaded:', entry.name, `${entry.duration.toFixed(2)}ms`);
          }
        });
      });

      observer.observe({ entryTypes: ['navigation', 'resource'] });
      return () => observer.disconnect();
    }
  }, []);

  const loadComponent = useCallback(async <P extends Record<string, unknown> = Record<string, unknown>>(
    componentId: string,
    importFn: () => Promise<{ default: React.ComponentType<P> }>,
    options: LazyComponentOptions = {}
  ) => {
    const mergedOptions = { ...globalOptions, ...options };
    triggerUpdate();
    return loadingManager.loadComponent(componentId, importFn, mergedOptions);
  }, [globalOptions, triggerUpdate]);

  const preloadComponent = useCallback(<P extends Record<string, unknown> = Record<string, unknown>>(
    componentId: string,
    importFn: () => Promise<{ default: React.ComponentType<P> }>,
    options: LazyComponentOptions = {}
  ) => {
    const mergedOptions = { ...globalOptions, ...options };
    loadingManager.preloadComponent(componentId, importFn, mergedOptions);
  }, [globalOptions]);

  const getLoadingState = useCallback((componentId: string) => {
    return loadingManager.getLoadingState(componentId);
  }, []);

  const clearCaches = useCallback(() => {
    loadingManager.clearCaches();
    triggerUpdate();
  }, [triggerUpdate]);

  const getCacheEffectiveness = useCallback(() => {
    return loadingManager.getCacheEffectiveness();
  }, []);

  const contextValue: LazyLoadingContextType = {
    loadComponent,
    preloadComponent,
    getLoadingState,
    clearCaches,
    getCacheEffectiveness
  };

  return (
    <LazyLoadingContext.Provider value={contextValue}>
      {children}
    </LazyLoadingContext.Provider>
  );
};
