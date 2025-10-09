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
  NETWORK_DEVICE: "NETWORK_DEVICE",
  STORAGE_DEVICE: "STORAGE_DEVICE",
  SECURITY_DEVICE: "SECURITY_DEVICE",
  VIRTUALIZATION: "VIRTUALIZATION",
  UNKNOWN: "UNKNOWN",
} as const;

export type AssetTypeFilter = typeof ASSET_TYPE_FILTERS[keyof typeof ASSET_TYPE_FILTERS];

/**
 * Grouped assets by type with counts
 */
export interface AssetsByType {
  ALL: Asset[];
  APPLICATION: Asset[];
  SERVER: Asset[];
  DATABASE: Asset[];
  NETWORK_DEVICE: Asset[];
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
}

/**
 * Filter options extracted from asset data
 */
export interface FilterOptions {
  environmentOptions: string[];
  criticalityOptions: string[];
}
