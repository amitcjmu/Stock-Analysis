/**
 * Decommission Flow Hooks Module
 *
 * Main export file for decommission flow React Query hooks and utilities.
 * All field names use snake_case to match backend (no transformations).
 */

// Export all hooks
export {
  useDecommissionFlowStatus,
  useInitializeDecommissionFlow,
  useResumeDecommissionFlow,
  usePauseDecommissionFlow,
  useCancelDecommissionFlow,
  useDecommissionFlows,
  useEligibleSystems,
  decommissionFlowKeys,
} from "./useDecommissionFlow";

// Export utility functions
export {
  isFlowActive,
  isFlowCompleted,
  isFlowFailed,
  isFlowPaused,
  getPhaseDisplayName,
  calculateProgress,
} from "./useDecommissionFlow";

// Re-export types from API service for convenience
export type {
  DecommissionPhase,
  DecommissionFlowStatus,
  DecommissionStrategy,
  InitializeDecommissionFlowRequest,
  DecommissionFlowResponse,
  DecommissionFlowStatusResponse,
  ResumeDecommissionFlowRequest,
  DecommissionFlowOperationResponse,
  DecommissionFlowListItem,
  EligibleSystemResponse,
} from "../../lib/api/decommissionFlowService";

// Re-export API service for direct access if needed
export { decommissionFlowService } from "../../lib/api/decommissionFlowService";
