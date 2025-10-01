/**
 * Collection State HTTP Polling Hook
 *
 * Replaces WebSocket functionality with HTTP polling for Vercel/Railway deployment.
 * Uses React Query with dynamic intervals based on flow state.
 *
 * CC Generated Collection State Polling Hook
 */

import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect } from 'react';
import { apiCall } from '@/config/api';

interface CollectionFlowState {
  flow_id?: string;
  id: string;
  status: string;
  current_phase?: string;
  progress?: number;
  progress_percentage?: number;
  message?: string;
  last_updated?: string;
  updated_at?: string;
  questionnaire_count?: number;
  error?: string;
  [key: string]: unknown; // Allow additional fields from backend
}

interface CollectionStatePollingOptions {
  flowId?: string;
  enabled?: boolean;
  onStatusUpdate?: (state: CollectionFlowState) => void;
  onQuestionnaireReady?: (state: CollectionFlowState) => void;
  onError?: (error: string) => void;
}

/**
 * Hook for polling collection flow state using HTTP with smart intervals
 */
interface UseCollectionStatePollingReturn {
  flowState: CollectionFlowState | undefined;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  isConnected: boolean;
  isActive: boolean;
  requestStatusUpdate: () => Promise<unknown>;
  lastUpdate: CollectionFlowState | undefined;
  flowId: string | undefined;
}

export const useCollectionStatePolling = (
  options: CollectionStatePollingOptions = {}
): UseCollectionStatePollingReturn => {
  const { flowId, enabled = true, onStatusUpdate, onQuestionnaireReady, onError } = options;

  // Query for flow state with smart polling intervals
  const {
    data: flowState,
    error,
    isLoading,
    isError,
    refetch
  } = useQuery({
    queryKey: ['collection-flow-state', flowId],
    queryFn: async (): Promise<CollectionFlowState> => {
      if (!flowId) {
        throw new Error('Flow ID is required');
      }

      const response = await apiCall(`/collection/flows/${flowId}`, {
        method: 'GET'
      });

      return response;
    },
    enabled: enabled && !!flowId,
    refetchInterval: (data) => {
      if (!data) return false;

      // Stop polling if flow is completed or failed
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'error') {
        return false;
      }

      // Active phases: poll every 2 seconds
      const activePhases = ['running', 'processing', 'executing', 'generating'];
      if (activePhases.includes(data.status) ||
          (data.current_phase && activePhases.includes(data.current_phase))) {
        return 2000; // 2 seconds for active processing
      }

      // Waiting/idle phases: poll every 15 seconds
      return 15000; // 15 seconds for waiting states
    },
    staleTime: 0, // Always consider stale for real-time updates
    retry: (failureCount, error: unknown) => {
      // Don't retry on 404 (flow not found)
      if (error && typeof error === 'object' && 'status' in error &&
          (error as { status: number }).status === 404) {
        return false;
      }

      // Retry up to 3 times for other errors
      return failureCount < 3;
    },
    retryDelay: (attemptIndex) => {
      // Exponential backoff: 1s, 2s, 4s
      return Math.min(1000 * 2 ** attemptIndex, 30000);
    }
  });

  // Handle state updates
  useEffect(() => {
    if (!flowState) return;

    // Trigger status update callback
    onStatusUpdate?.(flowState);

    // Check if questionnaires are ready
    if (flowState.questionnaire_count && flowState.questionnaire_count > 0) {
      onQuestionnaireReady?.(flowState);
    }

    // Handle errors
    if (flowState.error || flowState.status === 'error' || flowState.status === 'failed') {
      onError?.(flowState.error || `Flow ${flowState.status}: ${flowState.message}`);
    }
  }, [flowState, onStatusUpdate, onQuestionnaireReady, onError]);

  // Handle query errors
  useEffect(() => {
    if (isError && error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown polling error';
      onError?.(errorMessage);
    }
  }, [isError, error, onError]);

  // Manual status update function
  const requestStatusUpdate = useCallback(() => {
    return refetch();
  }, [refetch]);

  return {
    // State data
    flowState,
    isLoading,
    isError,
    error,

    // Status flags (compatibility with WebSocket interface)
    isConnected: !isError && !!flowState,
    isActive: enabled && !!flowId,

    // Actions
    requestStatusUpdate,

    // Compatibility with WebSocket interface
    lastUpdate: flowState,

    // For debugging
    flowId
  };
};

export default useCollectionStatePolling;
