/**
 * Discovery API Types - Main Export File
 * 
 * This file now serves as the main aggregator for all Discovery API types,
 * importing from modularized files to maintain backward compatibility
 * while providing better code organization.
 */

// Re-export all types from modular files to maintain backward compatibility
export * from './discovery/flow-management';
export * from './discovery/data-import';
export * from './discovery/attribute-mapping';
export * from './discovery/critical-attributes';
export * from './discovery/crew-analysis';
export * from './discovery/flow-state-management';
export * from './discovery/agent-clarifications';
export * from './discovery/progress-tracking';
export * from './discovery/training-learning';

// Import shared types
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

// Import types from modular files for internal use
import type {
  DiscoveryFlowData,
  FlowStatus,
  FlowState
} from './discovery/flow-management';

import type {
  ImportStatus,
  DataImportInfo,
  DataImportDetail,
  DataImportSummary,
  ParseOptions,
  ProcessingLog,
  ImportError,
  ImportWarning,
  ImportStatistics,
  ImportPreview,
  ImportValidationResult
} from './discovery/data-import';

import type {
  FieldMapping,
  MappingStatus,
  MappingType
} from './discovery/attribute-mapping';

// Local types that weren't extracted to modules
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

export interface DiscoveryFlowConfiguration {
  phases: PhaseConfiguration[];
  autoAdvance: boolean;
  validationLevel: 'strict' | 'normal' | 'lenient';
  parallelProcessing: boolean;
  agentConfiguration: AgentConfiguration;
  notificationSettings: NotificationSettings;
  retentionPolicy: RetentionPolicy;
}

export interface PhaseConfiguration {
  name: string;
  displayName: string;
  description: string;
  order: number;
  required: boolean;
  estimatedDuration: number;
  dependencies: string[];
  validationRules: ValidationRule[];
  automationLevel: 'manual' | 'semi_auto' | 'auto';
  agentAssignments: AgentAssignment[];
}

export interface AgentConfiguration {
  maxConcurrentTasks: number;
  timeoutSettings: TimeoutSettings;
  retrySettings: RetrySettings;
  learningEnabled: boolean;
  qualityThresholds: QualityThresholds;
}

export interface AgentAssignment {
  agentId: string;
  role: string;
  capabilities: string[];
  maxConcurrentTasks: number;
}

export interface TimeoutSettings {
  taskTimeout: number;
  phaseTimeout: number;
  flowTimeout: number;
}

export interface RetrySettings {
  maxRetries: number;
  retryDelay: number;
  backoffMultiplier: number;
}

export interface QualityThresholds {
  minConfidence: number;
  minAccuracy: number;
  maxErrorRate: number;
}

export interface NotificationSettings {
  enableEmail: boolean;
  enableWebhook: boolean;
  emailAddresses: string[];
  webhookUrls: string[];
  notificationTriggers: NotificationTrigger[];
}

export interface NotificationTrigger {
  event: string;
  condition?: string;
  enabled: boolean;
}

export interface RetentionPolicy {
  dataRetentionDays: number;
  logRetentionDays: number;
  archiveAfterDays: number;
  deleteAfterDays: number;
}

export interface FlowMetrics {
  totalDataImports: number;
  totalMappings: number;
  approvedMappings: number;
  completedPhases: number;
  totalPhases: number;
  averagePhaseTime: number;
  qualityScore: number;
  efficiency: number;
  userSatisfaction?: number;
}

export interface FlowMetricsSummary {
  dataVolume: number;
  mappingAccuracy: number;
  processingTime: number;
  errorRate: number;
}

export interface AgentInsight {
  id: string;
  agentId: string;
  type: string;
  category: string;
  confidence: number;
  description: string;
  recommendations?: string[];
  evidence?: Record<string, any>;
  createdAt: string;
}

export interface FlowEvent {
  id: string;
  type: string;
  timestamp: string;
  description: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  source: string;
  metadata?: Record<string, any>;
}

export interface FlowBlocker {
  id: string;
  type: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  phase?: string;
  estimatedResolutionTime?: number;
  resolutionSteps?: string[];
  escalated: boolean;
}

export interface FlowWarning {
  id: string;
  type: string;
  message: string;
  details?: string;
  phase?: string;
  canIgnore: boolean;
  recommendation?: string;
}

export interface FlowRecommendation {
  id: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  actionRequired: boolean;
  estimatedImpact: string;
}

export interface FlowAggregation {
  field: string;
  buckets: AggregationBucket[];
}

export interface AggregationBucket {
  key: string;
  count: number;
  percentage: number;
}

export interface FlowTrend {
  period: string;
  metric: string;
  values: TrendValue[];
  direction: 'up' | 'down' | 'stable';
}

export interface TrendValue {
  timestamp: string;
  value: number;
}

export interface PhaseCompletion {
  [phaseName: string]: {
    completed: boolean;
    progress: number;
    startTime?: string;
    endTime?: string;
  };
}

export interface DeletedResource {
  type: string;
  id: string;
  name: string;
  size?: number;
}

export interface RetentionInfo {
  retainedUntil: string;
  archivalPolicy: string;
  recoverable: boolean;
}

export interface ValidationRule {
  id: string;
  type: string;
  parameters: Record<string, any>;
  errorMessage: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

// Re-export all the enum types for backward compatibility
export type { FlowStatus, ImportStatus, MappingStatus, MappingType };

// Additional supporting types that are used across modules
export interface SimilarAttribute {
  attributeId: string;
  name: string;
  similarity: number;
  suggestedMerge?: boolean;
}