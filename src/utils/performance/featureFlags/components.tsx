/**
 * Feature Flags Components
 * React components for feature flag gating
 */

import React from 'react';
import { useFeatureFlag } from './hooks';
import type { FeatureGateProps } from './types';

/**
 * Component for feature flag gating
 */
export const FeatureGate: React.FC<FeatureGateProps> = ({ flag, children, fallback = null }) => {
  const isEnabled = useFeatureFlag(flag);
  return isEnabled ? <>{children}</> : <>{fallback}</>;
};
