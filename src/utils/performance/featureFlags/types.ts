/**
 * Feature Flags Types
 * Type definitions for the feature flags system
 */

import type { FeatureFlags } from '../../../contexts/GlobalContext/types';

export type { FeatureFlags };

export interface RemoteFeatureFlags {
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

export interface FeatureGateProps {
  flag: keyof FeatureFlags;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}
