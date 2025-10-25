import { apiCall } from "@/config/api";
import { CollectionFlowClient } from "./client";
import type {
  CollectionFlowCreateRequest,
  CollectionFlowResponse,
  CollectionFlowStatusResponse,
  FlowUpdateData,
  FlowContinueResult,
  CleanupResult,
  ApiError,
} from "./types";

/**
 * Flow CRUD operations
 * Handles creation, reading, updating, and deletion of collection flows
 */
export class FlowsApi extends CollectionFlowClient {
  async getFlowStatus(): Promise<CollectionFlowStatusResponse> {
    return await apiCall(`${this.baseUrl}/status`, { method: "GET" });
  }

  async createFlow(
    data: CollectionFlowCreateRequest,
  ): Promise<CollectionFlowResponse> {
    // Always allow multiple concurrent flows
    const requestData = {
      ...data,
      allow_multiple: true,
    };
    return await apiCall(`${this.baseUrl}/flows`, {
      method: "POST",
      body: JSON.stringify(requestData),
    });
  }

  async ensureFlow(missing_attributes?: Record<string, string[]>, assessment_flow_id?: string): Promise<CollectionFlowResponse> {
    // Bug #668 Fix: Pass missing_attributes to trigger gap creation and questionnaire generation
    // Bug Fix: Pass assessment_flow_id to link collection flow to assessment flow
    const body: Record<string, unknown> = {};
    if (missing_attributes) {
      body.missing_attributes = missing_attributes;
    }
    if (assessment_flow_id) {
      body.assessment_flow_id = assessment_flow_id;
    }

    return await apiCall(`${this.baseUrl}/flows/ensure`, {
      method: "POST",
      ...(Object.keys(body).length > 0 && { body: JSON.stringify(body) }),
    });
  }

  async getFlowDetails(flowId: string): Promise<CollectionFlowResponse> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}`, { method: "GET" });
  }

  async getFlowReadiness(flowId: string): Promise<{
    flow_id: string;
    engagement_id: string;
    apps_ready_for_assessment: number;
    quality: { collection_quality_score: number; confidence_score: number };
    phase_scores: { collection: number; discovery: number };
    issues: { total: number; critical: number; warning: number; info: number };
    updated_at?: string;
  }> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/readiness`, {
      method: "GET",
    });
  }

  async updateFlow(
    flowId: string,
    data: FlowUpdateData,
  ): Promise<CollectionFlowResponse> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async getIncompleteFlows(): Promise<CollectionFlowResponse[]> {
    return await apiCall(`${this.baseUrl}/incomplete`, { method: "GET" });
  }

  async getActivelyIncompleteFlows(): Promise<CollectionFlowResponse[]> {
    return await apiCall(`${this.baseUrl}/actively-incomplete`, { method: "GET" });
  }

  async getFlow(flowId: string): Promise<CollectionFlowResponse> {
    try {
      return await apiCall(`${this.baseUrl}/flows/${flowId}`, { method: "GET" });
    } catch (error: unknown) {
      // Bug #799 Fix: Enhanced error handling for better user feedback
      if (error && typeof error === 'object') {
        const apiError = error as ApiError;

        // Check for 404 - Flow not found
        if (apiError.status === 404 || apiError.response?.status === 404) {
          throw new Error(`404: Collection flow not found (ID: ${flowId})`);
        }

        // Check for 403 - Access denied
        if (apiError.status === 403 || apiError.response?.status === 403) {
          throw new Error('403: You do not have permission to access this collection flow');
        }

        // Check for 500 - Server error
        if (apiError.status === 500 || apiError.response?.status === 500) {
          throw new Error('500: Server error while loading flow. Please try again or contact support.');
        }
      }

      // Re-throw original error if not a specific HTTP error
      throw error;
    }
  }

  async getAllFlows(): Promise<CollectionFlowResponse[]> {
    return await apiCall(`${this.baseUrl}/flows`, { method: "GET" });
  }

  async continueFlow(
    flowId: string,
    resumeContext?: Record<string, unknown>,
  ): Promise<FlowContinueResult> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/continue`, {
      method: "POST",
      body: JSON.stringify({ resume_context: resumeContext }),
    });
  }

  async deleteFlow(
    flowId: string,
    force: boolean = false,
  ): Promise<{ status: string; message: string; flow_id: string }> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}?force=${force}`, {
      method: "DELETE",
    });
  }

  async batchDeleteFlows(
    flowIds: string[],
    force: boolean = false,
  ): Promise<{
    status: string;
    deleted_count: number;
    failed_count: number;
    deleted_flows: string[];
    failed_deletions: Array<{ flow_id: string; error: string }>;
  }> {
    return await apiCall(`${this.baseUrl}/flows/batch-delete?force=${force}`, {
      method: "POST",
      body: JSON.stringify(flowIds),
    });
  }

  async cleanupFlows(
    expirationHours: number = 72,
    dryRun: boolean = true,
    includeFailedFlows: boolean = true,
    includeCancelledFlows: boolean = true,
  ): Promise<CleanupResult> {
    const params = new URLSearchParams({
      expiration_hours: expirationHours.toString(),
      dry_run: dryRun.toString(),
      include_failed: includeFailedFlows.toString(),
      include_cancelled: includeCancelledFlows.toString(),
    });
    return await apiCall(`${this.baseUrl}/cleanup?${params}`, {
      method: "POST",
    });
  }

  async executeFlowPhase(
    flowId: string,
    phaseInput?: Record<string, unknown>,
  ): Promise<{
    phase: string;
    status: string;
    next_phase?: string;
    requires_user_input?: boolean;
  }> {
    try {
      return await apiCall(`${this.baseUrl}/flows/${flowId}/execute`, {
        method: "POST",
        body: JSON.stringify(phaseInput || {}),
      });
    } catch (error: unknown) {
      // Enhanced error handling for flow execution
      if (error && typeof error === "object") {
        const apiError = error as ApiError;

        if (apiError.status === 404 || apiError.response?.status === 404) {
          throw new Error(
            "Collection flow not found in Master Flow Orchestrator. The flow may be corrupted.",
          );
        }

        if (apiError.status === 409 || apiError.response?.status === 409) {
          throw new Error(
            "Flow execution conflict. Another operation may be in progress.",
          );
        }

        if (apiError.status === 422 || apiError.response?.status === 422) {
          throw new Error(
            "Flow execution failed due to invalid state or missing requirements.",
          );
        }
      }

      // Re-throw other errors as-is
      throw error;
    }
  }

  async updateFlowApplications(
    flowId: string,
    applicationIds: string[],
  ): Promise<{
    status: string;
    message: string;
    flow_id: string;
    selected_applications: number;
  }> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/applications`, {
      method: "POST",
      body: JSON.stringify({ selected_application_ids: applicationIds }),
    });
  }

  /**
   * Compute a simple health summary across incomplete flows.
   * - healthy_flows: number of non-problematic flows
   * - problematic_flows: running/paused flows with low progress or failed
   * - health_score: percentage of healthy flows
   */
  async getFlowHealthStatus(): Promise<{
    healthy_flows: number;
    problematic_flows: number;
    total_flows: number;
    health_score: number;
  }> {
    try {
      const incompleteFlows = await this.getIncompleteFlows();
      const totalFlows = incompleteFlows.length;

      if (totalFlows === 0) {
        return {
          healthy_flows: 0,
          problematic_flows: 0,
          total_flows: 0,
          health_score: 100,
        };
      }

      const problematicFlows = incompleteFlows.filter(
        (flow) =>
          flow.status === "failed" ||
          (flow.progress < 10 && this.isFlowStale(flow.updated_at)),
      ).length;

      const healthyFlows = totalFlows - problematicFlows;
      const healthScore = Math.round((healthyFlows / totalFlows) * 100);

      return {
        healthy_flows: healthyFlows,
        problematic_flows: problematicFlows,
        total_flows: totalFlows,
        health_score: healthScore,
      };
    } catch (error) {
      console.error("Failed to get flow health status:", error);
      return {
        healthy_flows: 0,
        problematic_flows: 0,
        total_flows: 0,
        health_score: 0,
      };
    }
  }

  /** Produce cleanup recommendations based on preview results from cleanupFlows. */
  async getCleanupRecommendations(): Promise<{
    total_flows: number;
    cleanup_candidates: number;
    estimated_space_recovery: string;
    recommendations: string[];
  }> {
    try {
      // Get cleanup preview
      const previewResult = await this.cleanupFlows(72, true, true, true);

      const recommendations = [];
      if (previewResult.flows_cleaned > 0) {
        recommendations.push(
          `${previewResult.flows_cleaned} flows can be cleaned up`,
        );
        recommendations.push(
          `${previewResult.space_recovered} of space can be recovered`,
        );
      }

      // Check for very old flows (90+ days)
      const oldFlowsPreview = await this.cleanupFlows(
        this.getOldFlowThreshold(),
        true,
        false,
        true,
      );
      if (oldFlowsPreview.flows_cleaned > 0) {
        recommendations.push(
          `${oldFlowsPreview.flows_cleaned} very old flows should be archived`,
        );
      }

      return {
        total_flows: previewResult.flows_details?.length || 0,
        cleanup_candidates: previewResult.flows_cleaned,
        estimated_space_recovery: previewResult.space_recovered,
        recommendations,
      };
    } catch (error) {
      console.error("Failed to get cleanup recommendations:", error);
      return {
        total_flows: 0,
        cleanup_candidates: 0,
        estimated_space_recovery: "0 KB",
        recommendations: ["Unable to analyze cleanup opportunities"],
      };
    }
  }
}
