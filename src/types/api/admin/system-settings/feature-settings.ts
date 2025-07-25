/**
 * Feature Settings Configuration Types
 *
 * Feature management configuration including feature flags, experiments,
 * rollouts, toggles, and beta features.
 *
 * Generated with CC for modular admin type organization.
 */

// Feature Settings Configuration
export interface FeatureSettings {
  flags: FeatureFlag[];
  experiments: ExperimentConfig[];
  rollouts: RolloutConfig[];
  toggles: ToggleConfig[];
  beta: BetaFeatureConfig[];
  deprecated: DeprecatedFeature[];
}

export interface FeatureFlag {
  name: string;
  enabled: boolean;
  percentage: number;
  conditions: Record<string, string | number | boolean | null>;
}

export interface ExperimentConfig {
  id: string;
  name: string;
  variants: Record<string, string | number | boolean | null>;
}

export interface RolloutConfig {
  strategy: string;
  percentage: number;
  criteria: Record<string, string | number | boolean | null>;
}

export interface ToggleConfig {
  id: string;
  enabled: boolean;
  conditions: Record<string, string | number | boolean | null>;
}

export interface BetaFeatureConfig {
  id: string;
  enabled: boolean;
  eligibility: Record<string, string | number | boolean | null>;
}

export interface DeprecatedFeature {
  id: string;
  deprecatedAt: string;
  removalDate: string;
}
