/**
 * Feature Flags Hooks
 * React hooks for feature flag management
 */

import { useState, useEffect } from 'react';
import { featureFlagsManager } from './manager';
import type { FeatureFlags } from './types';

/**
 * React hook for using feature flags
 */
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
