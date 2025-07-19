/**
 * Flow Orchestration Model Types
 * 
 * Detailed model interfaces for flow orchestration data structures.
 */

import {
  AgentConfiguration,
  LLMConfiguration,
  FlowExecutionContext,
  TimeRange,
  MetricSample,
  ExecutionError,
  ExecutionWarning,
  ValidationResult,
  BackupResult,
  DeletionResult,
  RetryPolicy,
  ExecutionConstraints
} from './base-types';

// Flow Configuration and Execution Models
export interface FlowInitializationConfig {
  flowType: string;
  flowName: string;
  flowDescription?: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  configuration: FlowConfiguration;
  parentFlowId?: string;
  dependencies?: string[];
  priority?: 'low' | 'medium' | 'high' | 'critical';
  scheduledStart?: string;
  timeout?: number;
}

export interface FlowExecutionResult {
  flowId: string;
  executionId: string;
  status: 'started' | 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  result?: any;
  error?: ExecutionError;
  metrics: ExecutionMetrics;
  startTime: string;
  endTime?: string;
  duration?: number;
}

export interface FlowStatusDetail {
  flowId: string;
  flowType: string;
  status: FlowStatus;
  currentPhase: string;
  nextPhase?: string;
  progress: number;
  phases: PhaseStatus[];
  agents: AgentStatus[];
  crews: CrewStatus[];
  childFlows: ChildFlowStatus[];
  parentFlowId?: string;
  metrics: FlowMetrics;
  events: RecentEvent[];
  errors: ExecutionError[];
  warnings: ExecutionWarning[];
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface FlowHistoryEntry {
  id: string;
  flowId: string;
  timestamp: string;
  eventType: string;
  eventData: Record<string, any>;
  userId?: string;
  agentId?: string;
  phaseId?: string;
  description: string;
  metadata: Record<string, any>;
}

export interface ActiveFlowSummary {
  flowId: string;
  flowType: string;
  flowName: string;
  status: FlowStatus;
  progress: number;
  currentPhase: string;
  assignedAgents: number;
  activeCrews: number;
  childFlows: number;
  priority: string;
  startTime: string;
  estimatedCompletion?: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
}

export interface FlowStateData {
  flowId: string;
  flowType: string;
  currentPhase: string;
  nextPhase?: string;
  previousPhase?: string;
  phaseCompletion: Record<string, boolean>;
  phaseData: Record<string, any>;
  agentStates: Record<string, AgentState>;
  crewStates: Record<string, CrewState>;
  sharedData: Record<string, any>;
  checkpoints: StateCheckpoint[];
  version: number;
  createdAt: string;
  updatedAt: string;
}

// Agent Models
export interface AgentInstance {
  id: string;
  configuration: AgentConfiguration;
  status: AgentStatus;
  deployedFlows: string[];
  metrics: AgentMetrics;
  createdAt: string;
  lastActiveAt: string;
}

export interface AgentStatus {
  agentId: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  currentTask?: string;
  currentFlowId?: string;
  performance: AgentPerformance;
  health: AgentHealth;
  lastHeartbeat: string;
  errorCount: number;
  warningCount: number;
}

export interface AgentMetrics {
  agentId: string;
  tasksCompleted: number;
  tasksInProgress: number;
  tasksFailed: number;
  averageTaskDuration: number;
  successRate: number;
  errorRate: number;
  memoryUsage: number;
  cpuUsage: number;
  networkIO: number;
  timeRange: TimeRange;
  samples: MetricSample[];
}

export interface AgentCoordination {
  coordinationType: 'sequential' | 'parallel' | 'conditional' | 'pipeline';
  agents: string[];
  dependencies: AgentDependency[];
  timeout: number;
  retryPolicy: RetryPolicy;
  failureStrategy: 'abort' | 'continue' | 'fallback';
  communicationProtocol: 'event' | 'message' | 'shared_state';
}

export interface CoordinationResult {
  coordinationId: string;
  status: 'success' | 'partial' | 'failed';
  results: AgentResult[];
  errors: CoordinationError[];
  metrics: CoordinationMetrics;
  startTime: string;
  endTime: string;
  duration: number;
}

export interface AgentMessage {
  id: string;
  fromAgentId: string;
  toAgentId?: string; // null for broadcast
  messageType: string;
  content: any;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  timestamp: string;
  deliveryStatus: 'sent' | 'delivered' | 'acknowledged' | 'failed';
  metadata: Record<string, any>;
}

export interface AgentCommunication {
  id: string;
  flowId: string;
  participants: string[];
  messageCount: number;
  communicationType: 'coordination' | 'data_sharing' | 'status_update' | 'error_report';
  startTime: string;
  endTime?: string;
  status: 'active' | 'completed' | 'failed';
  summary: string;
}

// Crew Models
export interface CrewConfiguration {
  name: string;
  description: string;
  agents: AgentConfiguration[];
  tasks: CrewTask[];
  process: 'sequential' | 'hierarchical' | 'consensus';
  manager?: AgentConfiguration;
  maxIterations: number;
  timeout: number;
  memoryEnabled: boolean;
  planningEnabled: boolean;
  outputFormat: 'json' | 'text' | 'structured';
  callbacks: CrewCallback[];
}

export interface CrewInstance {
  id: string;
  configuration: CrewConfiguration;
  status: CrewStatus;
  agents: AgentInstance[];
  tasks: CrewTaskInstance[];
  manager?: AgentInstance;
  createdAt: string;
  deployedAt?: string;
}

export interface CrewExecutionContext {
  flowId: string;
  executionId: string;
  inputs: Record<string, any>;
  parameters: Record<string, any>;
  context: Record<string, any>;
  constraints: ExecutionConstraints;
  callbacks: CrewCallback[];
}

export interface CrewExecutionResult {
  crewId: string;
  executionId: string;
  status: 'completed' | 'failed' | 'cancelled';
  result: any;
  taskResults: CrewTaskResult[];
  agentResults: AgentResult[];
  metrics: CrewMetrics;
  error?: ExecutionError;
  startTime: string;
  endTime: string;
  duration: number;
}

export interface CrewStatus {
  crewId: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'cancelled';
  currentTask?: string;
  completedTasks: number;
  totalTasks: number;
  progress: number;
  agents: AgentStatus[];
  error?: ExecutionError;
  startTime?: string;
  estimatedCompletion?: string;
}

export interface CrewResults {
  crewId: string;
  executionId: string;
  finalResult: any;
  taskResults: CrewTaskResult[];
  agentContributions: AgentContribution[];
  consensusReached: boolean;
  qualityScore: number;
  confidence: number;
  recommendations: string[];
  metadata: Record<string, any>;
}

export interface CrewMetrics {
  crewId: string;
  executionCount: number;
  successRate: number;
  averageExecutionTime: number;
  resourceUtilization: ResourceUtilization;
  qualityMetrics: QualityMetrics;
  collaborationMetrics: CollaborationMetrics;
  timeRange: TimeRange;
}

// Event Models
export interface FlowEvent {
  id: string;
  flowId: string;
  eventType: string;
  eventData: Record<string, any>;
  timestamp: string;
  source: 'system' | 'agent' | 'user' | 'external';
  sourceId?: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  category: string;
  description: string;
  metadata: Record<string, any>;
}

export interface EventSubscription {
  id: string;
  flowId: string;
  eventTypes: string[];
  callback: string;
  filters: EventFilters;
  status: 'active' | 'paused' | 'cancelled';
  createdAt: string;
  lastTriggered?: string;
}

export interface EventMetrics {
  flowId: string;
  totalEvents: number;
  eventsByType: Record<string, number>;
  eventsBySeverity: Record<string, number>;
  eventsByCategory: Record<string, number>;
  eventRate: number;
  averageProcessingTime: number;
  timeRange: TimeRange;
}

// Metrics and Monitoring Models
export interface FlowMetrics {
  flowId: string;
  executionTime: number;
  cpuUsage: number;
  memoryUsage: number;
  networkIO: number;
  diskIO: number;
  taskCount: number;
  completedTasks: number;
  failedTasks: number;
  retryCount: number;
  errorRate: number;
  throughput: number;
  latency: number;
  resourceEfficiency: number;
  qualityScore: number;
  userSatisfaction: number;
}

export interface SystemMetrics {
  totalFlows: number;
  activeFlows: number;
  completedFlows: number;
  failedFlows: number;
  totalAgents: number;
  activeAgents: number;
  totalCrews: number;
  activeCrews: number;
  systemLoad: number;
  memoryUsage: number;
  diskUsage: number;
  networkTraffic: number;
  errorRate: number;
  averageResponseTime: number;
  uptime: number;
}

export interface PerformanceMetrics {
  flowId: string;
  benchmarks: PerformanceBenchmark[];
  bottlenecks: PerformanceBottleneck[];
  optimizations: PerformanceOptimization[];
  trends: PerformanceTrend[];
  alerts: PerformanceAlert[];
  recommendations: string[];
}

export interface ResourceUsage {
  flowId: string;
  cpu: ResourceMetric;
  memory: ResourceMetric;
  network: ResourceMetric;
  disk: ResourceMetric;
  agents: AgentResourceUsage[];
  crews: CrewResourceUsage[];
  predictions: ResourcePrediction[];
  limits: ResourceLimits;
  alerts: ResourceAlert[];
}

export interface HealthStatus {
  overall: 'healthy' | 'warning' | 'critical' | 'down';
  components: ComponentHealth[];
  checks: HealthCheck[];
  lastChecked: string;
  uptime: number;
  version: string;
  environment: string;
}

export interface Alert {
  id: string;
  type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  description: string;
  flowId?: string;
  agentId?: string;
  crewId?: string;
  status: 'active' | 'acknowledged' | 'resolved';
  createdAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  acknowledgedBy?: string;
  resolvedBy?: string;
  metadata: Record<string, any>;
}

// Supporting Detail Types
export interface FlowConfiguration {
  maxDuration: number;
  retryPolicy: RetryPolicy;
  checkpointInterval: number;
  parallelism: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
  resources: ResourceRequirements;
  notifications: NotificationConfig;
}

export interface ExecutionMetrics {
  executionId: string;
  startTime: string;
  endTime?: string;
  duration: number;
  cpuTime: number;
  memoryPeak: number;
  networkIO: number;
  diskIO: number;
  taskCount: number;
  errorCount: number;
  warningCount: number;
  qualityScore: number;
}

export interface PhaseStatus {
  phaseId: string;
  phaseName: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  progress: number;
  startTime?: string;
  endTime?: string;
  duration?: number;
  agents: string[];
  crews: string[];
  dependencies: string[];
  outputs: Record<string, any>;
}

export interface ChildFlowStatus {
  flowId: string;
  flowType: string;
  status: FlowStatus;
  progress: number;
  currentPhase: string;
  relationship: 'child' | 'sibling' | 'dependency';
  createdAt: string;
}

export interface RecentEvent {
  id: string;
  eventType: string;
  description: string;
  timestamp: string;
  severity: string;
  source: string;
}

export interface AgentState {
  agentId: string;
  status: string;
  currentTask?: string;
  memory: Record<string, any>;
  context: Record<string, any>;
  performance: AgentPerformance;
  lastUpdate: string;
}

export interface CrewState {
  crewId: string;
  status: string;
  currentTask?: string;
  completedTasks: number;
  totalTasks: number;
  agents: string[];
  sharedMemory: Record<string, any>;
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
}

export interface AgentPerformance {
  tasksPerMinute: number;
  averageTaskDuration: number;
  successRate: number;
  errorRate: number;
  qualityScore: number;
  efficiency: number;
}

export interface AgentHealth {
  status: 'healthy' | 'warning' | 'critical' | 'down';
  lastCheck: string;
  issues: HealthIssue[];
  recommendations: string[];
}

export interface AgentDependency {
  agentId: string;
  dependsOn: string[];
  dependencyType: 'data' | 'completion' | 'resource';
  timeout: number;
}

export interface AgentResult {
  agentId: string;
  result: any;
  status: 'success' | 'failure' | 'partial';
  error?: ExecutionError;
  metrics: AgentMetrics;
  startTime: string;
  endTime: string;
  duration: number;
}

export interface CoordinationError {
  agentId: string;
  error: ExecutionError;
  impact: 'critical' | 'high' | 'medium' | 'low';
  mitigation: string;
}

export interface CoordinationMetrics {
  coordinationId: string;
  totalAgents: number;
  successfulAgents: number;
  failedAgents: number;
  averageResponseTime: number;
  coordinationOverhead: number;
  synchronizationTime: number;
  communicationLatency: number;
}

export interface CrewTask {
  id: string;
  name: string;
  description: string;
  agentId: string;
  dependencies: string[];
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  timeout: number;
  retryPolicy: RetryPolicy;
  priority: number;
}

export interface CrewTaskInstance {
  id: string;
  task: CrewTask;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  agentId: string;
  startTime?: string;
  endTime?: string;
  duration?: number;
  result?: any;
  error?: ExecutionError;
  retryCount: number;
}

export interface CrewCallback {
  event: string;
  handler: string;
  parameters: Record<string, any>;
}

export interface CrewTaskResult {
  taskId: string;
  result: any;
  status: 'success' | 'failure' | 'partial';
  agentId: string;
  error?: ExecutionError;
  metrics: TaskMetrics;
  startTime: string;
  endTime: string;
  duration: number;
}

export interface AgentContribution {
  agentId: string;
  contribution: any;
  weight: number;
  confidence: number;
  quality: number;
  relevance: number;
  metadata: Record<string, any>;
}

export interface ResourceUtilization {
  cpu: number;
  memory: number;
  network: number;
  disk: number;
  efficiency: number;
}

export interface QualityMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  consistency: number;
  completeness: number;
}

export interface CollaborationMetrics {
  communicationFrequency: number;
  consensusTime: number;
  conflictRate: number;
  collaborationEfficiency: number;
  teamCohesion: number;
}

export interface PerformanceBenchmark {
  name: string;
  value: number;
  unit: string;
  benchmark: number;
  status: 'good' | 'warning' | 'poor';
  trend: 'improving' | 'stable' | 'degrading';
}

export interface PerformanceBottleneck {
  location: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  recommendation: string;
  estimatedImprovement: number;
}

export interface PerformanceOptimization {
  type: string;
  description: string;
  impact: number;
  effort: 'low' | 'medium' | 'high';
  status: 'suggested' | 'implemented' | 'rejected';
}

export interface PerformanceTrend {
  metric: string;
  direction: 'up' | 'down' | 'stable';
  rate: number;
  confidence: number;
  prediction: number;
}

export interface PerformanceAlert {
  metric: string;
  threshold: number;
  currentValue: number;
  severity: 'info' | 'warning' | 'critical';
  message: string;
}

export interface ResourceMetric {
  current: number;
  peak: number;
  average: number;
  unit: string;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface AgentResourceUsage {
  agentId: string;
  cpu: number;
  memory: number;
  network: number;
  disk: number;
  efficiency: number;
}

export interface CrewResourceUsage {
  crewId: string;
  cpu: number;
  memory: number;
  network: number;
  disk: number;
  agents: AgentResourceUsage[];
  efficiency: number;
}

export interface ResourcePrediction {
  metric: string;
  predictedValue: number;
  confidence: number;
  timeHorizon: number;
  unit: string;
  trend: string;
}

export interface ResourceLimits {
  cpu: number;
  memory: number;
  network: number;
  disk: number;
  agents: number;
  crews: number;
}

export interface ResourceAlert {
  resource: string;
  currentUsage: number;
  threshold: number;
  severity: 'warning' | 'critical';
  message: string;
  recommendation: string;
}

export interface ComponentHealth {
  component: string;
  status: 'healthy' | 'warning' | 'critical' | 'down';
  message: string;
  lastChecked: string;
  metrics: Record<string, number>;
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  message: string;
  duration: number;
  lastRun: string;
  details: Record<string, any>;
}

export interface AlertConfiguration {
  name: string;
  description: string;
  conditions: AlertCondition[];
  actions: AlertAction[];
  enabled: boolean;
  severity: 'info' | 'warning' | 'error' | 'critical';
  cooldown: number;
  escalation: AlertEscalation;
}

export interface ResourceRequirements {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
  agents: number;
  crews: number;
}

export interface NotificationConfig {
  enabled: boolean;
  channels: string[];
  events: string[];
  threshold: string;
  recipients: string[];
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  severity: 'error' | 'warning';
}

export interface ValidationWarning {
  field: string;
  message: string;
  code: string;
  suggestion?: string;
}

export interface HealthIssue {
  type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: string;
  resolved: boolean;
}

export interface TaskMetrics {
  taskId: string;
  executionTime: number;
  cpuUsage: number;
  memoryUsage: number;
  networkIO: number;
  diskIO: number;
  qualityScore: number;
  errorCount: number;
  retryCount: number;
}

export interface AlertCondition {
  metric: string;
  operator: 'gt' | 'lt' | 'eq' | 'ne' | 'gte' | 'lte';
  threshold: number;
  duration: number;
  aggregation: 'avg' | 'max' | 'min' | 'sum' | 'count';
}

export interface AlertAction {
  type: 'email' | 'slack' | 'webhook' | 'sms' | 'ticket';
  target: string;
  parameters: Record<string, any>;
  enabled: boolean;
}

export interface AlertEscalation {
  enabled: boolean;
  levels: EscalationLevel[];
  timeout: number;
}

export interface EscalationLevel {
  level: number;
  recipients: string[];
  channels: string[];
  delay: number;
}

// Import EventFilters from base-types to avoid duplication
import { EventFilters } from './base-types';

export type FlowStatus = 'initializing' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'timeout';