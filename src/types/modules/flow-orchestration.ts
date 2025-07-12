/**
 * Flow Orchestration Module Namespace
 * 
 * TypeScript module boundaries for Flow Orchestration backend services.
 * Provides type definitions for CrewAI flows, agent coordination, and flow state management.
 */

import { ReactNode } from 'react';

// Base orchestration types
export interface AgentConfiguration {
  id: string;
  name: string;
  role: string;
  goal: string;
  backstory: string;
  capabilities: string[];
  tools: string[];
  llmConfig: LLMConfiguration;
  memoryEnabled: boolean;
  verboseLogging: boolean;
}

export interface LLMConfiguration {
  model: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  frequencyPenalty: number;
  presencePenalty: number;
}

export interface FlowExecutionContext {
  flowId: string;
  flowType: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  executionId: string;
  startTime: string;
  parameters: Record<string, any>;
  metadata: Record<string, any>;
}

// Flow Orchestration namespace declaration
declare namespace FlowOrchestration {
  // Core Services namespace
  namespace Services {
    interface MasterFlowOrchestratorService {
      initializeFlow: (config: FlowInitializationConfig) => Promise<FlowExecutionResult>;
      executeFlow: (flowId: string, context: FlowExecutionContext) => Promise<FlowExecutionResult>;
      pauseFlow: (flowId: string, reason?: string) => Promise<void>;
      resumeFlow: (flowId: string) => Promise<void>;
      terminateFlow: (flowId: string, reason?: string) => Promise<void>;
      getFlowStatus: (flowId: string) => Promise<FlowStatusDetail>;
      getFlowHistory: (flowId: string) => Promise<FlowHistoryEntry[]>;
      getActiveFlows: (filters?: FlowFilters) => Promise<ActiveFlowSummary[]>;
      registerChildFlow: (parentFlowId: string, childFlowId: string, flowType: string) => Promise<void>;
      unregisterChildFlow: (parentFlowId: string, childFlowId: string) => Promise<void>;
      cascadeFlowDeletion: (flowId: string) => Promise<DeletionResult>;
    }

    interface FlowStateManagerService {
      createFlowState: (flowId: string, initialState: FlowStateData) => Promise<FlowStateData>;
      updateFlowState: (flowId: string, updates: Partial<FlowStateData>) => Promise<FlowStateData>;
      getFlowState: (flowId: string) => Promise<FlowStateData>;
      deleteFlowState: (flowId: string) => Promise<void>;
      migrateFlowState: (sessionId: string, flowId: string) => Promise<FlowStateData>;
      validateFlowState: (flowId: string) => Promise<ValidationResult>;
      backupFlowState: (flowId: string) => Promise<BackupResult>;
      restoreFlowState: (flowId: string, backupId: string) => Promise<FlowStateData>;
    }

    interface AgentCoordinationService {
      createAgent: (config: AgentConfiguration) => Promise<AgentInstance>;
      deployAgent: (agentId: string, flowId: string) => Promise<void>;
      removeAgent: (agentId: string, flowId: string) => Promise<void>;
      getAgentStatus: (agentId: string) => Promise<AgentStatus>;
      getAgentMetrics: (agentId: string, timeRange?: TimeRange) => Promise<AgentMetrics>;
      coordinateAgents: (flowId: string, coordination: AgentCoordination) => Promise<CoordinationResult>;
      broadcastMessage: (flowId: string, message: AgentMessage) => Promise<void>;
      getAgentCommunication: (flowId: string) => Promise<AgentCommunication[]>;
    }

    interface CrewAIIntegrationService {
      createCrew: (config: CrewConfiguration) => Promise<CrewInstance>;
      executeCrew: (crewId: string, context: CrewExecutionContext) => Promise<CrewExecutionResult>;
      getCrewStatus: (crewId: string) => Promise<CrewStatus>;
      getCrewResults: (crewId: string) => Promise<CrewResults>;
      terminateCrew: (crewId: string) => Promise<void>;
      getCrewMetrics: (crewId: string) => Promise<CrewMetrics>;
      updateCrewConfiguration: (crewId: string, updates: Partial<CrewConfiguration>) => Promise<void>;
    }

    interface FlowEventService {
      publishEvent: (event: FlowEvent) => Promise<void>;
      subscribeToEvents: (flowId: string, eventTypes: string[]) => Promise<EventSubscription>;
      unsubscribeFromEvents: (subscriptionId: string) => Promise<void>;
      getEventHistory: (flowId: string, filters?: EventFilters) => Promise<FlowEvent[]>;
      getEventMetrics: (flowId: string, timeRange?: TimeRange) => Promise<EventMetrics>;
    }

    interface FlowMonitoringService {
      getFlowMetrics: (flowId: string) => Promise<FlowMetrics>;
      getSystemMetrics: () => Promise<SystemMetrics>;
      getPerformanceMetrics: (flowId: string) => Promise<PerformanceMetrics>;
      getResourceUsage: (flowId: string) => Promise<ResourceUsage>;
      getHealthStatus: () => Promise<HealthStatus>;
      createAlert: (alertConfig: AlertConfiguration) => Promise<Alert>;
      getAlerts: (filters?: AlertFilters) => Promise<Alert[]>;
      acknowledgeAlert: (alertId: string) => Promise<void>;
    }
  }

  // Models namespace
  namespace Models {
    interface FlowInitializationConfig {
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

    interface FlowExecutionResult {
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

    interface FlowStatusDetail {
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

    interface FlowHistoryEntry {
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

    interface ActiveFlowSummary {
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

    interface FlowStateData {
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

    interface AgentInstance {
      id: string;
      configuration: AgentConfiguration;
      status: AgentStatus;
      deployedFlows: string[];
      metrics: AgentMetrics;
      createdAt: string;
      lastActiveAt: string;
    }

    interface AgentStatus {
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

    interface AgentMetrics {
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

    interface AgentCoordination {
      coordinationType: 'sequential' | 'parallel' | 'conditional' | 'pipeline';
      agents: string[];
      dependencies: AgentDependency[];
      timeout: number;
      retryPolicy: RetryPolicy;
      failureStrategy: 'abort' | 'continue' | 'fallback';
      communicationProtocol: 'event' | 'message' | 'shared_state';
    }

    interface CoordinationResult {
      coordinationId: string;
      status: 'success' | 'partial' | 'failed';
      results: AgentResult[];
      errors: CoordinationError[];
      metrics: CoordinationMetrics;
      startTime: string;
      endTime: string;
      duration: number;
    }

    interface AgentMessage {
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

    interface AgentCommunication {
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

    interface CrewConfiguration {
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

    interface CrewInstance {
      id: string;
      configuration: CrewConfiguration;
      status: CrewStatus;
      agents: AgentInstance[];
      tasks: CrewTaskInstance[];
      manager?: AgentInstance;
      createdAt: string;
      deployedAt?: string;
    }

    interface CrewExecutionContext {
      flowId: string;
      executionId: string;
      inputs: Record<string, any>;
      parameters: Record<string, any>;
      context: Record<string, any>;
      constraints: ExecutionConstraints;
      callbacks: CrewCallback[];
    }

    interface CrewExecutionResult {
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

    interface CrewStatus {
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

    interface CrewResults {
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

    interface CrewMetrics {
      crewId: string;
      executionCount: number;
      successRate: number;
      averageExecutionTime: number;
      resourceUtilization: ResourceUtilization;
      qualityMetrics: QualityMetrics;
      collaborationMetrics: CollaborationMetrics;
      timeRange: TimeRange;
    }

    interface FlowEvent {
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

    interface EventSubscription {
      id: string;
      flowId: string;
      eventTypes: string[];
      callback: string;
      filters: EventFilters;
      status: 'active' | 'paused' | 'cancelled';
      createdAt: string;
      lastTriggered?: string;
    }

    interface EventMetrics {
      flowId: string;
      totalEvents: number;
      eventsByType: Record<string, number>;
      eventsBySeverity: Record<string, number>;
      eventsByCategory: Record<string, number>;
      eventRate: number;
      averageProcessingTime: number;
      timeRange: TimeRange;
    }

    interface FlowMetrics {
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

    interface SystemMetrics {
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

    interface PerformanceMetrics {
      flowId: string;
      benchmarks: PerformanceBenchmark[];
      bottlenecks: PerformanceBottleneck[];
      optimizations: PerformanceOptimization[];
      trends: PerformanceTrend[];
      alerts: PerformanceAlert[];
      recommendations: string[];
    }

    interface ResourceUsage {
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

    interface HealthStatus {
      overall: 'healthy' | 'warning' | 'critical' | 'down';
      components: ComponentHealth[];
      checks: HealthCheck[];
      lastChecked: string;
      uptime: number;
      version: string;
      environment: string;
    }

    interface Alert {
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

    // Supporting types
    interface FlowConfiguration {
      maxDuration: number;
      retryPolicy: RetryPolicy;
      checkpointInterval: number;
      parallelism: number;
      priority: 'low' | 'medium' | 'high' | 'critical';
      resources: ResourceRequirements;
      notifications: NotificationConfig;
    }

    interface ExecutionError {
      code: string;
      message: string;
      details: Record<string, any>;
      timestamp: string;
      source: string;
      flowId: string;
      agentId?: string;
      crewId?: string;
      phase?: string;
      retryable: boolean;
      severity: 'low' | 'medium' | 'high' | 'critical';
    }

    interface ExecutionMetrics {
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

    interface PhaseStatus {
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

    interface ChildFlowStatus {
      flowId: string;
      flowType: string;
      status: FlowStatus;
      progress: number;
      currentPhase: string;
      relationship: 'child' | 'sibling' | 'dependency';
      createdAt: string;
    }

    interface RecentEvent {
      id: string;
      eventType: string;
      description: string;
      timestamp: string;
      severity: string;
      source: string;
    }

    interface ExecutionWarning {
      code: string;
      message: string;
      details: Record<string, any>;
      timestamp: string;
      source: string;
      phase?: string;
      recommendation?: string;
    }

    interface AgentState {
      agentId: string;
      status: string;
      currentTask?: string;
      memory: Record<string, any>;
      context: Record<string, any>;
      performance: AgentPerformance;
      lastUpdate: string;
    }

    interface CrewState {
      crewId: string;
      status: string;
      currentTask?: string;
      completedTasks: number;
      totalTasks: number;
      agents: string[];
      sharedMemory: Record<string, any>;
      lastUpdate: string;
    }

    interface StateCheckpoint {
      id: string;
      timestamp: string;
      phase: string;
      data: Record<string, any>;
      hash: string;
      size: number;
      createdBy: string;
    }

    interface ValidationResult {
      isValid: boolean;
      errors: ValidationError[];
      warnings: ValidationWarning[];
      score: number;
      details: Record<string, any>;
    }

    interface BackupResult {
      backupId: string;
      flowId: string;
      timestamp: string;
      size: number;
      location: string;
      hash: string;
      status: 'completed' | 'failed';
      error?: string;
    }

    interface DeletionResult {
      flowId: string;
      deletedChildFlows: string[];
      deletedAgents: string[];
      deletedCrews: string[];
      deletedState: boolean;
      deletedBackups: string[];
      errors: string[];
      warnings: string[];
      completedAt: string;
    }

    interface TimeRange {
      start: string;
      end: string;
      duration: number;
    }

    interface MetricSample {
      timestamp: string;
      value: number;
      metadata?: Record<string, any>;
    }

    interface AgentPerformance {
      tasksPerMinute: number;
      averageTaskDuration: number;
      successRate: number;
      errorRate: number;
      qualityScore: number;
      efficiency: number;
    }

    interface AgentHealth {
      status: 'healthy' | 'warning' | 'critical' | 'down';
      lastCheck: string;
      issues: HealthIssue[];
      recommendations: string[];
    }

    interface AgentDependency {
      agentId: string;
      dependsOn: string[];
      dependencyType: 'data' | 'completion' | 'resource';
      timeout: number;
    }

    interface RetryPolicy {
      maxRetries: number;
      initialDelay: number;
      backoffMultiplier: number;
      maxDelay: number;
      retryableErrors: string[];
    }

    interface AgentResult {
      agentId: string;
      result: any;
      status: 'success' | 'failure' | 'partial';
      error?: ExecutionError;
      metrics: AgentMetrics;
      startTime: string;
      endTime: string;
      duration: number;
    }

    interface CoordinationError {
      agentId: string;
      error: ExecutionError;
      impact: 'critical' | 'high' | 'medium' | 'low';
      mitigation: string;
    }

    interface CoordinationMetrics {
      coordinationId: string;
      totalAgents: number;
      successfulAgents: number;
      failedAgents: number;
      averageResponseTime: number;
      coordinationOverhead: number;
      synchronizationTime: number;
      communicationLatency: number;
    }

    interface CrewTask {
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

    interface CrewTaskInstance {
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

    interface CrewCallback {
      event: string;
      handler: string;
      parameters: Record<string, any>;
    }

    interface ExecutionConstraints {
      maxDuration: number;
      maxMemory: number;
      maxCpuUsage: number;
      allowedResources: string[];
      requiredPermissions: string[];
      isolationLevel: 'none' | 'partial' | 'full';
    }

    interface CrewTaskResult {
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

    interface AgentContribution {
      agentId: string;
      contribution: any;
      weight: number;
      confidence: number;
      quality: number;
      relevance: number;
      metadata: Record<string, any>;
    }

    interface ResourceUtilization {
      cpu: number;
      memory: number;
      network: number;
      disk: number;
      efficiency: number;
    }

    interface QualityMetrics {
      accuracy: number;
      precision: number;
      recall: number;
      f1Score: number;
      consistency: number;
      completeness: number;
    }

    interface CollaborationMetrics {
      communicationFrequency: number;
      consensusTime: number;
      conflictRate: number;
      collaborationEfficiency: number;
      teamCohesion: number;
    }

    interface EventFilters {
      eventTypes?: string[];
      severities?: string[];
      categories?: string[];
      sources?: string[];
      timeRange?: TimeRange;
      searchTerm?: string;
    }

    interface PerformanceBenchmark {
      name: string;
      value: number;
      unit: string;
      benchmark: number;
      status: 'good' | 'warning' | 'poor';
      trend: 'improving' | 'stable' | 'degrading';
    }

    interface PerformanceBottleneck {
      location: string;
      description: string;
      impact: 'high' | 'medium' | 'low';
      recommendation: string;
      estimatedImprovement: number;
    }

    interface PerformanceOptimization {
      type: string;
      description: string;
      impact: number;
      effort: 'low' | 'medium' | 'high';
      status: 'suggested' | 'implemented' | 'rejected';
    }

    interface PerformanceTrend {
      metric: string;
      direction: 'up' | 'down' | 'stable';
      rate: number;
      confidence: number;
      prediction: number;
    }

    interface PerformanceAlert {
      metric: string;
      threshold: number;
      currentValue: number;
      severity: 'info' | 'warning' | 'critical';
      message: string;
    }

    interface ResourceMetric {
      current: number;
      peak: number;
      average: number;
      unit: string;
      trend: 'increasing' | 'decreasing' | 'stable';
    }

    interface AgentResourceUsage {
      agentId: string;
      cpu: number;
      memory: number;
      network: number;
      disk: number;
      efficiency: number;
    }

    interface CrewResourceUsage {
      crewId: string;
      cpu: number;
      memory: number;
      network: number;
      disk: number;
      agents: AgentResourceUsage[];
      efficiency: number;
    }

    interface ResourcePrediction {
      metric: string;
      predictedValue: number;
      confidence: number;
      timeHorizon: number;
      unit: string;
      trend: string;
    }

    interface ResourceLimits {
      cpu: number;
      memory: number;
      network: number;
      disk: number;
      agents: number;
      crews: number;
    }

    interface ResourceAlert {
      resource: string;
      currentUsage: number;
      threshold: number;
      severity: 'warning' | 'critical';
      message: string;
      recommendation: string;
    }

    interface ComponentHealth {
      component: string;
      status: 'healthy' | 'warning' | 'critical' | 'down';
      message: string;
      lastChecked: string;
      metrics: Record<string, number>;
    }

    interface HealthCheck {
      name: string;
      status: 'pass' | 'fail' | 'warn';
      message: string;
      duration: number;
      lastRun: string;
      details: Record<string, any>;
    }

    interface AlertConfiguration {
      name: string;
      description: string;
      conditions: AlertCondition[];
      actions: AlertAction[];
      enabled: boolean;
      severity: 'info' | 'warning' | 'error' | 'critical';
      cooldown: number;
      escalation: AlertEscalation;
    }

    interface AlertFilters {
      flowId?: string;
      agentId?: string;
      crewId?: string;
      status?: string[];
      severity?: string[];
      timeRange?: TimeRange;
      acknowledged?: boolean;
      resolved?: boolean;
    }

    interface FlowFilters {
      flowTypes?: string[];
      statuses?: string[];
      clientAccountIds?: string[];
      engagementIds?: string[];
      userIds?: string[];
      timeRange?: TimeRange;
      priorities?: string[];
      tags?: string[];
    }

    interface ResourceRequirements {
      cpu: number;
      memory: number;
      disk: number;
      network: number;
      agents: number;
      crews: number;
    }

    interface NotificationConfig {
      enabled: boolean;
      channels: string[];
      events: string[];
      threshold: string;
      recipients: string[];
    }

    interface ValidationError {
      field: string;
      message: string;
      code: string;
      severity: 'error' | 'warning';
    }

    interface ValidationWarning {
      field: string;
      message: string;
      code: string;
      suggestion?: string;
    }

    interface HealthIssue {
      type: string;
      severity: 'info' | 'warning' | 'error' | 'critical';
      message: string;
      timestamp: string;
      resolved: boolean;
    }

    interface TaskMetrics {
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

    interface AlertCondition {
      metric: string;
      operator: 'gt' | 'lt' | 'eq' | 'ne' | 'gte' | 'lte';
      threshold: number;
      duration: number;
      aggregation: 'avg' | 'max' | 'min' | 'sum' | 'count';
    }

    interface AlertAction {
      type: 'email' | 'slack' | 'webhook' | 'sms' | 'ticket';
      target: string;
      parameters: Record<string, any>;
      enabled: boolean;
    }

    interface AlertEscalation {
      enabled: boolean;
      levels: EscalationLevel[];
      timeout: number;
    }

    interface EscalationLevel {
      level: number;
      recipients: string[];
      channels: string[];
      delay: number;
    }

    type FlowStatus = 'initializing' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'timeout';
  }
}

// Export the namespace for external use
export { FlowOrchestration };

// Export base types for convenience
export type {
  AgentConfiguration,
  LLMConfiguration,
  FlowExecutionContext
};