/**
 * React hook for flow deletion with modal confirmation
 * Replaces native browser dialogs with React components
 * Fixes DISC-011: Browser native confirm dialog blocking UI access
 */

import type { useState } from 'react'
import { useCallback } from 'react'
import type { FlowDeletionRequest, FlowDeletionResult , FlowDeletionCandidate } from '@/services/flowDeletionService'
import { flowDeletionService } from '@/services/flowDeletionService'

export interface UseFlowDeletionState {
  isModalOpen: boolean;
  candidates: FlowDeletionCandidate[];
  deletionSource: FlowDeletionRequest['deletion_source'];
  isDeleting: boolean;
}

export interface UseFlowDeletionActions {
  requestDeletion: (
    flowIds: string[],
    clientAccountId: string,
    engagementId?: string,
    deletion_source?: FlowDeletionRequest['deletion_source'],
    user_id?: string
  ) => Promise<void>;
  confirmDeletion: () => Promise<void>;
  cancelDeletion: () => void;
}

export function useFlowDeletion(
  onDeletionComplete?: (result: FlowDeletionResult) => void,
  onDeletionError?: (error: Error) => void
): [UseFlowDeletionState, UseFlowDeletionActions] {
  const [state, setState] = useState<UseFlowDeletionState>({
    isModalOpen: false,
    candidates: [],
    deletionSource: 'manual',
    isDeleting: false
  });

  // Store deletion parameters for when user confirms
  const [pendingDeletion, setPendingDeletion] = useState<{
    flowIds: string[];
    clientAccountId: string;
    engagementId?: string;
    user_id?: string;
  } | null>(null);

  const requestDeletion = useCallback(async (
    flowIds: string[],
    clientAccountId: string,
    engagementId?: string,
    deletion_source: FlowDeletionRequest['deletion_source'] = 'manual',
    user_id?: string
  ) => {
    try {
      // Get flow details for confirmation
      const candidates = await flowDeletionService.identifyDeletionCandidates(
        clientAccountId,
        engagementId
      );

      // Filter to only requested flows
      const requestedCandidates = candidates.filter(c => 
        flowIds.includes(c.flowId)
      );

      // If no candidates found, create minimal candidates for requested IDs
      if (requestedCandidates.length === 0 && flowIds.length > 0) {
        flowIds.forEach(flowId => {
          requestedCandidates.push({
            flowId,
            flow_name: 'Unknown Flow',
            status: 'unknown',
            current_phase: 'unknown',
            progress_percentage: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            reason_for_deletion: deletion_source === 'manual' ? 'user_requested' : 'cleanup_recommended',
            auto_cleanup_eligible: true,
            deletion_impact: {
              data_to_delete: {
                workflow_state: 1,
                import_sessions: 0,
                field_mappings: 0,
                assets: 0,
                dependencies: 0,
                shared_memory_refs: 0
              },
              estimated_cleanup_time: '30s'
            }
          });
        });
      }

      // Store deletion parameters
      setPendingDeletion({
        flowIds,
        clientAccountId,
        engagementId,
        user_id
      });

      // Update state to show modal
      setState({
        isModalOpen: true,
        candidates: requestedCandidates,
        deletionSource: deletion_source,
        isDeleting: false
      });
    } catch (error) {
      console.error('Failed to prepare deletion request:', error);
      if (onDeletionError) {
        onDeletionError(error instanceof Error ? error : new Error('Failed to prepare deletion'));
      }
    }
  }, [onDeletionError]);

  const confirmDeletion = useCallback(async () => {
    if (!pendingDeletion || state.candidates.length === 0) {
      return;
    }

    setState(prev => ({ ...prev, isDeleting: true }));

    try {
      // Call the service with skipBrowserConfirm=true since we're using modal
      const result = await flowDeletionService.requestFlowDeletion(
        pendingDeletion.flowIds,
        pendingDeletion.clientAccountId,
        pendingDeletion.engagementId,
        state.deletionSource,
        pendingDeletion.user_id,
        true // skipBrowserConfirm - we already have user confirmation from modal
      );

      // Close modal
      setState({
        isModalOpen: false,
        candidates: [],
        deletionSource: 'manual',
        isDeleting: false
      });
      setPendingDeletion(null);

      // Notify completion
      if (onDeletionComplete) {
        onDeletionComplete(result);
      }
    } catch (error) {
      console.error('Flow deletion failed:', error);
      setState(prev => ({ ...prev, isDeleting: false }));
      if (onDeletionError) {
        onDeletionError(error instanceof Error ? error : new Error('Deletion failed'));
      }
    }
  }, [pendingDeletion, state.candidates, state.deletionSource, onDeletionComplete, onDeletionError]);

  const cancelDeletion = useCallback(() => {
    setState({
      isModalOpen: false,
      candidates: [],
      deletionSource: 'manual',
      isDeleting: false
    });
    setPendingDeletion(null);
  }, []);

  const actions: UseFlowDeletionActions = {
    requestDeletion,
    confirmDeletion,
    cancelDeletion
  };

  return [state, actions];
}

/**
 * Hook for flow cleanup recommendations
 * Provides cleanup recommendations without automatic execution
 */
export function useFlowCleanup() {
  const [recommendations, setRecommendations] = useState<FlowDeletionCandidate[]>([]);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
  const [isExecutingCleanup, setIsExecutingCleanup] = useState(false);

  const getCleanupRecommendations = useCallback(async (
    clientAccountId: string,
    engagementId?: string,
    flowType?: string
  ) => {
    setIsLoadingRecommendations(true);
    try {
      const candidates = await flowDeletionService.identifyDeletionCandidates(
        clientAccountId,
        engagementId,
        flowType
      );
      setRecommendations(candidates);
    } catch (error) {
      console.error('Failed to get cleanup recommendations:', error);
      setRecommendations([]);
    } finally {
      setIsLoadingRecommendations(false);
    }
  }, []);

  return {
    recommendations,
    isLoadingRecommendations,
    isExecutingCleanup,
    getCleanupRecommendations
  };
}