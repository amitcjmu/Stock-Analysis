import { FeatureFlags } from '../../contexts/GlobalContext/types';
import { featureFlagsStorage } from '../../contexts/GlobalContext/storage';

// Default feature flags configuration
const DEFAULT_FEATURE_FLAGS: FeatureFlags = {
  useRedisCache: process.env.NODE_ENV === 'production',
  enablePerformanceMonitoring: process.env.NODE_ENV === 'development',
  useWebSocketSync: true,
  enableContextDebugging: process.env.NODE_ENV === 'development',
  useProgressiveHydration: true,
};

// Environment-based overrides
const ENV_OVERRIDES: Partial<FeatureFlags> = {
  useRedisCache: process.env.VITE_USE_REDIS_CACHE === 'true',
  enablePerformanceMonitoring: process.env.VITE_ENABLE_PERFORMANCE_MONITORING === 'true',
  useWebSocketSync: process.env.VITE_USE_WEBSOCKET_SYNC !== 'false',
  enableContextDebugging: process.env.VITE_ENABLE_CONTEXT_DEBUGGING === 'true',
  useProgressiveHydration: process.env.VITE_USE_PROGRESSIVE_HYDRATION !== 'false',
};

// Remote feature flags (could be fetched from an API)
interface RemoteFeatureFlags {
  flags: Partial<FeatureFlags>;
  targetAudience?: {
    userIds?: string[];
    percentage?: number;
    segments?: string[];
  };
  schedule?: {
    startDate?: string;
    endDate?: string;
  };
}

/**
 * Feature flags manager
 */
class FeatureFlagsManager {
  private flags: FeatureFlags;
  private listeners: ((flags: FeatureFlags) => void)[] = [];
  private remoteFlags: RemoteFeatureFlags[] = [];

  constructor() {
    this.flags = this.loadFlags();
  }

  /**
   * Load feature flags from multiple sources
   */
  private loadFlags(): FeatureFlags {
    // Start with defaults
    let flags = { ...DEFAULT_FEATURE_FLAGS };

    // Apply stored flags
    const storedFlags = featureFlagsStorage.getFlags();
    if (storedFlags) {
      flags = { ...flags, ...storedFlags };
    }

    // Apply environment overrides
    Object.entries(ENV_OVERRIDES).forEach(([key, value]) => {
      if (value !== undefined) {
        (flags as any)[key] = value;
      }
    });

    return flags;
  }

  /**
   * Get current feature flags
   */
  getFlags(): FeatureFlags {
    return { ...this.flags };
  }

  /**
   * Get a specific feature flag
   */
  getFlag(key: keyof FeatureFlags): boolean {
    return this.flags[key];
  }

  /**
   * Update feature flags
   */
  updateFlags(updates: Partial<FeatureFlags>): void {
    const newFlags = { ...this.flags, ...updates };
    this.flags = newFlags;

    // Persist to storage
    featureFlagsStorage.setFlags(newFlags);

    // Notify listeners
    this.listeners.forEach(listener => listener(newFlags));
  }

  /**
   * Subscribe to feature flag changes
   */
  subscribe(listener: (flags: FeatureFlags) => void): () => void {
    this.listeners.push(listener);

    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Load remote feature flags (for A/B testing, gradual rollouts)
   */
  async loadRemoteFlags(apiEndpoint: string): Promise<void> {
    try {
      const response = await fetch(apiEndpoint);
      const remoteFlags: RemoteFeatureFlags[] = await response.json();

      this.remoteFlags = remoteFlags;
      this.applyRemoteFlags();
    } catch (error) {
      console.warn('Failed to load remote feature flags:', error);
    }
  }

  /**
   * Apply remote feature flags based on user context
   */
  private applyRemoteFlags(userId?: string, userSegments: string[] = []): void {
    const applicableFlags: Partial<FeatureFlags> = {};

    this.remoteFlags.forEach(remoteFlag => {
      if (this.shouldApplyRemoteFlag(remoteFlag, userId, userSegments)) {
        Object.assign(applicableFlags, remoteFlag.flags);
      }
    });

    if (Object.keys(applicableFlags).length > 0) {
      this.updateFlags(applicableFlags);
    }
  }

  /**
   * Check if a remote flag should be applied
   */
  private shouldApplyRemoteFlag(
    remoteFlag: RemoteFeatureFlags,
    userId?: string,
    userSegments: string[] = []
  ): boolean {
    const { targetAudience, schedule } = remoteFlag;

    // Check schedule
    if (schedule) {
      const now = new Date();
      if (schedule.startDate && new Date(schedule.startDate) > now) {
        return false;
      }
      if (schedule.endDate && new Date(schedule.endDate) < now) {
        return false;
      }
    }

    // Check target audience
    if (targetAudience) {
      // Specific user IDs
      if (targetAudience.userIds && userId) {
        return targetAudience.userIds.includes(userId);
      }

      // User segments
      if (targetAudience.segments && userSegments.length > 0) {
        return targetAudience.segments.some(segment => userSegments.includes(segment));
      }

      // Percentage rollout
      if (targetAudience.percentage && userId) {
        const hash = this.hashUserId(userId);
        return hash % 100 < targetAudience.percentage;
      }
    }

    return true; // Apply by default if no targeting rules
  }

  /**
   * Simple hash function for consistent percentage rollouts
   */
  private hashUserId(userId: string): number {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      const char = userId.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  /**
   * Reset to defaults
   */
  reset(): void {
    this.flags = { ...DEFAULT_FEATURE_FLAGS };
    featureFlagsStorage.clearFlags();
    this.listeners.forEach(listener => listener(this.flags));
  }

  /**
   * Get debug information
   */
  getDebugInfo(): {
    current: FeatureFlags;
    defaults: FeatureFlags;
    stored: FeatureFlags | null;
    environment: Partial<FeatureFlags>;
    remote: RemoteFeatureFlags[];
  } {
    return {
      current: this.getFlags(),
      defaults: DEFAULT_FEATURE_FLAGS,
      stored: featureFlagsStorage.getFlags(),
      environment: ENV_OVERRIDES,
      remote: this.remoteFlags,
    };
  }
}

// Global instance
export const featureFlagsManager = new FeatureFlagsManager();

/**
 * React hook for using feature flags
 */
import { useState, useEffect } from 'react';

export const useFeatureFlags = (): {
  flags: FeatureFlags;
  getFlag: (key: keyof FeatureFlags) => boolean;
  updateFlags: (updates: Partial<FeatureFlags>) => void;
} => {
  const [flags, setFlags] = useState<FeatureFlags>(featureFlagsManager.getFlags());

  useEffect(() => {
    const unsubscribe = featureFlagsManager.subscribe(setFlags);
    return unsubscribe;
  }, []);

  return {
    flags,
    getFlag: (key: keyof FeatureFlags) => flags[key],
    updateFlags: featureFlagsManager.updateFlags.bind(featureFlagsManager),
  };
};

/**
 * React hook for a specific feature flag
 */
export const useFeatureFlag = (key: keyof FeatureFlags): boolean => {
  const { getFlag } = useFeatureFlags();
  return getFlag(key);
};

/**
 * Higher-order component for feature flag gating
 */
import React from 'react';

export const withFeatureFlag = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  flagKey: keyof FeatureFlags,
  fallback?: React.ComponentType<P> | React.ReactElement | null
) => {
  return React.memo((props: P) => {
    const isEnabled = useFeatureFlag(flagKey);

    if (!isEnabled) {
      if (React.isValidElement(fallback)) {
        return fallback;
      }
      if (fallback) {
        const FallbackComponent = fallback as React.ComponentType<P>;
        return <FallbackComponent {...props} />;
      }
      return null;
    }

    return <WrappedComponent {...props} />;
  });
};

/**
 * Component for feature flag gating
 */
interface FeatureGateProps {
  flag: keyof FeatureFlags;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const FeatureGate: React.FC<FeatureGateProps> = ({ flag, children, fallback = null }) => {
  const isEnabled = useFeatureFlag(flag);
  return isEnabled ? <>{children}</> : <>{fallback}</>;
};

/**
 * Canary deployment utilities
 */
export const canaryUtils = {
  /**
   * Check if user is in canary group
   */
  isInCanaryGroup(userId: string, percentage: number = 10): boolean {
    const hash = featureFlagsManager['hashUserId'](userId);
    return hash % 100 < percentage;
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
  (window as any).__featureFlagsManager = featureFlagsManager;
  (window as any).__featureFlags = {
    manager: featureFlagsManager,
    canaryUtils,
    DEFAULT_FEATURE_FLAGS,
    ENV_OVERRIDES,
  };
}
