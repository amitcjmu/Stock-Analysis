/**
 * Decommission Flow React Query Hooks
 *
 * Custom React Query hooks for managing decommission flow state and operations.
 * Per ADR-006: Uses Master Flow Orchestrator (MFO) pattern.
 * Per Railway deployment: HTTP polling ONLY (no WebSockets/SSE).
 *
 * CRITICAL: All field names use snake_case to match backend (no transformations).
 *
 * Polling strategy:
 * - 5 seconds when flow is active (decommission_planning/data_migration/system_shutdown)
 * - 15 seconds when waiting for user input (paused)
 * - Stop polling when completed/failed
 *
 * Reference pattern: src/hooks/useAssessmentFlow/useAssessmentFlow.ts
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type {
  UseMutationResult,
  UseQueryResult,
} from "@tanstack/react-query";
import { decommissionFlowService } from "../../lib/api/decommissionFlowService";
import type {
  InitializeDecommissionFlowRequest,
  DecommissionFlowResponse,
  DecommissionFlowStatusResponse,
  ResumeDecommissionFlowRequest,
  UpdatePhaseRequest,
  DecommissionFlowOperationResponse,
  DecommissionFlowListItem,
  EligibleSystemResponse,
  DecommissionPhase,
} from "../../lib/api/decommissionFlowService";

// ============================================================================
// QUERY KEYS
// ============================================================================

/**
 * Query key factory for decommission flow queries
 * Ensures proper cache invalidation and data consistency
 */
export const decommissionFlowKeys = {
  all: ["decommission-flow"] as const,
  lists: () => [...decommissionFlowKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) =>
    [...decommissionFlowKeys.lists(), filters] as const,
  details: () => [...decommissionFlowKeys.all, "detail"] as const,
  detail: (flowId: string) => [...decommissionFlowKeys.details(), flowId] as const,
  status: (flowId: string) =>
    [...decommissionFlowKeys.detail(flowId), "status"] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

/**
 * Hook for fetching decommission flow status with polling
 *
 * Polling behavior (per Railway HTTP-only deployment):
 * - 5s interval when active (decommission_planning, data_migration, system_shutdown)
 * - 15s interval when paused
 * - No polling when completed/failed
 *
 * @param flowId - Decommission flow UUID (snake_case)
 * @param options - Additional query options
 * @returns Query result with status data (all fields in snake_case)
 */
export function useDecommissionFlowStatus(
  flowId: string | null | undefined,
  options?: {
    enabled?: boolean;
    refetchInterval?: number | false;
  }
): UseQueryResult<DecommissionFlowStatusResponse, Error> {
  return useQuery({
    queryKey: decommissionFlowKeys.status(flowId || ""),
    queryFn: () => {
      if (!flowId) {
        throw new Error("Flow ID is required");
      }
      return decommissionFlowService.getDecommissionFlowStatus(flowId);
    },
    enabled: !!flowId && (options?.enabled ?? true),
    // Polling configuration per Railway deployment (HTTP only)
    refetchInterval: (query) => {
      // Allow override from options
      if (options?.refetchInterval !== undefined) {
        return options.refetchInterval;
      }

      const data = query.state.data;
      if (!data) return false; // No data yet

      const status = data.status;

      // Stop polling when completed or failed
      if (status === "completed" || status === "failed") {
        return false;
      }

      // Poll every 5s when flow is actively processing
      if (
        status === "decommission_planning" ||
        status === "data_migration" ||
        status === "system_shutdown"
      ) {
        return 5000;
      }

      // Poll every 15s when paused (waiting for user input)
      if (status === "paused") {
        return 15000;
      }

      // Default: poll every 10s for other states
      return 10000;
    },
    // Ensure fresh data on window focus
    refetchOnWindowFocus: true,
    // Keep previous data while refetching
    placeholderData: (previousData) => previousData,
  });
}

// ============================================================================
// MUTATION HOOKS
// ============================================================================

/**
 * Hook for initializing new decommission flow
 *
 * Endpoint: POST /api/v1/decommission-flow/initialize
 * Per ADR-006: Creates master flow (lifecycle) + child flow (operational state)
 *
 * @returns Mutation object with mutate function and status
 */
export function useInitializeDecommissionFlow(): UseMutationResult<
  DecommissionFlowResponse,
  Error,
  InitializeDecommissionFlowRequest,
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: InitializeDecommissionFlowRequest) =>
      decommissionFlowService.initializeDecommissionFlow(params),
    onSuccess: (data) => {
      // Invalidate flow lists to show new flow
      queryClient.invalidateQueries({
        queryKey: decommissionFlowKeys.lists(),
      });

      // Set initial status data in cache
      queryClient.setQueryData(
        decommissionFlowKeys.status(data.flow_id),
        (oldData: DecommissionFlowStatusResponse | undefined) => {
          if (oldData) return oldData; // Keep existing data if present

          // Create initial status from response
          return {
            flow_id: data.flow_id,
            master_flow_id: data.flow_id, // MFO pattern
            status: data.status,
            current_phase: data.current_phase,
            system_count: data.selected_systems.length,
            phase_progress: {
              decommission_planning: "pending",
              data_migration: "pending",
              system_shutdown: "pending",
            },
            metrics: {
              systems_decommissioned: 0,
              estimated_savings: 0,
              compliance_score: 0,
            },
            runtime_state: {},
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            decommission_complete: false,
          } as DecommissionFlowStatusResponse;
        }
      );

      console.log(
        `✅ Decommission flow ${data.flow_id} initialized successfully`
      );
    },
    onError: (error) => {
      console.error("❌ Failed to initialize decommission flow:", error);
    },
  });
}

/**
 * Hook for resuming paused decommission flow
 *
 * Endpoint: POST /api/v1/decommission-flow/{flow_id}/resume
 * Per ADR-006: Updates both master and child flow state atomically
 *
 * @returns Mutation object with mutate function (flowId, params)
 */
export function useResumeDecommissionFlow(): UseMutationResult<
  DecommissionFlowResponse,
  Error,
  { flowId: string; params?: ResumeDecommissionFlowRequest },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ flowId, params = {} }) =>
      decommissionFlowService.resumeDecommissionFlow(flowId, params),
    onSuccess: (data, variables) => {
      // Invalidate status to trigger refetch
      queryClient.invalidateQueries({
        queryKey: decommissionFlowKeys.status(variables.flowId),
      });

      console.log(
        `✅ Decommission flow ${variables.flowId} resumed from ${data.current_phase}`
      );
    },
    onError: (error, variables) => {
      console.error(
        `❌ Failed to resume decommission flow ${variables.flowId}:`,
        error
      );
    },
  });
}

/**
 * Hook for updating decommission phase status
 *
 * Endpoint: POST /api/v1/decommission-flow/{flow_id}/phases/{phase_name}
 * Per ADR-006: Updates both master and child flow state atomically
 *
 * @returns Mutation object with mutate function (flowId, phaseName, params)
 */
export function useUpdatePhaseStatus(): UseMutationResult<
  DecommissionFlowStatusResponse,
  Error,
  { flowId: string; phaseName: DecommissionPhase; params: UpdatePhaseRequest },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ flowId, phaseName, params }) =>
      decommissionFlowService.updatePhaseStatus(flowId, phaseName, params),
    onSuccess: (data, variables) => {
      // Update status cache optimistically
      queryClient.setQueryData(
        decommissionFlowKeys.status(variables.flowId),
        data
      );

      // Trigger refetch to get latest state
      queryClient.invalidateQueries({
        queryKey: decommissionFlowKeys.status(variables.flowId),
      });

      console.log(
        `✅ Updated decommission phase ${variables.phaseName} to ${variables.params.phase_status}`
      );
    },
    onError: (error, variables) => {
      console.error(
        `❌ Failed to update decommission phase ${variables.phaseName}:`,
        error
      );
    },
  });
}

/**
 * Hook for pausing running decommission flow
 *
 * Endpoint: POST /api/v1/decommission-flow/{flow_id}/pause
 * Per ADR-006: Updates both master and child flow state atomically
 *
 * @returns Mutation object with mutate function (flowId)
 */
export function usePauseDecommissionFlow(): UseMutationResult<
  DecommissionFlowOperationResponse,
  Error,
  string,
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (flowId: string) =>
      decommissionFlowService.pauseDecommissionFlow(flowId),
    onSuccess: (data, flowId) => {
      // Update status cache optimistically
      queryClient.setQueryData(
        decommissionFlowKeys.status(flowId),
        (oldData: DecommissionFlowStatusResponse | undefined) => {
          if (!oldData) return oldData;

          return {
            ...oldData,
            status: data.status,
            current_phase: data.current_phase || oldData.current_phase,
            updated_at: new Date().toISOString(),
          };
        }
      );

      // Trigger refetch to get latest state
      queryClient.invalidateQueries({
        queryKey: decommissionFlowKeys.status(flowId),
      });

      console.log(`⏸️ Decommission flow ${flowId} paused at ${data.current_phase}`);
    },
    onError: (error, flowId) => {
      console.error(`❌ Failed to pause decommission flow ${flowId}:`, error);
    },
  });
}

/**
 * Hook for canceling decommission flow
 *
 * Endpoint: POST /api/v1/decommission-flow/{flow_id}/cancel
 * Per ADR-006: Updates both master and child flow state atomically
 *
 * @returns Mutation object with mutate function (flowId)
 */
export function useCancelDecommissionFlow(): UseMutationResult<
  DecommissionFlowOperationResponse,
  Error,
  string,
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (flowId: string) =>
      decommissionFlowService.cancelDecommissionFlow(flowId),
    onSuccess: (data, flowId) => {
      // Update status cache to show cancelled state
      queryClient.setQueryData(
        decommissionFlowKeys.status(flowId),
        (oldData: DecommissionFlowStatusResponse | undefined) => {
          if (!oldData) return oldData;

          return {
            ...oldData,
            status: data.status,
            updated_at: new Date().toISOString(),
          };
        }
      );

      // Invalidate queries to reflect cancellation
      queryClient.invalidateQueries({
        queryKey: decommissionFlowKeys.status(flowId),
      });
      queryClient.invalidateQueries({
        queryKey: decommissionFlowKeys.lists(),
      });

      console.log(`🚫 Decommission flow ${flowId} cancelled successfully`);
    },
    onError: (error, flowId) => {
      console.error(`❌ Failed to cancel decommission flow ${flowId}:`, error);
    },
  });
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Helper to determine if flow is actively processing
 * @param status - Flow status (snake_case)
 * @returns True if flow is in an active processing state
 */
export function isFlowActive(
  status: string | undefined
): boolean {
  if (!status) return false;

  return (
    status === "decommission_planning" ||
    status === "data_migration" ||
    status === "system_shutdown"
  );
}

/**
 * Helper to determine if flow is completed
 * @param status - Flow status (snake_case)
 * @returns True if flow has completed successfully
 */
export function isFlowCompleted(status: string | undefined): boolean {
  return status === "completed";
}

/**
 * Helper to determine if flow has failed
 * @param status - Flow status (snake_case)
 * @returns True if flow has failed
 */
export function isFlowFailed(status: string | undefined): boolean {
  return status === "failed";
}

/**
 * Helper to determine if flow is paused
 * @param status - Flow status (snake_case)
 * @returns True if flow is paused (waiting for user input)
 */
export function isFlowPaused(status: string | undefined): boolean {
  return status === "paused";
}

/**
 * Helper to get phase display name
 * @param phase - Phase name (snake_case per ADR-027)
 * @returns User-friendly display name
 */
export function getPhaseDisplayName(phase: string): string {
  const displayNames: Record<string, string> = {
    decommission_planning: "Decommission Planning",
    data_migration: "Data Migration",
    system_shutdown: "System Shutdown",
  };

  return displayNames[phase] || phase;
}

/**
 * Helper to calculate overall progress percentage
 * @param status - Flow status response (all fields snake_case)
 * @returns Progress percentage (0-100)
 */
export function calculateProgress(
  status: DecommissionFlowStatusResponse | undefined
): number {
  if (!status) return 0;

  const phaseProgress = status.phase_progress;
  let completedPhases = 0;
  const totalPhases = 3; // decommission_planning, data_migration, system_shutdown

  if (phaseProgress.decommission_planning === "completed") completedPhases++;
  if (phaseProgress.data_migration === "completed") completedPhases++;
  if (phaseProgress.system_shutdown === "completed") completedPhases++;

  // Add partial credit for current phase if in progress
  if (status.current_phase === "decommission_planning" && completedPhases === 0) {
    return 15; // 15% progress in first phase
  }
  if (status.current_phase === "data_migration" && completedPhases === 1) {
    return 50; // 50% progress in second phase
  }
  if (status.current_phase === "system_shutdown" && completedPhases === 2) {
    return 85; // 85% progress in final phase
  }

  // Full completion
  if (completedPhases === totalPhases) {
    return 100;
  }

  // Calculate percentage based on completed phases
  return Math.round((completedPhases / totalPhases) * 100);
}

// ============================================================================
// QUERY HOOKS (List & Eligible Systems)
// ============================================================================

/**
 * Hook for fetching list of all decommission flows
 *
 * Endpoint: GET /api/v1/decommission-flow/
 * Per ADR-006: Queries child flows (decommission_flows table)
 *
 * @param params - Optional filters (status, limit, offset)
 * @param options - Additional query options
 * @returns Query result with array of flow list items (all fields in snake_case)
 */
export function useDecommissionFlows(
  params?: {
    status?: string;
    limit?: number;
    offset?: number;
  },
  options?: {
    enabled?: boolean;
    refetchInterval?: number | false;
  }
): UseQueryResult<DecommissionFlowListItem[], Error> {
  return useQuery({
    queryKey: decommissionFlowKeys.list(params || {}),
    queryFn: () => decommissionFlowService.listDecommissionFlows(params),
    enabled: options?.enabled ?? true,
    refetchInterval: options?.refetchInterval ?? false,
    // Keep previous data while refetching
    placeholderData: (previousData) => previousData,
  });
}

/**
 * Hook for fetching systems eligible for decommission
 *
 * Endpoint: GET /api/v1/decommission-flow/eligible-systems
 * Returns assets with 6R strategy = "Retire" or marked decommission_eligible
 *
 * @param options - Additional query options
 * @returns Query result with array of eligible systems (all fields in snake_case)
 */
export function useEligibleSystems(options?: {
  enabled?: boolean;
  refetchInterval?: number | false;
}): UseQueryResult<EligibleSystemResponse[], Error> {
  return useQuery({
    queryKey: [...decommissionFlowKeys.all, "eligible-systems"] as const,
    queryFn: () => decommissionFlowService.getEligibleSystems(),
    enabled: options?.enabled ?? true,
    refetchInterval: options?.refetchInterval ?? false,
    // Keep previous data while refetching
    placeholderData: (previousData) => previousData,
  });
}
