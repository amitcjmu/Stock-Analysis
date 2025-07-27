/**
 * Consolidated Discovery Flow Status Hook
 *
 * This hook replaces multiple duplicate implementations:
 * - SimplifiedFlowStatus component's internal fetching
 * - useUnifiedDiscoveryFlow's status polling
 * - useCMDBImport's flow status polling
 *
 * Features:
 * - Configurable polling intervals
 * - Automatic polling stop for terminal states
 * - Proper handling of waiting_for_approval status
 * - Single source of truth for flow status
 */

import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { masterFlowService } from '@/services/api/masterFlowService';
import { useAuth } from '@/contexts/AuthContext';
import type { FlowStatusResponse } from '@/types/api';

interface UseDiscoveryFlowStatusOptions {
  /** Flow ID to monitor */
  flowId: string | null;
  /** Enable/disable polling */
  enabled?: boolean;
  /** Polling interval in milliseconds (default: 30000 for active flows) */
  pollingInterval?: number;
  /** Callback when status changes to waiting_for_approval */
  onWaitingForApproval?: () => void;
  /** Callback when flow completes */
  onComplete?: () => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

// Terminal states that should stop polling
const TERMINAL_STATES = ['completed', 'failed', 'cancelled', 'aborted', 'deleted'];

// States that indicate waiting for user action
const WAITING_STATES = ['waiting_for_approval', 'paused'];

// Active processing states that should continue polling
const ACTIVE_STATES = ['running', 'processing', 'active', 'in_progress'];

/**
 * Determines if polling should continue based on flow status
 */
export const shouldPollFlow = (status?: FlowStatusResponse): boolean => {
  if (!status) return false;

  // Stop polling for terminal states
  if (TERMINAL_STATES.includes(status.status)) return false;

  // Stop polling when waiting for user action
  if (WAITING_STATES.includes(status.status)) return false;
  if (status.awaitingUserApproval) return false;

  // Continue polling only for active states
  return ACTIVE_STATES.includes(status.status);
};

/**
 * Consolidated hook for monitoring discovery flow status
 */
export const useDiscoveryFlowStatus = ({
  flowId,
  enabled = true,
  pollingInterval = 30000, // 30 seconds default
  onWaitingForApproval,
  onComplete,
  onError
}: UseDiscoveryFlowStatusOptions): UseQueryResult<FlowStatusResponse, Error> => {
  const { client, engagement } = useAuth();

  const query = useQuery<FlowStatusResponse, Error>({
    queryKey: ['flow-status', flowId],
    queryFn: async () => {
      if (!flowId) throw new Error('Flow ID is required');

      const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
      const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";

      return await masterFlowService.getFlowStatus(flowId, clientAccountId, engagementId);
    },
    enabled: enabled && !!flowId,
    refetchInterval: (data) => {
      const status = data as FlowStatusResponse | undefined;

      // Check if we should continue polling
      if (!shouldPollFlow(status)) {
        // Trigger callbacks for state changes
        if (status?.status === 'waiting_for_approval' || status?.awaitingUserApproval) {
          onWaitingForApproval?.();
        } else if (status?.status === 'completed') {
          onComplete?.();
        }
        return false; // Stop polling
      }

      return pollingInterval;
    },
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: false,
    staleTime: 10000, // Consider data stale after 10 seconds
    retry: 2,
    onError: (error) => {
      console.error('Error fetching flow status:', error);
      onError?.(error);
    }
  });

  return query;
};

/**
 * Hook specifically for components that need more frequent updates
 * (e.g., visual progress indicators)
 */
export const useDiscoveryFlowStatusVisual = (flowId: string | null): unknown => {
  return useDiscoveryFlowStatus({
    flowId,
    pollingInterval: 5000, // 5 seconds for visual updates
  });
};

/**
 * Hook for dashboard views that need less frequent updates
 */
export const useDiscoveryFlowStatusDashboard = (flowId: string | null): unknown => {
  return useDiscoveryFlowStatus({
    flowId,
    pollingInterval: 60000, // 1 minute for dashboard
  });
};
