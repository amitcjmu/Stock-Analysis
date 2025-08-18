/**
 * Master Flow Service - Unified API for all flow operations
 * Replaces all legacy discovery, assessment, and other flow services
 */

import { ApiClient } from "../ApiClient";
import type { ApiResponse, ApiError } from "../../types/shared/api-types";
import type { EnhancedApiError } from "../../config/api";
import type { AuditableMetadata } from "../../types/shared/metadata-types";
import type { BaseMetadata } from "../../types/shared/metadata-types";
import type { ActiveFlowSummary } from "../../types/modules/flow-orchestration/model-types";
import { createMultiTenantHeaders } from "../../utils/api/multiTenantHeaders";
import type { MultiTenantContext } from "../../utils/api/apiTypes";

const apiClient = ApiClient.getInstance();
import type { AuthService } from "../../contexts/AuthContext/services/authService";

export interface FlowConfiguration extends BaseMetadata {
  flow_name?: string;
  auto_retry?: boolean;
  max_retries?: number;
  timeout_minutes?: number;
  notification_channels?: string[];
  agent_collaboration?: boolean;
}

export interface FlowMetrics {
  total_flows: number;
  active_flows: number;
  completed_flows: number;
  failed_flows: number;
  average_duration_minutes: number;
  success_rate: number;
  phase_metrics: Record<
    string,
    {
      total_executions: number;
      average_duration: number;
      success_rate: number;
    }
  >;
}

export interface MasterFlowRequest {
  clientAccountId: string;
  engagementId: string;
  flowType:
    | "discovery"
    | "assessment"
    | "planning"
    | "execution"
    | "modernize"
    | "finops"
    | "observability"
    | "decommission";
  config?: FlowConfiguration;
  userId?: string;
}

export interface MasterFlowResponse {
  flowId: string;
  status: "initializing" | "running" | "completed" | "failed" | "paused";
  flowType: string;
  progress: number;
  currentPhase: string;
  metadata: AuditableMetadata;
  createdAt: string;
  updatedAt: string;
}

export interface FlowStatusResponse {
  flowId: string;
  flow_id?: string; // Some endpoints return flow_id instead of flowId
  status: string;
  progress?: number;
  progress_percentage?: number; // Backend uses this
  currentPhase?: string;
  current_phase?: string; // Some endpoints use snake_case
  phase?: string; // Another variant
  phaseDetails?: Record<string, unknown>;
  phase_completion?: Record<string, boolean>; // For phase completion tracking
  errors?: string[];
  metadata?: Record<string, unknown>;
  awaitingUserApproval?: boolean;
  awaiting_user_approval?: boolean; // Snake case variant
  lastUpdated?: string;
  field_mappings?: Array<{
    id: string;
    source_field: string;
    target_field: string;
    status: string;
    confidence_score: number;
    match_type: string;
    suggested_by?: string;
    approved_by?: string;
    approved_at?: string;
    transformation_rules?: Record<string, unknown>;
    created_at?: string;
    updated_at?: string;
  }>;
  agent_insights?: Array<{
    id: string;
    agent_id: string;
    agent_name: string;
    insight_type: string;
    title: string;
    description: string;
    confidence: string | number;
    supporting_data: Record<string, unknown>;
    actionable: boolean;
    page: string;
    created_at: string;
    flow_id?: string;
    category?: string;
    message?: string;
    recommendation?: string;
    severity?: string;
  }>;
  raw_data?: Array<Record<string, unknown>>;
  import_metadata?: AuditableMetadata;
}

/**
 * Get multi-tenant headers for API requests using centralized utility
 */
const getMultiTenantHeaders = (
  clientAccountId: string,
  engagementId?: string,
  userId?: string,
): Record<string, string> => {
  const token = localStorage.getItem("auth_token");
  const context: MultiTenantContext = {
    clientAccountId,
    engagementId,
    userId,
  };

  const headers = {
    ...createMultiTenantHeaders(context),
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };

  return headers;
};

/**
 * Handle API errors consistently
 */
const handleApiError = (
  error: Error | { message?: string; code?: string },
  operation: string,
): void => {
  console.error(`MasterFlowService.${operation} failed:`, error);
  if (error instanceof Error) {
    throw new Error(`${operation} failed: ${error.message}`);
  }
  throw new Error(`${operation} failed: Unknown error`);
};

/**
 * Master Flow Service - Single API pattern for all flows
 */
export const masterFlowService = {
  /**
   * Initialize any type of flow via master orchestrator
   */
  async initializeFlow(
    request: MasterFlowRequest,
  ): Promise<MasterFlowResponse> {
    try {
      // Transform the request to match backend expectations
      const backendRequest = {
        flow_type: request.flowType,
        flow_name: request.config?.flow_name || `${request.flowType} Flow`,
        configuration: request.config || {},
        initial_state: {},
      };

      const response = await apiClient.post<{
        flow_id: string;
        status: string;
        flow_type: string;
        progress_percentage: number;
        phase: string;
        metadata: AuditableMetadata;
        created_at: string;
        updated_at: string;
      }>("/flows/", backendRequest, {
        headers: getMultiTenantHeaders(
          request.clientAccountId,
          request.engagementId,
          request.userId,
        ),
      });

      // Transform backend response to match frontend expectations
      return {
        flowId: response.flow_id,
        status: response.status as
          | "initializing"
          | "running"
          | "completed"
          | "failed"
          | "paused",
        flowType: response.flow_type,
        progress: response.progress_percentage || 0,
        currentPhase: response.phase || "initialization",
        metadata: response.metadata || {
          tags: {},
          labels: {},
          annotations: {},
          customFields: {},
        },
        createdAt: response.created_at,
        updatedAt: response.updated_at,
      };
    } catch (error) {
      handleApiError(error, "initializeFlow");
      throw error;
    }
  },

  /**
   * Get flow status for any flow type
   */
  async getFlowStatus(
    flowId: string,
    clientAccountId: string,
    engagementId?: string,
  ): Promise<FlowStatusResponse> {
    try {
      const response = await apiClient.get<FlowStatusResponse>(
        `/flows/${flowId}/status`,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        },
      );
      return response;
    } catch (error) {
      handleApiError(error, "getFlowStatus");
      throw error;
    }
  },

  /**
   * Get all active flows for a client
   */
  async getActiveFlows(
    clientAccountId: string,
    engagementId?: string,
    flowType?: string,
  ): Promise<ActiveFlowSummary[]> {
    const params = new URLSearchParams();
    if (flowType) params.append("flowType", flowType);

    const endpoint = `/flows/active${params.toString() ? `?${params}` : ""}`; // Fixed: Use MFO endpoint
    const headers = getMultiTenantHeaders(clientAccountId, engagementId);

    if (process.env.NODE_ENV !== 'production') {
      console.log("🔍 MasterFlowService.getActiveFlows - Making API call:", {
        endpoint,
        clientAccountId,
        engagementId,
        flowType,
      });
    }

    // Backend returns snake_case, so define the actual response type
    interface BackendFlowResponse {
      flow_id: string;
      flow_type: string;
      flow_name: string;
      status: string;
      phase?: string;
      progress_percentage?: number;
      created_at?: string;
      updated_at?: string;
      metadata?: Record<string, unknown>;
    }

    // Define unified-discovery response type for fallback
    interface UnifiedDiscoveryFlowResponse {
      flow_id?: string;
      flowId?: string;
      id?: string;
      flow_type?: string;
      flowType?: string;
      type?: string;
      flow_name?: string;
      flowName?: string;
      status: string;
      phase?: string;
      current_phase?: string;
      currentPhase?: string;
      progress_percentage?: number;
      progress?: number;
      created_at?: string;
      start_time?: string;
      startTime?: string;
      updated_at?: string;
      last_updated?: string;
      metadata?: Record<string, unknown>;
      engagement_id?: string;
      engagementId?: string;
      client_account_id?: string;
      client_id?: string;
      clientAccountId?: string;
    }

    try {
      const response = await apiClient.get<BackendFlowResponse[]>(endpoint, {
        headers,
      });

      if (process.env.NODE_ENV !== 'production') {
        console.log(
          "✅ MasterFlowService.getActiveFlows - Response received:",
          response,
        );
      }

      // Transform snake_case backend response to camelCase ActiveFlowSummary[]
      return response.map((flow) => ({
        flowId: flow.flow_id,
        flowType: flow.flow_type,
        flowName: flow.flow_name || flow.flow_type,
        status: flow.status as FlowStatus,
        progress: flow.progress_percentage || 0,
        currentPhase: flow.phase || "initialization",
        assignedAgents: 0, // Default values as these are not in backend response
        activeCrews: 0,
        childFlows: 0,
        priority: "normal",
        startTime: flow.created_at || new Date().toISOString(),
        estimatedCompletion: undefined,
        clientAccountId: clientAccountId,
        engagementId: engagementId || "",
        userId: "",
      }));
    } catch (error) {
      if (process.env.NODE_ENV !== 'production') {
        console.error(
          "❌ MasterFlowService.getActiveFlows - MFO API call failed:",
          error,
        );
      }

      // CC: Implement fallback to unified-discovery endpoint for issues #95 and #94
      // Gate fallback behind feature flag to prevent dual reads and maintain single source of truth
      if (!process.env.NEXT_PUBLIC_ENABLE_UNIFIED_DISCOVERY_FALLBACK) {
        if (process.env.NODE_ENV !== 'production') {
          console.warn(
            "❌ MasterFlowService.getActiveFlows - Fallback disabled by feature flag. Original error:",
            error,
          );
        }
        handleApiError(error, "getActiveFlows");
        throw error;
      }

      if (process.env.NODE_ENV !== 'production') {
        console.log(
          "🔄 MasterFlowService.getActiveFlows - Attempting fallback to unified-discovery endpoint...",
        );
      }

      try {
        // Try unified-discovery endpoint as fallback
        const fallbackEndpoint = `/unified-discovery/flows/active${params.toString() ? `?${params}` : ""}`;

        if (process.env.NODE_ENV !== 'production') {
          console.log(
            "🔍 MasterFlowService.getActiveFlows - Fallback API call:",
            {
              fallbackEndpoint,
              clientAccountId,
              engagementId,
              flowType,
            },
          );
        }

        const fallbackResponse = await apiClient.get<
          | UnifiedDiscoveryFlowResponse[]
          | { flows: UnifiedDiscoveryFlowResponse[] }
        >(fallbackEndpoint, {
          headers,
        });

        if (process.env.NODE_ENV !== 'production') {
          console.log(
            "✅ MasterFlowService.getActiveFlows - Fallback response received:",
            fallbackResponse,
          );
        }

        // Handle both array response and object with flows array (based on existing pattern)
        let flowsToProcess: UnifiedDiscoveryFlowResponse[] = [];

        if (Array.isArray(fallbackResponse)) {
          flowsToProcess = fallbackResponse;
          if (process.env.NODE_ENV !== 'production') {
            console.log(
              `🔄 Processing ${flowsToProcess.length} flows from unified-discovery API (array response)...`,
            );
          }
        } else if (
          fallbackResponse &&
          typeof fallbackResponse === "object" &&
          "flows" in fallbackResponse &&
          Array.isArray(fallbackResponse.flows)
        ) {
          flowsToProcess = fallbackResponse.flows;
          if (process.env.NODE_ENV !== 'production') {
            console.log(
              `🔄 Processing ${flowsToProcess.length} flows from unified-discovery API (object.flows response)...`,
            );
          }
        }

        // Transform unified-discovery response to ActiveFlowSummary[] format
        return flowsToProcess.map((flow) => {
          // Extract flow ID with multiple field name support
          const flowId = flow.flow_id || flow.flowId || flow.id || "";
          const flowType =
            flow.flow_type || flow.flowType || flow.type || "discovery";
          const flowName = flow.flow_name || flow.flowName || flowType;
          const currentPhase =
            flow.phase ||
            flow.current_phase ||
            flow.currentPhase ||
            "initialization";
          const progress = flow.progress_percentage || flow.progress || 0;
          const startTime =
            flow.created_at ||
            flow.start_time ||
            flow.startTime ||
            new Date().toISOString();
          const engagementIdFromFlow =
            flow.engagement_id || flow.engagementId || engagementId || "";
          const clientAccountIdFromFlow =
            flow.client_account_id ||
            flow.client_id ||
            flow.clientAccountId ||
            clientAccountId;

          return {
            flowId,
            flowType,
            flowName,
            status: flow.status as FlowStatus,
            progress,
            currentPhase,
            assignedAgents: 0, // Default values - unified-discovery doesn't provide these
            activeCrews: 0,
            childFlows: 0,
            priority: "normal",
            startTime,
            estimatedCompletion: undefined,
            clientAccountId: clientAccountIdFromFlow,
            engagementId: engagementIdFromFlow,
            userId: "",
          };
        });
      } catch (fallbackError) {
        if (process.env.NODE_ENV !== 'production') {
          console.error(
            "❌ MasterFlowService.getActiveFlows - Fallback to unified-discovery also failed:",
            fallbackError,
          );
        }

        // Log both errors for debugging in non-production
        if (process.env.NODE_ENV !== 'production') {
          console.error("Original MFO error:", error);
          console.error("Fallback unified-discovery error:", fallbackError);
        }

        // Handle the original error since both primary and fallback failed
        handleApiError(error, "getActiveFlows");
        throw error;
      }
    }
  },

  /**
   * Delete a flow
   */
  async deleteFlow(
    flowId: string,
    clientAccountId: string,
    engagementId?: string,
  ): Promise<void> {
    const headers = getMultiTenantHeaders(clientAccountId, engagementId);

    try {
      // Use proper MFO endpoint for flow deletion
      await apiClient.delete(`/flows/${flowId}`, undefined, {
        // Fixed: Use MFO endpoint
        headers,
      });
      if (process.env.NODE_ENV !== 'production') {
        console.log(
          `✅ MasterFlowService.deleteFlow - Successfully deleted flow ${flowId} via MFO endpoint`,
        );
      }
    } catch (error) {
      if (process.env.NODE_ENV !== 'production') {
        console.error(
          `❌ MasterFlowService.deleteFlow - MFO deletion failed for flow ${flowId}:`,
          error,
        );
      }

      // CC: Implement fallback to unified-discovery endpoint for consistent flow operations
      // SECURITY WARNING: Gate fallback behind feature flag to prevent dual deletes and maintain single source of truth
      if (!process.env.NEXT_PUBLIC_ENABLE_UNIFIED_DISCOVERY_FALLBACK) {
        if (process.env.NODE_ENV !== 'production') {
          console.warn(
            `❌ MasterFlowService.deleteFlow - Fallback disabled by feature flag for flow ${flowId}. Original error:`,
            error,
          );
        }
        handleApiError(error, "deleteFlow");
        throw error;
      }

      if (process.env.NODE_ENV !== 'production') {
        console.log(
          `🔄 MasterFlowService.deleteFlow - Attempting fallback deletion for flow ${flowId}...`,
        );
      }

      try {
        // Try unified-discovery endpoint as fallback
        const fallbackEndpoint = `/unified-discovery/flows/${flowId}`;

        if (process.env.NODE_ENV !== 'production') {
          console.log("🔍 MasterFlowService.deleteFlow - Fallback deletion:", {
            fallbackEndpoint,
            flowId,
            clientAccountId,
            engagementId,
          });
        }

        await apiClient.delete(fallbackEndpoint, undefined, {
          headers,
        });

        if (process.env.NODE_ENV !== 'production') {
          console.log(
            `✅ MasterFlowService.deleteFlow - Successfully deleted flow ${flowId} via unified-discovery fallback`,
          );
        }
      } catch (fallbackError) {
        if (process.env.NODE_ENV !== 'production') {
          console.error(
            `❌ MasterFlowService.deleteFlow - Fallback deletion also failed for flow ${flowId}:`,
            fallbackError,
          );
        }

        // Log both errors for debugging in non-production
        if (process.env.NODE_ENV !== 'production') {
          console.error("Original MFO deletion error:", error);
          console.error(
            "Fallback unified-discovery deletion error:",
            fallbackError,
          );
        }

        // Handle the original error since both primary and fallback failed
        handleApiError(error, "deleteFlow");
        throw error;
      }
    }
  },

  /**
   * Update flow configuration
   */
  async updateFlowConfig(
    flowId: string,
    config: FlowConfiguration,
    clientAccountId: string,
    engagementId?: string,
  ): Promise<void> {
    try {
      await apiClient.put(`/flows/${flowId}/config`, config, {
        headers: getMultiTenantHeaders(clientAccountId, engagementId),
      });
    } catch (error) {
      handleApiError(error, "updateFlowConfig");
      throw error;
    }
  },

  /**
   * Pause a flow
   */
  async pauseFlow(
    flowId: string,
    clientAccountId: string,
    engagementId?: string,
  ): Promise<void> {
    try {
      await apiClient.post(
        `/flows/${flowId}/pause`,
        {},
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        },
      );
    } catch (error) {
      handleApiError(error, "pauseFlow");
      throw error;
    }
  },

  /**
   * Resume a flow
   */
  async resumeFlow(
    flowId: string,
    clientAccountId: string,
    engagementId?: string,
  ): Promise<ApiResponse<{ success: boolean; message?: string }>> {
    try {
      const response = await apiClient.post<
        ApiResponse<{ success: boolean; message?: string }>
      >(
        `/flows/${flowId}/resume`,
        {},
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        },
      );
      return response;
    } catch (error) {
      handleApiError(error, "resumeFlow");
      throw error;
    }
  },

  /**
   * Retry a failed flow
   */
  async retryFlow(
    flowId: string,
    clientAccountId: string,
    engagementId?: string,
  ): Promise<ApiResponse<{ success: boolean; message?: string }>> {
    try {
      const response = await apiClient.post<
        ApiResponse<{ success: boolean; message?: string }>
      >(
        `/flows/${flowId}/retry`,
        {},
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        },
      );
      return response;
    } catch (error) {
      handleApiError(error, "retryFlow");
      throw error;
    }
  },

  /**
   * Execute a specific phase of a flow
   */
  async executePhase(
    flowId: string,
    phase: string,
    data: Record<string, unknown>,
    clientAccountId: string,
    engagementId?: string,
  ): Promise<{
    success: boolean;
    phase: string;
    status: string;
    message?: string;
    data?: Record<string, unknown>;
    errors?: string[];
  }> {
    try {
      const response = await apiClient.post<{
        success: boolean;
        phase: string;
        status: string;
        message?: string;
        data?: Record<string, unknown>;
        errors?: string[];
      }>(
        `/flows/${flowId}/execute`,
        {
          phase,
          phase_input: data,
          force: false,
        },
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        },
      );
      return response;
    } catch (error) {
      handleApiError(error, "executePhase");
      throw error;
    }
  },

  /**
   * Get flow metrics and analytics
   */
  async getFlowMetrics(
    clientAccountId: string,
    engagementId?: string,
    flowType?: string,
  ): Promise<FlowMetrics> {
    try {
      const params = new URLSearchParams();
      if (flowType) params.append("flowType", flowType);

      const response = await apiClient.get<FlowMetrics>(
        `/flows/metrics${params.toString() ? `?${params}` : ""}`,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        },
      );
      return response;
    } catch (error) {
      handleApiError(error, "getFlowMetrics");
      throw error;
    }
  },

  // Legacy compatibility methods for discovery flows

  /**
   * Initialize discovery flow (legacy compatibility)
   */
  async initializeDiscoveryFlow(
    clientAccountId: string,
    engagementId: string,
    config?: FlowConfiguration,
  ): Promise<MasterFlowResponse> {
    return this.initializeFlow({
      clientAccountId,
      engagementId,
      flowType: "discovery",
      config,
    });
  },

  /**
   * Get discovery flow status (legacy compatibility)
   */
  async getDiscoveryFlowStatus(
    flowId: string,
    clientAccountId: string,
    engagementId?: string,
  ): Promise<FlowStatusResponse> {
    return this.getFlowStatus(flowId, clientAccountId, engagementId);
  },

  /**
   * Get active discovery flows (legacy compatibility)
   */
  async getActiveDiscoveryFlows(
    clientAccountId: string,
    engagementId?: string,
  ): Promise<ActiveFlowSummary[]> {
    return this.getActiveFlows(clientAccountId, engagementId, "discovery");
  },
};

export default masterFlowService;
