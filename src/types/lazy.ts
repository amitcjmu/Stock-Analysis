/**
 * Type definitions for lazy loading system
 * Advanced code splitting and lazy loading implementation
 */

export enum LoadingPriority {
  CRITICAL = 0,   // Login, main layout - immediate load
  HIGH = 1,       // Discovery page, navigation - preload
  NORMAL = 2,     // Secondary features - load on demand
  LOW = 3         // Admin, utilities - load when needed
}

export interface LazyComponentOptions {
  priority?: LoadingPriority;
  preload?: boolean;
  fallback?: React.ComponentType;
  errorBoundary?: React.ComponentType<{ error: Error; retry: () => void }>;
  timeout?: number;
  retryAttempts?: number;
  cacheStrategy?: 'memory' | 'session' | 'persistent';
}

export interface LazyLoadingMetrics {
  componentName: string;
  loadStartTime: number;
  loadEndTime: number;
  loadDuration: number;
  chunkSize?: number;
  cacheHit: boolean;
  retryCount: number;
  priority: LoadingPriority;
  userAgent: string;
  connectionType?: string;
}

export interface BundleAnalysis {
  totalBundleSize: number;
  initialBundleSize: number;
  chunkSizes: Record<string, number>;
  loadedChunks: string[];
  pendingChunks: string[];
  cacheEffectiveness: number;
  performanceScore: number;
}

export interface LoadingState {
  isLoading: boolean;
  error: Error | null;
  retryCount: number;
  loadStartTime: number;
  component: React.ComponentType | null;
}

export interface PreloadStrategy {
  routes: string[];
  components: string[];
  priority: LoadingPriority;
  trigger: 'viewport' | 'hover' | 'idle' | 'manual';
  delay?: number;
}

export interface LazyHookModule<T = unknown> {
  [key: string]: T;
}

export interface LazyUtilityModule<T = unknown> {
  [key: string]: T;
}

export type LazyComponentImport<P = Record<string, unknown>> = () => Promise<{ default: React.ComponentType<P> }>;
export type LazyHookImport<T = unknown> = () => Promise<LazyHookModule<T>>;
export type LazyUtilityImport<T = unknown> = () => Promise<LazyUtilityModule<T>>;
