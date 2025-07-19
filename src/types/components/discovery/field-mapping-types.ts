/**
 * Field Mapping Component Types
 * 
 * Types for field mapping components, filters, and related functionality.
 */

import { ReactNode } from 'react';
import { BaseDiscoveryProps, FieldMapping, ValidationError } from './base-types';

// Field Mappings component types
export interface FieldMappingsTabProps extends BaseDiscoveryProps {
  flowId: string;
  onMappingUpdate?: (mapping: FieldMapping) => void;
  showAdvanced?: boolean;
  readonly?: boolean;
  enableBulkOperations?: boolean;
  enableFiltering?: boolean;
  enableSorting?: boolean;
  enableExport?: boolean;
  enableImport?: boolean;
  customActions?: FieldMappingAction[];
  onCustomAction?: (action: FieldMappingAction, mappings: FieldMapping[]) => void;
  validationEnabled?: boolean;
  autoSave?: boolean;
  autoSaveInterval?: number;
  onValidationChange?: (isValid: boolean, errors: ValidationError[]) => void;
  theme?: 'light' | 'dark' | 'auto';
  density?: 'compact' | 'normal' | 'comfortable';
  layout?: 'table' | 'card' | 'list';
}

export interface MappingFiltersProps extends BaseDiscoveryProps {
  filters: MappingFilter[];
  onFilterChange: (filters: MappingFilter[]) => void;
  availableFields: string[];
  searchTerm?: string;
  onSearchChange?: (term: string) => void;
  presetFilters?: FilterPreset[];
  onPresetSelect?: (preset: FilterPreset) => void;
  savePresetEnabled?: boolean;
  onSavePreset?: (name: string, filters: MappingFilter[]) => void;
  clearFiltersEnabled?: boolean;
  onClearFilters?: () => void;
  advancedFiltering?: boolean;
  filterGroups?: FilterGroup[];
  onFilterGroupChange?: (groups: FilterGroup[]) => void;
  quickFilters?: QuickFilter[];
  onQuickFilterToggle?: (filter: QuickFilter) => void;
}

export interface AttributeMappingTableProps extends BaseDiscoveryProps {
  mappings: FieldMapping[];
  onMappingChange: (mappingId: string, newTarget: string) => void;
  onApproveMapping: (mappingId: string) => void;
  onRejectMapping: (mappingId: string, reason?: string) => void;
  loading?: boolean;
  error?: string | null;
  columns?: ColumnDefinition[];
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  selectable?: boolean;
  selectedMappings?: string[];
  onSelectionChange?: (selectedMappings: string[]) => void;
  bulkActions?: BulkAction[];
  onBulkAction?: (action: BulkAction, mappings: string[]) => void;
  pagination?: PaginationConfig;
  onPageChange?: (page: number, pageSize: number) => void;
  expandable?: boolean;
  onRowExpand?: (mappingId: string) => void;
  renderExpandedContent?: (mapping: FieldMapping) => ReactNode;
  virtualScrolling?: boolean;
  rowHeight?: number;
  estimatedRowHeight?: number;
  stickyHeader?: boolean;
  resizableColumns?: boolean;
  reorderableColumns?: boolean;
  onColumnReorder?: (columns: ColumnDefinition[]) => void;
  onColumnResize?: (columnId: string, width: number) => void;
  customRenderers?: Record<string, (value: any, mapping: FieldMapping) => ReactNode>;
  onRowClick?: (mapping: FieldMapping) => void;
  onRowDoubleClick?: (mapping: FieldMapping) => void;
  onRowContextMenu?: (mapping: FieldMapping, event: React.MouseEvent) => void;
  striped?: boolean;
  bordered?: boolean;
  hover?: boolean;
  compact?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'bordered' | 'striped' | 'hover';
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
}

// Supporting types
export interface FieldMappingAction {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: (mappings: FieldMapping[]) => void;
  disabled?: boolean;
  tooltip?: string;
}

export interface FilterPreset {
  id: string;
  name: string;
  description?: string;
  filters: MappingFilter[];
  isDefault?: boolean;
  isShared?: boolean;
  createdBy?: string;
  createdAt?: string;
}

export interface FilterGroup {
  id: string;
  name: string;
  operator: 'and' | 'or';
  filters: MappingFilter[];
  enabled: boolean;
}

export interface QuickFilter {
  id: string;
  label: string;
  filter: MappingFilter;
  active: boolean;
  count?: number;
}

export interface BulkAction {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: (mappings: string[]) => void;
  confirmationRequired?: boolean;
  confirmationMessage?: string;
  disabled?: boolean;
  tooltip?: string;
}

export interface PaginationConfig {
  page: number;
  pageSize: number;
  totalPages?: number;
  totalCount?: number;
  showPageSizeSelect?: boolean;
  pageSizeOptions?: number[];
  showTotal?: boolean;
  showQuickJumper?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export interface MappingFilter {
  field: string;
  operator: 'eq' | 'ne' | 'contains' | 'startsWith' | 'endsWith' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'not_in';
  value: any;
  label?: string;
  enabled?: boolean;
}

export interface ColumnDefinition {
  id: string;
  header: string;
  accessor: string;
  type: 'text' | 'number' | 'boolean' | 'date' | 'custom';
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  editable?: boolean;
  width?: number | string;
  minWidth?: number;
  maxWidth?: number;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, row: any) => ReactNode;
  renderFilter?: (value: any, onChange: (value: any) => void) => ReactNode;
  renderEdit?: (value: any, onChange: (value: any) => void) => ReactNode;
  formatValue?: (value: any) => string;
  parseValue?: (value: string) => any;
  validateValue?: (value: any) => boolean | string;
  tooltip?: string;
  icon?: string | ReactNode;
  sticky?: boolean;
  hidden?: boolean;
  resizable?: boolean;
  reorderable?: boolean;
  metadata?: Record<string, any>;
}