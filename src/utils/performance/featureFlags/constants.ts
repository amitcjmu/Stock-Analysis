/**
 * Feature Flags Constants
 * Default configurations and environment overrides
 */

import type { FeatureFlags } from './types';

// Default feature flags configuration
export const DEFAULT_FEATURE_FLAGS: FeatureFlags = {
  useRedisCache: process.env.NODE_ENV === 'production',
  enablePerformanceMonitoring: process.env.NODE_ENV === 'development',
  useWebSocketSync: true,
  enableContextDebugging: process.env.NODE_ENV === 'development',
  useProgressiveHydration: true,
};

// Environment-based overrides
export const ENV_OVERRIDES: Partial<FeatureFlags> = {
  useRedisCache: process.env.VITE_USE_REDIS_CACHE === 'true',
  enablePerformanceMonitoring: process.env.VITE_ENABLE_PERFORMANCE_MONITORING === 'true',
  useWebSocketSync: process.env.VITE_USE_WEBSOCKET_SYNC !== 'false',
  enableContextDebugging: process.env.VITE_ENABLE_CONTEXT_DEBUGGING === 'true',
  useProgressiveHydration: process.env.VITE_USE_PROGRESSIVE_HYDRATION !== 'false',
};