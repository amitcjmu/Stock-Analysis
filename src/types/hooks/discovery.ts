/**
 * Discovery Hook Types
 * 
 * Type definitions for discovery-specific hooks including attribute mapping,
 * flow detection, data import, and workflow orchestration patterns.
 */

import { ReactNode } from 'react';

// Base hook types
export interface BaseHookParams {
  enabled?: boolean;
  suspense?: boolean;
  retry?: boolean | number;
  retryDelay?: number;
  staleTime?: number;
  cacheTime?: number;
  refetchOnMount?: boolean;
  refetchOnWindowFocus?: boolean;
  refetchInterval?: number;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
  onSettled?: (data: any, error: Error | null) => void;
}

export interface BaseHookReturn<T = any> {
  data: T | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isSuccess: boolean;
  isIdle: boolean;
  isFetching: boolean;
  isStale: boolean;
  refetch: () => Promise<any>;
  remove: () => void;
  status: 'idle' | 'loading' | 'error' | 'success';
  fetchStatus: 'idle' | 'fetching' | 'paused';
  dataUpdatedAt: number;
  errorUpdatedAt: number;
}

// Attribute Mapping hook types
export interface UseAttributeMappingParams extends BaseHookParams {
  flowId?: string;
  dataImportId?: string;
  autoDetectFlow?: boolean;
  fallbackToSession?: boolean;
  requirePhase?: string;
  skipValidation?: boolean;
  includeAnalysis?: boolean;
  includeCriticalAttributes?: boolean;
  includeProgress?: boolean;
  includeMetadata?: boolean;
  refreshInterval?: number;
  onFlowDetected?: (flowId: string) => void;
  onMappingUpdate?: (mappings: FieldMapping[]) => void;
  onCriticalAttributeUpdate?: (attributes: CriticalAttribute[]) => void;
  onProgressUpdate?: (progress: MappingProgress) => void;
  onAnalysisComplete?: (analysis: CrewAnalysis[]) => void;
  onValidationComplete?: (isValid: boolean, errors: ValidationError[]) => void;
}

export interface UseAttributeMappingReturn {
  // Core data
  mappings: FieldMapping[];
  criticalAttributes: CriticalAttribute[];
  crewAnalysis: CrewAnalysis[];
  agenticData: { attributes: any[] };
  
  // Flow context
  flowId: string | null;
  flowState: FlowState | null;
  flow: DiscoveryFlowData | null;
  
  // Data imports
  dataImportId: string | null;
  availableDataImports: DataImport[];
  selectedDataImportId: string | null;
  
  // Progress tracking
  mappingProgress: MappingProgress;
  flowProgress: number;
  currentPhase: string;
  
  // Loading states
  isAgenticLoading: boolean;
  isFlowStateLoading: boolean;
  isAnalyzing: boolean;
  isMappingLoading: boolean;
  isCriticalAttributesLoading: boolean;
  isProgressLoading: boolean;
  
  // Error states
  agenticError: string | null;
  flowStateError: string | null;
  mappingError: string | null;
  criticalAttributesError: string | null;
  
  // Actions
  actions: AttributeMappingActions;
  
  // Status checks
  hasActiveFlow: boolean;
  canContinueToDataCleansing: () => boolean;
  canContinueToInventory: () => boolean;
  canContinueToAssessment: () => boolean;
  
  // Agent interactions
  agentClarifications: AgentClarification[];
  isClarificationsLoading: boolean;
  clarificationsError: string | null;
  refetchClarifications: () => Promise<void>;
  
  // Auto-detection
  urlFlowId: string | null;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  emergencyFlowId: string | null;
  finalFlowId: string | null;
  hasEffectiveFlow: boolean;
  flowList: DiscoveryFlowData[];
  isFlowListLoading: boolean;
  flowListError: string | null;
  
  // Validation
  validationResults: ValidationResult[];
  isValidationLoading: boolean;
  validationError: string | null;
  validateMappings: () => Promise<boolean>;
  validateCriticalAttributes: () => Promise<boolean>;
  validateAll: () => Promise<boolean>;
  
  // Metadata
  metadata: Record<string, any>;
  updateMetadata: (updates: Record<string, any>) => void;
}

export interface AttributeMappingActions {
  // Field mapping actions
  handleTriggerFieldMappingCrew: () => Promise<void>;
  handleApproveMapping: (mappingId: string) => Promise<void>;
  handleRejectMapping: (mappingId: string, rejectionReason?: string) => Promise<void>;
  handleMappingChange: (mappingId: string, newTarget: string) => Promise<void>;
  handleBulkMappingUpdate: (updates: BulkMappingUpdate[]) => Promise<void>;
  
  // Attribute actions
  handleAttributeUpdate: (attributeId: string, updates: Partial<CriticalAttribute>) => Promise<void>;
  handleAttributeCreate: (attribute: Omit<CriticalAttribute, 'id'>) => Promise<void>;
  handleAttributeDelete: (attributeId: string) => Promise<void>;
  handleAttributeValidate: (attributeId: string) => Promise<ValidationResult>;
  
  // Data import actions
  handleDataImportSelection: (importId: string) => Promise<void>;
  handleDataImportUpload: (file: File) => Promise<void>;
  handleDataImportDelete: (importId: string) => Promise<void>;
  
  // Analysis actions
  triggerCrewAnalysis: (analysisType?: string) => Promise<void>;
  triggerFieldMappingAnalysis: () => Promise<void>;
  triggerAttributeAnalysis: () => Promise<void>;
  triggerValidationAnalysis: () => Promise<void>;
  
  // Refresh actions
  refetchAgentic: () => Promise<void>;
  refetchCriticalAttributes: () => Promise<void>;
  refetchMappings: () => Promise<void>;
  refetchProgress: () => Promise<void>;
  refetchAll: () => Promise<void>;
  
  // Status checks
  checkMappingApprovalStatus: (dataImportId: string) => Promise<MappingApprovalStatus>;
  checkAttributeCompleteness: () => Promise<AttributeCompletenessStatus>;
  checkFlowReadiness: (targetPhase?: string) => Promise<FlowReadinessStatus>;
  
  // Navigation actions
  navigateToPhase: (phase: string) => void;
  navigateToDataCleansing: () => void;
  navigateToInventory: () => void;
  navigateToAssessment: () => void;
  
  // Persistence actions
  saveProgress: () => Promise<void>;
  saveToSession: () => void;
  loadFromSession: () => void;
  clearSession: () => void;
  
  // Export/Import actions
  exportMappings: (format: ExportFormat) => Promise<void>;
  importMappings: (file: File) => Promise<void>;
  exportCriticalAttributes: (format: ExportFormat) => Promise<void>;
  importCriticalAttributes: (file: File) => Promise<void>;
}

// Flow Detection hook types
export interface UseFlowDetectionParams extends BaseHookParams {
  autoDetect?: boolean;
  fallbackToSession?: boolean;
  requirePhase?: string;
  skipValidation?: boolean;
  enableEmergencyFallback?: boolean;
  enableUrlParsing?: boolean;
  enableLocalStorage?: boolean;
  enableAutoRedirect?: boolean;
  onFlowDetected?: (flowId: string, source: FlowDetectionSource) => void;
  onFlowNotFound?: () => void;
  onFlowValidationFailed?: (flowId: string, error: Error) => void;
  onAutoRedirect?: (path: string) => void;
}

export interface UseFlowDetectionReturn {
  // Detected flow IDs
  urlFlowId: string | null;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  emergencyFlowId: string | null;
  finalFlowId: string | null;
  sessionFlowId: string | null;
  
  // Detection status
  hasEffectiveFlow: boolean;
  isDetecting: boolean;
  detectionComplete: boolean;
  detectionSource: FlowDetectionSource | null;
  
  // Flow list
  flowList: DiscoveryFlowData[];
  isFlowListLoading: boolean;
  flowListError: string | null;
  
  // Navigation
  pathname: string;
  navigate: (path: string) => void;
  
  // Actions
  forceDetection: () => Promise<void>;
  clearDetection: () => void;
  setManualFlow: (flowId: string) => void;
  validateFlow: (flowId: string) => Promise<boolean>;
  
  // Debugging
  detectionDebug: FlowDetectionDebug;
  detectionHistory: FlowDetectionHistoryEntry[];
  
  // Metadata
  detectionMetadata: Record<string, any>;
}

// Field Mappings hook types
export interface UseFieldMappingsParams extends BaseHookParams {
  flowId: string;
  dataImportId?: string;
  autoRefresh?: boolean;
  includeValidation?: boolean;
  includeAnalysis?: boolean;
  includeProgress?: boolean;
  filterBy?: MappingFilter[];
  sortBy?: MappingSortConfig;
  onMappingUpdate?: (mapping: FieldMapping) => void;
  onMappingValidated?: (mapping: FieldMapping, result: ValidationResult) => void;
  onBulkUpdate?: (mappings: FieldMapping[]) => void;
}

export interface UseFieldMappingsReturn extends BaseHookReturn<FieldMapping[]> {
  mappings: FieldMapping[];
  filteredMappings: FieldMapping[];
  sortedMappings: FieldMapping[];
  totalMappings: number;
  pendingMappings: number;
  approvedMappings: number;
  rejectedMappings: number;
  
  // Actions
  updateMapping: (mappingId: string, updates: Partial<FieldMapping>) => Promise<void>;
  deleteMapping: (mappingId: string) => Promise<void>;
  bulkUpdateMappings: (updates: BulkMappingUpdate[]) => Promise<void>;
  approveMapping: (mappingId: string) => Promise<void>;
  rejectMapping: (mappingId: string, reason?: string) => Promise<void>;
  validateMapping: (mappingId: string) => Promise<ValidationResult>;
  
  // Filtering and sorting
  applyFilters: (filters: MappingFilter[]) => void;
  clearFilters: () => void;
  applySorting: (sort: MappingSortConfig) => void;
  clearSorting: () => void;
  
  // Search
  searchMappings: (query: string) => FieldMapping[];
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  
  // Selection
  selectedMappings: string[];
  setSelectedMappings: (mappingIds: string[]) => void;
  selectAllMappings: () => void;
  clearSelection: () => void;
  
  // Validation
  validationResults: Record<string, ValidationResult>;
  isValidationLoading: boolean;
  validateAllMappings: () => Promise<Record<string, ValidationResult>>;
  
  // Progress
  progress: MappingProgress;
  isProgressLoading: boolean;
  refreshProgress: () => Promise<void>;
  
  // Export/Import
  exportMappings: (format: ExportFormat) => Promise<void>;
  importMappings: (file: File) => Promise<void>;
}

// Critical Attributes hook types
export interface UseCriticalAttributesParams extends BaseHookParams {
  flowId: string;
  autoRefresh?: boolean;
  filterByStatus?: string[];
  filterByCategory?: string[];
  filterByPriority?: string[];
  includeValidation?: boolean;
  includeBusinessRules?: boolean;
  sortBy?: AttributeSortConfig;
  onAttributeUpdate?: (attribute: CriticalAttribute) => void;
  onAttributeValidated?: (attribute: CriticalAttribute, result: ValidationResult) => void;
  onBusinessRuleUpdate?: (attributeId: string, rules: BusinessRule[]) => void;
}

export interface UseCriticalAttributesReturn extends BaseHookReturn<CriticalAttribute[]> {
  attributes: CriticalAttribute[];
  filteredAttributes: CriticalAttribute[];
  sortedAttributes: CriticalAttribute[];
  totalAttributes: number;
  mappedAttributes: number;
  unmappedAttributes: number;
  partiallyMappedAttributes: number;
  
  // Actions
  updateAttribute: (attributeId: string, updates: Partial<CriticalAttribute>) => Promise<void>;
  createAttribute: (attribute: Omit<CriticalAttribute, 'id'>) => Promise<void>;
  deleteAttribute: (attributeId: string) => Promise<void>;
  validateAttribute: (attributeId: string) => Promise<ValidationResult>;
  
  // Business rules
  addBusinessRule: (attributeId: string, rule: BusinessRule) => Promise<void>;
  updateBusinessRule: (attributeId: string, ruleId: string, updates: Partial<BusinessRule>) => Promise<void>;
  deleteBusinessRule: (attributeId: string, ruleId: string) => Promise<void>;
  validateBusinessRules: (attributeId: string) => Promise<ValidationResult>;
  
  // Filtering and sorting
  applyFilters: (filters: AttributeFilter[]) => void;
  clearFilters: () => void;
  applySorting: (sort: AttributeSortConfig) => void;
  clearSorting: () => void;
  
  // Categories and priorities
  categories: string[];
  priorities: string[];
  updateCategory: (attributeId: string, category: string) => Promise<void>;
  updatePriority: (attributeId: string, priority: string) => Promise<void>;
  
  // Validation
  validationResults: Record<string, ValidationResult>;
  isValidationLoading: boolean;
  validateAllAttributes: () => Promise<Record<string, ValidationResult>>;
  
  // Completeness
  completenessStatus: AttributeCompletenessStatus;
  isCompletenessLoading: boolean;
  checkCompleteness: () => Promise<AttributeCompletenessStatus>;
  
  // Export/Import
  exportAttributes: (format: ExportFormat) => Promise<void>;
  importAttributes: (file: File) => Promise<void>;
}

// Import Data hook types
export interface UseImportDataParams extends BaseHookParams {
  flowId: string;
  includeMetadata?: boolean;
  pageSize?: number;
  autoRefresh?: boolean;
  filterBy?: ImportFilter[];
  sortBy?: ImportSortConfig;
  onImportComplete?: (importData: DataImport) => void;
  onImportError?: (error: ImportError) => void;
  onFileSelect?: (file: File) => void;
}

export interface UseImportDataReturn extends BaseHookReturn<DataImport[]> {
  imports: DataImport[];
  filteredImports: DataImport[];
  sortedImports: DataImport[];
  selectedImport: DataImport | null;
  totalImports: number;
  completedImports: number;
  failedImports: number;
  processingImports: number;
  
  // Actions
  selectImport: (importId: string) => Promise<void>;
  refreshImports: () => Promise<void>;
  uploadFile: (file: File) => Promise<DataImport>;
  deleteImport: (importId: string) => Promise<void>;
  retryImport: (importId: string) => Promise<void>;
  
  // File upload
  uploadProgress: number;
  isUploading: boolean;
  uploadError: string | null;
  cancelUpload: () => void;
  
  // Preview
  previewData: (importId: string) => Promise<PreviewData>;
  isPreviewLoading: boolean;
  previewError: string | null;
  
  // Validation
  validateImport: (importId: string) => Promise<ImportValidationResult>;
  isValidationLoading: boolean;
  validationError: string | null;
  
  // Filtering and sorting
  applyFilters: (filters: ImportFilter[]) => void;
  clearFilters: () => void;
  applySorting: (sort: ImportSortConfig) => void;
  clearSorting: () => void;
  
  // Statistics
  importStatistics: ImportStatistics;
  isStatisticsLoading: boolean;
  refreshStatistics: () => Promise<void>;
}

// Crew Analysis hook types
export interface UseCrewAnalysisParams extends BaseHookParams {
  flowId: string;
  analysisTypes?: string[];
  autoTrigger?: boolean;
  triggerOnDataChange?: boolean;
  refreshInterval?: number;
  includeRecommendations?: boolean;
  includeMetadata?: boolean;
  onAnalysisComplete?: (analysis: CrewAnalysis[]) => void;
  onAnalysisError?: (error: Error) => void;
  onRecommendationGenerated?: (recommendations: string[]) => void;
}

export interface UseCrewAnalysisReturn extends BaseHookReturn<CrewAnalysis[]> {
  analysis: CrewAnalysis[];
  filteredAnalysis: CrewAnalysis[];
  latestAnalysis: CrewAnalysis | null;
  totalAnalyses: number;
  completedAnalyses: number;
  failedAnalyses: number;
  inProgressAnalyses: number;
  
  // Actions
  triggerAnalysis: (analysisType?: string, parameters?: Record<string, any>) => Promise<void>;
  retryAnalysis: (analysisId: string) => Promise<void>;
  cancelAnalysis: (analysisId: string) => Promise<void>;
  deleteAnalysis: (analysisId: string) => Promise<void>;
  
  // Analysis types
  availableAnalysisTypes: AnalysisType[];
  selectedAnalysisType: string | null;
  setSelectedAnalysisType: (type: string) => void;
  
  // Parameters
  analysisParameters: Record<string, any>;
  setAnalysisParameters: (params: Record<string, any>) => void;
  resetParameters: () => void;
  
  // Recommendations
  recommendations: string[];
  isRecommendationsLoading: boolean;
  generateRecommendations: (analysisId: string) => Promise<string[]>;
  
  // Comparison
  compareAnalyses: (analysisIds: string[]) => Promise<AnalysisComparison>;
  isComparisonLoading: boolean;
  comparisonResult: AnalysisComparison | null;
  
  // Export
  exportAnalysis: (analysisId: string, format: ExportFormat) => Promise<void>;
  exportAllAnalyses: (format: ExportFormat) => Promise<void>;
  
  // Filtering
  applyFilters: (filters: AnalysisFilter[]) => void;
  clearFilters: () => void;
  
  // History
  analysisHistory: CrewAnalysis[];
  isHistoryLoading: boolean;
  loadHistory: (limit?: number) => Promise<void>;
}

// Training Progress hook types
export interface UseTrainingProgressParams extends BaseHookParams {
  flowId: string;
  modelId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
  includeMetrics?: boolean;
  includeLogs?: boolean;
  onTrainingComplete?: (progress: TrainingProgress) => void;
  onTrainingError?: (error: Error) => void;
  onModelReady?: (modelInfo: ModelInfo) => void;
}

export interface UseTrainingProgressReturn extends BaseHookReturn<TrainingProgress> {
  progress: TrainingProgress;
  metrics: TrainingMetrics | null;
  logs: TrainingLog[];
  status: TrainingStatus;
  
  // Actions
  startTraining: (config?: TrainingConfig) => Promise<void>;
  stopTraining: () => Promise<void>;
  pauseTraining: () => Promise<void>;
  resumeTraining: () => Promise<void>;
  resetTraining: () => Promise<void>;
  
  // Configuration
  trainingConfig: TrainingConfig;
  updateTrainingConfig: (updates: Partial<TrainingConfig>) => void;
  resetConfig: () => void;
  
  // Models
  availableModels: ModelInfo[];
  selectedModel: ModelInfo | null;
  selectModel: (modelId: string) => void;
  
  // Datasets
  availableDatasets: Dataset[];
  selectedDataset: Dataset | null;
  selectDataset: (datasetId: string) => void;
  uploadDataset: (file: File) => Promise<Dataset>;
  
  // Hyperparameters
  hyperparameters: Hyperparameters;
  updateHyperparameters: (updates: Partial<Hyperparameters>) => void;
  resetHyperparameters: () => void;
  optimizeHyperparameters: () => Promise<Hyperparameters>;
  
  // Validation
  validationConfig: ValidationConfig;
  updateValidationConfig: (updates: Partial<ValidationConfig>) => void;
  runValidation: () => Promise<ValidationResult>;
  
  // Export
  exportModel: () => Promise<void>;
  exportMetrics: (format: ExportFormat) => Promise<void>;
  exportLogs: (format: ExportFormat) => Promise<void>;
  
  // Monitoring
  isMonitoring: boolean;
  startMonitoring: () => void;
  stopMonitoring: () => void;
  
  // Comparison
  compareModels: (modelIds: string[]) => Promise<ModelComparison>;
  isComparisonLoading: boolean;
  comparisonResult: ModelComparison | null;
}

// Supporting types
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

export interface MappingProgress {
  totalMappings: number;
  completedMappings: number;
  pendingMappings: number;
  approvedMappings: number;
  rejectedMappings: number;
  progressPercentage: number;
  lastUpdated: string;
}

export interface FlowState {
  flowId: string;
  currentPhase: string;
  nextPhase?: string;
  previousPhase?: string;
  phaseCompletion: Record<string, boolean>;
  phaseData: Record<string, any>;
  agentInsights: Record<string, any>;
  agentProgress: Record<string, number>;
  agentStatus: Record<string, string>;
  createdAt: string;
  updatedAt: string;
}

export interface DiscoveryFlowData {
  id: string;
  flowId: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  flowName: string;
  flowDescription?: string;
  status: 'active' | 'completed' | 'failed' | 'paused' | 'waiting_for_user' | 'migrated';
  progress: number;
  phases: {
    dataImportCompleted: boolean;
    attributeMappingCompleted: boolean;
    dataCleansingCompleted: boolean;
    inventoryCompleted: boolean;
    dependenciesCompleted: boolean;
    techDebtCompleted: boolean;
  };
  currentPhase: string;
  nextPhase?: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
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

export interface AgentClarification {
  id: string;
  agentId: string;
  question: string;
  context: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'answered' | 'dismissed';
  response?: string;
  createdAt: string;
  answeredAt?: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  score: number;
  details: Record<string, any>;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  severity: 'error' | 'warning' | 'info';
  value?: any;
  metadata?: Record<string, any>;
}

export interface ValidationWarning {
  field: string;
  message: string;
  code: string;
  suggestion?: string;
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

export interface BulkMappingUpdate {
  mappingId: string;
  updates: Partial<FieldMapping>;
}

export interface MappingApprovalStatus {
  total: number;
  approved: number;
  rejected: number;
  pending: number;
  canProceed: boolean;
}

export interface AttributeCompletenessStatus {
  total: number;
  complete: number;
  incomplete: number;
  missing: number;
  percentage: number;
  canProceed: boolean;
}

export interface FlowReadinessStatus {
  isReady: boolean;
  phase: string;
  blockers: string[];
  warnings: string[];
  requirements: FlowRequirement[];
}

export interface FlowRequirement {
  id: string;
  name: string;
  description: string;
  status: 'met' | 'not_met' | 'partial';
  required: boolean;
  details?: string;
}

export type FlowDetectionSource = 'url' | 'auto' | 'session' | 'emergency' | 'manual';

export interface FlowDetectionDebug {
  urlParsing: {
    success: boolean;
    flowId?: string;
    error?: string;
    pathname: string;
  };
  autoDetection: {
    success: boolean;
    flowId?: string;
    error?: string;
    method: string;
  };
  sessionStorage: {
    success: boolean;
    flowId?: string;
    error?: string;
    key: string;
  };
  localStorage: {
    success: boolean;
    flowId?: string;
    error?: string;
    key: string;
  };
  validation: {
    success: boolean;
    flowId?: string;
    error?: string;
    details?: Record<string, any>;
  };
}

export interface FlowDetectionHistoryEntry {
  timestamp: string;
  source: FlowDetectionSource;
  flowId: string | null;
  success: boolean;
  error?: string;
  metadata?: Record<string, any>;
}

export interface MappingFilter {
  field: string;
  operator: 'eq' | 'ne' | 'contains' | 'startsWith' | 'endsWith' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'not_in';
  value: any;
  label?: string;
  enabled?: boolean;
}

export interface MappingSortConfig {
  field: string;
  direction: 'asc' | 'desc';
  label?: string;
}

export interface AttributeFilter {
  field: string;
  operator: string;
  value: any;
  label?: string;
  enabled?: boolean;
}

export interface AttributeSortConfig {
  field: string;
  direction: 'asc' | 'desc';
  label?: string;
}

export interface ImportFilter {
  field: string;
  operator: string;
  value: any;
  label?: string;
  enabled?: boolean;
}

export interface ImportSortConfig {
  field: string;
  direction: 'asc' | 'desc';
  label?: string;
}

export interface ImportError {
  row: number;
  column: string;
  message: string;
  severity: 'error' | 'warning';
  code?: string;
  suggestion?: string;
}

export interface PreviewData {
  headers: string[];
  rows: any[][];
  totalRows: number;
  sampleSize: number;
  schema: ColumnSchema[];
}

export interface ColumnSchema {
  name: string;
  type: string;
  nullable: boolean;
  unique: boolean;
  examples: any[];
  statistics?: ColumnStatistics;
}

export interface ColumnStatistics {
  count: number;
  nullCount: number;
  uniqueCount: number;
  minValue?: any;
  maxValue?: any;
  avgValue?: any;
  distribution?: Record<string, number>;
}

export interface ImportValidationResult {
  isValid: boolean;
  errors: ImportError[];
  warnings: ImportError[];
  statistics: ImportStatistics;
  schema: ColumnSchema[];
}

export interface ImportStatistics {
  totalRows: number;
  validRows: number;
  invalidRows: number;
  emptyRows: number;
  duplicateRows: number;
  columns: number;
  fileSize: number;
  processedAt: string;
}

export interface AnalysisType {
  id: string;
  name: string;
  description?: string;
  parameters?: AnalysisParameter[];
  icon?: ReactNode;
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

export interface AnalysisFinding {
  type: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  recommendation: string;
  impact: string;
  confidence: number;
  metadata?: Record<string, any>;
}

export interface AnalysisFilter {
  field: string;
  operator: string;
  value: any;
  label?: string;
  enabled?: boolean;
}

export interface AnalysisComparison {
  analyses: CrewAnalysis[];
  similarities: AnalysisSimilarity[];
  differences: AnalysisDifference[];
  summary: string;
  confidence: number;
}

export interface AnalysisSimilarity {
  field: string;
  value: any;
  confidence: number;
  description: string;
}

export interface AnalysisDifference {
  field: string;
  values: Record<string, any>;
  significance: 'high' | 'medium' | 'low';
  description: string;
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

export interface TrainingLog {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error' | 'fatal';
  message: string;
  source?: string;
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

export interface TrainingConfig {
  modelType: string;
  datasetId: string;
  hyperparameters: Hyperparameters;
  validationConfig: ValidationConfig;
  outputConfig: OutputConfig;
  schedulingConfig: SchedulingConfig;
  monitoringConfig: MonitoringConfig;
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

export interface OutputConfig {
  saveModel: boolean;
  saveMetrics: boolean;
  saveLogs: boolean;
  outputPath: string;
  format: 'pickle' | 'onnx' | 'tensorflow' | 'pytorch';
  compression: boolean;
}

export interface SchedulingConfig {
  priority: 'low' | 'medium' | 'high';
  maxDuration: number;
  retryAttempts: number;
  scheduling: 'immediate' | 'queued' | 'scheduled';
  scheduledTime?: string;
}

export interface MonitoringConfig {
  enabled: boolean;
  metricsEnabled: boolean;
  logsEnabled: boolean;
  alertsEnabled: boolean;
  alertThresholds: Record<string, number>;
  notificationChannels: string[];
}

export interface ModelComparison {
  models: ModelInfo[];
  metrics: ModelComparisonMetric[];
  summary: string;
  recommendation: string;
  confidence: number;
}

export interface ModelComparisonMetric {
  name: string;
  values: Record<string, number>;
  winner: string;
  significance: 'high' | 'medium' | 'low';
  description: string;
}

export interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  mimeType: string;
  description?: string;
}