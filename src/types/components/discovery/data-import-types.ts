/**
 * Data Import Component Types
 * 
 * Types for data import selectors, file upload areas, and raw data tables.
 */

import type { ReactNode, ChangeEvent, DragEvent, MouseEvent, FC, ComponentProps, HTMLAttributes } from 'react';
import type { BaseDiscoveryProps, DataImport, ValidationError } from './base-types';
import type { ColumnDefinition, PaginationConfig } from './field-mapping-types';

// Data Import component types
export interface DataImportSelectorProps extends BaseDiscoveryProps {
  availableImports: DataImport[];
  selectedImportId: string | null;
  onImportSelect: (importId: string, event?: MouseEvent<HTMLElement>) => Promise<void> | void;
  loading?: boolean;
  error?: string | null;
  disabled?: boolean;
  enableUpload?: boolean;
  onFileUpload?: (files: File[], event?: ChangeEvent<HTMLInputElement> | DragEvent<HTMLDivElement>) => Promise<void> | void;
  uploadConfig?: UploadConfig;
  enablePreview?: boolean;
  onPreview?: (importId: string, event?: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  enableDelete?: boolean;
  onDelete?: (importId: string, event?: MouseEvent<HTMLButtonElement>) => Promise<boolean> | boolean;
  enableDuplicate?: boolean;
  onDuplicate?: (importId: string, event?: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  filters?: ImportFilter[];
  onFilterChange?: (filters: ImportFilter[], event?: ChangeEvent<HTMLSelectElement | HTMLInputElement>) => void;
  sorting?: SortConfig;
  onSortChange?: (sort: SortConfig, event?: MouseEvent<HTMLButtonElement>) => void;
  layout?: 'list' | 'grid' | 'table';
  gridColumns?: number;
  showMetadata?: boolean;
  showProgress?: boolean;
  showStats?: boolean;
  refreshInterval?: number;
  onRefresh?: (event?: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  customActions?: ImportAction[];
  onCustomAction?: (action: ImportAction, imports: DataImport[], event?: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  multiSelect?: boolean;
  selectedImportIds?: string[];
  onSelectionChange?: (importIds: string[]) => void;
  searchable?: boolean;
  searchQuery?: string;
  onSearchChange?: (query: string, event?: ChangeEvent<HTMLInputElement>) => void;
  theme?: 'light' | 'dark' | 'auto';
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'bordered' | 'filled';
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
  onError?: (error: Error) => void;
}

export interface FileUploadAreaProps extends BaseDiscoveryProps {
  onFileUpload: (files: File[], event?: ChangeEvent<HTMLInputElement> | DragEvent<HTMLDivElement>) => Promise<void> | void;
  acceptedTypes?: string[];
  maxFileSize?: number; // in bytes
  maxFiles?: number;
  multiple?: boolean;
  disabled?: boolean;
  loading?: boolean;
  progress?: number; // 0-100
  error?: string | null;
  dragAndDrop?: boolean;
  showProgress?: boolean;
  showPreview?: boolean;
  enablePaste?: boolean;
  enableUrlUpload?: boolean;
  onUrlUpload?: (url: string, event?: ChangeEvent<HTMLInputElement>) => Promise<void> | void;
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
  chunkSize?: number; // in bytes
  resumableUpload?: boolean;
  encryptionEnabled?: boolean;
  virusScanEnabled?: boolean;
  onUploadComplete?: (result: UploadResult) => void;
  onUploadProgress?: (progress: UploadProgress) => void;
  onUploadError?: (error: UploadError) => void;
  onDragOver?: (event: DragEvent<HTMLDivElement>) => void;
  onDragLeave?: (event: DragEvent<HTMLDivElement>) => void;
  onDrop?: (event: DragEvent<HTMLDivElement>) => void;
  onFileRemove?: (file: File, index: number) => void;
  previewComponent?: FC<{ file: File; onRemove: () => void }>;
  theme?: 'light' | 'dark' | 'auto';
  size?: 'sm' | 'md' | 'lg';
  variant?: 'dashed' | 'solid' | 'filled';
  borderRadius?: 'none' | 'sm' | 'md' | 'lg' | 'full';
  allowedFileCategories?: Array<'document' | 'image' | 'video' | 'audio' | 'archive' | 'code'>;
}

export interface RawDataTableProps<TData = Record<string, unknown>> extends BaseDiscoveryProps {
  data: TData[];
  columns: Array<ColumnDefinition<TData>>;
  loading?: boolean;
  error?: string | null;
  onRowSelect?: (row: TData, event?: MouseEvent<HTMLTableRowElement>) => void;
  selectable?: boolean;
  selectedRows?: TData[];
  onSelectionChange?: (selectedRows: TData[], event?: ChangeEvent<HTMLInputElement>) => void;
  searchable?: boolean;
  searchQuery?: string;
  onSearchChange?: (query: string, event?: ChangeEvent<HTMLInputElement>) => void;
  filterable?: boolean;
  filters?: TableFilter[];
  onFilterChange?: (filters: TableFilter[], event?: ChangeEvent<HTMLSelectElement | HTMLInputElement>) => void;
  sortable?: boolean;
  sorting?: TableSort[];
  onSortChange?: (sorting: TableSort[], event?: MouseEvent<HTMLButtonElement>) => void;
  pagination?: PaginationConfig;
  onPageChange?: (page: number, pageSize: number, event?: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  totalCount?: number;
  serverSide?: boolean;
  onServerSideChange?: (params: ServerSideParams) => Promise<void> | void;
  expandable?: boolean;
  expandedRows?: string[];
  onRowExpand?: (rowId: string, row: TData, event?: MouseEvent<HTMLButtonElement>) => void;
  renderExpandedContent?: (row: TData, index: number) => ReactNode;
  groupable?: boolean;
  groupBy?: keyof TData;
  onGroupByChange?: (groupBy: keyof TData, event?: ChangeEvent<HTMLSelectElement>) => void;
  renderGroupHeader?: (group: string, count: number, rows: TData[]) => ReactNode;
  virtualScrolling?: boolean;
  rowHeight?: number;
  estimatedRowHeight?: number;
  stickyHeader?: boolean;
  stickyColumns?: Array<keyof TData>;
  resizableColumns?: boolean;
  reorderableColumns?: boolean;
  onColumnReorder?: (columns: Array<ColumnDefinition<TData>>, event?: DragEvent<HTMLTableHeaderCellElement>) => void;
  onColumnResize?: (columnId: keyof TData, width: number, event?: MouseEvent<HTMLDivElement>) => void;
  columnVisibility?: Record<keyof TData, boolean>;
  onColumnVisibilityChange?: (visibility: Record<keyof TData, boolean>) => void;
  exportEnabled?: boolean;
  exportFormats?: ExportFormat[];
  onExport?: (format: ExportFormat, data: TData[], event?: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  customActions?: Array<TableAction<TData>>;
  onCustomAction?: (action: TableAction<TData>, rows: TData[], event?: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  onRowClick?: (row: TData, index: number, event: MouseEvent<HTMLTableRowElement>) => void;
  onRowDoubleClick?: (row: TData, index: number, event: MouseEvent<HTMLTableRowElement>) => void;
  onRowContextMenu?: (row: TData, index: number, event: MouseEvent<HTMLTableRowElement>) => void;
  onCellClick?: (row: TData, column: ColumnDefinition<TData>, value: unknown, event: MouseEvent<HTMLTableCellElement>) => void;
  onCellDoubleClick?: (row: TData, column: ColumnDefinition<TData>, value: unknown, event: MouseEvent<HTMLTableCellElement>) => void;
  onCellEdit?: (row: TData, column: ColumnDefinition<TData>, newValue: unknown, oldValue: unknown) => Promise<boolean> | boolean;
  editableColumns?: Array<keyof TData>;
  editMode?: 'inline' | 'modal' | 'drawer';
  renderEditCell?: (row: TData, column: ColumnDefinition<TData>, value: unknown, onChange: (value: unknown) => void, onCancel: () => void, onSave: () => void) => ReactNode;
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
  maxHeight?: number | string;
  minHeight?: number | string;
  fixedLayout?: boolean;
  showRowNumbers?: boolean;
  onValidationError?: (errors: ValidationError[], row: TData) => void;
  validationEnabled?: boolean;
  autoSave?: boolean;
  autoSaveDelay?: number;
  onAutoSave?: (row: TData, changes: Partial<TData>) => Promise<boolean> | boolean;
}

// Supporting types
export interface UploadConfig {
  endpoint: string;
  method: 'POST' | 'PUT' | 'PATCH';
  headers?: Record<string, string>;
  chunkSize?: number; // in bytes, default 1MB
  maxRetries?: number; // default 3
  timeout?: number; // in milliseconds, default 30000
  resumable?: boolean;
  encryption?: boolean;
  compression?: boolean;
  virusScan?: boolean;
  parallelUploads?: number; // max concurrent uploads
  onBeforeUpload?: (file: File) => Promise<boolean> | boolean;
  onAfterUpload?: (result: UploadResult) => Promise<void> | void;
  transformRequest?: (formData: FormData) => FormData;
  transformResponse?: (response: Response) => Promise<UploadResult>;
}

export interface ImportFilter {
  field: string;
  operator: string;
  value: unknown;
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
  handler: (imports: DataImport[], event?: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  disabled?: boolean | ((imports: DataImport[]) => boolean);
  tooltip?: string;
  confirmationRequired?: boolean;
  confirmationMessage?: string | ((imports: DataImport[]) => string);
  variant?: 'primary' | 'secondary' | 'danger' | 'warning' | 'success';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  shortcut?: string;
}

export interface FileValidationRule {
  type: 'size' | 'type' | 'name' | 'extension' | 'mime' | 'dimension' | 'custom';
  parameters: Record<string, unknown>;
  message: string;
  severity?: 'error' | 'warning' | 'info';
  validator?: (file: File) => Promise<boolean> | boolean;
  asyncValidator?: (file: File) => Promise<{ isValid: boolean; message?: string }>;
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
  publicUrl?: string;
  thumbnailUrl?: string;
  metadata?: Record<string, unknown>;
  size?: number;
  mimeType?: string;
  originalName?: string;
  processedName?: string;
  checksum?: string;
  error?: string;
  warnings?: string[];
  uploadedAt?: string;
  processingTime?: number;
}

export interface UploadProgress {
  loaded: number; // bytes loaded
  total: number; // total bytes
  percentage: number; // 0-100
  speed?: number; // bytes per second
  remainingTime?: number; // seconds remaining
  fileName?: string;
  fileIndex?: number; // for multiple file uploads
  totalFiles?: number;
  stage?: 'uploading' | 'processing' | 'validating' | 'complete';
  eta?: Date; // estimated completion time
}

export interface UploadError {
  code: string;
  message: string;
  file?: File;
  fileName?: string;
  retryable?: boolean;
  severity?: 'error' | 'warning' | 'fatal';
  details?: Record<string, unknown>;
  timestamp?: string;
  retryCount?: number;
  maxRetries?: number;
  suggestion?: string;
}

export interface TableFilter {
  column: string;
  operator: string;
  value: unknown;
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
  include?: string[]; // related data to include
  fields?: string[]; // specific fields to return
  expand?: string[]; // expand nested objects
  cursor?: string; // for cursor-based pagination
  totalCount?: boolean; // whether to include total count
}

export interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  mimeType: string;
  description?: string;
  icon?: string | ReactNode;
  maxRows?: number; // max rows for this format
  supportsFiltering?: boolean;
  supportsSorting?: boolean;
  supportsGrouping?: boolean;
  customOptions?: Record<string, unknown>;
  preview?: boolean; // whether format supports preview
}

export interface TableAction<TData = Record<string, unknown>> {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: (rows: TData[], event?: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  disabled?: boolean | ((rows: TData[]) => boolean);
  tooltip?: string | ((rows: TData[]) => string);
  confirmationRequired?: boolean;
  confirmationMessage?: string | ((rows: TData[]) => string);
  variant?: 'primary' | 'secondary' | 'danger' | 'warning' | 'success';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  shortcut?: string;
  position?: 'toolbar' | 'context' | 'both';
  requiresSelection?: boolean;
  maxSelectionCount?: number;
  minSelectionCount?: number;
}