/**
 * Master Flow Service - Unified API for all flow operations
 * Replaces all legacy discovery, assessment, and other flow services
 */

import { ApiClient } from "../ApiClient";
import type { ApiResponse, ApiError } from "../../types/shared/api-types";
import type { EnhancedApiError } from "../../config/api";
import type { AuditableMetadata } from "../../types/shared/metadata-types";
import type { BaseMetadata } from "../../types/shared/metadata-types";
import type { ActiveFlowSummary, FlowStatus } from "../../types/modules/flow-orchestration/model-types";
import type { FlowContinuationResponse } from "../../types/api/flow-continuation";
import { createMultiTenantHeaders } from "../../utils/api/multiTenantHeaders";
import type { MultiTenantContext } from "../../utils/api/apiTypes";
import { tokenStorage } from "../../contexts/AuthContext/storage";

const apiClient = ApiClient.getInstance();
import type { AuthService } from "../../contexts/AuthContext/services/authService";

// Centralized flow endpoints - ALL use plural /flows/
const FLOW_ENDPOINTS = {
  // Unified Discovery
  initialize: '/unified-discovery/flows/initialize',
  list: '/unified-discovery/flows/active',
  status: (id: string) => `/unified-discovery/flows/${id}/status`,
  execute: (id: string) => `/unified-discovery/flows/${id}/execute`,
  pause: (id: string) => `/unified-discovery/flows/${id}/pause`,
  resume: (id: string) => `/unified-discovery/flows/${id}/resume`,
  retry: (id: string) => `/unified-discovery/flows/${id}/retry`,
  delete: (id: string) => `/unified-discovery/flows/${id}`,
  config: (id: string) => `/unified-discovery/flows/${id}/config`,
  fieldMappings: (id: string) => `/unified-discovery/flows/${id}/field-mappings`,

  // Data Import
  importData: (id: string) => `/data-import/flows/${id}/import-data`,
  validation: (id: string) => `/data-import/flows/${id}/validation`,

  // Agent Insights
  agentInsights: (id: string) => `/agent-insights/flows/${id}/agent-insights`,

  // Flow Health
  health: '/flows/health',
} as const;

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
  client_account_id: string;
  engagement_id: string;
  flow_type:
    | "discovery"
    | "assessment"
    | "planning"
    | "execution"
    | "modernize"
    | "finops"
    | "observability"
    | "decommission";
  config?: FlowConfiguration;
  user_id?: string;
}

export interface MasterFlowResponse {
  flow_id: string;
  status: "initializing" | "running" | "completed" | "failed" | "paused";
  flow_type: string;
  progress: number;
  current_phase: string;
  metadata: AuditableMetadata;
  created_at: string;
  updated_at: string;
}

export interface FlowStatusResponse {
  flow_id: string;
  status: string;
  progress?: number;
  progress_percentage?: number;
  current_phase?: string;
  phase?: string;
  phase_details?: Record<string, unknown>;
  phase_completion?: Record<string, boolean>;
  phase_state?: Record<string, unknown>;  // CC: Added for conflict resolution tracking
  errors?: string[];
  metadata?: Record<string, unknown>;
  awaiting_user_approval?: boolean;
  last_updated?: string;
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
  client_account_id: string,
  engagement_id?: string,
  user_id?: string,
): Record<string, string> => {
  const token = tokenStorage.getToken();
  const context: MultiTenantContext = {
    clientAccountId: client_account_id,
    engagementId: engagement_id,
    userId: user_id,
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
      // Use snake_case directly
      const backendRequest = {
        flow_type: request.flow_type,
        flow_name: request.config?.flow_name || `${request.flow_type} Flow`,
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
      }>(FLOW_ENDPOINTS.initialize, backendRequest, {
        headers: getMultiTenantHeaders(
          request.client_account_id,
          request.engagement_id,
          request.user_id,
        ),
      });

      // Use snake_case directly from backend response
      return {
        flow_id: response.flow_id,
        status: response.status as
          | "initializing"
          | "running"
          | "completed"
          | "failed"
          | "paused",
        flow_type: response.flow_type,
        progress: response.progress_percentage || 0,
        current_phase: response.phase || "initialization",
        metadata: response.metadata || {
          tags: {},
          labels: {},
          annotations: {},
          customFields: {},
        },
        created_at: response.created_at,
        updated_at: response.updated_at,
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
    flow_id: string,
    client_account_id: string,
    engagement_id?: string,
  ): Promise<FlowStatusResponse> {
    try {
      const response = await apiClient.get<FlowStatusResponse>(
        FLOW_ENDPOINTS.status(flow_id),
        {
          headers: getMultiTenantHeaders(client_account_id, engagement_id),
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
    client_account_id: string,
    engagement_id?: string,
    flow_type?: string,
  ): Promise<ActiveFlowSummary[]> {
    const params = new URLSearchParams();
    if (flow_type) params.append("flow_type", flow_type);

    const endpoint = `/master-flows/active${params.toString() ? `?${params}` : ""}`; // Fixed: Use correct MFO endpoint path
    const headers = getMultiTenantHeaders(client_account_id, engagement_id);

    if (process.env.NODE_ENV !== 'production') {
      console.log("🔍 MasterFlowService.getActiveFlows - Making API call:", {
        endpoint,
        client_account_id,
        engagement_id,
        flow_type,
      });
    }

    // Backend returns snake_case, so define the actual response type
    interface BackendFlowResponse {
      master_flow_id?: string;  // MFO endpoint returns this
      flow_id?: string;  // Fallback field
      flow_type: string;
      flow_name: string;
      status: string;
      current_phase?: string;  // CC FIX: Backend returns current_phase, not phase
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

      // CC FIX: Transform to snake_case ActiveFlowSummary[] to match type definition
      // Backend returns snake_case, frontend types expect snake_case
      return response.map((flow) => ({
        flow_id: flow.master_flow_id || flow.flow_id || "",
        flow_type: flow.flow_type,
        flow_name: flow.flow_name || flow.flow_type,
        status: flow.status as FlowStatus,
        progress_percentage: flow.progress_percentage || 0,  // CC FIX: Use progress_percentage, not progress (for deletion modal)
        current_phase: flow.current_phase || "initialization",  // FIX: Use current_phase, not phase
        assigned_agents: 0, // Default values as these are not in backend response
        active_crews: 0,
        child_flows: 0,
        priority: "normal",
        start_time: flow.updated_at || flow.created_at || new Date().toISOString(),  // FIX: Use updated_at for last activity
        estimated_completion: undefined,
        client_account_id: client_account_id,
        engagement_id: engagement_id || "",
        user_id: "",
      }));
    } catch (error) {
      if (process.env.NODE_ENV !== 'production') {
        console.error(
          "❌ MasterFlowService.getActiveFlows - MFO API call failed:",
          error,
        );
      }

      // CC: Implement fallback to unified-discovery endpoint for issues #95 and #94
      // Enable fallback based on environment variable
      const enableFallback = process.env.NEXT_PUBLIC_ENABLE_UNIFIED_DISCOVERY_FALLBACK === 'true';
      if (!enableFallback) {
        if (process.env.NODE_ENV !== 'production') {
          console.warn(
            "❌ MasterFlowService.getActiveFlows - Fallback disabled. Original error:",
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
        const fallbackEndpoint = `${FLOW_ENDPOINTS.list}${params.toString() ? `?${params}` : ""}`;

        if (process.env.NODE_ENV !== 'production') {
          console.log(
            "🔍 MasterFlowService.getActiveFlows - Fallback API call:",
            {
              fallbackEndpoint,
              clientAccountId: client_account_id,
              engagementId: engagement_id,
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

        // CC FIX: Transform unified-discovery response to snake_case ActiveFlowSummary[] format
        return flowsToProcess.map((flow) => {
          // Extract values with multiple field name support
          const flowId = flow.flow_id || flow.flowId || flow.id || "";
          const flowType =
            flow.flow_type || flow.flowType || flow.type || "discovery";
          const flowName = flow.flow_name || flow.flowName || flowType;
          const currentPhase =
            flow.current_phase ||
            flow.phase ||
            flow.currentPhase ||
            "initialization";  // FIX: Prioritize current_phase over phase
          const progress = flow.progress_percentage || flow.progress || 0;
          const startTime =
            flow.updated_at ||  // FIX: Use updated_at for last activity
            flow.last_updated ||
            flow.created_at ||
            flow.start_time ||
            flow.startTime ||
            new Date().toISOString();
          const engagementIdFromFlow =
            flow.engagement_id || flow.engagementId || engagement_id || "";
          const clientAccountIdFromFlow =
            flow.client_account_id ||
            flow.client_id ||
            flow.clientAccountId ||
            client_account_id;

          // Return snake_case to match ActiveFlowSummary type
          return {
            flow_id: flowId,
            flow_type: flowType,
            flow_name: flowName,
            status: flow.status as FlowStatus,
            progress_percentage: progress,  // CC FIX: Use progress_percentage, not progress (for deletion modal)
            current_phase: currentPhase,
            assigned_agents: 0, // Default values - unified-discovery doesn't provide these
            active_crews: 0,
            child_flows: 0,
            priority: "normal",
            start_time: startTime,
            estimated_completion: undefined,
            client_account_id: clientAccountIdFromFlow,
            engagement_id: engagementIdFromFlow,
            user_id: "",
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
      await apiClient.delete(`/master-flows/${flowId}`, undefined, {
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
      if (String(process.env.NEXT_PUBLIC_ENABLE_UNIFIED_DISCOVERY_FALLBACK || '').toLowerCase() !== 'true') {
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
        const fallbackEndpoint = FLOW_ENDPOINTS.delete(flowId);

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
      await apiClient.put(FLOW_ENDPOINTS.config(flowId), config, {
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
        FLOW_ENDPOINTS.pause(flowId),
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
  ): Promise<ApiResponse<FlowContinuationResponse>> {
    try {
      const response = await apiClient.post<
        ApiResponse<FlowContinuationResponse>
      >(
        `/flow-processing/continue/${flowId}`,
        {},
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
          timeout: 300000, // 5 minutes timeout for flow resumption (CrewAI agents can take 90-120s)
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
    force?: boolean,
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
        FLOW_ENDPOINTS.execute(flowId),
        {
          phase,
          phase_input: data,
          force: force || false,
          // CC FIX: Send validation_overrides for backend compatibility
          ...(force && { validation_overrides: { force_execution: true } }),
        },
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
          timeout: 300000, // 5 minutes timeout for phase execution (CrewAI agents can take 90-120s)
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

  /**
   * Get assessment flow status with application count (via MFO)
   *
   * CC FIX: Backend returns `selected_applications` and `progress_percentage`,
   * but hook expects `application_count` and `progress`. Transform at service layer.
   */
  async getAssessmentStatus(
    flowId: string,
    clientAccountId: string,
    engagementId?: string,
  ): Promise<{
    flow_id: string;
    status: string;
    progress: number;
    current_phase: string;
    application_count: number;
  }> {
    try {
      // Backend actual response format (snake_case fields from Python)
      const response = await apiClient.get<{
        flow_id: string;
        status: string;
        progress_percentage: number;  // Backend returns this
        current_phase: string;
        selected_applications: number;  // Backend returns this (count of apps)
      }>(
        `/master-flows/${flowId}/assessment-status`,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        },
      );

      // Transform to hook's expected format
      return {
        flow_id: response.flow_id,
        status: response.status,
        progress: response.progress_percentage,  // Transform field name
        current_phase: response.current_phase,
        application_count: response.selected_applications,  // Transform field name
      };
    } catch (error) {
      handleApiError(error, "getAssessmentStatus");
      throw error;
    }
  },

  /**
   * Get assessment applications with full details (via MFO)
   *
   * CC FIX: Backend returns application_asset_groups (canonical applications),
   * but hook expects individual application details. Transform groups to individual app records.
   */
  async getAssessmentApplications(
    flowId: string,
    clientAccountId: string,
    engagementId?: string,
  ): Promise<{
    applications: Array<{
      application_id: string;
      application_name: string;
      application_type: string;
      environment: string;
      business_criticality: string;
      technology_stack: string[];
      complexity_score: number;
      readiness_score: number;
      discovery_completed_at: string;
    }>;
  }> {
    try {
      // Backend returns application_asset_groups structure
      const response = await apiClient.get<{
        flow_id: string;
        applications: Array<{
          canonical_application_id: string | null;
          canonical_application_name: string;
          asset_ids: string[];
          asset_count: number;
          asset_types: string[];
          readiness_summary: {
            ready: number;
            not_ready: number;
            in_progress: number;
          };
        }>;
        total_applications: number;
        total_assets: number;
        unmapped_assets: number;
      }>(
        `/master-flows/${flowId}/assessment-applications`,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        },
      );

      // Transform application groups to individual application records
      // NOTE: Each group represents a canonical application with multiple assets
      // Handle case where applications field may be undefined/null during initialization
      return {
        applications: (response.applications || []).map(group => {
          // Calculate readiness score from readiness_summary
          const totalAssets = group.asset_count;
          const readyAssets = group.readiness_summary.ready;
          const readiness_score = totalAssets > 0 ? (readyAssets / totalAssets) * 10 : 0;

          // Determine business criticality based on readiness
          const notReady = group.readiness_summary.not_ready;
          const business_criticality = notReady > totalAssets * 0.7 ? 'high' :
                                       notReady > totalAssets * 0.4 ? 'medium' : 'low';

          return {
            application_id: group.canonical_application_id || `unmapped-${group.canonical_application_name}`,
            application_name: group.canonical_application_name,
            application_type: group.asset_types[0] || 'application',  // Use first asset type
            environment: 'production',  // Default - not in group data
            business_criticality,
            technology_stack: [],  // Not available in group summary
            complexity_score: Math.min(group.asset_count, 10),  // Asset count as proxy for complexity
            readiness_score: Math.round(readiness_score * 10) / 10,  // Round to 1 decimal
            discovery_completed_at: new Date().toISOString(),  // Not available in group data
          };
        }),
      };
    } catch (error) {
      handleApiError(error, "getAssessmentApplications");
      throw error;
    }
  },

  /**
   * Get assessment readiness summary and asset-level blockers (via MFO)
   * Phase 4 Day 21: Assessment Architecture Enhancement
   */
  async getAssessmentReadiness(
    flow_id: string,
    client_account_id: string,
    engagement_id?: string,
  ): Promise<import('@/types/assessment').AssessmentReadinessResponse> {
    try {
      const response = await apiClient.get<import('@/types/assessment').AssessmentReadinessResponse>(
        `/master-flows/${flow_id}/assessment-readiness`,
        {
          headers: getMultiTenantHeaders(client_account_id, engagement_id),
        },
      );
      // Backend returns snake_case directly
      return response;
    } catch (error) {
      handleApiError(error, "getAssessmentReadiness");
      throw error;
    }
  },

  /**
   * Get assessment progress by attribute category (via MFO)
   * Phase 4 Day 21: Assessment Architecture Enhancement
   */
  async getAssessmentProgress(
    flow_id: string,
    client_account_id: string,
    engagement_id?: string,
  ): Promise<import('@/types/assessment').AssessmentProgressResponse> {
    try {
      const response = await apiClient.get<import('@/types/assessment').AssessmentProgressResponse>(
        `/master-flows/${flow_id}/assessment-progress`,
        {
          headers: getMultiTenantHeaders(client_account_id, engagement_id),
        },
      );
      // Backend returns snake_case directly
      return response;
    } catch (error) {
      handleApiError(error, "getAssessmentProgress");
      throw error;
    }
  },
};

export default masterFlowService;
