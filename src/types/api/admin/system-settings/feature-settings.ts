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
  conditions: Record<string, any>;
}

export interface ExperimentConfig {
  id: string;
  name: string;
  variants: Record<string, any>;
}

export interface RolloutConfig {
  strategy: string;
  percentage: number;
  criteria: Record<string, any>;
}

export interface ToggleConfig {
  id: string;
  enabled: boolean;
  conditions: Record<string, any>;
}

export interface BetaFeatureConfig {
  id: string;
  enabled: boolean;
  eligibility: Record<string, any>;
}

export interface DeprecatedFeature {
  id: string;
  deprecatedAt: string;
  removalDate: string;
}