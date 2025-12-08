/**
 * ApplicationSelection Types
 * Type definitions for the ApplicationSelection module
 */

import type { Asset } from "@/types/asset";

/**
 * Asset type filter options
 */
export const ASSET_TYPE_FILTERS = {
  ALL: "ALL",
  APPLICATION: "APPLICATION",
  SERVER: "SERVER",
  DATABASE: "DATABASE",
  NETWORK: "NETWORK",  // Bug #971 Fix: Consolidated network types
  STORAGE_DEVICE: "STORAGE_DEVICE",
  SECURITY_DEVICE: "SECURITY_DEVICE",
  VIRTUALIZATION: "VIRTUALIZATION",
  UNKNOWN: "UNKNOWN",
} as const;

/**
 * Bug #971 Fix: Map variations of asset types to standard categories.
 * Backend may return "network" while frontend expects "NETWORK" or "NETWORK_DEVICE".
 */
export const ASSET_TYPE_NORMALIZATION: Record<string, string> = {
  // Network variations
  NETWORK: "NETWORK",
  NETWORKS: "NETWORK",
  NETWORK_DEVICE: "NETWORK",  // Consolidate to NETWORK for display
  NETWORK_DEVICES: "NETWORK",
  // Server variations
  SERVER: "SERVER",
  SERVERS: "SERVER",
  VM: "SERVER",
  VIRTUAL_MACHINE: "SERVER",
  // Database variations
  DATABASE: "DATABASE",
  DATABASES: "DATABASE",
  DB: "DATABASE",
  // Application variations
  APPLICATION: "APPLICATION",
  APPLICATIONS: "APPLICATION",
  APP: "APPLICATION",
  // Storage variations
  STORAGE: "STORAGE_DEVICE",
  STORAGE_DEVICE: "STORAGE_DEVICE",
  // Security variations
  SECURITY: "SECURITY_DEVICE",
  SECURITY_DEVICE: "SECURITY_DEVICE",
  FIREWALL: "SECURITY_DEVICE",
  // Virtualization
  VIRTUALIZATION: "VIRTUALIZATION",
  HYPERVISOR: "VIRTUALIZATION",
};

export type AssetTypeFilter = typeof ASSET_TYPE_FILTERS[keyof typeof ASSET_TYPE_FILTERS];

/**
 * Grouped assets by type with counts
 */
export interface AssetsByType {
  ALL: Asset[];
  APPLICATION: Asset[];
  SERVER: Asset[];
  DATABASE: Asset[];
  COMPONENT: Asset[];
  NETWORK: Asset[];  // Bug #971 Fix: Consolidated network types here
  STORAGE_DEVICE: Asset[];
  SECURITY_DEVICE: Asset[];
  VIRTUALIZATION: Asset[];
  UNKNOWN: Asset[];
}

/**
 * Search and filter state
 */
export interface FilterState {
  searchTerm: string;
  environmentFilter: string;
  criticalityFilter: string;
  selectedAssetTypes: Set<string>;
}

/**
 * Selection state and actions
 */
export interface SelectionState {
  selectedApplications: Set<string>;
  isSubmitting: boolean;
  submitError: string | null;
}

/**
 * Asset pagination response from API
 */
export interface AssetPageData {
  assets: Asset[];
  pagination: {
    current_page: number;
    total_count: number;
    has_next: boolean;
    total_pages: number;
  };
  currentPage: number;
  summary?: AssetSummary;
}

/**
 * Filter options extracted from asset data
 */
export interface FilterOptions {
  environmentOptions: string[];
  criticalityOptions: string[];
}

/**
 * Asset summary statistics from backend API
 * Shared type definition to avoid duplication (DRY principle)
 */
export interface AssetSummary {
  total: number;
  applications: number;
  servers: number;
  databases: number;
  components: number;
  network: number;
  storage: number;
  security: number;
  virtualization: number;
  containers: number;
  load_balancers: number;
  unknown: number;
  discovered?: number;
  pending?: number;
}
