/**
 * Discovery Flow Detection Hook Types
 * 
 * Type definitions for flow detection hooks including automatic flow detection,
 * import data management, and workflow orchestration.
 */

import type { BaseHookParams } from './base-hooks'
import { BaseHookReturn } from './base-hooks'

// Flow Detection hook types
export interface UseFlowDetectionParams extends BaseHookParams {
  dataImportId?: string;
  autoStart?: boolean;
  includeInactive?: boolean;
  includeSystemFlows?: boolean;
  confidenceThreshold?: number;
  maxSuggestions?: number;
  includePreviousFlows?: boolean;
  includeTemplateFlows?: boolean;
  sortBy?: FlowDetectionSortOption;
  filters?: FlowDetectionFilter[];
}

export interface UseFlowDetectionReturn {
  detectedFlows: DetectedFlow[];
  suggestions: FlowSuggestion[];
  confidence: FlowDetectionConfidence;
  analytics: FlowDetectionAnalytics;
  templates: FlowTemplate[];
  history: FlowDetectionHistory[];
  actions: FlowDetectionActions;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isSuccess: boolean;
  refetch: () => Promise<unknown>;
  detectFlows: (dataImportId: string) => Promise<DetectedFlow[]>;
  selectFlow: (flowId: string) => Promise<void>;
  createFlowFromTemplate: (templateId: string, data: unknown) => Promise<DetectedFlow>;
  customizeFlow: (flowId: string, customizations: FlowCustomization) => Promise<DetectedFlow>;
  validateFlow: (flowId: string) => Promise<FlowValidation>;
  previewFlow: (flowId: string) => Promise<FlowPreview>;
  startFlow: (flowId: string, options?: StartFlowOptions) => Promise<FlowExecution>;
  pauseFlow: (flowId: string) => Promise<void>;
  resumeFlow: (flowId: string) => Promise<void>;
  stopFlow: (flowId: string) => Promise<void>;
  retryFlow: (flowId: string) => Promise<void>;
  getFlowStatus: (flowId: string) => Promise<FlowStatus>;
  getFlowLogs: (flowId: string) => Promise<FlowLog[]>;
  getFlowMetrics: (flowId: string) => Promise<FlowMetrics>;
  exportFlow: (flowId: string, format: string) => Promise<Blob>;
  importFlow: (file: File) => Promise<DetectedFlow>;
  shareFlow: (flowId: string, users: string[]) => Promise<void>;
  favoriteFlow: (flowId: string) => Promise<void>;
  unfavoriteFlow: (flowId: string) => Promise<void>;
  rateFlow: (flowId: string, rating: number) => Promise<void>;
  commentOnFlow: (flowId: string, comment: string) => Promise<void>;
  getFlowRecommendations: () => Promise<FlowRecommendation[]>;
  searchFlows: (query: string) => Promise<DetectedFlow[]>;
  filterFlows: (filters: FlowDetectionFilter[]) => Promise<DetectedFlow[]>;
  compareFlows: (flowIds: string[]) => Promise<FlowComparison>;
  optimizeFlow: (flowId: string) => Promise<FlowOptimization>;
  scheduleFlow: (flowId: string, schedule: FlowSchedule) => Promise<void>;
  unscheduleFlow: (flowId: string) => Promise<void>;
  cloneFlow: (flowId: string) => Promise<DetectedFlow>;
  archiveFlow: (flowId: string) => Promise<void>;
  restoreFlow: (flowId: string) => Promise<void>;
  deleteFlow: (flowId: string) => Promise<void>;
}

export interface UseImportDataParams extends BaseHookParams {
  includeProcessed?: boolean;
  includeFailures?: boolean;
  sortBy?: ImportDataSortOption;
  sortOrder?: 'asc' | 'desc';
  pageSize?: number;
  page?: number;
  searchTerm?: string;
  filters?: ImportDataFilter[];
  groupBy?: ImportDataGroupOption;
}

export interface UseImportDataReturn extends BaseHookReturn<DataImport[]> {
  imports: DataImport[];
  pending: DataImport[];
  processing: DataImport[];
  completed: DataImport[];
  failed: DataImport[];
  statistics: ImportStatistics;
  analytics: ImportAnalytics;
  actions: ImportDataActions;
  templates: ImportTemplate[];
  configurations: ImportConfiguration[];
  validations: ImportValidation[];
  transformations: ImportTransformation[];
  createImport: (data: CreateImportRequest) => Promise<DataImport>;
  updateImport: (id: string, updates: Partial<DataImport>) => Promise<DataImport>;
  deleteImport: (id: string) => Promise<void>;
  retryImport: (id: string) => Promise<void>;
  cancelImport: (id: string) => Promise<void>;
  pauseImport: (id: string) => Promise<void>;
  resumeImport: (id: string) => Promise<void>;
  validateImport: (id: string) => Promise<ImportValidation>;
  previewImport: (id: string, options?: PreviewOptions) => Promise<ImportPreview>;
  transformImport: (id: string, transformations: ImportTransformation[]) => Promise<DataImport>;
  mapImportFields: (id: string, mappings: FieldMapping[]) => Promise<DataImport>;
  configureImport: (id: string, configuration: ImportConfiguration) => Promise<DataImport>;
  scheduleImport: (id: string, schedule: ImportSchedule) => Promise<void>;
  unscheduleImport: (id: string) => Promise<void>;
  exportImportResults: (id: string, format: string) => Promise<Blob>;
  getImportLogs: (id: string) => Promise<ImportLog[]>;
  getImportMetrics: (id: string) => Promise<ImportMetrics>;
  getImportStatus: (id: string) => Promise<ImportStatus>;
  getImportErrors: (id: string) => Promise<ImportError[]>;
  getImportWarnings: (id: string) => Promise<ImportWarning[]>;
  getImportSummary: (id: string) => Promise<ImportSummary>;
  compareImports: (importIds: string[]) => Promise<ImportComparison>;
  mergeImports: (importIds: string[]) => Promise<DataImport>;
  splitImport: (id: string, criteria: SplitCriteria) => Promise<DataImport[]>;
  duplicateImport: (id: string) => Promise<DataImport>;
  archiveImport: (id: string) => Promise<void>;
  restoreImport: (id: string) => Promise<void>;
  purgeImport: (id: string) => Promise<void>;
}

// Supporting types for flow detection
export interface DetectedFlow {
  id: string;
  name: string;
  description: string;
  type: FlowType;
  confidence: number;
  status: FlowStatus;
  priority: FlowPriority;
  category: string;
  tags: string[];
  phases: FlowPhase[];
  requirements: FlowRequirement[];
  dependencies: FlowDependency[];
  outputs: FlowOutput[];
  metrics: FlowMetrics;
  template: FlowTemplate;
  customizations: FlowCustomization[];
  schedule: FlowSchedule;
  notifications: FlowNotification[];
  permissions: FlowPermission[];
  audit: FlowAudit[];
  metadata: Record<string, string | number | boolean | null>;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy: string;
  version: number;
  isActive: boolean;
  isFavorite: boolean;
  isShared: boolean;
  rating: number;
  usageCount: number;
  lastExecuted?: string;
  nextExecution?: string;
  executionHistory: FlowExecution[];
}

export interface FlowSuggestion {
  id: string;
  flowId: string;
  type: SuggestionType;
  title: string;
  description: string;
  confidence: number;
  impact: SuggestionImpact;
  effort: SuggestionEffort;
  category: string;
  reasoning: string;
  evidence: SuggestionEvidence[];
  alternatives: FlowAlternative[];
  prerequisites: string[];
  risks: SuggestionRisk[];
  benefits: SuggestionBenefit[];
  implementation: ImplementationPlan;
  timeline: SuggestionTimeline;
  cost: SuggestionCost;
  roi: SuggestionROI;
  feedback: SuggestionFeedback[];
  status: SuggestionStatus;
  createdAt: string;
  updatedAt: string;
  expiresAt?: string;
}

export interface DataImport {
  id: string;
  name: string;
  description?: string;
  source: ImportSource;
  status: ImportStatus;
  type: ImportType;
  format: ImportFormat;
  size: number;
  records: number;
  processedRecords: number;
  successfulRecords: number;
  failedRecords: number;
  warnings: number;
  errors: ImportError[];
  validations: ImportValidation[];
  transformations: ImportTransformation[];
  mappings: FieldMapping[];
  configuration: ImportConfiguration;
  schedule: ImportSchedule;
  metadata: ImportMetadata;
  tags: string[];
  category: string;
  priority: ImportPriority;
  owner: string;
  permissions: ImportPermission[];
  audit: ImportAudit[];
  startedAt?: string;
  completedAt?: string;
  failedAt?: string;
  duration?: number;
  estimatedDuration?: number;
  progress: ImportProgress;
  logs: ImportLog[];
  metrics: ImportMetrics;
  notifications: ImportNotification[];
  dependencies: ImportDependency[];
  outputs: ImportOutput[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy: string;
  version: number;
}

// Flow detection confidence and analytics
export interface FlowDetectionConfidence {
  overall: number;
  byType: Record<FlowType, number>;
  byCategory: Record<string, number>;
  factors: ConfidenceFactor[];
  distribution: ConfidenceDistribution;
  trends: ConfidenceTrend[];
  benchmarks: ConfidenceBenchmark[];
}

export interface FlowDetectionAnalytics {
  totalDetections: number;
  successfulDetections: number;
  failedDetections: number;
  averageConfidence: number;
  detectionRate: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  topFlowTypes: FlowTypeStat[];
  topCategories: CategoryStat[];
  trends: AnalyticsTrend[];
  insights: AnalyticsInsight[];
  recommendations: AnalyticsRecommendation[];
  performance: PerformanceMetrics;
  quality: QualityMetrics;
  usage: UsageMetrics;
}

export interface FlowDetectionActions {
  detect: (dataImportId: string, options?: DetectionOptions) => Promise<DetectedFlow[]>;
  select: (flowId: string) => Promise<void>;
  create: (template: FlowTemplate, data: unknown) => Promise<DetectedFlow>;
  customize: (flowId: string, customizations: FlowCustomization) => Promise<DetectedFlow>;
  validate: (flowId: string) => Promise<FlowValidation>;
  preview: (flowId: string) => Promise<FlowPreview>;
  start: (flowId: string, options?: StartFlowOptions) => Promise<FlowExecution>;
  stop: (flowId: string) => Promise<void>;
  pause: (flowId: string) => Promise<void>;
  resume: (flowId: string) => Promise<void>;
  retry: (flowId: string) => Promise<void>;
  cancel: (flowId: string) => Promise<void>;
  delete: (flowId: string) => Promise<void>;
  clone: (flowId: string) => Promise<DetectedFlow>;
  archive: (flowId: string) => Promise<void>;
  restore: (flowId: string) => Promise<void>;
  share: (flowId: string, users: string[]) => Promise<void>;
  unshare: (flowId: string, users: string[]) => Promise<void>;
  favorite: (flowId: string) => Promise<void>;
  unfavorite: (flowId: string) => Promise<void>;
  rate: (flowId: string, rating: number) => Promise<void>;
  comment: (flowId: string, comment: string) => Promise<void>;
  tag: (flowId: string, tags: string[]) => Promise<void>;
  untag: (flowId: string, tags: string[]) => Promise<void>;
  categorize: (flowId: string, category: string) => Promise<void>;
  setPriority: (flowId: string, priority: FlowPriority) => Promise<void>;
  schedule: (flowId: string, schedule: FlowSchedule) => Promise<void>;
  unschedule: (flowId: string) => Promise<void>;
  export: (flowId: string, format: string) => Promise<Blob>;
  import: (file: File) => Promise<DetectedFlow>;
  compare: (flowIds: string[]) => Promise<FlowComparison>;
  optimize: (flowId: string) => Promise<FlowOptimization>;
  analyze: (flowId: string) => Promise<FlowAnalysis>;
  monitor: (flowId: string) => Promise<FlowMonitoring>;
  diagnose: (flowId: string) => Promise<FlowDiagnosis>;
  repair: (flowId: string) => Promise<FlowRepair>;
  backup: (flowId: string) => Promise<FlowBackup>;
  restore_backup: (flowId: string, backupId: string) => Promise<DetectedFlow>;
  migrate: (flowId: string, target: MigrationTarget) => Promise<FlowMigration>;
  rollback: (flowId: string, version: number) => Promise<DetectedFlow>;
  checkpoint: (flowId: string) => Promise<FlowCheckpoint>;
  rollback_checkpoint: (flowId: string, checkpointId: string) => Promise<DetectedFlow>;
}

export interface ImportDataActions {
  create: (data: CreateImportRequest) => Promise<DataImport>;
  update: (id: string, updates: Partial<DataImport>) => Promise<DataImport>;
  delete: (id: string) => Promise<void>;
  start: (id: string) => Promise<void>;
  stop: (id: string) => Promise<void>;
  pause: (id: string) => Promise<void>;
  resume: (id: string) => Promise<void>;
  retry: (id: string) => Promise<void>;
  cancel: (id: string) => Promise<void>;
  validate: (id: string) => Promise<ImportValidation>;
  preview: (id: string, options?: PreviewOptions) => Promise<ImportPreview>;
  transform: (id: string, transformations: ImportTransformation[]) => Promise<DataImport>;
  map: (id: string, mappings: FieldMapping[]) => Promise<DataImport>;
  configure: (id: string, configuration: ImportConfiguration) => Promise<DataImport>;
  schedule: (id: string, schedule: ImportSchedule) => Promise<void>;
  unschedule: (id: string) => Promise<void>;
  export: (id: string, format: string) => Promise<Blob>;
  duplicate: (id: string) => Promise<DataImport>;
  merge: (importIds: string[]) => Promise<DataImport>;
  split: (id: string, criteria: SplitCriteria) => Promise<DataImport[]>;
  archive: (id: string) => Promise<void>;
  restore: (id: string) => Promise<void>;
  purge: (id: string) => Promise<void>;
}

// Enum types
export type FlowType = 'discovery' | 'migration' | 'assessment' | 'optimization' | 'validation' | 'transformation' | 'integration' | 'custom';
export type FlowStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'scheduled';
export type FlowPriority = 'low' | 'medium' | 'high' | 'critical';
export type ImportStatus = 'pending' | 'validating' | 'transforming' | 'importing' | 'completed' | 'failed' | 'cancelled';
export type ImportType = 'full' | 'incremental' | 'delta' | 'sync' | 'merge' | 'replace';
export type ImportFormat = 'csv' | 'excel' | 'json' | 'xml' | 'database' | 'api' | 'file' | 'stream';
export type ImportPriority = 'low' | 'medium' | 'high' | 'critical';
export type SuggestionType = 'optimization' | 'best_practice' | 'alternative' | 'enhancement' | 'fix' | 'warning';
export type SuggestionImpact = 'low' | 'medium' | 'high' | 'critical';
export type SuggestionEffort = 'minimal' | 'low' | 'medium' | 'high' | 'extensive';
export type SuggestionStatus = 'new' | 'reviewed' | 'accepted' | 'rejected' | 'implemented' | 'expired';
export type FlowDetectionSortOption = 'name' | 'confidence' | 'created_at' | 'updated_at' | 'priority' | 'status';
export type ImportDataSortOption = 'name' | 'created_at' | 'updated_at' | 'status' | 'priority' | 'size';
export type ImportDataGroupOption = 'status' | 'type' | 'format' | 'priority' | 'created_by' | 'category';

// Additional supporting interfaces would be defined here
// (FlowPhase, FlowRequirement, FlowDependency, etc.)
// Due to length constraints, I'll include the most essential ones:

export interface FlowTemplate {
  id: string;
  name: string;
  description: string;
  type: FlowType;
  category: string;
  version: string;
  phases: FlowPhaseTemplate[];
  requirements: FlowRequirementTemplate[];
  parameters: FlowParameterTemplate[];
  isPublic: boolean;
  isSystem: boolean;
  usageCount: number;
  rating: number;
  tags: string[];
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface FlowCustomization {
  id: string;
  type: CustomizationType;
  target: string;
  configuration: Record<string, string | number | boolean | null>;
  isActive: boolean;
  priority: number;
}

export interface FlowValidation {
  isValid: boolean;
  errors: FlowValidationError[];
  warnings: FlowValidationWarning[];
  score: number;
  recommendations: FlowValidationRecommendation[];
}

export interface FlowPreview {
  phases: FlowPhasePreview[];
  estimatedDuration: number;
  estimatedResources: ResourceEstimate[];
  potentialIssues: PotentialIssue[];
  recommendations: PreviewRecommendation[];
}

export interface FlowExecution {
  id: string;
  flowId: string;
  status: FlowStatus;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  progress: ExecutionProgress;
  currentPhase?: string;
  results: ExecutionResult[];
  logs: ExecutionLog[];
  metrics: ExecutionMetrics;
  errors: ExecutionError[];
}

export interface ImportSource {
  type: ImportSourceType;
  location: string;
  credentials?: ImportCredentials;
  configuration: SourceConfiguration;
}

export interface ImportConfiguration {
  delimiter?: string;
  encoding?: string;
  hasHeaders?: boolean;
  skipRows?: number;
  maxRows?: number;
  batchSize?: number;
  parallel?: boolean;
  validation?: ValidationConfiguration;
  transformation?: TransformationConfiguration;
  errorHandling?: ErrorHandlingConfiguration;
}

export type ImportSourceType = 'file' | 'database' | 'api' | 'stream' | 'url' | 'ftp' | 's3' | 'azure' | 'gcp';
export type CustomizationType = 'parameter' | 'phase' | 'validation' | 'transformation' | 'notification' | 'permission';

// Filter interfaces
export interface FlowDetectionFilter {
  field: string;
  operator: FilterOperator;
  value: unknown;
}

export interface ImportDataFilter {
  field: string;
  operator: FilterOperator;
  value: unknown;
}

export type FilterOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'in' | 'not_in' | 'greater_than' | 'less_than';

// Statistics and metrics interfaces
export interface ImportStatistics {
  total: number;
  byStatus: Record<ImportStatus, number>;
  byType: Record<ImportType, number>;
  byFormat: Record<ImportFormat, number>;
  totalRecords: number;
  successRate: number;
  averageDuration: number;
}

export interface ImportAnalytics {
  trends: AnalyticsTrend[];
  insights: AnalyticsInsight[];
  recommendations: AnalyticsRecommendation[];
  performance: PerformanceMetrics;
  quality: QualityMetrics;
}

// Common analytics types
export interface AnalyticsTrend {
  metric: string;
  direction: 'up' | 'down' | 'stable';
  change: number;
  period: string;
  significance: 'low' | 'medium' | 'high';
}

export interface AnalyticsInsight {
  type: 'opportunity' | 'issue' | 'trend' | 'anomaly';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  confidence: number;
  recommendations: string[];
}

export interface AnalyticsRecommendation {
  type: 'optimization' | 'best_practice' | 'fix' | 'enhancement';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  effort: 'minimal' | 'low' | 'medium' | 'high';
  priority: number;
  actions: RecommendationAction[];
}

export interface RecommendationAction {
  type: string;
  description: string;
  parameters?: Record<string, string | number | boolean | null>;
}

export interface PerformanceMetrics {
  throughput: number;
  latency: number;
  errorRate: number;
  availability: number;
  resourceUtilization: ResourceUtilization;
}

export interface QualityMetrics {
  accuracy: number;
  completeness: number;
  consistency: number;
  validity: number;
  timeliness: number;
}

export interface ResourceUtilization {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
}

export interface UsageMetrics {
  activeUsers: number;
  totalSessions: number;
  averageSessionDuration: number;
  featuresUsed: FeatureUsage[];
  popularActions: ActionUsage[];
}

export interface FeatureUsage {
  feature: string;
  usageCount: number;
  uniqueUsers: number;
  averageTime: number;
}

export interface ActionUsage {
  action: string;
  count: number;
  successRate: number;
  averageTime: number;
}