/**
 * Feature Flags
 * Barrel export for all feature flags functionality
 */

// Types
export type { FeatureFlags, RemoteFeatureFlags, FeatureGateProps } from './types';

// Constants
export { DEFAULT_FEATURE_FLAGS, ENV_OVERRIDES } from './constants';

// Manager
export { featureFlagsManager } from './manager';

// Hooks
export { useFeatureFlags, useFeatureFlag } from './hooks';

// Components
export { FeatureGate } from './components';

// Higher-order components
export { withFeatureFlag } from './hoc';

// Utilities
export { canaryUtils } from './utils';