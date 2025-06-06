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
  department?: string;
  business_criticality?: string;
  location?: string;
  
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

// Six R Strategy constants
export const SIX_R_STRATEGIES = {
  REHOST: 'Rehost',
  REPLATFORM: 'Replatform', 
  REFACTOR: 'Refactor',
  REARCHITECT: 'Rearchitect',
  RETIRE: 'Retire',
  RETAIN: 'Retain'
} as const;

export type SixRStrategy = typeof SIX_R_STRATEGIES[keyof typeof SIX_R_STRATEGIES];

// Business criticality constants
export const BUSINESS_CRITICALITY = {
  CRITICAL: 'Critical',
  HIGH: 'High',
  MEDIUM: 'Medium', 
  LOW: 'Low',
  UNKNOWN: 'Unknown'
} as const;

export type BusinessCriticality = typeof BUSINESS_CRITICALITY[keyof typeof BUSINESS_CRITICALITY]; 