/**
 * Feature Flags Higher-Order Components
 * Non-component utilities for feature flag gating
 */

import React from 'react';
import { useFeatureFlag } from './hooks';
import type { FeatureFlags } from './types';

/**
 * Higher-order component for feature flag gating
 */
export const withFeatureFlag = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  flagKey: keyof FeatureFlags,
  fallback?: React.ComponentType<P> | React.ReactElement | null
): React.ComponentType<P> => {
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