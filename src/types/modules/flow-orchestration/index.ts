/**
 * Flow Orchestration Module
 * 
 * Centralized exports for all flow orchestration types and interfaces.
 */

// Re-export all base types
export type * from './base-types';

// Re-export all service interfaces
export type * from './service-interfaces';

// Re-export all model types
export type * from './model-types';

// Create namespace for backward compatibility
import type * as BaseTypes from './base-types';
import type * as ServiceInterfaces from './service-interfaces';
import type * as ModelTypes from './model-types';

export namespace FlowOrchestration {
  export namespace Services {
    export type MasterFlowOrchestratorService = ServiceInterfaces.MasterFlowOrchestratorService;
    export type FlowStateManagerService = ServiceInterfaces.FlowStateManagerService;
    export type AgentCoordinationService = ServiceInterfaces.AgentCoordinationService;
    export type CrewAIIntegrationService = ServiceInterfaces.CrewAIIntegrationService;
    export type FlowEventService = ServiceInterfaces.FlowEventService;
    export type FlowMonitoringService = ServiceInterfaces.FlowMonitoringService;
  }
  
  export namespace Models {
    // Flow Configuration and Execution Models
    export type FlowInitializationConfig = ModelTypes.FlowInitializationConfig;
    export type FlowExecutionResult = ModelTypes.FlowExecutionResult;
    export type FlowStatusDetail = ModelTypes.FlowStatusDetail;
    export type FlowHistoryEntry = ModelTypes.FlowHistoryEntry;
    export type ActiveFlowSummary = ModelTypes.ActiveFlowSummary;
    export type FlowStateData = ModelTypes.FlowStateData;
    
    // Agent Models
    export type AgentInstance = ModelTypes.AgentInstance;
    export type AgentStatus = ModelTypes.AgentStatus;
    export type AgentMetrics = ModelTypes.AgentMetrics;
    export type AgentCoordination = ModelTypes.AgentCoordination;
    export type CoordinationResult = ModelTypes.CoordinationResult;
    export type AgentMessage = ModelTypes.AgentMessage;
    export type AgentCommunication = ModelTypes.AgentCommunication;
    
    // Crew Models
    export type CrewConfiguration = ModelTypes.CrewConfiguration;
    export type CrewInstance = ModelTypes.CrewInstance;
    export type CrewExecutionContext = ModelTypes.CrewExecutionContext;
    export type CrewExecutionResult = ModelTypes.CrewExecutionResult;
    export type CrewStatus = ModelTypes.CrewStatus;
    export type CrewResults = ModelTypes.CrewResults;
    export type CrewMetrics = ModelTypes.CrewMetrics;
    
    // Event Models
    export type FlowEvent = ModelTypes.FlowEvent;
    export type EventSubscription = ModelTypes.EventSubscription;
    export type EventMetrics = ModelTypes.EventMetrics;
    
    // Metrics and Monitoring Models
    export type FlowMetrics = ModelTypes.FlowMetrics;
    export type SystemMetrics = ModelTypes.SystemMetrics;
    export type PerformanceMetrics = ModelTypes.PerformanceMetrics;
    export type ResourceUsage = ModelTypes.ResourceUsage;
    export type HealthStatus = ModelTypes.HealthStatus;
    export type Alert = ModelTypes.Alert;
    
    // Supporting Detail Types
    export type FlowConfiguration = ModelTypes.FlowConfiguration;
    export type ExecutionMetrics = ModelTypes.ExecutionMetrics;
    export type PhaseStatus = ModelTypes.PhaseStatus;
    export type ChildFlowStatus = ModelTypes.ChildFlowStatus;
    export type RecentEvent = ModelTypes.RecentEvent;
    export type AgentState = ModelTypes.AgentState;
    export type CrewState = ModelTypes.CrewState;
    export type StateCheckpoint = ModelTypes.StateCheckpoint;
    export type AgentPerformance = ModelTypes.AgentPerformance;
    export type AgentHealth = ModelTypes.AgentHealth;
    export type AgentDependency = ModelTypes.AgentDependency;
    export type AgentResult = ModelTypes.AgentResult;
    export type CoordinationError = ModelTypes.CoordinationError;
    export type CoordinationMetrics = ModelTypes.CoordinationMetrics;
    export type CrewTask = ModelTypes.CrewTask;
    export type CrewTaskInstance = ModelTypes.CrewTaskInstance;
    export type CrewCallback = ModelTypes.CrewCallback;
    export type CrewTaskResult = ModelTypes.CrewTaskResult;
    export type AgentContribution = ModelTypes.AgentContribution;
    export type ResourceUtilization = ModelTypes.ResourceUtilization;
    export type QualityMetrics = ModelTypes.QualityMetrics;
    export type CollaborationMetrics = ModelTypes.CollaborationMetrics;
    export type PerformanceBenchmark = ModelTypes.PerformanceBenchmark;
    export type PerformanceBottleneck = ModelTypes.PerformanceBottleneck;
    export type PerformanceOptimization = ModelTypes.PerformanceOptimization;
    export type PerformanceTrend = ModelTypes.PerformanceTrend;
    export type PerformanceAlert = ModelTypes.PerformanceAlert;
    export type ResourceMetric = ModelTypes.ResourceMetric;
    export type AgentResourceUsage = ModelTypes.AgentResourceUsage;
    export type CrewResourceUsage = ModelTypes.CrewResourceUsage;
    export type ResourcePrediction = ModelTypes.ResourcePrediction;
    export type ResourceLimits = ModelTypes.ResourceLimits;
    export type ResourceAlert = ModelTypes.ResourceAlert;
    export type ComponentHealth = ModelTypes.ComponentHealth;
    export type HealthCheck = ModelTypes.HealthCheck;
    export type AlertConfiguration = ModelTypes.AlertConfiguration;
    export type ResourceRequirements = ModelTypes.ResourceRequirements;
    export type NotificationConfig = ModelTypes.NotificationConfig;
    export type ValidationError = ModelTypes.ValidationError;
    export type ValidationWarning = ModelTypes.ValidationWarning;
    export type HealthIssue = ModelTypes.HealthIssue;
    export type TaskMetrics = ModelTypes.TaskMetrics;
    export type AlertCondition = ModelTypes.AlertCondition;
    export type AlertAction = ModelTypes.AlertAction;
    export type AlertEscalation = ModelTypes.AlertEscalation;
    export type EscalationLevel = ModelTypes.EscalationLevel;
    export type FlowStatus = ModelTypes.FlowStatus;
    
    // Base Types
    export type FlowFilters = BaseTypes.FlowFilters;
    export type EventFilters = BaseTypes.EventFilters;
    export type AlertFilters = BaseTypes.AlertFilters;
    export type ValidationResult = BaseTypes.ValidationResult;
    export type BackupResult = BaseTypes.BackupResult;
    export type DeletionResult = BaseTypes.DeletionResult;
    export type RetryPolicy = BaseTypes.RetryPolicy;
    export type ExecutionConstraints = BaseTypes.ExecutionConstraints;
  }
}