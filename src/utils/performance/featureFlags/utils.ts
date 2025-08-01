/**
 * Feature Flags Utilities
 * Utility functions for feature flag management and canary deployments
 */

import { featureFlagsManager } from './manager';
import { DEFAULT_FEATURE_FLAGS, ENV_OVERRIDES } from './constants';
import type { FeatureFlags } from './types';

/**
 * Canary deployment utilities
 */
export const canaryUtils = {
  /**
   * Check if user is in canary group
   */
  isInCanaryGroup(userId: string, percentage: number = 10): boolean {
    // Simple hash function for consistent percentage rollouts
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      const char = userId.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    const absHash = Math.abs(hash);
    return absHash % 100 < percentage;
  },

  /**
   * Get canary flags for a user
   */
  getCanaryFlags(userId: string): Partial<FeatureFlags> {
    const canaryFlags: Partial<FeatureFlags> = {};

    // Example: Enable Redis cache for 20% of users
    if (this.isInCanaryGroup(userId, 20)) {
      canaryFlags.useRedisCache = true;
    }

    // Example: Enable performance monitoring for 50% of users
    if (this.isInCanaryGroup(userId, 50)) {
      canaryFlags.enablePerformanceMonitoring = true;
    }

    return canaryFlags;
  },
};

// Export for debugging in development
if (process.env.NODE_ENV === 'development') {
  (window as typeof window & { __featureFlagsManager?: unknown; __featureFlags?: unknown }).__featureFlagsManager = featureFlagsManager;
  (window as typeof window & { __featureFlagsManager?: unknown; __featureFlags?: unknown }).__featureFlags = {
    manager: featureFlagsManager,
    canaryUtils,
    DEFAULT_FEATURE_FLAGS,
    ENV_OVERRIDES,
  };
}
