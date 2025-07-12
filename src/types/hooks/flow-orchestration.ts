/**
 * Flow Orchestration Hook Types
 * 
 * Type definitions for flow orchestration hooks including flow management,
 * agent coordination, task execution, and workflow state management.
 */

import { BaseAsyncHookParams, BaseAsyncHookReturn } from './shared';

// Flow Management Hook Types
export interface UseFlowManagementParams extends BaseAsyncHookParams {
  flowType?: string;
  clientAccountId?: string;
  engagementId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
  includeArchived?: boolean;
  includeMetrics?: boolean;
  onFlowStateChange?: (flowId: string, newState: FlowState) => void;
  onFlowError?: (flowId: string, error: Error) => void;
  onFlowComplete?: (flowId: string, result: any) => void;
}

export interface UseFlowManagementReturn extends BaseAsyncHookReturn<FlowSummary[]> {
  flows: FlowSummary[];
  activeFlows: FlowSummary[];
  completedFlows: FlowSummary[];
  failedFlows: FlowSummary[];
  totalFlows: number;
  
  // Flow CRUD operations
  createFlow: (flowData: CreateFlowData) => Promise<Flow>;
  updateFlow: (flowId: string, updates: Partial<FlowData>) => Promise<Flow>;
  deleteFlow: (flowId: string) => Promise<void>;
  archiveFlow: (flowId: string) => Promise<void>;
  restoreFlow: (flowId: string) => Promise<void>;
  
  // Flow execution
  startFlow: (flowId: string, config?: FlowExecutionConfig) => Promise<void>;
  pauseFlow: (flowId: string) => Promise<void>;
  resumeFlow: (flowId: string) => Promise<void>;
  stopFlow: (flowId: string, reason?: string) => Promise<void>;
  restartFlow: (flowId: string) => Promise<void>;
  
  // Flow monitoring
  getFlowStatus: (flowId: string) => Promise<FlowStatus>;
  getFlowMetrics: (flowId: string) => Promise<FlowMetrics>;
  getFlowLogs: (flowId: string, options?: LogOptions) => Promise<FlowLog[]>;
  subscribeToFlow: (flowId: string, callback: FlowEventCallback) => () => void;
  
  // Bulk operations
  bulkStart: (flowIds: string[]) => Promise<BulkOperationResult>;
  bulkStop: (flowIds: string[]) => Promise<BulkOperationResult>;
  bulkDelete: (flowIds: string[]) => Promise<BulkOperationResult>;
  bulkArchive: (flowIds: string[]) => Promise<BulkOperationResult>;
  
  // Filtering and searching
  filterFlows: (criteria: FlowFilterCriteria) => FlowSummary[];
  searchFlows: (query: string) => FlowSummary[];
  sortFlows: (sortBy: FlowSortOption, direction: 'asc' | 'desc') => void;
  
  // State management
  selectedFlows: string[];
  setSelectedFlows: (flowIds: string[]) => void;
  selectAllFlows: () => void;
  clearSelection: () => void;
  
  // Statistics
  flowStatistics: FlowStatistics;
  refreshStatistics: () => Promise<void>;
}

// Flow State Hook Types
export interface UseFlowStateParams extends BaseAsyncHookParams {
  flowId: string;
  includeHistory?: boolean;
  includeMetrics?: boolean;
  includeAgentStates?: boolean;
  includeTaskStates?: boolean;
  realTimeUpdates?: boolean;
  onStateChange?: (newState: FlowState, previousState: FlowState) => void;
  onPhaseChange?: (newPhase: string, previousPhase: string) => void;
  onError?: (error: FlowError) => void;
}

export interface UseFlowStateReturn extends BaseAsyncHookReturn<FlowState> {
  state: FlowState;
  currentPhase: string;
  nextPhase: string | null;
  previousPhase: string | null;
  progress: number;
  
  // Phase management
  phases: FlowPhase[];
  phaseStates: Record<string, PhaseState>;
  canProgressToPhase: (phase: string) => boolean;
  progressToPhase: (phase: string) => Promise<void>;
  rollbackToPhase: (phase: string) => Promise<void>;
  
  // State history
  stateHistory: FlowStateHistoryEntry[];
  restoreState: (timestamp: number) => Promise<void>;
  compareStates: (timestamp1: number, timestamp2: number) => StateComparison;
  
  // Agent states
  agentStates: Record<string, AgentState>;
  getAgentState: (agentId: string) => AgentState | null;
  updateAgentState: (agentId: string, state: Partial<AgentState>) => void;
  
  // Task states
  taskStates: Record<string, TaskState>;
  getTaskState: (taskId: string) => TaskState | null;
  updateTaskState: (taskId: string, state: Partial<TaskState>) => void;
  
  // Metrics
  metrics: FlowMetrics;
  refreshMetrics: () => Promise<void>;
  
  // Validation
  isValid: boolean;
  validationErrors: ValidationError[];
  validate: () => Promise<ValidationResult>;
  
  // Persistence
  saveState: () => Promise<void>;
  loadState: (timestamp?: number) => Promise<void>;
  exportState: () => FlowStateExport;
  importState: (stateExport: FlowStateExport) => Promise<void>;
}

// Agent Coordination Hook Types
export interface UseAgentCoordinationParams extends BaseAsyncHookParams {
  flowId: string;
  includeMetrics?: boolean;
  includeInsights?: boolean;
  includeHealth?: boolean;
  monitoringEnabled?: boolean;
  onAgentEvent?: (event: AgentEvent) => void;
  onCoordinationError?: (error: CoordinationError) => void;
  onTaskAssignment?: (agentId: string, taskId: string) => void;
}

export interface UseAgentCoordinationReturn extends BaseAsyncHookReturn<AgentCoordination> {
  coordination: AgentCoordination;
  agents: Agent[];
  activeAgents: Agent[];
  availableAgents: Agent[];
  busyAgents: Agent[];
  errorAgents: Agent[];
  
  // Agent management
  createAgent: (agentConfig: AgentConfig) => Promise<Agent>;
  updateAgent: (agentId: string, updates: Partial<AgentConfig>) => Promise<Agent>;
  deleteAgent: (agentId: string) => Promise<void>;
  startAgent: (agentId: string) => Promise<void>;
  stopAgent: (agentId: string) => Promise<void>;
  restartAgent: (agentId: string) => Promise<void>;
  
  // Task assignment
  assignTask: (agentId: string, taskId: string) => Promise<TaskAssignment>;
  unassignTask: (agentId: string, taskId: string) => Promise<void>;
  reassignTask: (fromAgentId: string, toAgentId: string, taskId: string) => Promise<TaskAssignment>;
  autoAssignTasks: (strategy?: AssignmentStrategy) => Promise<TaskAssignment[]>;
  
  // Communication
  sendMessage: (agentId: string, message: AgentMessage) => Promise<void>;
  broadcastMessage: (message: AgentMessage, filter?: AgentFilter) => Promise<void>;
  subscribeToAgent: (agentId: string, callback: AgentEventCallback) => () => void;
  
  // Coordination strategies
  coordinationStrategy: CoordinationStrategy;
  setCoordinationStrategy: (strategy: CoordinationStrategy) => void;
  executeCoordination: () => Promise<CoordinationResult>;
  
  // Health monitoring
  agentHealth: Record<string, AgentHealth>;
  getAgentHealth: (agentId: string) => AgentHealth;
  checkAllAgentHealth: () => Promise<Record<string, AgentHealth>>;
  
  // Performance metrics
  agentMetrics: Record<string, AgentMetrics>;
  getAgentMetrics: (agentId: string) => AgentMetrics;
  getCoordinationMetrics: () => CoordinationMetrics;
  
  // Insights
  agentInsights: AgentInsight[];
  getAgentInsights: (agentId: string) => AgentInsight[];
  generateInsights: () => Promise<AgentInsight[]>;
}

// Task Execution Hook Types
export interface UseTaskExecutionParams extends BaseAsyncHookParams {
  flowId?: string;
  taskId?: string;
  includeSubtasks?: boolean;
  includeDependencies?: boolean;
  includeMetrics?: boolean;
  includeLogs?: boolean;
  realTimeUpdates?: boolean;
  onTaskStateChange?: (taskId: string, newState: TaskState) => void;
  onTaskComplete?: (taskId: string, result: TaskResult) => void;
  onTaskError?: (taskId: string, error: TaskError) => void;
}

export interface UseTaskExecutionReturn extends BaseAsyncHookReturn<Task[]> {
  tasks: Task[];
  activeTasks: Task[];
  completedTasks: Task[];
  failedTasks: Task[];
  pendingTasks: Task[];
  totalTasks: number;
  
  // Task CRUD operations
  createTask: (taskData: CreateTaskData) => Promise<Task>;
  updateTask: (taskId: string, updates: Partial<TaskData>) => Promise<Task>;
  deleteTask: (taskId: string) => Promise<void>;
  cloneTask: (taskId: string, modifications?: Partial<TaskData>) => Promise<Task>;
  
  // Task execution
  executeTask: (taskId: string, params?: TaskExecutionParams) => Promise<TaskResult>;
  executeMultipleTasks: (taskIds: string[], params?: BulkExecutionParams) => Promise<TaskResult[]>;
  pauseTask: (taskId: string) => Promise<void>;
  resumeTask: (taskId: string) => Promise<void>;
  cancelTask: (taskId: string, reason?: string) => Promise<void>;
  retryTask: (taskId: string, retryConfig?: RetryConfig) => Promise<TaskResult>;
  
  // Task dependencies
  getDependencies: (taskId: string) => TaskDependency[];
  addDependency: (taskId: string, dependencyId: string, type?: DependencyType) => Promise<void>;
  removeDependency: (taskId: string, dependencyId: string) => Promise<void>;
  resolveDependencies: (taskId: string) => Promise<DependencyResolution[]>;
  
  // Task scheduling
  scheduleTask: (taskId: string, schedule: TaskSchedule) => Promise<void>;
  unscheduleTask: (taskId: string) => Promise<void>;
  rescheduleTask: (taskId: string, newSchedule: TaskSchedule) => Promise<void>;
  getSchedule: (taskId: string) => TaskSchedule | null;
  
  // Task monitoring
  getTaskStatus: (taskId: string) => TaskStatus;
  getTaskMetrics: (taskId: string) => TaskMetrics;
  getTaskLogs: (taskId: string, options?: LogOptions) => Promise<TaskLog[]>;
  subscribeToTask: (taskId: string, callback: TaskEventCallback) => () => void;
  
  // Batch operations
  batchExecute: (taskIds: string[]) => Promise<BatchExecutionResult>;
  batchCancel: (taskIds: string[]) => Promise<BatchOperationResult>;
  batchRetry: (taskIds: string[]) => Promise<BatchExecutionResult>;
  
  // Task queues
  taskQueues: TaskQueue[];
  getQueue: (queueId: string) => TaskQueue | null;
  addToQueue: (taskId: string, queueId: string, priority?: number) => Promise<void>;
  removeFromQueue: (taskId: string, queueId: string) => Promise<void>;
  processQueue: (queueId: string) => Promise<QueueProcessingResult>;
  
  // Statistics and analytics
  taskStatistics: TaskStatistics;
  getExecutionAnalytics: () => ExecutionAnalytics;
  getPerformanceMetrics: () => PerformanceMetrics;
}

// Workflow State Hook Types
export interface UseWorkflowStateParams extends BaseAsyncHookParams {
  workflowId: string;
  includeSteps?: boolean;
  includeHistory?: boolean;
  includeMetrics?: boolean;
  includeValidation?: boolean;
  realTimeUpdates?: boolean;
  onStateChange?: (newState: WorkflowState) => void;
  onStepComplete?: (stepId: string, result: StepResult) => void;
  onWorkflowComplete?: (result: WorkflowResult) => void;
  onError?: (error: WorkflowError) => void;
}

export interface UseWorkflowStateReturn extends BaseAsyncHookReturn<WorkflowState> {
  state: WorkflowState;
  currentStep: WorkflowStep | null;
  nextStep: WorkflowStep | null;
  previousStep: WorkflowStep | null;
  completedSteps: WorkflowStep[];
  remainingSteps: WorkflowStep[];
  progress: number;
  
  // Workflow control
  startWorkflow: (params?: WorkflowStartParams) => Promise<void>;
  pauseWorkflow: () => Promise<void>;
  resumeWorkflow: () => Promise<void>;
  stopWorkflow: (reason?: string) => Promise<void>;
  restartWorkflow: () => Promise<void>;
  
  // Step navigation
  executeStep: (stepId: string, params?: StepExecutionParams) => Promise<StepResult>;
  skipStep: (stepId: string, reason?: string) => Promise<void>;
  retryStep: (stepId: string, retryConfig?: RetryConfig) => Promise<StepResult>;
  goToStep: (stepId: string) => Promise<void>;
  
  // Step management
  steps: WorkflowStep[];
  getStep: (stepId: string) => WorkflowStep | null;
  updateStep: (stepId: string, updates: Partial<WorkflowStepData>) => Promise<WorkflowStep>;
  addStep: (stepData: WorkflowStepData, position?: number) => Promise<WorkflowStep>;
  removeStep: (stepId: string) => Promise<void>;
  
  // Conditional logic
  evaluateCondition: (condition: WorkflowCondition) => boolean;
  getBranch: (branchCondition: BranchCondition) => WorkflowBranch | null;
  executeBranch: (branchId: string) => Promise<void>;
  
  // Variables and context
  variables: WorkflowVariables;
  setVariable: (name: string, value: any) => void;
  getVariable: (name: string) => any;
  deleteVariable: (name: string) => void;
  clearVariables: () => void;
  
  // Workflow history
  executionHistory: WorkflowExecutionEntry[];
  getHistoryEntry: (timestamp: number) => WorkflowExecutionEntry | null;
  rollbackToEntry: (timestamp: number) => Promise<void>;
  
  // Validation
  isValid: boolean;
  validationErrors: WorkflowValidationError[];
  validateWorkflow: () => Promise<WorkflowValidationResult>;
  validateStep: (stepId: string) => Promise<StepValidationResult>;
  
  // Export/Import
  exportWorkflow: () => WorkflowExport;
  importWorkflow: (workflowExport: WorkflowExport) => Promise<void>;
}

// Flow Analytics Hook Types
export interface UseFlowAnalyticsParams extends BaseAsyncHookParams {
  flowId?: string;
  flowType?: string;
  timeRange?: TimeRange;
  metrics?: string[];
  dimensions?: string[];
  includeComparisons?: boolean;
  includeTrends?: boolean;
  includeForecasts?: boolean;
  includeBenchmarks?: boolean;
  onAnalyticsUpdate?: (analytics: FlowAnalytics) => void;
}

export interface UseFlowAnalyticsReturn extends BaseAsyncHookReturn<FlowAnalytics> {
  analytics: FlowAnalytics;
  metrics: FlowMetrics;
  trends: FlowTrend[];
  forecasts: FlowForecast[];
  benchmarks: FlowBenchmark[];
  comparisons: FlowComparison[];
  
  // Metric queries
  getMetric: (metricName: string) => MetricValue | null;
  getMetricHistory: (metricName: string, timeRange?: TimeRange) => MetricDataPoint[];
  calculateMetric: (metricDefinition: MetricDefinition) => Promise<MetricValue>;
  
  // Trend analysis
  getTrend: (metricName: string) => FlowTrend | null;
  calculateTrend: (metricName: string, timeRange: TimeRange) => Promise<FlowTrend>;
  detectAnomalies: (metricName: string) => Promise<Anomaly[]>;
  
  // Forecasting
  getForecast: (metricName: string) => FlowForecast | null;
  generateForecast: (metricName: string, horizonDays: number) => Promise<FlowForecast>;
  validateForecast: (forecastId: string) => Promise<ForecastValidation>;
  
  // Benchmarking
  getBenchmark: (metricName: string) => FlowBenchmark | null;
  createBenchmark: (metricName: string, criteria: BenchmarkCriteria) => Promise<FlowBenchmark>;
  compareToBenchmark: (metricName: string, benchmarkId: string) => Promise<BenchmarkComparison>;
  
  // Custom analytics
  createCustomMetric: (definition: CustomMetricDefinition) => Promise<CustomMetric>;
  executeQuery: (query: AnalyticsQuery) => Promise<QueryResult>;
  createReport: (reportConfig: ReportConfiguration) => Promise<AnalyticsReport>;
  
  // Real-time updates
  subscribeToMetric: (metricName: string, callback: MetricUpdateCallback) => () => void;
  subscribeToTrend: (metricName: string, callback: TrendUpdateCallback) => () => void;
  
  // Export capabilities
  exportAnalytics: (format: ExportFormat) => Promise<AnalyticsExport>;
  exportMetrics: (metricNames: string[], format: ExportFormat) => Promise<MetricsExport>;
  exportReport: (reportId: string, format: ExportFormat) => Promise<ReportExport>;
}

// Supporting Types
export interface FlowSummary {
  id: string;
  name: string;
  type: string;
  status: FlowStatus;
  progress: number;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  clientAccountId: string;
  engagementId: string;
  metadata: Record<string, any>;
}

export interface FlowState {
  flowId: string;
  status: FlowStatus;
  currentPhase: string;
  nextPhase?: string;
  progress: number;
  phaseStates: Record<string, PhaseState>;
  agentStates: Record<string, AgentState>;
  taskStates: Record<string, TaskState>;
  variables: Record<string, any>;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface PhaseState {
  phase: string;
  status: PhaseStatus;
  startedAt?: string;
  completedAt?: string;
  progress: number;
  prerequisites: string[];
  dependencies: string[];
  outputs: Record<string, any>;
  errors: PhaseError[];
}

export interface AgentState {
  agentId: string;
  status: AgentStatus;
  currentTask?: string;
  assignedTasks: string[];
  completedTasks: string[];
  performance: AgentPerformance;
  lastActivity: string;
  health: AgentHealth;
}

export interface TaskState {
  taskId: string;
  status: TaskStatus;
  assignedAgent?: string;
  startedAt?: string;
  completedAt?: string;
  progress: number;
  dependencies: string[];
  result?: TaskResult;
  error?: TaskError;
}

export interface WorkflowState {
  workflowId: string;
  status: WorkflowStatus;
  currentStep?: string;
  completedSteps: string[];
  variables: WorkflowVariables;
  context: WorkflowContext;
  history: WorkflowExecutionEntry[];
  errors: WorkflowError[];
}

export type FlowStatus = 'created' | 'initializing' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
export type PhaseStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
export type AgentStatus = 'idle' | 'busy' | 'error' | 'offline' | 'maintenance';
export type TaskStatus = 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
export type WorkflowStatus = 'draft' | 'active' | 'paused' | 'completed' | 'failed' | 'cancelled';

// Additional supporting interfaces would continue here...
// (This is a comprehensive but truncated version for brevity)