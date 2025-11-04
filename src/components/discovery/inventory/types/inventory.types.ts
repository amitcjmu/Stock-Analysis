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
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}
