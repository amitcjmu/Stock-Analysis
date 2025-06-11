import { Asset } from '@/types/discovery';

export interface InventoryFilters {
  page?: number;
  page_size?: number;
  filter?: string;
  department?: string;
  environment?: string;
  criticality?: string;
  search?: string;
}

export interface InventorySummary {
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

export interface InventoryPagination {
  current_page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface InventoryResponse {
  assets: Asset[];
  summary: InventorySummary;
  pagination: InventoryPagination;
  last_updated: string | null;
  data_source: string;
  suggested_headers: string[];
  app_mappings: any[];
  unlinked_assets: any[];
  unlinked_summary: {
    total_unlinked: number;
    by_type: Record<string, number>;
  };
  available_departments: string[];
  available_environments: string[];
  available_criticalities: string[];
}

export interface BulkUpdateVariables {
  assetIds: string[];
  updateData: {
    environment?: string;
    department?: string;
    criticality?: string;
    asset_type?: string;
  };
}

export interface ColumnVisibility {
  [key: string]: boolean;
}

export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

export interface AssetTableProps {
  assets: Asset[];
  selectedAssets: string[];
  onSelectAsset: (id: string) => void;
  onSelectAll: (checked: boolean) => void;
  onSort: (key: string) => void;
  sortConfig: SortConfig | null;
  isLoading: boolean;
  error: Error | null;
  columnVisibility: ColumnVisibility;
}

export interface FilterBarProps {
  filters: InventoryFilters;
  onFilterChange: (updates: Partial<InventoryFilters>) => void;
  onReset: () => void;
  availableDepartments: string[];
  availableEnvironments: string[];
  availableCriticalities: string[];
}

export interface BulkEditDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: BulkUpdateVariables['updateData']) => void;
  selectedCount: number;
}
