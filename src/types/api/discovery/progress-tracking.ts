/**
 * Discovery Progress Tracking API Types
 *
 * Type definitions for tracking mapping and flow progress including
 * timeline monitoring, projections, and bottleneck analysis.
 */

import type {
  GetRequest,
  GetResponse
} from '../shared';

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

// Progress Tracking Models
export interface MappingProgressDetail {
  flowId: string;
  dataImportId?: string;
  totalMappings: number;
  completedMappings: number;
  pendingMappings: number;
  approvedMappings: number;
  rejectedMappings: number;
  reviewRequiredMappings: number;
  progressPercentage: number;
  startTime: string;
  lastUpdateTime: string;
  estimatedCompletionTime?: string;
  averageMappingTime: number;
  velocity: MappingVelocity;
  qualityMetrics: MappingQualityMetrics;
}

export interface MappingVelocity {
  mappingsPerHour: number;
  approvalsPerHour: number;
  trend: 'increasing' | 'stable' | 'decreasing';
  projectedCompletion: string;
}

export interface MappingQualityMetrics {
  averageConfidence: number;
  autoApprovalRate: number;
  rejectionRate: number;
  reviewCycleTime: number;
}

export interface ProgressBottleneck {
  type: 'approval' | 'validation' | 'resource' | 'dependency';
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  affectedMappings: number;
  estimatedDelay: number;
  suggestedActions: string[];
}

export interface ProgressProjection {
  scenario: 'optimistic' | 'realistic' | 'pessimistic';
  completionDate: string;
  confidence: number;
  assumptions: string[];
  riskFactors: string[];
}

export interface FlowProgressDetail {
  flowId: string;
  overallProgress: number;
  phaseProgress: Record<string, PhaseProgress>;
  currentPhase: string;
  blockers: ProgressBlocker[];
  milestones: Milestone[];
  velocity: FlowVelocity;
  estimatedCompletion: string;
  actualStartTime: string;
  lastUpdateTime: string;
}

export interface PhaseProgress {
  phaseName: string;
  status: PhaseStatus;
  progress: number;
  startTime?: string;
  endTime?: string;
  estimatedDuration: number;
  actualDuration?: number;
  tasks: TaskProgress[];
}

export interface TaskProgress {
  taskId: string;
  taskName: string;
  status: TaskStatus;
  progress: number;
  assignee?: string;
  estimatedTime: number;
  actualTime?: number;
  dependencies: string[];
}

export interface ProgressBlocker {
  id: string;
  type: 'resource' | 'approval' | 'technical' | 'data' | 'external';
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  affectedPhases: string[];
  estimatedImpact: number;
  resolutionSteps: string[];
  escalated: boolean;
}

export interface Milestone {
  id: string;
  name: string;
  description: string;
  targetDate: string;
  actualDate?: string;
  status: 'upcoming' | 'at_risk' | 'achieved' | 'missed';
  dependencies: string[];
  deliverables: string[];
}

export interface FlowVelocity {
  phasesPerWeek: number;
  tasksPerDay: number;
  trend: 'accelerating' | 'stable' | 'decelerating';
  historicalAverage: number;
  projectedCompletion: string;
}

export interface ProgressTimeline {
  timestamp: string;
  phase: string;
  event: TimelineEvent;
  description: string;
  impact: 'positive' | 'neutral' | 'negative';
  metrics?: Record<string, number>;
}

export interface TimelineEvent {
  type: 'phase_start' | 'phase_complete' | 'milestone' | 'blocker' | 'acceleration' | 'delay';
  significance: 'minor' | 'moderate' | 'major' | 'critical';
  automated: boolean;
}

export interface ProgressMetrics {
  overallEfficiency: number;
  timeToValue: number;
  qualityScore: number;
  resourceUtilization: number;
  riskScore: number;
  userSatisfaction?: number;
  businessImpact: BusinessImpactMetrics;
}

export interface BusinessImpactMetrics {
  valueRealized: number;
  costSavings: number;
  timeToMarket: number;
  riskReduction: number;
  complianceScore: number;
}

// Enums and Types
export type PhaseStatus = 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'cancelled';
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'blocked' | 'cancelled' | 'on_hold';
