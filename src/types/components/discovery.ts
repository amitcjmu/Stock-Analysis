/**
 * Discovery Component Types
 * 
 * Type definitions for discovery-specific components including field mappings,
 * data import, attribute management, and workflow interfaces.
 */

import { ReactNode } from 'react';

// Base discovery component types
export interface BaseDiscoveryProps {
  className?: string;
  children?: ReactNode;
}

export interface FieldMapping {
  id: string;
  sourceField: string;
  targetField: string;
  mappingType: 'direct' | 'transformed' | 'calculated' | 'conditional';
  transformationLogic?: string;
  validationRules?: ValidationRule[];
  confidence: number;
  status: 'pending' | 'approved' | 'rejected' | 'in_review';
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  reviewedBy?: string;
  rejectionReason?: string;
  metadata?: Record<string, any>;
}

export interface CriticalAttribute {
  id: string;
  name: string;
  description: string;
  dataType: string;
  isRequired: boolean;
  defaultValue?: any;
  validationRules: ValidationRule[];
  mappingStatus: 'mapped' | 'unmapped' | 'partially_mapped';
  sourceFields: string[];
  targetField?: string;
  businessRules?: BusinessRule[];
  priority: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  tags: string[];
  metadata: Record<string, any>;
}

export interface DataImport {
  id: string;
  flowId: string;
  fileName: string;
  fileSize: number;
  fileType: string;
  recordsTotal: number;
  recordsProcessed: number;
  recordsValid: number;
  recordsInvalid: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  errors?: ImportError[];
  uploadedAt: string;
  processedAt?: string;
  uploadedBy: string;
  metadata?: Record<string, any>;
}

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

// Critical Attributes component types
export interface CriticalAttributesTabProps extends BaseDiscoveryProps {
  attributes: CriticalAttribute[];
  onAttributeUpdate: (attributeId: string, updates: Partial<CriticalAttribute>) => void;
  flowId: string;
  readonly?: boolean;
  enableBulkOperations?: boolean;
  enableFiltering?: boolean;
  enableSorting?: boolean;
  enableGrouping?: boolean;
  groupBy?: string;
  onGroupByChange?: (groupBy: string) => void;
  enableExport?: boolean;
  customActions?: AttributeAction[];
  onCustomAction?: (action: AttributeAction, attributes: CriticalAttribute[]) => void;
  validationEnabled?: boolean;
  onValidationChange?: (isValid: boolean, errors: ValidationError[]) => void;
  categories?: AttributeCategory[];
  onCategoryFilter?: (categories: string[]) => void;
  priorities?: AttributePriority[];
  onPriorityFilter?: (priorities: string[]) => void;
  layout?: 'table' | 'card' | 'grid' | 'kanban';
  cardLayout?: CardLayoutConfig;
  gridLayout?: GridLayoutConfig;
  kanbanLayout?: KanbanLayoutConfig;
}

export interface AttributeEditorProps extends BaseDiscoveryProps {
  attribute: CriticalAttribute;
  onUpdate: (updates: Partial<CriticalAttribute>) => void;
  onSave: () => void;
  onCancel: () => void;
  readonly?: boolean;
  validationEnabled?: boolean;
  validationErrors?: ValidationError[];
  businessRules?: BusinessRule[];
  onBusinessRuleAdd?: (rule: BusinessRule) => void;
  onBusinessRuleUpdate?: (ruleId: string, updates: Partial<BusinessRule>) => void;
  onBusinessRuleDelete?: (ruleId: string) => void;
  availableDataTypes?: DataTypeOption[];
  availableCategories?: string[];
  availableTags?: string[];
  onTagAdd?: (tag: string) => void;
  onTagRemove?: (tag: string) => void;
  customFields?: CustomField[];
  onCustomFieldUpdate?: (fieldId: string, value: any) => void;
  tabs?: AttributeEditorTab[];
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

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

// Analysis component types
export interface CrewAnalysisPanelProps extends BaseDiscoveryProps {
  analysis: CrewAnalysis[];
  onTriggerAnalysis: () => void;
  loading?: boolean;
  error?: string | null;
  analysisTypes?: AnalysisType[];
  selectedAnalysisType?: string;
  onAnalysisTypeChange?: (type: string) => void;
  parameters?: AnalysisParameters;
  onParametersChange?: (parameters: AnalysisParameters) => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onRefresh?: () => void;
  enableComparison?: boolean;
  comparisonBaseline?: string;
  onComparisonBaselineChange?: (baseline: string) => void;
  enableExport?: boolean;
  exportFormats?: ExportFormat[];
  onExport?: (format: ExportFormat, data: CrewAnalysis[]) => void;
  enableSharing?: boolean;
  onShare?: (analysis: CrewAnalysis[]) => void;
  customActions?: AnalysisAction[];
  onCustomAction?: (action: AnalysisAction, analysis: CrewAnalysis[]) => void;
  layout?: 'list' | 'grid' | 'timeline' | 'chart';
  gridColumns?: number;
  chartType?: ChartType;
  onChartTypeChange?: (type: ChartType) => void;
  filters?: AnalysisFilter[];
  onFilterChange?: (filters: AnalysisFilter[]) => void;
  groupBy?: string;
  onGroupByChange?: (groupBy: string) => void;
  showDetails?: boolean;
  onToggleDetails?: () => void;
  expandedItems?: string[];
  onItemExpand?: (itemId: string) => void;
  renderAnalysisItem?: (analysis: CrewAnalysis) => ReactNode;
  renderAnalysisDetails?: (analysis: CrewAnalysis) => ReactNode;
}

export interface TrainingProgressTabProps extends BaseDiscoveryProps {
  progress: TrainingProgress;
  onProgressUpdate: (updates: Partial<TrainingProgress>) => void;
  flowId: string;
  enableTraining?: boolean;
  onStartTraining?: () => void;
  onStopTraining?: () => void;
  onPauseTraining?: () => void;
  onResumeTraining?: () => void;
  trainingStatus?: TrainingStatus;
  trainingMetrics?: TrainingMetrics;
  onMetricsRefresh?: () => void;
  enableModelComparison?: boolean;
  availableModels?: ModelInfo[];
  selectedModel?: string;
  onModelSelect?: (modelId: string) => void;
  enableHyperparameterTuning?: boolean;
  hyperparameters?: Hyperparameters;
  onHyperparameterChange?: (params: Hyperparameters) => void;
  enableDatasetManagement?: boolean;
  datasets?: Dataset[];
  selectedDataset?: string;
  onDatasetSelect?: (datasetId: string) => void;
  onDatasetUpload?: (files: File[]) => void;
  enableValidation?: boolean;
  validationConfig?: ValidationConfig;
  onValidationConfigChange?: (config: ValidationConfig) => void;
  enableExport?: boolean;
  onExportModel?: () => void;
  onExportMetrics?: () => void;
  customActions?: TrainingAction[];
  onCustomAction?: (action: TrainingAction) => void;
  chartConfig?: ChartConfig;
  onChartConfigChange?: (config: ChartConfig) => void;
  showLogs?: boolean;
  logs?: TrainingLog[];
  onLogsRefresh?: () => void;
  logLevel?: LogLevel;
  onLogLevelChange?: (level: LogLevel) => void;
}

// Supporting types for complex component props
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

export interface ValidationRule {
  type: string;
  parameters: Record<string, any>;
  message: string;
  severity?: 'error' | 'warning' | 'info';
}

export interface BusinessRule {
  id: string;
  name: string;
  description: string;
  logic: string;
  priority: number;
  enabled: boolean;
  conditions: RuleCondition[];
  actions: RuleAction[];
  metadata?: Record<string, any>;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  severity: 'error' | 'warning' | 'info';
  value?: any;
  metadata?: Record<string, any>;
}

export interface ImportError {
  row: number;
  column: string;
  message: string;
  severity: 'error' | 'warning';
  code?: string;
  suggestion?: string;
}

export interface MappingFilter {
  field: string;
  operator: 'eq' | 'ne' | 'contains' | 'startsWith' | 'endsWith' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'not_in';
  value: any;
  label?: string;
  enabled?: boolean;
}

export interface CrewAnalysis {
  id: string;
  analysisType: string;
  findings: AnalysisFinding[];
  recommendations: string[];
  confidence: number;
  executedAt: string;
  executedBy: string;
  status: 'completed' | 'in_progress' | 'failed';
  metadata: Record<string, any>;
}

export interface TrainingProgress {
  totalSamples: number;
  processedSamples: number;
  accuracy: number;
  lastTrainingRun: string;
  modelVersion: string;
  status: 'idle' | 'training' | 'paused' | 'completed' | 'failed';
  elapsedTime: number;
  estimatedTimeRemaining?: number;
  currentEpoch: number;
  totalEpochs: number;
  loss: number;
  validationLoss?: number;
  metrics: Record<string, number>;
}

// Additional supporting interfaces
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

export interface AttributeAction {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: (attributes: CriticalAttribute[]) => void;
  disabled?: boolean;
  tooltip?: string;
}

export interface AttributeCategory {
  id: string;
  name: string;
  description?: string;
  color?: string;
  icon?: string | ReactNode;
}

export interface AttributePriority {
  id: string;
  name: string;
  level: number;
  color?: string;
  icon?: string | ReactNode;
}

export interface CardLayoutConfig {
  columns: number;
  spacing: number;
  showHeaders: boolean;
  showMetadata: boolean;
  compactMode: boolean;
}

export interface GridLayoutConfig {
  columns: number;
  rowHeight: number;
  spacing: number;
  responsive: boolean;
  breakpoints: Record<string, number>;
}

export interface KanbanLayoutConfig {
  swimlanes: string[];
  cardHeight: number;
  spacing: number;
  dragAndDrop: boolean;
  collapsible: boolean;
}

export interface DataTypeOption {
  value: string;
  label: string;
  description?: string;
  validator?: (value: any) => boolean;
  formatter?: (value: any) => string;
  parser?: (value: string) => any;
}

export interface CustomField {
  id: string;
  name: string;
  type: 'text' | 'number' | 'boolean' | 'date' | 'select' | 'multiselect' | 'textarea';
  label: string;
  placeholder?: string;
  required?: boolean;
  options?: { value: any; label: string }[];
  validation?: ValidationRule[];
  value?: any;
  metadata?: Record<string, any>;
}

export interface AttributeEditorTab {
  id: string;
  label: string;
  icon?: string | ReactNode;
  content: ReactNode;
  disabled?: boolean;
  badge?: string | number;
}

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

export interface AnalysisType {
  id: string;
  name: string;
  description?: string;
  parameters?: AnalysisParameter[];
  icon?: string | ReactNode;
}

export interface AnalysisParameters {
  [key: string]: any;
}

export interface AnalysisParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'multiselect';
  label: string;
  description?: string;
  required?: boolean;
  defaultValue?: any;
  options?: { value: any; label: string }[];
  min?: number;
  max?: number;
  step?: number;
}

export interface AnalysisAction {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: (analysis: CrewAnalysis[]) => void;
  disabled?: boolean;
  tooltip?: string;
}

export interface ChartType {
  id: string;
  name: string;
  icon?: string | ReactNode;
  config?: Record<string, any>;
}

export interface AnalysisFilter {
  field: string;
  operator: string;
  value: any;
  label?: string;
  enabled?: boolean;
}

export interface AnalysisFinding {
  type: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  recommendation: string;
  impact: string;
  confidence: number;
  metadata?: Record<string, any>;
}

export interface TrainingStatus {
  status: 'idle' | 'training' | 'paused' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  progress: number;
  currentEpoch: number;
  totalEpochs: number;
  message?: string;
}

export interface TrainingMetrics {
  accuracy: number;
  loss: number;
  validationAccuracy?: number;
  validationLoss?: number;
  precision?: number;
  recall?: number;
  f1Score?: number;
  customMetrics?: Record<string, number>;
  history: MetricHistory[];
}

export interface MetricHistory {
  epoch: number;
  timestamp: string;
  metrics: Record<string, number>;
}

export interface ModelInfo {
  id: string;
  name: string;
  version: string;
  description?: string;
  architecture: string;
  parameters: number;
  trainingData?: string;
  accuracy?: number;
  size: number;
  createdAt: string;
  metadata?: Record<string, any>;
}

export interface Hyperparameters {
  learningRate: number;
  batchSize: number;
  epochs: number;
  optimizer: string;
  momentum?: number;
  weightDecay?: number;
  dropout?: number;
  hiddenLayers?: number;
  hiddenUnits?: number;
  activationFunction?: string;
  lossFunction?: string;
  customParameters?: Record<string, any>;
}

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  size: number;
  recordCount: number;
  features: number;
  labels?: string[];
  splitRatio?: { train: number; validation: number; test: number };
  createdAt: string;
  metadata?: Record<string, any>;
}

export interface ValidationConfig {
  enabled: boolean;
  splitRatio: number;
  stratified: boolean;
  crossValidation: boolean;
  folds?: number;
  metrics: string[];
  earlyStoppingEnabled: boolean;
  patience?: number;
  minDelta?: number;
}

export interface TrainingAction {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: () => void;
  disabled?: boolean;
  tooltip?: string;
}

export interface ChartConfig {
  chartType: string;
  metrics: string[];
  timeRange: string;
  aggregation: string;
  showLegend: boolean;
  showGrid: boolean;
  colors: string[];
  width?: number;
  height?: number;
}

export interface TrainingLog {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  source?: string;
  metadata?: Record<string, any>;
}

export interface RuleCondition {
  field: string;
  operator: string;
  value: any;
  logicalOperator?: 'and' | 'or';
}

export interface RuleAction {
  type: string;
  parameters: Record<string, any>;
  description?: string;
}

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';