/**
 * Discovery API Types
 * 
 * Type definitions for Discovery flow API endpoints, requests, and responses.
 * Covers data import, attribute mapping, flow management, and analysis APIs.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  ListRequest,
  ListResponse,
  GetRequest,
  GetResponse,
  CreateRequest,
  CreateResponse,
  UpdateRequest,
  UpdateResponse,
  DeleteRequest,
  DeleteResponse,
  FileUploadRequest,
  FileUploadResponse,
  ExportRequest,
  ExportResponse,
  ImportRequest,
  ImportResponse,
  ValidationResult,
  PaginationInfo,
  FilterParameter,
  SortParameter
} from './shared';

// Flow Management APIs
export interface InitializeDiscoveryFlowRequest extends BaseApiRequest {
  flowName: string;
  flowDescription?: string;
  context: MultiTenantContext;
  configuration?: DiscoveryFlowConfiguration;
  template?: string;
  parentFlowId?: string;
  metadata?: Record<string, any>;
}

export interface InitializeDiscoveryFlowResponse extends BaseApiResponse<DiscoveryFlowData> {
  data: DiscoveryFlowData;
  flowId: string;
  initialState: FlowState;
  nextSteps: string[];
  recommendations?: string[];
}

export interface GetDiscoveryFlowStatusRequest extends GetRequest {
  flowId: string;
  includeDetails?: boolean;
  includeAgentInsights?: boolean;
  includePhaseData?: boolean;
  includeMetrics?: boolean;
}

export interface GetDiscoveryFlowStatusResponse extends BaseApiResponse<FlowStatusDetail> {
  data: FlowStatusDetail;
  realTimeUpdates?: boolean;
  nextRefresh?: string;
}

export interface ListDiscoveryFlowsRequest extends ListRequest {
  status?: FlowStatus[];
  phases?: string[];
  clientAccountIds?: string[];
  engagementIds?: string[];
  userIds?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'updated' | 'completed';
  };
  includeArchived?: boolean;
  includeMetrics?: boolean;
}

export interface ListDiscoveryFlowsResponse extends ListResponse<DiscoveryFlowSummary> {
  data: DiscoveryFlowSummary[];
  aggregations?: FlowAggregation[];
  trends?: FlowTrend[];
}

export interface UpdateDiscoveryFlowRequest extends UpdateRequest<Partial<DiscoveryFlowData>> {
  flowId: string;
  data: Partial<DiscoveryFlowData>;
  validateTransition?: boolean;
  skipValidation?: boolean;
  notifyAgents?: boolean;
}

export interface UpdateDiscoveryFlowResponse extends UpdateResponse<DiscoveryFlowData> {
  data: DiscoveryFlowData;
  transitionResult?: PhaseTransitionResult;
  agentNotifications?: AgentNotification[];
}

export interface DeleteDiscoveryFlowRequest extends DeleteRequest {
  flowId: string;
  deleteAssociatedData?: boolean;
  archiveInstead?: boolean;
  reason?: string;
}

export interface DeleteDiscoveryFlowResponse extends DeleteResponse {
  flowId: string;
  archived: boolean;
  deletedResources: DeletedResource[];
  retentionInfo?: RetentionInfo;
}

// Data Import APIs
export interface UploadDataImportRequest extends FileUploadRequest {
  flowId: string;
  importType?: 'cmdb' | 'asset_inventory' | 'dependency_map' | 'custom';
  skipValidation?: boolean;
  autoProcess?: boolean;
  mapping?: FieldMapping[];
  parseOptions?: ParseOptions;
}

export interface UploadDataImportResponse extends FileUploadResponse {
  data: DataImportInfo;
  importId: string;
  validationResult?: ImportValidationResult;
  processingStatus: 'queued' | 'processing' | 'completed' | 'failed';
}

export interface GetDataImportRequest extends GetRequest {
  importId: string;
  includePreview?: boolean;
  includeStatistics?: boolean;
  includeErrors?: boolean;
  includeValidation?: boolean;
}

export interface GetDataImportResponse extends GetResponse<DataImportDetail> {
  data: DataImportDetail;
  processingLogs?: ProcessingLog[];
  downloadUrl?: string;
}

export interface ListDataImportsRequest extends ListRequest {
  flowId: string;
  status?: ImportStatus[];
  importType?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'uploaded' | 'processed' | 'completed';
  };
  includeStatistics?: boolean;
}

export interface ListDataImportsResponse extends ListResponse<DataImportSummary> {
  data: DataImportSummary[];
  totalSize: number;
  totalRecords: number;
  statusCounts: Record<ImportStatus, number>;
}

export interface ProcessDataImportRequest extends BaseApiRequest {
  importId: string;
  context: MultiTenantContext;
  options?: ProcessingOptions;
  mapping?: FieldMapping[];
  validation?: ValidationOptions;
  dryRun?: boolean;
}

export interface ProcessDataImportResponse extends BaseApiResponse<ProcessingResult> {
  data: ProcessingResult;
  processingId: string;
  estimatedDuration?: number;
  status: 'queued' | 'processing' | 'completed' | 'failed';
}

export interface DeleteDataImportRequest extends DeleteRequest {
  importId: string;
  deleteFromStorage?: boolean;
  reason?: string;
}

export interface DeleteDataImportResponse extends DeleteResponse {
  importId: string;
  deletedFromStorage: boolean;
  affectedFlows: string[];
}

// Attribute Mapping APIs
export interface GetFieldMappingsRequest extends GetRequest {
  flowId: string;
  dataImportId?: string;
  status?: MappingStatus[];
  mappingType?: MappingType[];
  includeValidation?: boolean;
  includeAnalysis?: boolean;
}

export interface GetFieldMappingsResponse extends ListResponse<FieldMapping> {
  data: FieldMapping[];
  statistics: MappingStatistics;
  validationSummary?: ValidationSummary;
  recommendations?: MappingRecommendation[];
}

export interface CreateFieldMappingRequest extends CreateRequest<FieldMappingInput> {
  flowId: string;
  data: FieldMappingInput;
  autoValidate?: boolean;
  generateAnalysis?: boolean;
}

export interface CreateFieldMappingResponse extends CreateResponse<FieldMapping> {
  data: FieldMapping;
  validationResult?: ValidationResult;
  analysisResult?: MappingAnalysis;
}

export interface UpdateFieldMappingRequest extends UpdateRequest<Partial<FieldMapping>> {
  mappingId: string;
  data: Partial<FieldMapping>;
  validateMapping?: boolean;
  updateAnalysis?: boolean;
}

export interface UpdateFieldMappingResponse extends UpdateResponse<FieldMapping> {
  data: FieldMapping;
  validationResult?: ValidationResult;
  analysisUpdate?: MappingAnalysis;
}

export interface BulkUpdateMappingsRequest extends BaseApiRequest {
  flowId: string;
  context: MultiTenantContext;
  operations: MappingOperation[];
  validateAll?: boolean;
  continueOnError?: boolean;
}

export interface BulkUpdateMappingsResponse extends BaseApiResponse<BulkMappingResult> {
  data: BulkMappingResult;
  successful: number;
  failed: number;
  validationResults?: ValidationResult[];
}

export interface ApproveMappingRequest extends BaseApiRequest {
  mappingId: string;
  context: MultiTenantContext;
  approvalComment?: string;
  autoProgress?: boolean;
}

export interface ApproveMappingResponse extends BaseApiResponse<FieldMapping> {
  data: FieldMapping;
  approved: boolean;
  flowProgressed: boolean;
  nextActions?: string[];
}

export interface RejectMappingRequest extends BaseApiRequest {
  mappingId: string;
  context: MultiTenantContext;
  rejectionReason: string;
  suggestedChanges?: string[];
  requiresManualReview?: boolean;
}

export interface RejectMappingResponse extends BaseApiResponse<FieldMapping> {
  data: FieldMapping;
  rejected: boolean;
  suggestions?: MappingRecommendation[];
  alternativeOptions?: AlternativeMapping[];
}

// Critical Attributes APIs
export interface GetCriticalAttributesRequest extends GetRequest {
  flowId: string;
  category?: string[];
  priority?: AttributePriority[];
  mappingStatus?: AttributeMappingStatus[];
  includeBusinessRules?: boolean;
  includeValidation?: boolean;
}

export interface GetCriticalAttributesResponse extends ListResponse<CriticalAttribute> {
  data: CriticalAttribute[];
  completenessScore: number;
  missingCritical: string[];
  recommendations?: AttributeRecommendation[];
}

export interface CreateCriticalAttributeRequest extends CreateRequest<CriticalAttributeInput> {
  flowId: string;
  data: CriticalAttributeInput;
  validateDefinition?: boolean;
  checkDuplicates?: boolean;
}

export interface CreateCriticalAttributeResponse extends CreateResponse<CriticalAttribute> {
  data: CriticalAttribute;
  duplicateCheck?: DuplicateCheckResult;
  validationResult?: ValidationResult;
}

export interface UpdateCriticalAttributeRequest extends UpdateRequest<Partial<CriticalAttribute>> {
  attributeId: string;
  data: Partial<CriticalAttribute>;
  validateChanges?: boolean;
  updateMappings?: boolean;
}

export interface UpdateCriticalAttributeResponse extends UpdateResponse<CriticalAttribute> {
  data: CriticalAttribute;
  mappingUpdates?: FieldMapping[];
  validationResult?: ValidationResult;
}

export interface ValidateAttributeRequest extends BaseApiRequest {
  attributeId: string;
  context: MultiTenantContext;
  validationType?: 'definition' | 'mapping' | 'business_rules' | 'all';
  includeRecommendations?: boolean;
}

export interface ValidateAttributeResponse extends BaseApiResponse<AttributeValidationResult> {
  data: AttributeValidationResult;
  recommendations?: AttributeRecommendation[];
  autoFixSuggestions?: AutoFixSuggestion[];
}

// Crew Analysis APIs
export interface TriggerCrewAnalysisRequest extends BaseApiRequest {
  flowId: string;
  context: MultiTenantContext;
  analysisType: AnalysisType;
  parameters?: AnalysisParameters;
  targetScope?: AnalysisScope;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

export interface TriggerCrewAnalysisResponse extends BaseApiResponse<AnalysisJob> {
  data: AnalysisJob;
  analysisId: string;
  estimatedCompletion?: string;
  dependencies?: string[];
}

export interface GetCrewAnalysisRequest extends GetRequest {
  analysisId: string;
  includeDetails?: boolean;
  includeRecommendations?: boolean;
  includeMetadata?: boolean;
}

export interface GetCrewAnalysisResponse extends GetResponse<CrewAnalysisResult> {
  data: CrewAnalysisResult;
  relatedAnalyses?: RelatedAnalysis[];
  actionableInsights?: ActionableInsight[];
}

export interface ListCrewAnalysesRequest extends ListRequest {
  flowId: string;
  analysisType?: AnalysisType[];
  status?: AnalysisStatus[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'completed';
  };
  includeMetrics?: boolean;
}

export interface ListCrewAnalysesResponse extends ListResponse<CrewAnalysisSummary> {
  data: CrewAnalysisSummary[];
  trendData?: AnalysisTrend[];
  performanceMetrics?: AnalysisPerformanceMetrics;
}

export interface GetAnalysisRecommendationsRequest extends GetRequest {
  analysisId: string;
  category?: RecommendationCategory[];
  priority?: RecommendationPriority[];
  implementationDifficulty?: ImplementationDifficulty[];
}

export interface GetAnalysisRecommendationsResponse extends ListResponse<AnalysisRecommendation> {
  data: AnalysisRecommendation[];
  prioritizedList: string[];
  implementationPlan?: ImplementationPlan;
}

// Flow State Management APIs
export interface GetFlowStateRequest extends GetRequest {
  flowId: string;
  includeHistory?: boolean;
  includeAgentStates?: boolean;
  includeCheckpoints?: boolean;
}

export interface GetFlowStateResponse extends GetResponse<FlowStateDetail> {
  data: FlowStateDetail;
  stateHistory?: FlowStateHistory[];
  availableTransitions?: FlowTransition[];
}

export interface UpdateFlowStateRequest extends UpdateRequest<Partial<FlowState>> {
  flowId: string;
  data: Partial<FlowState>;
  validateTransition?: boolean;
  createCheckpoint?: boolean;
  notifyAgents?: boolean;
}

export interface UpdateFlowStateResponse extends UpdateResponse<FlowState> {
  data: FlowState;
  transitionResult?: StateTransitionResult;
  checkpointId?: string;
  notifications?: StateChangeNotification[];
}

export interface TransitionFlowPhaseRequest extends BaseApiRequest {
  flowId: string;
  context: MultiTenantContext;
  targetPhase: string;
  skipValidation?: boolean;
  force?: boolean;
  reason?: string;
}

export interface TransitionFlowPhaseResponse extends BaseApiResponse<PhaseTransitionResult> {
  data: PhaseTransitionResult;
  newState: FlowState;
  validationResults?: ValidationResult[];
  warnings?: string[];
}

// Agent Clarifications APIs
export interface GetAgentClarificationsRequest extends GetRequest {
  flowId: string;
  agentId?: string;
  status?: ClarificationStatus[];
  priority?: ClarificationPriority[];
  category?: ClarificationCategory[];
}

export interface GetAgentClarificationsResponse extends ListResponse<AgentClarification> {
  data: AgentClarification[];
  pendingCount: number;
  highPriorityCount: number;
  overdueCount: number;
}

export interface CreateClarificationRequest extends CreateRequest<ClarificationInput> {
  flowId: string;
  data: ClarificationInput;
  notifyUser?: boolean;
  escalationLevel?: EscalationLevel;
}

export interface CreateClarificationResponse extends CreateResponse<AgentClarification> {
  data: AgentClarification;
  notificationSent: boolean;
  escalated: boolean;
}

export interface RespondToClarificationRequest extends BaseApiRequest {
  clarificationId: string;
  context: MultiTenantContext;
  response: string;
  attachments?: string[];
  markAsResolved?: boolean;
}

export interface RespondToClarificationResponse extends BaseApiResponse<AgentClarification> {
  data: AgentClarification;
  resolved: boolean;
  followUpActions?: FollowUpAction[];
}

// Progress Tracking APIs
export interface GetMappingProgressRequest extends GetRequest {
  flowId: string;
  dataImportId?: string;
  includeDetails?: boolean;
  includeProjections?: boolean;
}

export interface GetMappingProgressResponse extends GetResponse<MappingProgressDetail> {
  data: MappingProgressDetail;
  projections?: ProgressProjection[];
  bottlenecks?: ProgressBottleneck[];
}

export interface GetFlowProgressRequest extends GetRequest {
  flowId: string;
  includePhaseBreakdown?: boolean;
  includeTimeline?: boolean;
  includeMetrics?: boolean;
}

export interface GetFlowProgressResponse extends GetResponse<FlowProgressDetail> {
  data: FlowProgressDetail;
  timeline?: ProgressTimeline[];
  metrics?: ProgressMetrics;
  estimatedCompletion?: string;
}

// Training and Learning APIs
export interface GetTrainingProgressRequest extends GetRequest {
  flowId: string;
  modelId?: string;
  includeMetrics?: boolean;
  includeLogs?: boolean;
  includeHistory?: boolean;
}

export interface GetTrainingProgressResponse extends GetResponse<TrainingProgressDetail> {
  data: TrainingProgressDetail;
  performanceMetrics?: TrainingMetrics;
  logs?: TrainingLog[];
  history?: TrainingHistory[];
}

export interface StartTrainingRequest extends BaseApiRequest {
  flowId: string;
  context: MultiTenantContext;
  modelConfig: ModelConfiguration;
  trainingConfig: TrainingConfiguration;
  datasetConfig: DatasetConfiguration;
}

export interface StartTrainingResponse extends BaseApiResponse<TrainingJob> {
  data: TrainingJob;
  trainingId: string;
  estimatedDuration?: number;
  resourceAllocation?: ResourceAllocation;
}

export interface StopTrainingRequest extends BaseApiRequest {
  trainingId: string;
  context: MultiTenantContext;
  saveProgress?: boolean;
  reason?: string;
}

export interface StopTrainingResponse extends BaseApiResponse<TrainingStopResult> {
  data: TrainingStopResult;
  finalMetrics?: TrainingMetrics;
  savedModel?: ModelInfo;
}

// Data Models
export interface DiscoveryFlowConfiguration {
  phases: PhaseConfiguration[];
  autoAdvance: boolean;
  validationLevel: 'strict' | 'normal' | 'lenient';
  parallelProcessing: boolean;
  agentConfiguration: AgentConfiguration;
  notificationSettings: NotificationSettings;
  retentionPolicy: RetentionPolicy;
}

export interface DiscoveryFlowData {
  id: string;
  flowId: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  flowName: string;
  flowDescription?: string;
  status: FlowStatus;
  progress: number;
  phases: PhaseCompletion;
  currentPhase: string;
  nextPhase?: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  configuration: DiscoveryFlowConfiguration;
  metadata?: Record<string, any>;
}

export interface FlowState {
  flowId: string;
  currentPhase: string;
  nextPhase?: string;
  previousPhase?: string;
  phaseCompletion: Record<string, boolean>;
  phaseData: Record<string, any>;
  agentStates: Record<string, AgentState>;
  sharedData: Record<string, any>;
  checkpoints: StateCheckpoint[];
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface FlowStatusDetail extends DiscoveryFlowData {
  state: FlowState;
  metrics: FlowMetrics;
  agentInsights: AgentInsight[];
  recentEvents: FlowEvent[];
  blockers: FlowBlocker[];
  warnings: FlowWarning[];
  recommendations: FlowRecommendation[];
}

export interface DiscoveryFlowSummary {
  id: string;
  flowId: string;
  flowName: string;
  status: FlowStatus;
  progress: number;
  currentPhase: string;
  createdAt: string;
  updatedAt: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  metrics?: FlowMetricsSummary;
}

export interface DataImportInfo {
  id: string;
  flowId: string;
  fileName: string;
  originalName: string;
  fileSize: number;
  fileType: string;
  importType: string;
  status: ImportStatus;
  recordsTotal: number;
  recordsProcessed: number;
  recordsValid: number;
  recordsInvalid: number;
  uploadedAt: string;
  processedAt?: string;
  uploadedBy: string;
  metadata?: Record<string, any>;
}

export interface DataImportDetail extends DataImportInfo {
  parseOptions: ParseOptions;
  processingLogs: ProcessingLog[];
  errors: ImportError[];
  warnings: ImportWarning[];
  statistics: ImportStatistics;
  preview?: ImportPreview;
  validationResult?: ImportValidationResult;
}

export interface DataImportSummary {
  id: string;
  fileName: string;
  fileSize: number;
  status: ImportStatus;
  recordsTotal: number;
  uploadedAt: string;
  uploadedBy: string;
}

export interface FieldMapping {
  id: string;
  flowId: string;
  dataImportId: string;
  sourceField: string;
  targetField: string;
  mappingType: MappingType;
  transformationLogic?: string;
  validationRules: ValidationRule[];
  confidence: number;
  status: MappingStatus;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  reviewedBy?: string;
  rejectionReason?: string;
  analysisResult?: MappingAnalysis;
  metadata?: Record<string, any>;
}

export interface FieldMappingInput {
  sourceField: string;
  targetField: string;
  mappingType: MappingType;
  transformationLogic?: string;
  validationRules?: ValidationRule[];
  metadata?: Record<string, any>;
}

export interface CriticalAttribute {
  id: string;
  flowId: string;
  name: string;
  description: string;
  dataType: string;
  isRequired: boolean;
  defaultValue?: any;
  validationRules: ValidationRule[];
  mappingStatus: AttributeMappingStatus;
  sourceFields: string[];
  targetField?: string;
  businessRules: BusinessRule[];
  priority: AttributePriority;
  category: string;
  tags: string[];
  completeness: number;
  qualityScore: number;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, any>;
}

export interface CriticalAttributeInput {
  name: string;
  description: string;
  dataType: string;
  isRequired: boolean;
  defaultValue?: any;
  validationRules?: ValidationRule[];
  businessRules?: BusinessRule[];
  priority: AttributePriority;
  category: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface CrewAnalysisResult {
  id: string;
  flowId: string;
  analysisType: AnalysisType;
  status: AnalysisStatus;
  findings: AnalysisFinding[];
  recommendations: AnalysisRecommendation[];
  confidence: number;
  quality: number;
  executedAt: string;
  completedAt?: string;
  executedBy: string;
  parameters: AnalysisParameters;
  scope: AnalysisScope;
  metrics: AnalysisMetrics;
  metadata: Record<string, any>;
}

export interface CrewAnalysisSummary {
  id: string;
  analysisType: AnalysisType;
  status: AnalysisStatus;
  confidence: number;
  findingsCount: number;
  recommendationsCount: number;
  executedAt: string;
  completedAt?: string;
  executionTime?: number;
}

export interface AgentClarification {
  id: string;
  flowId: string;
  agentId: string;
  category: ClarificationCategory;
  priority: ClarificationPriority;
  status: ClarificationStatus;
  question: string;
  context: string;
  suggestedActions: string[];
  response?: string;
  attachments: string[];
  createdAt: string;
  respondedAt?: string;
  resolvedAt?: string;
  escalationLevel: EscalationLevel;
  metadata?: Record<string, any>;
}

export interface ClarificationInput {
  agentId: string;
  category: ClarificationCategory;
  priority: ClarificationPriority;
  question: string;
  context: string;
  suggestedActions?: string[];
  attachments?: string[];
  escalationLevel?: EscalationLevel;
  metadata?: Record<string, any>;
}

// Supporting types and enums
export type FlowStatus = 'initializing' | 'active' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'archived';
export type ImportStatus = 'uploading' | 'validating' | 'processing' | 'completed' | 'failed' | 'cancelled';
export type MappingStatus = 'pending' | 'approved' | 'rejected' | 'in_review' | 'auto_approved';
export type MappingType = 'direct' | 'transformed' | 'calculated' | 'conditional' | 'lookup' | 'derived';
export type AttributeMappingStatus = 'mapped' | 'unmapped' | 'partially_mapped' | 'conflicted';
export type AttributePriority = 'critical' | 'high' | 'medium' | 'low';
export type AnalysisType = 'mapping_validation' | 'data_quality' | 'completeness' | 'consistency' | 'relationships' | 'anomaly_detection';
export type AnalysisStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'timeout';
export type ClarificationStatus = 'pending' | 'in_progress' | 'answered' | 'resolved' | 'dismissed' | 'escalated';
export type ClarificationPriority = 'urgent' | 'high' | 'medium' | 'low';
export type ClarificationCategory = 'mapping' | 'validation' | 'business_rule' | 'data_quality' | 'workflow' | 'technical';
export type EscalationLevel = 'none' | 'supervisor' | 'expert' | 'administrator';
export type RecommendationCategory = 'improvement' | 'optimization' | 'fix' | 'enhancement' | 'best_practice';
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low' | 'optional';
export type ImplementationDifficulty = 'trivial' | 'easy' | 'moderate' | 'difficult' | 'complex';

// Additional detailed interfaces would continue here...
// (Truncated for brevity, but would include all remaining supporting interfaces)

export interface PhaseConfiguration {
  name: string;
  order: number;
  dependencies: string[];
  validationRules: ValidationRule[];
  autoAdvance: boolean;
  timeout?: number;
}

export interface PhaseCompletion {
  dataImportCompleted: boolean;
  attributeMappingCompleted: boolean;
  dataCleansingCompleted: boolean;
  inventoryCompleted: boolean;
  dependenciesCompleted: boolean;
  techDebtCompleted: boolean;
}

export interface AgentConfiguration {
  enabled: boolean;
  maxConcurrency: number;
  timeout: number;
  retryPolicy: RetryPolicy;
  learningEnabled: boolean;
  feedbackEnabled: boolean;
}

export interface NotificationSettings {
  emailEnabled: boolean;
  realTimeEnabled: boolean;
  webhookEnabled: boolean;
  channels: NotificationChannel[];
}

export interface RetentionPolicy {
  dataRetentionDays: number;
  archiveAfterDays: number;
  deleteAfterDays: number;
  compressAfterDays: number;
}

export interface AgentState {
  agentId: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  currentTask?: string;
  progress: number;
  memory: Record<string, any>;
  context: Record<string, any>;
  lastUpdate: string;
}

export interface StateCheckpoint {
  id: string;
  timestamp: string;
  phase: string;
  data: Record<string, any>;
  hash: string;
  size: number;
  createdBy: string;
  automatic: boolean;
}

export interface FlowMetrics {
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  averageTaskDuration: number;
  dataQualityScore: number;
  progressVelocity: number;
  bottleneckCount: number;
  agentEfficiency: number;
  userSatisfaction?: number;
}

export interface FlowMetricsSummary {
  progress: number;
  dataQualityScore: number;
  completedTasks: number;
  totalTasks: number;
  estimatedCompletion?: string;
}

export interface AgentInsight {
  agentId: string;
  type: 'observation' | 'recommendation' | 'warning' | 'error';
  message: string;
  confidence: number;
  timestamp: string;
  context: Record<string, any>;
  actionable: boolean;
  category: string;
}

export interface FlowEvent {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  source: 'system' | 'agent' | 'user';
  sourceId: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  metadata: Record<string, any>;
}

export interface FlowBlocker {
  id: string;
  type: 'validation' | 'dependency' | 'resource' | 'approval' | 'technical';
  description: string;
  severity: 'blocking' | 'warning';
  resolution?: string;
  estimatedImpact: number;
  createdAt: string;
}

export interface FlowWarning {
  id: string;
  type: string;
  message: string;
  recommendation?: string;
  dismissible: boolean;
  createdAt: string;
}

export interface FlowRecommendation {
  id: string;
  category: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  effort: 'low' | 'medium' | 'high';
  impact: 'low' | 'medium' | 'high';
  actionable: boolean;
  actions?: string[];
}

export interface ParseOptions {
  delimiter?: string;
  quoteChar?: string;
  escapeChar?: string;
  encoding?: string;
  hasHeader?: boolean;
  skipRows?: number;
  maxRows?: number;
  dateFormat?: string;
  numberFormat?: string;
  booleanFormat?: Record<string, boolean>;
  nullValues?: string[];
}

export interface ProcessingLog {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  details?: Record<string, any>;
}

export interface ImportError {
  row?: number;
  column?: string;
  field?: string;
  code: string;
  message: string;
  value?: any;
  severity: 'error' | 'warning';
}

export interface ImportWarning {
  row?: number;
  column?: string;
  field?: string;
  code: string;
  message: string;
  value?: any;
  suggestion?: string;
}

export interface ImportStatistics {
  totalRows: number;
  validRows: number;
  invalidRows: number;
  emptyRows: number;
  duplicateRows: number;
  columns: number;
  fileSize: number;
  processingTime: number;
  dataTypes: Record<string, number>;
  qualityMetrics: DataQualityMetrics;
}

export interface DataQualityMetrics {
  completeness: number;
  consistency: number;
  accuracy: number;
  validity: number;
  uniqueness: number;
  integrity: number;
}

export interface ImportPreview {
  headers: string[];
  sampleRows: any[][];
  totalRows: number;
  sampleSize: number;
  schema: ColumnSchema[];
  detectedTypes: Record<string, string>;
}

export interface ColumnSchema {
  name: string;
  dataType: string;
  nullable: boolean;
  unique: boolean;
  minValue?: any;
  maxValue?: any;
  avgValue?: any;
  nullCount: number;
  uniqueCount: number;
  examples: any[];
}

export interface ImportValidationResult {
  isValid: boolean;
  score: number;
  errors: ImportError[];
  warnings: ImportWarning[];
  statistics: ImportStatistics;
  recommendations: string[];
}

export interface ProcessingOptions {
  batchSize?: number;
  parallelProcessing?: boolean;
  skipValidation?: boolean;
  continueOnError?: boolean;
  generatePreview?: boolean;
  calculateStatistics?: boolean;
}

export interface ProcessingResult {
  processingId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  recordsProcessed: number;
  recordsTotal: number;
  errors: ProcessingError[];
  startTime: string;
  endTime?: string;
  estimatedCompletion?: string;
}

export interface ProcessingError {
  type: 'parsing' | 'validation' | 'transformation' | 'storage';
  message: string;
  details?: Record<string, any>;
  recoverable: boolean;
}

export interface ValidationRule {
  type: string;
  parameters: Record<string, any>;
  message: string;
  severity: 'error' | 'warning' | 'info';
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

export interface MappingStatistics {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  inReview: number;
  autoApproved: number;
  confidence: {
    high: number;
    medium: number;
    low: number;
  };
  types: Record<MappingType, number>;
}

export interface ValidationSummary {
  totalValidated: number;
  passed: number;
  failed: number;
  warnings: number;
  overallScore: number;
  criticalIssues: number;
}

export interface MappingRecommendation {
  id: string;
  mappingId: string;
  type: 'improvement' | 'alternative' | 'correction';
  confidence: number;
  description: string;
  suggestedMapping?: FieldMappingInput;
  reasoning: string;
  impact: 'low' | 'medium' | 'high';
}

export interface MappingAnalysis {
  confidence: number;
  accuracy: number;
  completeness: number;
  consistency: number;
  recommendations: string[];
  warnings: string[];
  metadata: Record<string, any>;
}

export interface MappingOperation {
  type: 'create' | 'update' | 'delete' | 'approve' | 'reject';
  mappingId?: string;
  data?: Partial<FieldMapping>;
  reason?: string;
}

export interface BulkMappingResult {
  operations: MappingOperationResult[];
  summary: {
    successful: number;
    failed: number;
    skipped: number;
  };
  validationResults: ValidationResult[];
}

export interface MappingOperationResult {
  operation: MappingOperation;
  success: boolean;
  result?: FieldMapping;
  error?: string;
  validationResult?: ValidationResult;
}

export interface AlternativeMapping {
  sourceField: string;
  targetField: string;
  confidence: number;
  reasoning: string;
  advantages: string[];
  disadvantages: string[];
}

export interface AttributeValidationResult extends ValidationResult {
  attributeId: string;
  mappingValidation?: ValidationResult;
  businessRuleValidation?: ValidationResult;
  completenessCheck?: CompletenessCheck;
  qualityAssessment?: QualityAssessment;
}

export interface CompletenessCheck {
  score: number;
  missing: string[];
  recommendations: string[];
}

export interface QualityAssessment {
  score: number;
  issues: QualityIssue[];
  recommendations: string[];
}

export interface QualityIssue {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affectedRecords?: number;
  suggestion?: string;
}

export interface AttributeRecommendation {
  id: string;
  attributeId: string;
  type: 'definition' | 'mapping' | 'validation' | 'business_rule';
  priority: RecommendationPriority;
  description: string;
  suggestedChanges: Record<string, any>;
  reasoning: string;
  impact: string;
  effort: ImplementationDifficulty;
}

export interface AutoFixSuggestion {
  id: string;
  type: 'auto_fix' | 'semi_auto' | 'manual';
  description: string;
  changes: Record<string, any>;
  confidence: number;
  reversible: boolean;
  testable: boolean;
}

export interface DuplicateCheckResult {
  hasDuplicates: boolean;
  duplicates: DuplicateAttribute[];
  similarAttributes: SimilarAttribute[];
}

export interface DuplicateAttribute {
  attributeId: string;
  name: string;
  similarity: number;
  differences: string[];
}

export interface SimilarAttribute {
  attributeId: string;
  name: string;
  similarity: number;
  suggestedMerge: boolean;
}

export interface AnalysisJob {
  id: string;
  flowId: string;
  analysisType: AnalysisType;
  status: AnalysisStatus;
  progress: number;
  parameters: AnalysisParameters;
  scope: AnalysisScope;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  estimatedDuration?: number;
  resourceAllocation?: ResourceAllocation;
}

export interface AnalysisParameters {
  includeDataQuality?: boolean;
  includeRelationships?: boolean;
  includeAnomalies?: boolean;
  confidenceThreshold?: number;
  sampleSize?: number;
  customParameters?: Record<string, any>;
}

export interface AnalysisScope {
  dataImports?: string[];
  attributes?: string[];
  mappings?: string[];
  phases?: string[];
  fullFlow?: boolean;
}

export interface ResourceAllocation {
  cpuCores: number;
  memoryMB: number;
  estimatedCost: number;
  maxDuration: number;
}

export interface AnalysisFinding {
  id: string;
  type: string;
  category: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  description: string;
  details: Record<string, any>;
  evidence: Evidence[];
  confidence: number;
  impact: string;
  location?: string;
  affectedEntities?: string[];
}

export interface Evidence {
  type: 'data' | 'statistic' | 'pattern' | 'rule' | 'comparison';
  description: string;
  value?: any;
  source?: string;
  metadata?: Record<string, any>;
}

export interface AnalysisRecommendation {
  id: string;
  findingId?: string;
  category: RecommendationCategory;
  priority: RecommendationPriority;
  title: string;
  description: string;
  rationale: string;
  steps: RecommendationStep[];
  effort: ImplementationDifficulty;
  impact: string;
  riskLevel: 'low' | 'medium' | 'high';
  dependencies?: string[];
  alternatives?: string[];
  estimatedTime?: number;
  estimatedCost?: number;
}

export interface RecommendationStep {
  order: number;
  description: string;
  automated: boolean;
  estimatedTime?: number;
  prerequisites?: string[];
  verification?: string;
}

export interface ImplementationPlan {
  totalEffort: number;
  estimatedDuration: number;
  phases: ImplementationPhase[];
  dependencies: PlanDependency[];
  risks: PlanRisk[];
  resources: RequiredResource[];
}

export interface ImplementationPhase {
  name: string;
  order: number;
  recommendations: string[];
  estimatedDuration: number;
  prerequisites: string[];
  deliverables: string[];
}

export interface PlanDependency {
  type: 'technical' | 'resource' | 'approval' | 'external';
  description: string;
  impact: 'blocking' | 'delay' | 'optional';
  estimatedResolution: number;
}

export interface PlanRisk {
  type: string;
  probability: 'low' | 'medium' | 'high';
  impact: 'low' | 'medium' | 'high';
  mitigation: string;
  contingency?: string;
}

export interface RequiredResource {
  type: 'human' | 'technical' | 'financial';
  description: string;
  quantity: number;
  duration: number;
  availability?: string;
}

export interface RelatedAnalysis {
  analysisId: string;
  analysisType: AnalysisType;
  relationship: 'predecessor' | 'successor' | 'parallel' | 'dependency';
  relevance: number;
  summary: string;
}

export interface ActionableInsight {
  id: string;
  type: 'immediate' | 'planned' | 'strategic';
  priority: 'urgent' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action: string;
  deadline?: string;
  assignee?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
}

export interface AnalysisTrend {
  metric: string;
  timeframe: string;
  direction: 'improving' | 'stable' | 'declining';
  rate: number;
  confidence: number;
  projection?: TrendProjection;
}

export interface TrendProjection {
  timeframe: string;
  expectedValue: number;
  confidence: number;
  scenarios: ProjectionScenario[];
}

export interface ProjectionScenario {
  name: string;
  probability: number;
  expectedValue: number;
  description: string;
}

export interface AnalysisPerformanceMetrics {
  averageExecutionTime: number;
  successRate: number;
  accuracyScore: number;
  resourceUtilization: number;
  userSatisfaction?: number;
  trendData: PerformanceTrend[];
}

export interface PerformanceTrend {
  metric: string;
  values: TimeSeriesValue[];
  trend: 'up' | 'down' | 'stable';
  changeRate: number;
}

export interface TimeSeriesValue {
  timestamp: string;
  value: number;
}

export interface AnalysisMetrics {
  executionTime: number;
  resourceUsage: ResourceUsage;
  accuracyMetrics: AccuracyMetrics;
  qualityMetrics: QualityMetrics;
  performanceMetrics: PerformanceMetrics;
}

export interface ResourceUsage {
  cpuTime: number;
  memoryPeak: number;
  diskIO: number;
  networkIO: number;
  cost: number;
}

export interface AccuracyMetrics {
  precision: number;
  recall: number;
  f1Score: number;
  accuracy: number;
  specificity: number;
  sensitivity: number;
}

export interface QualityMetrics {
  completeness: number;
  consistency: number;
  accuracy: number;
  timeliness: number;
  validity: number;
  uniqueness: number;
}

export interface PerformanceMetrics {
  throughput: number;
  latency: number;
  errorRate: number;
  availability: number;
  scalability: number;
}

export interface FlowStateDetail extends FlowState {
  stateHistory: FlowStateHistory[];
  agentStates: Record<string, AgentStateDetail>;
  validationResults: ValidationResult[];
  performanceMetrics: StatePerformanceMetrics;
}

export interface FlowStateHistory {
  timestamp: string;
  phase: string;
  action: string;
  actor: string;
  changes: Record<string, any>;
  reason?: string;
}

export interface AgentStateDetail extends AgentState {
  performance: AgentPerformance;
  history: AgentStateHistory[];
  insights: AgentInsight[];
  clarifications: AgentClarification[];
}

export interface AgentPerformance {
  tasksCompleted: number;
  averageTaskTime: number;
  successRate: number;
  qualityScore: number;
  learningProgress: number;
  userRating?: number;
}

export interface AgentStateHistory {
  timestamp: string;
  status: string;
  task?: string;
  changes: Record<string, any>;
  performance?: AgentPerformance;
}

export interface StatePerformanceMetrics {
  transitionTime: number;
  validationTime: number;
  persistenceTime: number;
  agentResponseTime: number;
  overallEfficiency: number;
}

export interface FlowTransition {
  fromPhase: string;
  toPhase: string;
  conditions: TransitionCondition[];
  validations: ValidationRule[];
  automated: boolean;
  estimatedDuration?: number;
}

export interface TransitionCondition {
  type: 'completion' | 'approval' | 'validation' | 'manual' | 'time';
  description: string;
  required: boolean;
  currentStatus: 'met' | 'not_met' | 'pending';
  details?: Record<string, any>;
}

export interface StateTransitionResult {
  success: boolean;
  fromPhase: string;
  toPhase: string;
  transitionTime: number;
  validationResults: ValidationResult[];
  warnings: string[];
  rollbackAvailable: boolean;
}

export interface PhaseTransitionResult extends StateTransitionResult {
  agentNotifications: AgentNotification[];
  nextSteps: string[];
  automaticActions: AutomaticAction[];
}

export interface AgentNotification {
  agentId: string;
  type: 'phase_change' | 'task_assignment' | 'clarification_request' | 'alert';
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  actionRequired: boolean;
  deadline?: string;
}

export interface AutomaticAction {
  type: string;
  description: string;
  scheduled: boolean;
  scheduledTime?: string;
  dependencies?: string[];
}

export interface StateChangeNotification {
  type: 'user' | 'agent' | 'system' | 'webhook';
  target: string;
  message: string;
  channels: string[];
  sent: boolean;
  error?: string;
}

export interface FollowUpAction {
  type: 'task' | 'reminder' | 'escalation' | 'review';
  description: string;
  assignee?: string;
  dueDate?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  automated: boolean;
}

export interface MappingProgressDetail {
  flowId: string;
  dataImportId?: string;
  totalMappings: number;
  completedMappings: number;
  pendingMappings: number;
  approvedMappings: number;
  rejectedMappings: number;
  progressPercentage: number;
  velocity: ProgressVelocity;
  bottlenecks: ProgressBottleneck[];
  projections: ProgressProjection[];
  qualityMetrics: MappingQualityMetrics;
  lastUpdated: string;
}

export interface ProgressVelocity {
  current: number;
  average: number;
  trend: 'increasing' | 'stable' | 'decreasing';
  efficiency: number;
}

export interface ProgressBottleneck {
  type: 'validation' | 'approval' | 'complexity' | 'dependency' | 'resource';
  description: string;
  impact: number;
  estimatedResolution: number;
  suggestions: string[];
}

export interface ProgressProjection {
  scenario: 'optimistic' | 'realistic' | 'pessimistic';
  estimatedCompletion: string;
  confidence: number;
  assumptions: string[];
  risks: string[];
}

export interface MappingQualityMetrics {
  averageConfidence: number;
  validationPassRate: number;
  reworkRate: number;
  automationRate: number;
  userSatisfaction?: number;
}

export interface FlowProgressDetail {
  flowId: string;
  overallProgress: number;
  phaseProgress: Record<string, number>;
  completedPhases: string[];
  currentPhase: string;
  nextPhase?: string;
  blockedPhases: string[];
  velocity: ProgressVelocity;
  timeline: ProgressTimeline[];
  milestones: ProgressMilestone[];
  risks: ProgressRisk[];
  estimatedCompletion: string;
  confidenceLevel: number;
}

export interface ProgressTimeline {
  phase: string;
  startDate: string;
  endDate?: string;
  estimatedEndDate: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'cancelled';
  progress: number;
  milestones: ProgressMilestone[];
}

export interface ProgressMilestone {
  id: string;
  name: string;
  description: string;
  targetDate: string;
  actualDate?: string;
  status: 'upcoming' | 'on_track' | 'at_risk' | 'overdue' | 'completed';
  criticality: 'low' | 'medium' | 'high' | 'critical';
}

export interface ProgressRisk {
  id: string;
  type: 'schedule' | 'quality' | 'resource' | 'dependency' | 'technical';
  probability: 'low' | 'medium' | 'high';
  impact: 'low' | 'medium' | 'high';
  description: string;
  mitigation?: string;
  owner?: string;
}

export interface ProgressMetrics {
  efficiency: number;
  quality: number;
  velocity: number;
  predictability: number;
  riskLevel: number;
  teamProductivity: number;
  automationLevel: number;
  userEngagement: number;
}

export interface TrainingProgressDetail {
  trainingId: string;
  flowId: string;
  modelId: string;
  status: TrainingStatus;
  progress: number;
  currentEpoch: number;
  totalEpochs: number;
  elapsedTime: number;
  estimatedTimeRemaining?: number;
  currentLoss: number;
  bestLoss: number;
  currentAccuracy: number;
  bestAccuracy: number;
  metrics: TrainingMetrics;
  configuration: TrainingConfiguration;
  resourceUsage: TrainingResourceUsage;
  checkpoints: TrainingCheckpoint[];
}

export interface TrainingStatus {
  phase: 'initializing' | 'training' | 'validating' | 'completed' | 'failed' | 'cancelled';
  message?: string;
  lastUpdate: string;
  stable: boolean;
}

export interface TrainingMetrics {
  loss: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  validationLoss?: number;
  validationAccuracy?: number;
  learningRate: number;
  customMetrics?: Record<string, number>;
  history: MetricHistory[];
}

export interface MetricHistory {
  epoch: number;
  timestamp: string;
  metrics: Record<string, number>;
}

export interface TrainingLog {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  source: string;
  epoch?: number;
  metadata?: Record<string, any>;
}

export interface TrainingHistory {
  trainingId: string;
  startTime: string;
  endTime?: string;
  finalMetrics?: TrainingMetrics;
  configuration: TrainingConfiguration;
  outcome: 'completed' | 'failed' | 'cancelled' | 'interrupted';
  notes?: string;
}

export interface ModelConfiguration {
  architecture: string;
  parameters: Record<string, any>;
  pretrainedModel?: string;
  customLayers?: LayerConfiguration[];
  optimization: OptimizationConfiguration;
}

export interface LayerConfiguration {
  type: string;
  parameters: Record<string, any>;
  position: number;
}

export interface OptimizationConfiguration {
  optimizer: string;
  learningRate: number;
  momentum?: number;
  weightDecay?: number;
  schedule?: LearningRateSchedule;
}

export interface LearningRateSchedule {
  type: 'constant' | 'step' | 'exponential' | 'cosine' | 'polynomial';
  parameters: Record<string, any>;
}

export interface TrainingConfiguration {
  epochs: number;
  batchSize: number;
  validationSplit: number;
  earlyStoppingEnabled: boolean;
  patience?: number;
  minDelta?: number;
  checkpointFrequency: number;
  saveTopK: number;
  shuffleData: boolean;
  augmentationEnabled: boolean;
  augmentationConfig?: AugmentationConfiguration;
}

export interface AugmentationConfiguration {
  enabled: boolean;
  techniques: string[];
  probability: number;
  parameters: Record<string, any>;
}

export interface DatasetConfiguration {
  datasetId: string;
  splitRatio: DataSplitRatio;
  preprocessing: PreprocessingConfiguration;
  validation: DataValidationConfiguration;
  caching: boolean;
}

export interface DataSplitRatio {
  train: number;
  validation: number;
  test: number;
  stratified: boolean;
}

export interface PreprocessingConfiguration {
  normalization: boolean;
  scaling: 'none' | 'standard' | 'minmax' | 'robust';
  featureSelection: boolean;
  dimensionalityReduction?: DimensionalityReductionConfiguration;
  customTransforms?: TransformConfiguration[];
}

export interface DimensionalityReductionConfiguration {
  technique: 'pca' | 'tsne' | 'umap' | 'autoencoder';
  targetDimensions: number;
  parameters: Record<string, any>;
}

export interface TransformConfiguration {
  name: string;
  type: string;
  parameters: Record<string, any>;
  order: number;
}

export interface DataValidationConfiguration {
  enabled: boolean;
  schemaValidation: boolean;
  qualityChecks: string[];
  outlierDetection: boolean;
  missingValueHandling: 'skip' | 'impute' | 'flag';
  duplicateHandling: 'skip' | 'keep_first' | 'keep_last' | 'aggregate';
}

export interface TrainingJob {
  id: string;
  flowId: string;
  status: 'queued' | 'initializing' | 'running' | 'completed' | 'failed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  estimatedDuration?: number;
  queuePosition?: number;
  resourceRequirements: ResourceRequirements;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

export interface ResourceRequirements {
  cpuCores: number;
  memoryGB: number;
  gpuRequired: boolean;
  gpuMemoryGB?: number;
  storageGB: number;
  networkBandwidth?: number;
}

export interface TrainingResourceUsage {
  cpuUtilization: number;
  memoryUsage: number;
  memoryPeak: number;
  gpuUtilization?: number;
  gpuMemoryUsage?: number;
  diskIO: number;
  networkIO: number;
  cost: number;
  efficiency: number;
}

export interface TrainingCheckpoint {
  epoch: number;
  timestamp: string;
  metrics: Record<string, number>;
  modelPath: string;
  optimizerState: string;
  size: number;
  isBest: boolean;
}

export interface TrainingStopResult {
  trainingId: string;
  finalEpoch: number;
  finalMetrics: TrainingMetrics;
  modelSaved: boolean;
  modelPath?: string;
  reason: 'user_requested' | 'completed' | 'early_stopping' | 'error' | 'timeout';
  message?: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  version: string;
  architecture: string;
  parameters: number;
  size: number;
  accuracy?: number;
  trainingTime?: number;
  datasetId?: string;
  createdAt: string;
  description?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface DeletedResource {
  type: string;
  id: string;
  name?: string;
  status: 'deleted' | 'archived' | 'failed';
  error?: string;
}

export interface RetentionInfo {
  archiveDate?: string;
  deleteDate?: string;
  retentionDays: number;
  dataLocation?: string;
  recoverable: boolean;
}

export interface FlowAggregation {
  field: string;
  buckets: AggregationBucket[];
  total: number;
}

export interface AggregationBucket {
  key: string;
  count: number;
  percentage: number;
}

export interface FlowTrend {
  metric: string;
  timeframe: string;
  direction: 'up' | 'down' | 'stable';
  changeRate: number;
  dataPoints: TrendDataPoint[];
}

export interface TrendDataPoint {
  timestamp: string;
  value: number;
}

export interface RetryPolicy {
  maxRetries: number;
  initialDelay: number;
  backoffMultiplier: number;
  maxDelay: number;
}

export interface NotificationChannel {
  type: 'email' | 'webhook' | 'sms' | 'push';
  target: string;
  enabled: boolean;
  events: string[];
  configuration?: Record<string, any>;
}