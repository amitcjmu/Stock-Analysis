/**
 * Asset Types - Unified Asset Model
 *
 * These interfaces match the unified Asset model from the backend
 * after the cmdb_assets consolidation.
 */

export interface Asset {
  // Core identification
  id: number;
  client_account_id: string;
  engagement_id: string;
  name: string;
  hostname?: string;
  asset_type: string;

  // Technical details
  ip_address?: string;
  operating_system?: string;
  environment?: string;
  cpu_cores?: number;
  memory_gb?: number;
  storage_gb?: number;

  // Business information
  business_owner?: string;
  technical_owner?: string;
  department?: string;
  business_criticality?: string;
  location?: string;
  business_unit?: string;
  vendor?: string;

  // CMDB Enhancement Fields (Issue #833)
  application_type?: string;
  lifecycle?: string;
  hosting_model?: string;
  server_role?: string;
  security_zone?: string;
  database_type?: string;
  database_version?: string;
  database_size_gb?: number;
  cpu_utilization_percent_max?: number;
  memory_utilization_percent_max?: number;
  storage_free_gb?: number;
  storage_used_gb?: number;
  tech_debt_flags?: string;
  pii_flag?: boolean;
  application_data_classification?: string;
  has_saas_replacement?: boolean;
  risk_level?: string;
  tshirt_size?: string;
  proposed_treatmentplan_rationale?: string;
  annual_cost_estimate?: number;
  backup_policy?: string;
  asset_tags?: string[];

  // Migration information
  six_r_strategy?: string;
  sixr_ready?: boolean;
  migration_complexity?: number;
  migration_priority?: number;
  migration_wave?: number;

  // Dependencies and relationships
  dependencies?: string;
  dependents?: string;

  // Source and audit information
  discovery_source?: string;
  discovery_method?: string;
  discovered_at?: string;
  created_by?: string;
  source_file?: string;

  // Timestamps
  created_at: string;
  updated_at?: string;

  // AI Gap Analysis Status Tracking (Issue #1043)
  ai_gap_analysis_status?: number;  // 0=not started, 1=in progress, 2=completed
  ai_gap_analysis_timestamp?: string;  // Timestamp when AI analysis completed

  // Soft delete fields (Issue #912)
  deleted_at?: string;
  deleted_by?: string;
  is_deleted?: boolean;
}

export interface AssetSummary {
  total: number;
  filtered: number;
  applications: number;
  servers: number;
  databases: number;
  devices: number;
  unknown: number;
  discovered: number;
  pending: number;
  device_breakdown: {
    network: number;
    storage: number;
    security: number;
    infrastructure: number;
    virtualization: number;
  };
}

export interface AssetPagination {
  current_page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface AssetListResponse {
  assets: Asset[];
  pagination: AssetPagination;
  summary?: AssetSummary;
}

export interface AssetFilterParams {
  asset_type?: string;
  environment?: string;
  department?: string;
  business_criticality?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface BulkAssetUpdate {
  asset_ids: string[];
  updates: Partial<Pick<Asset, 'environment' | 'department' | 'business_criticality' | 'asset_type'>>;
}

// Asset type constants
export const ASSET_TYPES = {
  SERVER: 'SERVER',
  APPLICATION: 'APPLICATION',
  DATABASE: 'DATABASE',
  NETWORK_DEVICE: 'NETWORK_DEVICE',
  STORAGE_DEVICE: 'STORAGE_DEVICE',
  SECURITY_DEVICE: 'SECURITY_DEVICE',
  VIRTUALIZATION: 'VIRTUALIZATION',
  UNKNOWN: 'UNKNOWN'
} as const;

export type AssetType = typeof ASSET_TYPES[keyof typeof ASSET_TYPES];

// Six R Strategy constants - Standardized to 6 canonical strategies (October 2025)
// Note: "replace" consolidates both COTS replacement (formerly "repurchase")
// and custom rewrites (formerly "rewrite")
// "retain" is out of scope for migration platform
export const SIX_R_STRATEGIES = {
  REHOST: 'rehost',
  REPLATFORM: 'replatform',
  REFACTOR: 'refactor',
  REARCHITECT: 'rearchitect',
  REPLACE: 'replace',
  RETIRE: 'retire'
} as const;

export type SixRStrategy = typeof SIX_R_STRATEGIES[keyof typeof SIX_R_STRATEGIES];

// Display labels for UI presentation
export const SIX_R_STRATEGY_LABELS: Record<SixRStrategy, string> = {
  rehost: 'Rehost (Lift & Shift)',
  replatform: 'Replatform (Reconfigure)',
  refactor: 'Refactor (Modify Code)',
  rearchitect: 'Rearchitect (Cloud-Native)',
  replace: 'Replace (COTS/SaaS or Rewrite)',
  retire: 'Retire (Decommission)'
};

// Backward compatibility helper - maps old strategy values to new canonical ones
export function normalizeStrategy(strategy: string | undefined): SixRStrategy | undefined {
  if (!strategy) return undefined;

  const normalized = strategy.toLowerCase().trim();

  // Map deprecated strategies to new ones
  const strategyMapping: Record<string, SixRStrategy> = {
    'rewrite': 'replace',
    'repurchase': 'replace',
    'retain': 'rehost' // Fallback since retention is out of scope
  };

  // Check if it's a deprecated strategy
  if (normalized in strategyMapping) {
    return strategyMapping[normalized];
  }

  // Check if it's already a valid canonical strategy
  const validStrategies = Object.values(SIX_R_STRATEGIES);
  if (validStrategies.includes(normalized as SixRStrategy)) {
    return normalized as SixRStrategy;
  }

  // Unknown strategy
  return undefined;
}

// Business criticality constants
export const BUSINESS_CRITICALITY = {
  CRITICAL: 'Critical',
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
  UNKNOWN: 'Unknown'
} as const;

export type BusinessCriticality = typeof BUSINESS_CRITICALITY[keyof typeof BUSINESS_CRITICALITY];
