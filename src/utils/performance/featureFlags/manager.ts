/**
 * Feature Flags Manager
 * Central manager for feature flags with remote loading and user targeting
 */

import { featureFlagsStorage } from '../../../contexts/GlobalContext/storage';
import { DEFAULT_FEATURE_FLAGS, ENV_OVERRIDES } from './constants';
import type { FeatureFlags, RemoteFeatureFlags } from './types';

/**
 * Feature flags manager
 */
class FeatureFlagsManager {
  private flags: FeatureFlags;
  private listeners: Array<(flags: FeatureFlags) => void> = [];
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
        (flags as Record<string, unknown>)[key] = value;
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