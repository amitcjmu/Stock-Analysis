/**
 * Data Import Component Types
 * 
 * Types for data import selectors, file upload areas, and raw data tables.
 */

import { ReactNode } from 'react';
import { BaseDiscoveryProps, DataImport } from './base-types';
import { ColumnDefinition, PaginationConfig } from './field-mapping-types';

// Data Import component types
export interface DataImportSelectorProps extends BaseDiscoveryProps {
  availableImports: DataImport[];
  selectedImportId: string | null;
  onImportSelect: (importId: string) => void;
  loading?: boolean;
  error?: string | null;
  enableUpload?: boolean;
  onFileUpload?: (files: File[]) => void;
  uploadConfig?: UploadConfig;
  enablePreview?: boolean;
  onPreview?: (importId: string) => void;
  enableDelete?: boolean;
  onDelete?: (importId: string) => void;
  enableDuplicate?: boolean;
  onDuplicate?: (importId: string) => void;
  filters?: ImportFilter[];
  onFilterChange?: (filters: ImportFilter[]) => void;
  sorting?: SortConfig;
  onSortChange?: (sort: SortConfig) => void;
  layout?: 'list' | 'grid' | 'table';
  gridColumns?: number;
  showMetadata?: boolean;
  showProgress?: boolean;
  showStats?: boolean;
  refreshInterval?: number;
  onRefresh?: () => void;
  customActions?: ImportAction[];
  onCustomAction?: (action: ImportAction, imports: DataImport[]) => void;
}

export interface FileUploadAreaProps extends BaseDiscoveryProps {
  onFileUpload: (files: File[]) => void;
  acceptedTypes?: string[];
  maxFileSize?: number;
  multiple?: boolean;
  disabled?: boolean;
  loading?: boolean;
  progress?: number;
  error?: string | null;
  dragAndDrop?: boolean;
  showProgress?: boolean;
  showPreview?: boolean;
  enablePaste?: boolean;
  enableUrlUpload?: boolean;
  onUrlUpload?: (url: string) => void;
  uploadConfig?: UploadConfig;
  validationRules?: FileValidationRule[];
  onValidationError?: (errors: FileValidationError[]) => void;
  customUploadButton?: ReactNode;
  uploadButtonText?: string;
  uploadButtonIcon?: string | ReactNode;
  description?: string;
  hint?: string;
  examples?: string[];
  showExamples?: boolean;
  compressImages?: boolean;
  maxImageDimensions?: { width: number; height: number };
  autoUpload?: boolean;
  chunkSize?: number;
  resumableUpload?: boolean;
  encryptionEnabled?: boolean;
  virusScanEnabled?: boolean;
  onUploadComplete?: (result: UploadResult) => void;
  onUploadProgress?: (progress: UploadProgress) => void;
  onUploadError?: (error: UploadError) => void;
}

export interface RawDataTableProps extends BaseDiscoveryProps {
  data: any[];
  columns: ColumnDefinition[];
  loading?: boolean;
  error?: string | null;
  onRowSelect?: (row: any) => void;
  selectable?: boolean;
  selectedRows?: any[];
  onSelectionChange?: (selectedRows: any[]) => void;
  searchable?: boolean;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  filterable?: boolean;
  filters?: TableFilter[];
  onFilterChange?: (filters: TableFilter[]) => void;
  sortable?: boolean;
  sorting?: TableSort[];
  onSortChange?: (sorting: TableSort[]) => void;
  pagination?: PaginationConfig;
  onPageChange?: (page: number, pageSize: number) => void;
  totalCount?: number;
  serverSide?: boolean;
  onServerSideChange?: (params: ServerSideParams) => void;
  expandable?: boolean;
  expandedRows?: string[];
  onRowExpand?: (rowId: string) => void;
  renderExpandedContent?: (row: any) => ReactNode;
  groupable?: boolean;
  groupBy?: string;
  onGroupByChange?: (groupBy: string) => void;
  renderGroupHeader?: (group: string, count: number) => ReactNode;
  virtualScrolling?: boolean;
  rowHeight?: number;
  estimatedRowHeight?: number;
  stickyHeader?: boolean;
  stickyColumns?: string[];
  resizableColumns?: boolean;
  reorderableColumns?: boolean;
  onColumnReorder?: (columns: ColumnDefinition[]) => void;
  onColumnResize?: (columnId: string, width: number) => void;
  columnVisibility?: Record<string, boolean>;
  onColumnVisibilityChange?: (visibility: Record<string, boolean>) => void;
  exportEnabled?: boolean;
  exportFormats?: ExportFormat[];
  onExport?: (format: ExportFormat, data: any[]) => void;
  customActions?: TableAction[];
  onCustomAction?: (action: TableAction, rows: any[]) => void;
  onRowClick?: (row: any) => void;
  onRowDoubleClick?: (row: any) => void;
  onRowContextMenu?: (row: any, event: React.MouseEvent) => void;
  onCellClick?: (row: any, column: ColumnDefinition, value: any) => void;
  onCellDoubleClick?: (row: any, column: ColumnDefinition, value: any) => void;
  onCellEdit?: (row: any, column: ColumnDefinition, newValue: any) => void;
  editableColumns?: string[];
  editMode?: 'inline' | 'modal' | 'drawer';
  renderEditCell?: (row: any, column: ColumnDefinition, value: any, onChange: (value: any) => void) => ReactNode;
  striped?: boolean;
  bordered?: boolean;
  hover?: boolean;
  compact?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'bordered' | 'striped' | 'hover';
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
  theme?: 'light' | 'dark' | 'auto';
  density?: 'compact' | 'normal' | 'comfortable';
}

// Supporting types
export interface UploadConfig {
  endpoint: string;
  method: 'POST' | 'PUT';
  headers?: Record<string, string>;
  chunkSize?: number;
  maxRetries?: number;
  timeout?: number;
  resumable?: boolean;
  encryption?: boolean;
  compression?: boolean;
  virusScan?: boolean;
}

export interface ImportFilter {
  field: string;
  operator: string;
  value: any;
  label?: string;
  enabled?: boolean;
}

export interface SortConfig {
  field: string;
  direction: 'asc' | 'desc';
  label?: string;
}

export interface ImportAction {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: (imports: DataImport[]) => void;
  disabled?: boolean;
  tooltip?: string;
}

export interface FileValidationRule {
  type: 'size' | 'type' | 'name' | 'custom';
  parameters: Record<string, any>;
  message: string;
  validator?: (file: File) => boolean;
}

export interface FileValidationError {
  file: File;
  rule: FileValidationRule;
  message: string;
}

export interface UploadResult {
  success: boolean;
  fileId?: string;
  url?: string;
  metadata?: Record<string, any>;
  error?: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  speed?: number;
  remainingTime?: number;
}

export interface UploadError {
  code: string;
  message: string;
  file?: File;
  retryable?: boolean;
}

export interface TableFilter {
  column: string;
  operator: string;
  value: any;
  label?: string;
  enabled?: boolean;
}

export interface TableSort {
  column: string;
  direction: 'asc' | 'desc';
}

export interface ServerSideParams {
  page: number;
  pageSize: number;
  search?: string;
  filters?: TableFilter[];
  sorting?: TableSort[];
  groupBy?: string;
}

export interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  mimeType: string;
  description?: string;
}

export interface TableAction {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: (rows: any[]) => void;
  disabled?: boolean;
  tooltip?: string;
}