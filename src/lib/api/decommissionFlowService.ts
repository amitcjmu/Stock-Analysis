/**
 * Decommission Flow API Service
 *
 * API client functions for interacting with the decommission flow backend.
 * Per ADR-006: Uses Master Flow Orchestrator (MFO) pattern for all flow operations.
 * Per ADR-027: Phase names match FlowTypeConfig (decommission_planning, data_migration, system_shutdown).
 *
 * CRITICAL: Uses snake_case for ALL fields to match backend (no camelCase transformations).
 *
 * Reference: backend/app/api/v1/endpoints/decommission_flow/flow_management.py
 */

import { apiCall } from "../../config/api";

// ============================================================================
// TYPE DEFINITIONS (snake_case ONLY)
// ============================================================================

/**
 * Decommission flow phases (per ADR-027 FlowTypeConfig)
 */
export type DecommissionPhase =
  | "decommission_planning"
  | "data_migration"
  | "system_shutdown";

/**
 * Decommission flow operational status (child flow state per ADR-012)
 */
export type DecommissionFlowStatus =
  | "initialized"
  | "decommission_planning"
  | "data_migration"
  | "system_shutdown"
  | "completed"
  | "paused"
  | "failed";

/**
 * Strategy configuration for decommission execution
 */
export interface DecommissionStrategy {
  priority: "cost_savings" | "risk_reduction" | "compliance";
  execution_mode: "immediate" | "scheduled" | "phased";
  rollback_enabled: boolean;
  stakeholder_approvals?: string[];
}

/**
 * Request for initializing new decommission flow
 */
export interface InitializeDecommissionFlowRequest {
  selected_system_ids: string[]; // ✅ snake_case (Asset UUIDs)
  flow_name?: string; // Optional descriptive name
  decommission_strategy?: DecommissionStrategy;
}

/**
 * Response from decommission flow initialization/operations
 */
export interface DecommissionFlowResponse {
  flow_id: string; // ✅ snake_case
  status: string;
  current_phase: string; // ✅ snake_case
  next_phase: string | null; // ✅ snake_case
  selected_systems: string[]; // ✅ snake_case (UUIDs)
  message: string;
}

/**
 * Detailed status response for decommission flow
 */
export interface DecommissionFlowStatusResponse {
  flow_id: string; // ✅ snake_case
  master_flow_id: string; // ✅ snake_case (MFO)
  status: string;
  current_phase: string; // ✅ snake_case
  system_count: number; // ✅ snake_case

  // Phase progress (ADR-027: names match FlowTypeConfig)
  phase_progress: { // ✅ snake_case
    decommission_planning: "pending" | "in_progress" | "completed" | "failed";
    data_migration: "pending" | "in_progress" | "completed" | "failed";
    system_shutdown: "pending" | "in_progress" | "completed" | "failed";
  };

  // Aggregated metrics
  metrics: {
    systems_decommissioned: number; // ✅ snake_case
    estimated_savings: number; // ✅ snake_case
    compliance_score: number; // ✅ snake_case
  };

  // Runtime state
  runtime_state: { // ✅ snake_case
    current_agent?: string; // ✅ snake_case
    pending_approvals?: string[]; // ✅ snake_case
    warnings?: string[];
  };

  // Timestamps
  created_at: string; // ✅ snake_case (ISO 8601)
  updated_at: string; // ✅ snake_case (ISO 8601)

  // Completion indicators
  decommission_complete: boolean; // ✅ snake_case
}

/**
 * Request for resuming paused decommission flow
 */
export interface ResumeDecommissionFlowRequest {
  phase?: DecommissionPhase; // Optional phase to resume from
  user_input?: Record<string, unknown>; // ✅ snake_case (optional user data)
}

/**
 * Response from pause/cancel operations
 */
export interface DecommissionFlowOperationResponse {
  flow_id: string; // ✅ snake_case
  status: string;
  current_phase?: string; // ✅ snake_case
  message: string;
}

/**
 * List item for decommission flows (query response)
 */
export interface DecommissionFlowListItem {
  flow_id: string; // ✅ snake_case
  master_flow_id: string; // ✅ snake_case
  flow_name: string; // ✅ snake_case
  status: string;
  current_phase: string; // ✅ snake_case
  system_count: number; // ✅ snake_case
  estimated_savings: number; // ✅ snake_case
  created_at: string; // ✅ snake_case (ISO 8601)
  updated_at: string; // ✅ snake_case (ISO 8601)
  runtime_state?: unknown; // ✅ Optional runtime state (includes compliance_score, etc.)
}

/**
 * System eligible for decommission
 */
export interface EligibleSystemResponse {
  asset_id: string; // ✅ snake_case
  asset_name: string; // ✅ snake_case
  six_r_strategy: string | null; // ✅ snake_case
  annual_cost: number; // ✅ snake_case
  decommission_eligible: boolean; // ✅ snake_case
  grace_period_end: string | null; // ✅ snake_case (ISO 8601)
  retirement_reason: string; // ✅ snake_case
}

// ============================================================================
// API CLIENT
// ============================================================================

/**
 * Decommission Flow API Client
 *
 * All endpoints use:
 * - snake_case field names (matching backend)
 * - POST requests with request body (NOT query parameters)
 * - Multi-tenant headers (X-Client-Account-ID, X-Engagement-ID)
 * - MFO endpoints per ADR-006
 */
export const decommissionFlowService = {
  /**
   * Initialize new decommission flow for selected systems
   *
   * Endpoint: POST /api/v1/decommission-flow/initialize
   * Per ADR-006: Creates both master flow (lifecycle) and child flow (operational state)
   *
   * @param params - Initialization parameters with snake_case fields
   * @returns Promise with flow_id and initial status
   */
  async initializeDecommissionFlow(
    params: InitializeDecommissionFlowRequest
  ): Promise<DecommissionFlowResponse> {
    // ✅ CORRECT: POST with request body (NOT query parameters)
    return apiCall("/decommission-flow/initialize", {
      method: "POST",
      body: JSON.stringify(params),
    });
  },

  /**
   * Get current status and progress of decommission flow
   *
   * Endpoint: GET /api/v1/decommission-flow/{flow_id}/status
   * Per ADR-012: Returns child flow operational status (not master flow lifecycle)
   *
   * @param flowId - Decommission flow UUID
   * @returns Promise with detailed status including phase_progress and metrics
   */
  async getDecommissionFlowStatus(
    flowId: string
  ): Promise<DecommissionFlowStatusResponse> {
    // ✅ CORRECT: GET request (status queries use GET)
    return apiCall(`/decommission-flow/${flowId}/status`, {
      method: "GET",
    });
  },

  /**
   * Resume paused decommission flow from specific phase
   *
   * Endpoint: POST /api/v1/decommission-flow/{flow_id}/resume
   * Per ADR-006: Updates both master and child flow state atomically
   *
   * @param flowId - Decommission flow UUID
   * @param params - Resume parameters (optional phase, user_input)
   * @returns Promise with updated flow status
   */
  async resumeDecommissionFlow(
    flowId: string,
    params: ResumeDecommissionFlowRequest = {}
  ): Promise<DecommissionFlowResponse> {
    // ✅ CORRECT: POST with request body
    return apiCall(`/decommission-flow/${flowId}/resume`, {
      method: "POST",
      body: JSON.stringify(params),
    });
  },

  /**
   * Pause running decommission flow
   *
   * Endpoint: POST /api/v1/decommission-flow/{flow_id}/pause
   * Per ADR-006: Updates both master and child flow state atomically
   *
   * @param flowId - Decommission flow UUID
   * @returns Promise with paused status
   */
  async pauseDecommissionFlow(
    flowId: string
  ): Promise<DecommissionFlowOperationResponse> {
    // ✅ CORRECT: POST with no body needed
    return apiCall(`/decommission-flow/${flowId}/pause`, {
      method: "POST",
    });
  },

  /**
   * Cancel decommission flow (marks as failed/deleted)
   *
   * Endpoint: POST /api/v1/decommission-flow/{flow_id}/cancel
   * Per ADR-006: Updates both master and child flow state atomically
   *
   * @param flowId - Decommission flow UUID
   * @returns Promise with cancellation confirmation
   */
  async cancelDecommissionFlow(
    flowId: string
  ): Promise<DecommissionFlowOperationResponse> {
    // ✅ CORRECT: POST with no body needed
    return apiCall(`/decommission-flow/${flowId}/cancel`, {
      method: "POST",
    });
  },

  /**
   * List all decommission flows for current client/engagement
   *
   * Endpoint: GET /api/v1/decommission-flow/
   * Per ADR-006: Queries child flows (decommission_flows table)
   *
   * @param params - Optional filters (status, limit, offset)
   * @returns Promise with array of flow list items
   */
  async listDecommissionFlows(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<DecommissionFlowListItem[]> {
    // ✅ CORRECT: GET request with query parameters
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append("status", params.status);
    if (params?.limit) queryParams.append("limit", params.limit.toString());
    if (params?.offset) queryParams.append("offset", params.offset.toString());

    const url = `/decommission-flow/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;

    return apiCall(url, {
      method: "GET",
    });
  },

  /**
   * Get systems eligible for decommission
   *
   * Endpoint: GET /api/v1/decommission-flow/eligible-systems
   * Returns assets with 6R strategy = "Retire" or marked decommission_eligible
   *
   * @returns Promise with array of eligible systems
   */
  async getEligibleSystems(): Promise<EligibleSystemResponse[]> {
    // ✅ CORRECT: GET request (no parameters)
    return apiCall("/decommission-flow/eligible-systems", {
      method: "GET",
    });
  },
};
