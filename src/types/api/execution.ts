/**
 * Execution API Types
 * 
 * Type definitions for Migration Execution flow API endpoints, requests, and responses.
 * Covers execution management, task orchestration, progress tracking, and monitoring.
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
  ValidationResult
} from './shared';

// Execution Flow Management APIs
export interface InitializeExecutionFlowRequest extends BaseApiRequest {
  flowName: string;
  flowDescription?: string;
  context: MultiTenantContext;
  executionPlan: ExecutionPlanReference;
  environment: ExecutionEnvironment;
  approvals: ExecutionApproval[];
  parentFlowId?: string;
  configuration?: ExecutionFlowConfiguration;
  metadata?: Record<string, any>;
}

export interface InitializeExecutionFlowResponse extends BaseApiResponse<ExecutionFlowData> {
  data: ExecutionFlowData;
  flowId: string;
  initialState: ExecutionState;
  executionPlan: ExecutionPlan;
  nextActions: ExecutionAction[];
  prerequisites: ExecutionPrerequisite[];
}

export interface GetExecutionFlowStatusRequest extends GetRequest {
  flowId: string;
  includeDetails?: boolean;
  includeProgress?: boolean;
  includeTasks?: boolean;
  includeMetrics?: boolean;
  includeIssues?: boolean;
  includeRisks?: boolean;
  realTime?: boolean;
}

export interface GetExecutionFlowStatusResponse extends BaseApiResponse<ExecutionStatusDetail> {
  data: ExecutionStatusDetail;
  progress: ExecutionProgress;
  tasks: TaskStatus[];
  metrics: ExecutionMetrics;
  issues: ExecutionIssue[];
  risks: ExecutionRisk[];
  realTimeUpdates?: boolean;
  nextRefresh?: string;
}

export interface ListExecutionFlowsRequest extends ListRequest {
  executionTypes?: string[];
  status?: ExecutionStatus[];
  priorities?: string[];
  environments?: string[];
  clientAccountIds?: string[];
  engagementIds?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'updated' | 'started' | 'completed';
  };
  includeArchived?: boolean;
  includeMetrics?: boolean;
}

export interface ListExecutionFlowsResponse extends ListResponse<ExecutionFlowSummary> {
  data: ExecutionFlowSummary[];
  aggregations?: ExecutionAggregation[];
  trends?: ExecutionTrend[];
  portfolioMetrics?: ExecutionPortfolioMetrics;
}

export interface UpdateExecutionFlowRequest extends UpdateRequest<Partial<ExecutionFlowData>> {
  flowId: string;
  data: Partial<ExecutionFlowData>;
  updateType?: 'status' | 'configuration' | 'schedule' | 'resources';
  validateChanges?: boolean;
  notifyStakeholders?: boolean;
}

export interface UpdateExecutionFlowResponse extends UpdateResponse<ExecutionFlowData> {
  data: ExecutionFlowData;
  changeImpact?: ExecutionChangeImpact;
  notifications?: ExecutionNotification[];
  approvalRequired?: boolean;
}

// Execution Control APIs
export interface StartExecutionRequest extends BaseApiRequest {
  flowId: string;
  startType?: 'immediate' | 'scheduled' | 'manual';
  scheduledTime?: string;
  preExecutionChecks?: boolean;
  notificationSettings?: NotificationSettings;
  context: MultiTenantContext;
}

export interface StartExecutionResponse extends BaseApiResponse<ExecutionStartResult> {
  data: ExecutionStartResult;
  executionId: string;
  status: ExecutionStatus;
  startedAt: string;
  estimatedCompletion?: string;
  trackingUrl: string;
}

export interface PauseExecutionRequest extends BaseApiRequest {
  flowId: string;
  reason: string;
  gracefulShutdown?: boolean;
  preserveState?: boolean;
  notifyStakeholders?: boolean;
  context: MultiTenantContext;
}

export interface PauseExecutionResponse extends BaseApiResponse<ExecutionControlResult> {
  data: ExecutionControlResult;
  pausedAt: string;
  statePreserved: boolean;
  resumable: boolean;
  nextActions: string[];
}

export interface ResumeExecutionRequest extends BaseApiRequest {
  flowId: string;
  validateState?: boolean;
  recoverFromFailures?: boolean;
  updateSchedule?: boolean;
  context: MultiTenantContext;
}

export interface ResumeExecutionResponse extends BaseApiResponse<ExecutionControlResult> {
  data: ExecutionControlResult;
  resumedAt: string;
  stateRecovered: boolean;
  scheduleUpdated: boolean;
  nextTasks: TaskInfo[];
}

export interface StopExecutionRequest extends BaseApiRequest {
  flowId: string;
  reason: string;
  stopType: 'graceful' | 'immediate' | 'emergency';
  rollbackRequired?: boolean;
  preserveLogs?: boolean;
  context: MultiTenantContext;
}

export interface StopExecutionResponse extends BaseApiResponse<ExecutionControlResult> {
  data: ExecutionControlResult;
  stoppedAt: string;
  rollbackRequired: boolean;
  rollbackPlan?: RollbackPlan;
  cleanupRequired: boolean;
}

// Task Management APIs
export interface CreateTaskRequest extends CreateRequest<TaskData> {
  flowId: string;
  data: TaskData;
  parentTaskId?: string;
  dependencies?: TaskDependency[];
  scheduling?: TaskScheduling;
  resourceRequirements?: TaskResourceRequirement[];
  validation?: TaskValidation;
}

export interface CreateTaskResponse extends CreateResponse<TaskResult> {
  data: TaskResult;
  taskId: string;
  scheduledFor?: string;
  dependencies: TaskDependency[];
  resourceAllocations: ResourceAllocation[];
}

export interface GetTaskStatusRequest extends GetRequest {
  taskId: string;
  includeDetails?: boolean;
  includeLogs?: boolean;
  includeMetrics?: boolean;
  includeSubtasks?: boolean;
  includeDependencies?: boolean;
}

export interface GetTaskStatusResponse extends GetResponse<TaskStatusDetail> {
  data: TaskStatusDetail;
  logs: TaskLog[];
  metrics: TaskMetrics;
  subtasks: TaskStatus[];
  dependencies: TaskDependencyStatus[];
}

export interface ListTasksRequest extends ListRequest {
  flowId?: string;
  parentTaskId?: string;
  status?: TaskStatus[];
  types?: string[];
  priorities?: string[];
  assignees?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'updated' | 'started' | 'completed' | 'due';
  };
  includeDependencies?: boolean;
}

export interface ListTasksResponse extends ListResponse<TaskSummary> {
  data: TaskSummary[];
  dependencyGraph?: TaskDependencyGraph;
  criticalPath?: CriticalPath;
  statistics: TaskStatistics;
}

export interface UpdateTaskRequest extends UpdateRequest<Partial<TaskData>> {
  taskId: string;
  data: Partial<TaskData>;
  updateDependencies?: boolean;
  reschedule?: boolean;
  reallocateResources?: boolean;
}

export interface UpdateTaskResponse extends UpdateResponse<TaskResult> {
  data: TaskResult;
  dependencyImpacts?: TaskDependencyImpact[];
  scheduleChanges?: ScheduleChange[];
  resourceChanges?: ResourceChange[];
}

export interface ExecuteTaskRequest extends BaseApiRequest {
  taskId: string;
  executionMode?: 'sync' | 'async' | 'batch';
  parameters?: Record<string, any>;
  overrides?: TaskOverride[];
  context: MultiTenantContext;
}

export interface ExecuteTaskResponse extends BaseApiResponse<TaskExecutionResult> {
  data: TaskExecutionResult;
  executionId: string;
  status: TaskExecutionStatus;
  output?: unknown;
  logs: TaskExecutionLog[];
}

// Monitoring and Tracking APIs
export interface GetExecutionMetricsRequest extends BaseApiRequest {
  flowId?: string;
  executionId?: string;
  timeRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
  granularity?: 'minute' | 'hour' | 'day';
  context: MultiTenantContext;
}

export interface GetExecutionMetricsResponse extends BaseApiResponse<ExecutionMetrics> {
  data: ExecutionMetrics;
  trends: MetricTrend[];
  benchmarks: MetricBenchmark[];
  alerts: MetricAlert[];
}

export interface GetExecutionLogsRequest extends BaseApiRequest {
  flowId?: string;
  executionId?: string;
  taskId?: string;
  logLevel?: 'debug' | 'info' | 'warn' | 'error' | 'fatal';
  timeRange?: {
    start: string;
    end: string;
  };
  search?: string;
  pageSize?: number;
  context: MultiTenantContext;
}

export interface GetExecutionLogsResponse extends BaseApiResponse<ExecutionLog[]> {
  data: ExecutionLog[];
  totalLogs: number;
  hasMore: boolean;
  searchHighlights?: LogHighlight[];
}

export interface CreateExecutionCheckpointRequest extends BaseApiRequest {
  flowId: string;
  name: string;
  description?: string;
  includeState?: boolean;
  includeData?: boolean;
  includeConfiguration?: boolean;
  context: MultiTenantContext;
}

export interface CreateExecutionCheckpointResponse extends BaseApiResponse<ExecutionCheckpoint> {
  data: ExecutionCheckpoint;
  checkpointId: string;
  size: number;
  createdAt: string;
  restoreInstructions: string[];
}

export interface RestoreExecutionCheckpointRequest extends BaseApiRequest {
  flowId: string;
  checkpointId: string;
  restoreType: 'full' | 'partial' | 'state_only';
  validateBeforeRestore?: boolean;
  context: MultiTenantContext;
}

export interface RestoreExecutionCheckpointResponse extends BaseApiResponse<ExecutionRestoreResult> {
  data: ExecutionRestoreResult;
  restoredAt: string;
  restoredComponents: string[];
  validationResults: ValidationResult[];
  nextActions: string[];
}

// Issue and Risk Management APIs
export interface ReportExecutionIssueRequest extends CreateRequest<ExecutionIssueData> {
  flowId: string;
  data: ExecutionIssueData;
  severity: IssueSeverity;
  category: IssueCategory;
  impactAssessment?: ImpactAssessment;
  suggestedResolution?: string;
}

export interface ReportExecutionIssueResponse extends CreateResponse<ExecutionIssue> {
  data: ExecutionIssue;
  issueId: string;
  assignedTo?: string;
  escalationLevel: number;
  resolutionPlan?: ResolutionPlan;
}

export interface GetExecutionIssuesRequest extends ListRequest {
  flowId?: string;
  executionId?: string;
  taskId?: string;
  severity?: IssueSeverity[];
  category?: IssueCategory[];
  status?: IssueStatus[];
  assignedTo?: string;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface GetExecutionIssuesResponse extends ListResponse<ExecutionIssue> {
  data: ExecutionIssue[];
  statistics: IssueStatistics;
  trends: IssueTrend[];
  resolutionMetrics: ResolutionMetrics;
}

export interface UpdateExecutionIssueRequest extends UpdateRequest<Partial<ExecutionIssueData>> {
  issueId: string;
  data: Partial<ExecutionIssueData>;
  addResolutionStep?: ResolutionStep;
  updateStatus?: IssueStatus;
  reassign?: string;
}

export interface UpdateExecutionIssueResponse extends UpdateResponse<ExecutionIssue> {
  data: ExecutionIssue;
  statusChanged: boolean;
  escalated: boolean;
  notifications: IssueNotification[];
}

// Rollback and Recovery APIs
export interface CreateRollbackPlanRequest extends CreateRequest<RollbackPlanData> {
  flowId: string;
  data: RollbackPlanData;
  rollbackScope: RollbackScope;
  checkpoints: string[];
  validationCriteria: ValidationCriteria[];
  approvalRequired?: boolean;
}

export interface CreateRollbackPlanResponse extends CreateResponse<RollbackPlan> {
  data: RollbackPlan;
  planId: string;
  estimatedDuration: number;
  riskAssessment: RollbackRiskAssessment;
  prerequisites: RollbackPrerequisite[];
}

export interface ExecuteRollbackRequest extends BaseApiRequest {
  planId: string;
  rollbackType: 'full' | 'partial' | 'point_in_time';
  targetCheckpoint?: string;
  validateBefore?: boolean;
  dryRun?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteRollbackResponse extends BaseApiResponse<RollbackExecution> {
  data: RollbackExecution;
  rollbackId: string;
  status: RollbackStatus;
  startedAt: string;
  estimatedCompletion?: string;
}

export interface GetRollbackStatusRequest extends GetRequest {
  rollbackId: string;
  includeDetails?: boolean;
  includeLogs?: boolean;
  includeValidation?: boolean;
}

export interface GetRollbackStatusResponse extends GetResponse<RollbackStatus> {
  data: RollbackStatusDetail;
  progress: RollbackProgress;
  logs: RollbackLog[];
  validation: RollbackValidation;
}

// Execution Analytics and Reporting APIs
export interface GetExecutionAnalyticsRequest extends BaseApiRequest {
  flowId?: string;
  executionIds?: string[];
  timeRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
  dimensions?: string[];
  aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count';
  context: MultiTenantContext;
}

export interface GetExecutionAnalyticsResponse extends BaseApiResponse<ExecutionAnalytics> {
  data: ExecutionAnalytics;
  insights: ExecutionInsight[];
  trends: ExecutionTrend[];
  benchmarks: ExecutionBenchmark[];
  predictions: ExecutionPrediction[];
}

export interface GenerateExecutionReportRequest extends BaseApiRequest {
  flowId: string;
  reportType: 'progress' | 'completion' | 'issues' | 'performance' | 'comprehensive';
  format: 'pdf' | 'html' | 'docx' | 'json';
  timeRange?: {
    start: string;
    end: string;
  };
  sections?: string[];
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GenerateExecutionReportResponse extends BaseApiResponse<ExecutionReport> {
  data: ExecutionReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

// Supporting Data Types
export interface ExecutionFlowData {
  id: string;
  flowId: string;
  flowName: string;
  flowDescription?: string;
  executionType: string;
  status: ExecutionStatus;
  priority: 'low' | 'medium' | 'high' | 'critical' | 'emergency';
  environment: ExecutionEnvironment;
  progress: number;
  phases: ExecutionPhases;
  currentPhase: string;
  executionPlan: ExecutionPlanReference;
  approvals: ExecutionApproval[];
  clientAccountId: string;
  engagementId: string;
  userId: string;
  startedAt?: string;
  pausedAt?: string;
  resumedAt?: string;
  completedAt?: string;
  stoppedAt?: string;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, any>;
}

export interface ExecutionEnvironment {
  name: string;
  type: 'development' | 'testing' | 'staging' | 'production' | 'disaster_recovery';
  region: string;
  cloud: string;
  configuration: EnvironmentConfiguration;
  security: SecurityConfiguration;
  monitoring: MonitoringConfiguration;
  networking: NetworkConfiguration;
  access: AccessConfiguration;
  compliance: ComplianceConfiguration;
}

export interface ExecutionFlowConfiguration {
  parallelism: number;
  retryPolicy: RetryPolicy;
  timeoutSettings: TimeoutSettings;
  errorHandling: ErrorHandlingPolicy;
  logging: LoggingConfiguration;
  monitoring: MonitoringConfiguration;
  notifications: NotificationConfiguration;
  checkpointing: CheckpointingConfiguration;
  rollback: RollbackConfiguration;
  security: SecurityConfiguration;
}

export interface ExecutionState {
  flowId: string;
  status: ExecutionStatus;
  currentPhase: string;
  nextPhase?: string;
  phaseStates: Record<string, PhaseState>;
  taskStates: Record<string, TaskState>;
  resourceStates: Record<string, ResourceState>;
  checkpoints: ExecutionCheckpoint[];
  metrics: ExecutionMetrics;
  issues: ExecutionIssue[];
  risks: ExecutionRisk[];
  decisions: ExecutionDecision[];
  approvals: ExecutionApproval[];
  createdAt: string;
  updatedAt: string;
}

export type ExecutionStatus = 
  | 'pending' | 'initializing' | 'ready' | 'running' 
  | 'paused' | 'resuming' | 'stopping' | 'stopped' 
  | 'completed' | 'failed' | 'cancelled' | 'rollback_required' 
  | 'rolling_back' | 'rolled_back';

export type TaskStatus = 
  | 'pending' | 'ready' | 'running' | 'paused' 
  | 'completed' | 'failed' | 'cancelled' | 'skipped' 
  | 'waiting_for_dependencies' | 'waiting_for_approval' 
  | 'waiting_for_resources';

export type IssueSeverity = 'low' | 'medium' | 'high' | 'critical' | 'blocker';
export type IssueCategory = 'technical' | 'business' | 'security' | 'compliance' | 'performance' | 'resource';
export type IssueStatus = 'open' | 'in_progress' | 'resolved' | 'closed' | 'escalated';
export type RollbackStatus = 'planned' | 'ready' | 'executing' | 'completed' | 'failed' | 'cancelled';

// Additional supporting interfaces would continue here...
// (This is a comprehensive but truncated version for brevity)