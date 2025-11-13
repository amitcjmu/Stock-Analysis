import { apiCall } from "@/config/api";
import { CollectionFlowClient } from "./client";
import type {
  AdaptiveQuestionnaireResponse,
  CollectionGapAnalysisResponse,
  CompletenessMetrics,
  DataGap,
  ScanGapsResponse,
  GapUpdate,
  UpdateGapsResponse,
  ApiError,
} from "./types";

/**
 * Questionnaire operations
 * Handles questionnaire fetching, gap analysis, and questionnaire-related workflows
 */
export class QuestionnairesApi extends CollectionFlowClient {
  async getFlowQuestionnaires(
    flowId: string,
  ): Promise<AdaptiveQuestionnaireResponse[]> {
    try {
      // Simply return the response from the backend - it now returns a bootstrap questionnaire
      // when no assets are selected, but add better error handling
      return await apiCall(`${this.baseUrl}/flows/${flowId}/questionnaires`, {
        method: "GET",
      });
    } catch (error: unknown) {
      // Enhanced error handling for questionnaire fetching
      if (error && typeof error === "object") {
        const apiError = error as ApiError;

        if (apiError.status === 404 || apiError.response?.status === 404) {
          throw new Error(
            "Collection flow not found. The flow may have been deleted or you may not have access.",
          );
        }

        if (apiError.status === 422 || apiError.response?.status === 422) {
          // Check for specific 422 error about asset selection
          const detail =
            apiError.response?.data?.detail || apiError.response?.detail;
          if (
            detail &&
            typeof detail === "string" &&
            detail.includes("no_applications_selected")
          ) {
            const enhancedError = new Error(
              "No applications selected for collection. Please select assets first.",
            ) as Error & { code: string; status: number };
            enhancedError.code = "no_applications_selected";
            enhancedError.status = 422;
            throw enhancedError;
          }
          throw new Error(
            "Invalid request. Please check your flow configuration.",
          );
        }

        if (apiError.status === 403 || apiError.response?.status === 403) {
          throw new Error(
            "Access denied. You do not have permission to access this collection flow.",
          );
        }

        if (apiError.status === 500 || apiError.response?.status === 500) {
          throw new Error(
            "Server error occurred while fetching questionnaires. Please try again.",
          );
        }
      }

      // Re-throw other errors as-is
      throw error;
    }
  }

  async getQuestionnaireResponses(
    flowId: string,
    questionnaireId: string,
  ): Promise<{ responses: Record<string, unknown> }> {
    try {
      return await apiCall(
        `${this.baseUrl}/flows/${flowId}/questionnaires/${questionnaireId}/responses`,
        {
          method: "GET",
        },
      );
    } catch (err: unknown) {
      console.error("Failed to get questionnaire responses:", err);
      // Return empty responses on error to allow form to still function
      return { responses: {} };
    }
  }

  async getFlowGaps(flowId: string): Promise<CollectionGapAnalysisResponse[]> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/gaps`, {
      method: "GET",
    });
  }

  async getCompletenessMetrics(flowId: string): Promise<CompletenessMetrics> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/completeness`, {
      method: "GET",
    });
  }

  async refreshCompletenessMetrics(
    flowId: string,
    categoryId?: string,
  ): Promise<CompletenessMetrics> {
    const body = categoryId
      ? JSON.stringify({ category_id: categoryId })
      : undefined;
    return await apiCall(
      `${this.baseUrl}/flows/${flowId}/completeness/refresh`,
      {
        method: "POST",
        body,
      },
    );
  }

  // Get existing gaps for a flow
  async getGaps(flowId: string): Promise<DataGap[]> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/gaps`, {
      method: "GET",
    });
  }

  // Phase 1: Two-Phase Gap Analysis - Programmatic Scan
  async scanGaps(
    flowId: string,
    selectedAssetIds: string[],
  ): Promise<ScanGapsResponse> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/scan-gaps`, {
      method: "POST",
      body: JSON.stringify({ selected_asset_ids: selectedAssetIds }),
    });
  }

  // Phase 2: Two-Phase Gap Analysis - AI Enhancement (Non-Blocking)
  async analyzeGaps(
    flowId: string,
    gaps: DataGap[],
    selectedAssetIds: string[],
  ): Promise<{
    job_id: string;
    status: string;
    progress_url: string;
    message: string;
  }> {
    // Returns 202 Accepted with job_id immediately (non-blocking)
    return await apiCall(`${this.baseUrl}/flows/${flowId}/analyze-gaps`, {
      method: "POST",
      body: JSON.stringify({ gaps, selected_asset_ids: selectedAssetIds }),
      timeout: 10000, // 10s timeout for job submission
    });
  }

  // Poll enhancement progress (for non-blocking AI analysis)
  async getEnhancementProgress(flowId: string): Promise<{
    status: string;
    processed: number;
    total: number;
    current_asset?: string;
    percentage: number;
    updated_at?: string;
    // Bug #892 Fix: Include detailed error information
    error?: string;
    error_type?: string;
    error_category?: string;
    user_message?: string;
  }> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/enhancement-progress`, {
      method: "GET",
      timeout: 5000,
    });
  }

  // Update gap with manual resolution
  async updateGaps(
    flowId: string,
    updates: GapUpdate[],
  ): Promise<UpdateGapsResponse> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/update-gaps`, {
      method: "PUT",
      body: JSON.stringify({ updates }),
    });
  }
}
