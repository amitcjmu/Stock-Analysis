/**
 * Flow Continuation API Types
 *
 * These types match the backend FlowContinuationResponse from flow_processing.py
 * Used when resuming or continuing flows to get intelligent agent guidance
 */

// User guidance from the intelligent agent
export interface UserGuidance {
  primary_message: string;
  action_items: string[];
  user_actions: string[];
  system_actions: string[];
  estimated_completion_time?: number;
}

// Routing context for navigation
export interface RoutingContext {
  target_page: string;
  recommended_page: string;
  flow_id: string;
  phase: string;
  flow_type: string;
}

// Task result from agent analysis
export interface TaskResult {
  task_id: string;
  task_name: string;
  status: string;
  confidence: number;
  next_steps: string[];
}

// Phase status with tasks
export interface PhaseStatus {
  phase_id: string;
  phase_name: string;
  status: string;
  completion_percentage: number;
  tasks: TaskResult[];
  estimated_time_remaining?: number;
}

// Complete flow continuation response from backend
export interface FlowContinuationResponse {
  success: boolean;
  flow_id: string;
  flow_type: string;
  current_phase: string;
  routing_context: RoutingContext;
  user_guidance: UserGuidance;
  checklist_status: PhaseStatus[];
  agent_insights: Array<{
    agent: string;
    analysis: string;
    confidence: number;
    issues_found: string[];
  }>;
  confidence: number;
  reasoning: string;
  execution_time: number;
}

// Request to continue a flow
export interface FlowContinuationRequest {
  requested_action?: string;
  phase_override?: string;
  force_validation?: boolean;
}
