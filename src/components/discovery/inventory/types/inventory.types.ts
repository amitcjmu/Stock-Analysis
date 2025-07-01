export interface AssetInventory {
  id: string;
  asset_name: string;
  asset_type?: string;
  environment?: string;
  operating_system?: string;
  location?: string;
  status?: string;
  business_criticality?: string;
  risk_score?: number;
  migration_readiness?: number;
  dependencies?: string;
  last_updated?: string;
  confidence_score?: number;
  criticality?: string;
  [key: string]: any;
}

export interface InventoryProgress {
  total_assets: number;
  classified_assets: number;
  servers: number;
  applications: number;
  databases: number;
  devices: number;
  classification_accuracy: number;
}

export interface InventoryContentProps {
  className?: string;
  flowId?: string;
}

export interface AssetFilters {
  searchTerm: string;
  selectedAssetType: string;
  selectedEnvironment: string;
  showAdvancedFilters: boolean;
}

export interface PaginationState {
  currentPage: number;
  recordsPerPage: number;
}

export interface ClassificationCard {
  type: string;
  label: string;
  count: number;
  icon: any;
  color: string;
}