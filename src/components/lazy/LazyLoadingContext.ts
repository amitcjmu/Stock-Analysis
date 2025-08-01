/**
 * Lazy Loading Context - Context definitions for lazy loading
 * 
 * Separated from provider component to maintain react-refresh compatibility.
 */

import { createContext } from 'react';
import type { LazyComponentOptions, LoadingState } from '@/types/lazy';

export interface LazyLoadingContextType {
  loadComponent: <P extends Record<string, unknown> = Record<string, unknown>>(
    componentId: string,
    importFn: () => Promise<{ default: React.ComponentType<P> }>,
    options?: LazyComponentOptions
  ) => Promise<React.ComponentType<P>>;
  preloadComponent: <P extends Record<string, unknown> = Record<string, unknown>>(
    componentId: string,
    importFn: () => Promise<{ default: React.ComponentType<P> }>,
    options?: LazyComponentOptions
  ) => void;
  getLoadingState: (componentId: string) => LoadingState | null;
  clearCaches: () => void;
  getCacheEffectiveness: () => number;
}

export const LazyLoadingContext = createContext<LazyLoadingContextType | null>(null);