/**
 * Assessment Flow API Client
 *
 * Replaces deprecated sixrApi with MFO-integrated assessment endpoints.
 * Uses Assessment Flow with proper Master Flow Orchestrator integration per ADR-006.
 *
 * Migration: Phase 3 of Assessment Flow MFO Migration (Issue #839)
 * Parent Issue: #611 - Assessment Flow Complete - Treatments Visible
 * Migration Plan: /docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md
 *
 * TYPE GENERATION (Issue #592):
 * This file demonstrates usage of auto-generated types from OpenAPI schema.
 * Run `npm run generate-types` to regenerate types from backend.
 */

import { apiClient, getAuthHeaders } from '@/lib/api/apiClient';
import type {
  ComprehensiveGapReport,
  BatchReadinessSummary,
} from '@/types/assessment';

// Import generated types from OpenAPI schema (Issue #592)
import type { ApiSchemas } from '@/types/generated';

// =============================================================================
// Generated Type Aliases (Issue #592 - API Contract Testing)
// =============================================================================
// These types are now sourced from the auto-generated OpenAPI schema.
// Run `npm run generate-types` to regenerate from backend.
// See: src/types/generated/api.ts for all available types.

/**
 * Assessment flow response - sourced from OpenAPI schema.
 * @see components.schemas.AssessmentFlowResponse in generated/api.ts
 */
export type GeneratedAssessmentFlowResponse = ApiSchemas['AssessmentFlowResponse'];

/**
 * Assessment flow status response - sourced from OpenAPI schema.
 * @see components.schemas.AssessmentFlowStatusResponse in generated/api.ts
 */
export type GeneratedAssessmentFlowStatusResponse = ApiSchemas['AssessmentFlowStatusResponse'];

/**
 * Assessment flow status enum - sourced from OpenAPI schema.
 * Values: "initialized" | "processing" | "paused_for_user_input" | "completed" | "error"
 */
export type GeneratedAssessmentFlowStatus = ApiSchemas['AssessmentFlowStatus'];

/**
 * Accept recommendation request - sourced from OpenAPI schema.
 */
export type GeneratedAcceptRecommendationRequest = ApiSchemas['AcceptRecommendationRequest'];

/**
 * Accept recommendation response - sourced from OpenAPI schema.
 */
export type GeneratedAcceptRecommendationResponse = ApiSchemas['AcceptRecommendationResponse'];

// =============================================================================
// Request/Response Types (Using snake_case per CLAUDE.md field naming convention)
// =============================================================================
// NOTE: These manual types are kept for backward compatibility.
// New code should prefer the Generated* type aliases above.

/**
 * Request to create a new assessment flow.
 *
 * IMPORTANT: All field names use snake_case (NOT camelCase) per CLAUDE.md
 * August 2025 field naming convention update.
 */
export interface AssessmentFlowCreateRequest {
  /** Array of application UUID strings */
  selected_application_ids: string[];
  /** Optional flow name */
  flow_name?: string;
  /** Optional parameters for slider values */
  parameters?: {
    business_value?: number;
    technical_complexity?: number;
    migration_urgency?: number;
    compliance_requirements?: number;
    cost_sensitivity?: number;
    risk_tolerance?: number;
    innovation_priority?: number;
  };
}

/**
 * Response when creating or querying assessment flow.
 *
 * CRITICAL: Uses snake_case field names to match backend.
 * NO transformation needed (api-field-transformer.ts is deprecated).
 *
 * @deprecated Prefer GeneratedAssessmentFlowResponse for type-safe backend alignment
 */
export interface AssessmentFlowResponse {
  /** Master flow_id from crewai_flow_state_extensions table */
  flow_id: string;
  /** Flow lifecycle status: running, paused, completed */
  status: 'running' | 'paused' | 'completed' | 'failed';
  /** Current assessment phase */
  current_phase: string;
  /** Next phase in the assessment flow */
  next_phase?: string;
  /** Number of selected applications */
  selected_applications?: number;
  /** Response message */
  message: string;
}

/**
 * Detailed status response for assessment flow.
 * Includes progress tracking and phase data.
 *
 * @deprecated Prefer GeneratedAssessmentFlowStatusResponse for type-safe backend alignment
 */
export interface AssessmentFlowStatusResponse {
  flow_id: string;
  status: 'running' | 'paused' | 'completed' | 'failed';
  current_phase: string;
  next_phase?: string;
  progress_percentage: number;
  phase_data?: Record<string, unknown>;
  selected_applications: number;
  assessment_complete: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * 6R migration decision for a single application.
 */
export interface SixRDecision {
  app_id: string;
  recommended_strategy: string;
  confidence_score: number;
  reasoning: string;
  estimated_effort?: string;
  estimated_timeline?: string;
  risk_level?: string;
}

/**
 * Response containing all 6R decisions for a flow.
 */
export interface SixRDecisionsResponse {
  flow_id: string;
  sixr_decisions_by_application?: Record<string, SixRDecision>;
  application_id?: string;
  sixr_decision?: SixRDecision;
}

/**
 * Request to update a 6R decision for an application.
 */
export interface SixRDecisionUpdateRequest {
  strategy: string;
  reasoning: string;
  confidence_level: number;
}

/**
 * Tech debt analysis for an application.
 */
export interface TechDebtAnalysis {
  app_id: string;
  tech_debt_items: Array<{
    category: string;
    severity: string;
    description: string;
    estimated_effort: string;
    priority: number;
  }>;
  overall_score: number;
}

/**
 * Response containing tech debt analysis.
 */
export interface TechDebtResponse {
  flow_id: string;
  tech_debt_by_application?: Record<string, TechDebtAnalysis>;
  application_id?: string;
  tech_debt_analysis?: TechDebtAnalysis;
}

/**
 * Request to resume a paused assessment flow.
 */
export interface ResumeFlowRequest {
  phase?: string;
}

// =============================================================================
// Assessment Flow API Client
// =============================================================================

/**
 * API client for Assessment Flow endpoints.
 *
 * All methods use HTTP polling (NOT WebSockets) per coding-agent-guide.md ban list.
 * All field names use snake_case to match backend (NO transformation needed).
 *
 * Endpoints:
 * - POST /api/v1/assessment-flow/initialize - Create new assessment flow
 * - GET /api/v1/assessment-flow/{flow_id}/status - Get flow status
 * - GET /api/v1/assessment-flow/{flow_id}/sixr-decisions - Get 6R recommendations
 * - PUT /api/v1/assessment-flow/{flow_id}/sixr-decisions/{app_id} - Update decision
 * - GET /api/v1/assessment-flow/{flow_id}/tech-debt - Get tech debt analysis
 * - POST /api/v1/assessment-flow/{flow_id}/resume - Resume paused flow
 * - POST /api/v1/assessment-flow/{flow_id}/finalize - Complete assessment
 */
export class AssessmentFlowApiClient {
  /**
   * Create a new assessment flow through MFO.
   *
   * Flow:
   * 1. Validates applications are ready for assessment
   * 2. Creates master flow in crewai_flow_state_extensions
   * 3. Creates child flow in assessment_flows
   * 4. Links via flow_id
   * 5. Starts background assessment process
   *
   * @param request - Assessment flow creation request
   * @returns flow_id of created assessment flow
   *
   * @example
   * const flowId = await assessmentFlowApi.createAssessmentFlow({
   *   selected_application_ids: ['uuid1', 'uuid2', 'uuid3'],
   *   flow_name: 'Q4 2025 Migration Assessment'
   * });
   */
  async createAssessmentFlow(
    request: AssessmentFlowCreateRequest
  ): Promise<string> {
    try {
      console.log('Creating assessment flow:', request);

      // CRITICAL: Use request body for POST (NOT query parameters)
      // Per /docs/guidelines/API_REQUEST_PATTERNS.md
      const response = await apiClient.post<AssessmentFlowResponse>(
        '/assessment-flow/initialize',
        request
      );

      return response.flow_id;
    } catch (error) {
      console.error('Failed to create assessment flow:', error);
      throw error;
    }
  }

  /**
   * Get current status and progress of assessment flow.
   *
   * Uses MFO integration to query both:
   * - Master flow (crewai_flow_state_extensions): lifecycle status
   * - Child flow (assessment_flows): phase data and operational state
   *
   * @param flowId - Assessment flow identifier
   * @returns Detailed flow status with progress
   *
   * @example
   * const status = await assessmentFlowApi.getAssessmentStatus('flow-uuid');
   * console.log(`Progress: ${status.progress_percentage}%`);
   */
  async getAssessmentStatus(
    flowId: string
  ): Promise<AssessmentFlowStatusResponse> {
    try {
      const response = await apiClient.get<AssessmentFlowStatusResponse>(
        `/assessment-flow/${flowId}/status`
      );

      return response;
    } catch (error) {
      console.error('Failed to get assessment status:', error);
      throw error;
    }
  }

  /**
   * Get 6R migration decisions for all or specific application.
   *
   * Returns AI-generated 6R recommendations:
   * - Rehost, Replatform, Refactor, Repurchase, Retire, Retain
   * - Confidence scores and reasoning
   * - Estimated effort and timeline
   *
   * @param flowId - Assessment flow identifier
   * @param appId - Optional specific application ID filter
   * @returns 6R decisions by application
   *
   * @example
   * // Get all decisions
   * const allDecisions = await assessmentFlowApi.getSixRDecisions('flow-uuid');
   *
   * // Get specific application decision
   * const appDecision = await assessmentFlowApi.getSixRDecisions('flow-uuid', 'app-uuid');
   */
  async getSixRDecisions(
    flowId: string,
    appId?: string
  ): Promise<SixRDecisionsResponse> {
    try {
      const endpoint = appId
        ? `/assessment-flow/${flowId}/sixr-decisions?app_id=${appId}`
        : `/assessment-flow/${flowId}/sixr-decisions`;

      const response = await apiClient.get<SixRDecisionsResponse>(endpoint);
      return response;
    } catch (error) {
      console.error('Failed to get 6R decisions:', error);
      throw error;
    }
  }

  /**
   * Update 6R migration decision for specific application.
   *
   * Allows user to accept/modify the AI recommendation:
   * - Change strategy (e.g., from Rehost to Refactor)
   * - Add custom reasoning
   * - Adjust confidence level
   *
   * CRITICAL: Updates asset table six_r_strategy field for wave planning.
   *
   * @param flowId - Assessment flow identifier
   * @param appId - Application identifier
   * @param strategy - 6R migration strategy
   * @param reasoning - Decision reasoning and details
   * @param confidenceLevel - Confidence level (0.0 to 1.0)
   *
   * @example
   * await assessmentFlowApi.acceptRecommendation(
   *   'flow-uuid',
   *   'app-uuid',
   *   'rehost',
   *   'Application is stable and low-risk for lift-and-shift',
   *   0.95
   * );
   */
  async acceptRecommendation(
    flowId: string,
    appId: string,
    strategy: string,
    reasoning: string,
    confidenceLevel: number = 1.0
  ): Promise<void> {
    try {
      // CRITICAL: Use request body for PUT (NOT query parameters)
      await apiClient.put(
        `/assessment-flow/${flowId}/sixr-decisions/${appId}`,
        {
          strategy,
          reasoning,
          confidence_level: confidenceLevel
        }
      );
    } catch (error) {
      console.error('Failed to accept recommendation:', error);
      throw error;
    }
  }

  /**
   * Get tech debt analysis for all or specific application.
   *
   * Returns technical debt assessment:
   * - Debt items by category (code quality, security, performance, etc.)
   * - Severity levels and priority scores
   * - Estimated remediation effort
   *
   * @param flowId - Assessment flow identifier
   * @param appId - Optional specific application ID filter
   * @returns Tech debt analysis by application
   *
   * @example
   * const techDebt = await assessmentFlowApi.getTechDebtAnalysis('flow-uuid');
   */
  async getTechDebtAnalysis(
    flowId: string,
    appId?: string
  ): Promise<TechDebtResponse> {
    try {
      const endpoint = appId
        ? `/assessment-flow/${flowId}/tech-debt?app_id=${appId}`
        : `/assessment-flow/${flowId}/tech-debt`;

      const response = await apiClient.get<TechDebtResponse>(endpoint);
      return response;
    } catch (error) {
      console.error('Failed to get tech debt analysis:', error);
      throw error;
    }
  }

  /**
   * Resume paused assessment flow from specific phase.
   *
   * Uses MFO integration to atomically update both:
   * - Master flow status (from paused to running)
   * - Child flow current_phase (optional phase override)
   *
   * @param flowId - Assessment flow identifier
   * @param phase - Optional phase to resume from (continues from current if not specified)
   * @returns Updated flow response
   *
   * @example
   * // Resume from current phase
   * await assessmentFlowApi.resumeAssessmentFlow('flow-uuid');
   *
   * // Resume from specific phase
   * await assessmentFlowApi.resumeAssessmentFlow('flow-uuid', 'tech_debt_analysis');
   */
  async resumeAssessmentFlow(
    flowId: string,
    phase?: string
  ): Promise<AssessmentFlowResponse> {
    try {
      // CRITICAL: Use request body for POST (NOT query parameters)
      const response = await apiClient.post<AssessmentFlowResponse>(
        `/assessment-flow/${flowId}/resume`,
        { phase }
      );

      return response;
    } catch (error) {
      console.error('Failed to resume assessment flow:', error);
      throw error;
    }
  }

  /**
   * Finalize assessment flow and mark complete.
   *
   * Final step in assessment workflow:
   * - Validates all phases complete
   * - Marks master flow as completed
   * - Prepares applications for wave planning
   *
   * @param flowId - Assessment flow identifier
   *
   * @example
   * await assessmentFlowApi.finalizeAssessment('flow-uuid');
   */
  async finalizeAssessment(flowId: string): Promise<void> {
    try {
      // CRITICAL: Use request body for POST (NOT query parameters)
      await apiClient.post(`/assessment-flow/${flowId}/finalize`, {});
    } catch (error) {
      console.error('Failed to finalize assessment:', error);
      throw error;
    }
  }

  /**
   * GAP-5 FIX: Initiate decommission flow from assessment.
   *
   * Creates a linked decommission flow for applications marked as 'Retire'
   * or 'Retain' in the 6R assessment decisions.
   *
   * @param flowId - Assessment flow identifier (source of 6R decisions)
   * @param applicationIds - List of application IDs to decommission
   * @param flowName - Optional name for the decommission flow
   *
   * @returns Decommission flow creation result
   *
   * @example
   * // Initiate decommission for retired applications
   * const result = await assessmentFlowApi.initiateDecommission(
   *   'assessment-flow-uuid',
   *   ['app-uuid-1', 'app-uuid-2'],
   *   'Q4 2025 System Retirement'
   * );
   * console.log(`Decommission flow created: ${result.decommission_flow_id}`);
   */
  async initiateDecommission(
    flowId: string,
    applicationIds: string[],
    flowName?: string
  ): Promise<{
    assessment_flow_id: string;
    decommission_flow_id: string;
    decommission_master_flow_id: string;
    applications_to_decommission: string[];
    skipped_applications: Array<{ application_id: string; current_strategy: string }>;
    status: string;
    message: string;
  }> {
    try {
      const response = await apiClient.post<{
        assessment_flow_id: string;
        decommission_flow_id: string;
        decommission_master_flow_id: string;
        applications_to_decommission: string[];
        skipped_applications: Array<{ application_id: string; current_strategy: string }>;
        status: string;
        message: string;
      }>(`/master-flows/${flowId}/assessment/initiate-decommission`, {
        application_ids: applicationIds,
        flow_name: flowName,
      });
      return response;
    } catch (error) {
      console.error('Failed to initiate decommission from assessment:', error);
      throw error;
    }
  }

  /**
   * Get comprehensive gap analysis for a single asset.
   *
   * Endpoint: GET /api/v1/assessment-flow/{flow_id}/asset-readiness/{asset_id}
   * Returns: ComprehensiveGapReport
   *
   * Part of Issue #980: Intelligent Multi-Layer Gap Detection System (Day 12)
   *
   * @param flowId - Assessment flow identifier
   * @param assetId - Asset identifier to analyze
   * @returns Comprehensive gap report with all inspector results
   *
   * @example
   * const gapReport = await assessmentFlowApi.getAssetReadiness(
   *   'flow-uuid',
   *   'asset-uuid'
   * );
   * console.log(`Completeness: ${gapReport.overall_completeness}`);
   * console.log(`Ready: ${gapReport.is_ready_for_assessment}`);
   */
  async getAssetReadiness(
    flowId: string,
    assetId: string
  ): Promise<ComprehensiveGapReport> {
    try {
      const response = await apiClient.get<ComprehensiveGapReport>(
        `/assessment-flow/${flowId}/asset-readiness/${assetId}`
      );

      return response;
    } catch (error) {
      console.error('Failed to get asset readiness:', error);
      throw error;
    }
  }

  /**
   * Get readiness summary for all assets in a flow.
   *
   * Endpoint: GET /api/v1/assessment-flow/{flow_id}/readiness-summary?detailed={bool}
   * Returns: BatchReadinessSummary
   *
   * Part of Issue #980: Intelligent Multi-Layer Gap Detection System (Day 12)
   *
   * @param flowId - Assessment flow identifier
   * @param detailed - If true, include full reports per asset (default: false for performance)
   * @returns Batch readiness summary with counts and optional detailed reports
   *
   * @example
   * // Lightweight summary for status checks
   * const summary = await assessmentFlowApi.getFlowReadinessSummary('flow-uuid', false);
   *
   * // Detailed summary with per-asset reports
   * const detailedSummary = await assessmentFlowApi.getFlowReadinessSummary('flow-uuid', true);
   */
  async getFlowReadinessSummary(
    flowId: string,
    detailed: boolean = false
  ): Promise<BatchReadinessSummary> {
    try {
      const response = await apiClient.get<BatchReadinessSummary>(
        `/assessment-flow/${flowId}/readiness-summary?detailed=${detailed}`
      );

      return response;
    } catch (error) {
      console.error('Failed to get flow readiness summary:', error);
      throw error;
    }
  }

  /**
   * Get list of ready/not-ready asset IDs.
   *
   * Endpoint: GET /api/v1/assessment-flow/{flow_id}/ready-assets?ready_only={bool}
   * Returns: string[] (asset UUIDs)
   *
   * Part of Issue #980: Intelligent Multi-Layer Gap Detection System (Day 12)
   *
   * @param flowId - Assessment flow identifier
   * @param readyOnly - If true, return only ready assets; if false, return not ready (default: true)
   * @returns Array of asset UUID strings matching readiness filter
   *
   * @example
   * // Get ready assets to proceed with assessment
   * const readyAssets = await assessmentFlowApi.getReadyAssets('flow-uuid', true);
   *
   * // Get not-ready assets that need data collection
   * const notReadyAssets = await assessmentFlowApi.getReadyAssets('flow-uuid', false);
   */
  async getReadyAssets(
    flowId: string,
    readyOnly: boolean = true
  ): Promise<string[]> {
    try {
      const response = await apiClient.get<string[]>(
        `/assessment-flow/${flowId}/ready-assets?ready_only=${readyOnly}`
      );

      return response;
    } catch (error) {
      console.error('Failed to get ready assets:', error);
      throw error;
    }
  }

  /**
   * Check if a specific phase has completed and saved results.
   *
   * Fix for Issue #1048: Verify backend phase execution before updating frontend state.
   *
   * @param flowId - Assessment flow ID
   * @param phaseName - Phase name to check (e.g., "tech_debt_assessment")
   * @returns Phase completion status and results
   */
  async getPhaseCompletionStatus(
    flowId: string,
    phaseName: string
  ): Promise<{
    status: 'completed' | 'pending';
    phase_name: string;
    results: Record<string, unknown> | null;
    completed_at?: string;
  }> {
    try {
      const response = await apiClient.get(
        `/master-flows/${flowId}/assessment/phase/${phaseName}/status`
      );

      return response;
    } catch (error) {
      console.error(`Failed to get phase ${phaseName} status:`, error);
      throw error;
    }
  }

  /**
   * Poll for phase completion with timeout.
   *
   * Fix for Issue #1048: Wait for backend to confirm phase execution.
   *
   * @param flowId - Assessment flow ID
   * @param phaseName - Phase name to wait for
   * @param timeoutMs - Maximum time to wait (default: 60 seconds)
   * @param intervalMs - Polling interval (default: 2 seconds)
   * @returns Phase completion status or throws after timeout
   */
  async waitForPhaseCompletion(
    flowId: string,
    phaseName: string,
    timeoutMs: number = 60000,
    intervalMs: number = 2000
  ): Promise<{
    status: 'completed' | 'pending';
    phase_name: string;
    results: Record<string, unknown> | null;
    completed_at?: string;
  }> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      const status = await this.getPhaseCompletionStatus(flowId, phaseName);

      if (status.status === 'completed') {
        return status;
      }

      // Wait before next poll
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }

    throw new Error(
      `Phase ${phaseName} did not complete within ${timeoutMs}ms. ` +
        `This may indicate a backend execution failure.`
    );
  }

  /**
   * Export assessment results in specified format.
   *
   * GAP-6 FIX: Wire frontend to backend export endpoint.
   * Uses getAuthHeaders() to include tenant context (X-Client-Account-ID, X-Engagement-ID).
   *
   * @param flowId - Assessment flow ID
   * @param format - Export format: 'json' (implemented), 'pdf' or 'excel' (stubs)
   * @returns Blob containing exported data for download
   */
  async exportAssessment(
    flowId: string,
    format: 'json' | 'pdf' | 'excel' = 'json'
  ): Promise<Blob> {
    try {
      // Get auth headers including tenant context (X-Client-Account-ID, X-Engagement-ID)
      // CRITICAL: Must use getAuthHeaders() to include multi-tenant headers
      const authHeaders = getAuthHeaders();

      // POST to backend export endpoint with format parameter
      const response = await fetch(
        `/api/v1/assessment-flow/${flowId}/export?format=${format}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...authHeaders, // Include Authorization, X-Client-Account-ID, X-Engagement-ID
          },
          credentials: 'include', // Include auth cookies
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Export failed: ${response.status} - ${errorText}`);
      }

      // Return blob for download
      return await response.blob();
    } catch (error) {
      console.error(`Failed to export assessment as ${format}:`, error);
      throw error;
    }
  }

  /**
   * Trigger download of exported assessment data.
   *
   * GAP-6 FIX: Helper to download exported blob as file.
   *
   * @param flowId - Assessment flow ID
   * @param format - Export format
   */
  async downloadExport(
    flowId: string,
    format: 'json' | 'pdf' | 'excel' = 'json'
  ): Promise<void> {
    const blob = await this.exportAssessment(flowId, format);

    // Create download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    // Set filename based on format
    const extension = format === 'excel' ? 'xlsx' : format;
    link.download = `assessment_${flowId}.${extension}`;

    // Trigger download
    document.body.appendChild(link);
    link.click();

    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

// =============================================================================
// Export Singleton Instance
// =============================================================================

/**
 * Singleton instance of Assessment Flow API client.
 *
 * Usage:
 * ```typescript
 * import { assessmentFlowApi } from '@/lib/api/assessmentFlow';
 *
 * const flowId = await assessmentFlowApi.createAssessmentFlow({
 *   selected_application_ids: ['uuid1', 'uuid2']
 * });
 * ```
 */
export const assessmentFlowApi = new AssessmentFlowApiClient();
