/**
 * Flow Orchestration Service Interfaces
 * 
 * Service interface definitions for the flow orchestration system.
 */

import type {
  FlowExecutionContext,
  TimeRange,
  ValidationResult,
  BackupResult,
  DeletionResult,
  FlowFilters,
  EventFilters,
  AlertFilters,
  AgentConfiguration
} from './base-types';

import type { FlowInitializationConfig, FlowExecutionResult, ActiveFlowSummary, FlowStateData, AgentStatus, CoordinationResult, AgentMessage, CrewExecutionContext, CrewExecutionResult, CrewStatus, FlowEvent, HealthStatus, AlertConfiguration } from './model-types'
import type { FlowStatusDetail, FlowHistoryEntry, AgentInstance, AgentMetrics, AgentCoordination, AgentCommunication, CrewConfiguration, CrewInstance, CrewResults, CrewMetrics, EventSubscription, EventMetrics, FlowMetrics, SystemMetrics, PerformanceMetrics, ResourceUsage, Alert } from './model-types'

export interface MasterFlowOrchestratorService {
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

export interface FlowStateManagerService {
  createFlowState: (flowId: string, initialState: FlowStateData) => Promise<FlowStateData>;
  updateFlowState: (flowId: string, updates: Partial<FlowStateData>) => Promise<FlowStateData>;
  getFlowState: (flowId: string) => Promise<FlowStateData>;
  deleteFlowState: (flowId: string) => Promise<void>;
  migrateFlowState: (sessionId: string, flowId: string) => Promise<FlowStateData>;
  validateFlowState: (flowId: string) => Promise<ValidationResult>;
  backupFlowState: (flowId: string) => Promise<BackupResult>;
  restoreFlowState: (flowId: string, backupId: string) => Promise<FlowStateData>;
}

export interface AgentCoordinationService {
  createAgent: (config: AgentConfiguration) => Promise<AgentInstance>;
  deployAgent: (agentId: string, flowId: string) => Promise<void>;
  removeAgent: (agentId: string, flowId: string) => Promise<void>;
  getAgentStatus: (agentId: string) => Promise<AgentStatus>;
  getAgentMetrics: (agentId: string, timeRange?: TimeRange) => Promise<AgentMetrics>;
  coordinateAgents: (flowId: string, coordination: AgentCoordination) => Promise<CoordinationResult>;
  broadcastMessage: (flowId: string, message: AgentMessage) => Promise<void>;
  getAgentCommunication: (flowId: string) => Promise<AgentCommunication[]>;
}

export interface CrewAIIntegrationService {
  createCrew: (config: CrewConfiguration) => Promise<CrewInstance>;
  executeCrew: (crewId: string, context: CrewExecutionContext) => Promise<CrewExecutionResult>;
  getCrewStatus: (crewId: string) => Promise<CrewStatus>;
  getCrewResults: (crewId: string) => Promise<CrewResults>;
  terminateCrew: (crewId: string) => Promise<void>;
  getCrewMetrics: (crewId: string) => Promise<CrewMetrics>;
  updateCrewConfiguration: (crewId: string, updates: Partial<CrewConfiguration>) => Promise<void>;
}

export interface FlowEventService {
  publishEvent: (event: FlowEvent) => Promise<void>;
  subscribeToEvents: (flowId: string, eventTypes: string[]) => Promise<EventSubscription>;
  unsubscribeFromEvents: (subscriptionId: string) => Promise<void>;
  getEventHistory: (flowId: string, filters?: EventFilters) => Promise<FlowEvent[]>;
  getEventMetrics: (flowId: string, timeRange?: TimeRange) => Promise<EventMetrics>;
}

export interface FlowMonitoringService {
  getFlowMetrics: (flowId: string) => Promise<FlowMetrics>;
  getSystemMetrics: () => Promise<SystemMetrics>;
  getPerformanceMetrics: (flowId: string) => Promise<PerformanceMetrics>;
  getResourceUsage: (flowId: string) => Promise<ResourceUsage>;
  getHealthStatus: () => Promise<HealthStatus>;
  createAlert: (alertConfig: AlertConfiguration) => Promise<Alert>;
  getAlerts: (filters?: AlertFilters) => Promise<Alert[]>;
  acknowledgeAlert: (alertId: string) => Promise<void>;
}