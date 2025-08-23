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
  flow_id: string;
  data_import_id?: string;
  include_details?: boolean;
  include_projections?: boolean;
}

export interface GetMappingProgressResponse extends GetResponse<MappingProgressDetail> {
  data: MappingProgressDetail;
  projections?: ProgressProjection[];
  bottlenecks?: ProgressBottleneck[];
}

export interface GetFlowProgressRequest extends GetRequest {
  flow_id: string;
  include_phase_breakdown?: boolean;
  include_timeline?: boolean;
  include_metrics?: boolean;
}

export interface GetFlowProgressResponse extends GetResponse<FlowProgressDetail> {
  data: FlowProgressDetail;
  timeline?: ProgressTimeline[];
  metrics?: ProgressMetrics;
  estimated_completion?: string;
}

// Progress Tracking Models
export interface MappingProgressDetail {
  flow_id: string;
  data_import_id?: string;
  total_mappings: number;
  completed_mappings: number;
  pending_mappings: number;
  approved_mappings: number;
  rejected_mappings: number;
  review_required_mappings: number;
  progress_percentage: number;
  start_time: string;
  last_update_time: string;
  estimated_completion_time?: string;
  average_mapping_time: number;
  velocity: MappingVelocity;
  quality_metrics: MappingQualityMetrics;
}

export interface MappingVelocity {
  mappings_per_hour: number;
  approvals_per_hour: number;
  trend: 'increasing' | 'stable' | 'decreasing';
  projected_completion: string;
}

export interface MappingQualityMetrics {
  average_confidence: number;
  auto_approval_rate: number;
  rejection_rate: number;
  review_cycle_time: number;
}

export interface ProgressBottleneck {
  type: 'approval' | 'validation' | 'resource' | 'dependency';
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  affected_mappings: number;
  estimated_delay: number;
  suggested_actions: string[];
}

export interface ProgressProjection {
  scenario: 'optimistic' | 'realistic' | 'pessimistic';
  completion_date: string;
  confidence: number;
  assumptions: string[];
  risk_factors: string[];
}

export interface FlowProgressDetail {
  flow_id: string;
  overall_progress: number;
  phase_progress: Record<string, PhaseProgress>;
  current_phase: string;
  blockers: ProgressBlocker[];
  milestones: Milestone[];
  velocity: FlowVelocity;
  estimated_completion: string;
  actual_start_time: string;
  last_update_time: string;
}

export interface PhaseProgress {
  phase_name: string;
  status: PhaseStatus;
  progress: number;
  start_time?: string;
  end_time?: string;
  estimated_duration: number;
  actual_duration?: number;
  tasks: TaskProgress[];
}

export interface TaskProgress {
  task_id: string;
  task_name: string;
  status: TaskStatus;
  progress: number;
  assignee?: string;
  estimated_time: number;
  actual_time?: number;
  dependencies: string[];
}

export interface ProgressBlocker {
  id: string;
  type: 'resource' | 'approval' | 'technical' | 'data' | 'external';
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  affected_phases: string[];
  estimated_impact: number;
  resolution_steps: string[];
  escalated: boolean;
}

export interface Milestone {
  id: string;
  name: string;
  description: string;
  target_date: string;
  actual_date?: string;
  status: 'upcoming' | 'at_risk' | 'achieved' | 'missed';
  dependencies: string[];
  deliverables: string[];
}

export interface FlowVelocity {
  phases_per_week: number;
  tasks_per_day: number;
  trend: 'accelerating' | 'stable' | 'decelerating';
  historical_average: number;
  projected_completion: string;
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
  overall_efficiency: number;
  time_to_value: number;
  quality_score: number;
  resource_utilization: number;
  risk_score: number;
  user_satisfaction?: number;
  business_impact: BusinessImpactMetrics;
}

export interface BusinessImpactMetrics {
  value_realized: number;
  cost_savings: number;
  time_to_market: number;
  risk_reduction: number;
  compliance_score: number;
}

// Enums and Types
export type PhaseStatus = 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'cancelled';
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'blocked' | 'cancelled' | 'on_hold';
