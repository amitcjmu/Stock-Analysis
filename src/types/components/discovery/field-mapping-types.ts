/**
 * Field Mapping Component Types
 * 
 * Types for field mapping components, filters, and related functionality.
 */

import type { ReactNode, MouseEvent, ChangeEvent, FC } from 'react';
import type { BaseDiscoveryProps, FieldMapping, ValidationError } from './base-types';

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
  customRenderers?: Record<string, (value: unknown, mapping: FieldMapping) => ReactNode>;
  onRowClick?: (mapping: FieldMapping) => void;
  onRowDoubleClick?: (mapping: FieldMapping) => void;
  onRowContextMenu?: (mapping: FieldMapping, event: MouseEvent<HTMLTableRowElement>) => void;
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
  value: unknown;
  label?: string;
  enabled?: boolean;
}

export interface ColumnDefinition<TData = Record<string, unknown>> {
  id: keyof TData | string;
  header: string;
  accessor: keyof TData | string;
  type: 'text' | 'number' | 'boolean' | 'date' | 'datetime' | 'email' | 'url' | 'phone' | 'currency' | 'percentage' | 'custom';
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  editable?: boolean;
  required?: boolean;
  width?: number | string;
  minWidth?: number;
  maxWidth?: number;
  align?: 'left' | 'center' | 'right';
  render?: (value: unknown, row: TData, index: number) => ReactNode;
  renderFilter?: (value: unknown, onChange: (value: unknown) => void, column: ColumnDefinition<TData>) => ReactNode;
  renderEdit?: (value: unknown, onChange: (value: unknown) => void, row: TData, column: ColumnDefinition<TData>) => ReactNode;
  formatValue?: (value: unknown, row: TData) => string;
  parseValue?: (value: string, row: TData) => unknown;
  validateValue?: (value: unknown, row: TData) => boolean | string | ValidationError[];
  tooltip?: string | ((row: TData, value: unknown) => string);
  icon?: string | ReactNode;
  sticky?: boolean;
  hidden?: boolean;
  resizable?: boolean;
  reorderable?: boolean;
  sortDirection?: 'asc' | 'desc' | null;
  defaultSort?: 'asc' | 'desc';
  cssClass?: string | ((value: unknown, row: TData) => string);
  metadata?: Record<string, unknown>;
  group?: string;
  description?: string;
  placeholder?: string;
  defaultValue?: unknown;
  options?: Array<{ label: string; value: unknown }>;
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    custom?: (value: unknown, row: TData) => boolean | string;
  };
}