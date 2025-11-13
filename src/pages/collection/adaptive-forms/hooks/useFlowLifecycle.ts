/**
 * useFlowLifecycle Hook
 * Manages flow initialization, deletion, and lifecycle effects
 * Extracted from AdaptiveForms.tsx - Flow lifecycle management
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from '@/components/ui/use-toast';
import { useFlowDeletion } from '@/hooks/useFlowDeletion';
import type { useAuth } from '@/contexts/AuthContext';
import { debugLog, debugWarn, debugError } from '@/utils/debug';

interface CollectionFlow {
  flow_id?: string;
  id?: string;
  status?: string;
  current_phase?: string;
}

interface UseFlowLifecycleProps {
  activeFlowId: string | null;
  client: ReturnType<typeof useAuth>['client'];
  engagement: ReturnType<typeof useAuth>['engagement'];
  user: ReturnType<typeof useAuth>['user'];
  blockingFlows: CollectionFlow[];
  refetchFlows: () => void;
}

interface UseFlowLifecycleReturn {
  deletingFlows: Set<string>;
  setDeletingFlows: React.Dispatch<React.SetStateAction<Set<string>>>;
  hasJustDeleted: boolean;
  setHasJustDeleted: React.Dispatch<React.SetStateAction<boolean>>;
  deletionState: ReturnType<typeof useFlowDeletion>[0];
  deletionActions: ReturnType<typeof useFlowDeletion>[1];
  handleContinueFlow: (flowId: string) => Promise<void>;
  handleDeleteFlow: (flowId: string) => Promise<void>;
  handleViewFlowDetails: (flowId: string, phase: string) => void;
}

/**
 * Hook for managing flow lifecycle (deletion, continuation, navigation)
 */
export const useFlowLifecycle = ({
  activeFlowId,
  client,
  engagement,
  user,
  blockingFlows,
  refetchFlows,
}: UseFlowLifecycleProps): UseFlowLifecycleReturn => {
  const navigate = useNavigate();

  // State to track flows being deleted
  const [deletingFlows, setDeletingFlows] = useState<Set<string>>(new Set());
  const [hasJustDeleted, setHasJustDeleted] = useState(false);

  // Use the flow deletion hook with modal confirmation
  const [deletionState, deletionActions] = useFlowDeletion(
    async (result) => {
      // Refresh flows after successful deletion
      await refetchFlows();
      setHasJustDeleted(true);

      // Remove from deleting set only for successfully deleted flows
      result.results.forEach((res) => {
        const normalizedFlowId = String(res.flowId || '');
        if (res.success) {
          setDeletingFlows((prev) => {
            const newSet = new Set(prev);
            newSet.delete(normalizedFlowId);
            return newSet;
          });
        } else {
          // Failed deletion - unhide the flow
          setDeletingFlows((prev) => {
            const newSet = new Set(prev);
            newSet.delete(normalizedFlowId);
            return newSet;
          });
        }
      });
    },
    (error) => {
      debugError('Flow deletion failed:', error);

      // On error, unhide all flows that were being deleted
      deletionState.candidates.forEach((flowId) => {
        const normalizedFlowId = String(flowId || '');
        setDeletingFlows((prev) => {
          const newSet = new Set(prev);
          newSet.delete(normalizedFlowId);
          return newSet;
        });
      });

      toast({
        title: 'Error',
        description: error.message || 'Failed to delete flow',
        variant: 'destructive',
      });
    }
  );

  // Flow management handlers
  const handleContinueFlow = async (flowId: string): Promise<void> => {
    try {
      if (!flowId) {
        debugError('Cannot continue flow: flowId is missing');
        return;
      }
      // Navigate to adaptive forms page with flowId to resume the flow
      navigate(`/collection/adaptive-forms?flowId=${encodeURIComponent(flowId)}`);
    } catch (error) {
      debugError('Failed to continue collection flow:', error);
    }
  };

  const handleDeleteFlow = async (flowId: string): Promise<void> => {
    if (!client?.id) {
      toast({
        title: 'Error',
        description: 'Client context is required for flow deletion',
        variant: 'destructive',
      });
      return;
    }

    // Find the flow data from blockingFlows to pass to deletion modal
    const flowToDelete = blockingFlows.find(f =>
      String(f.flow_id || f.id) === String(flowId)
    );

    // Request deletion with modal confirmation, passing flow data for display
    await deletionActions.requestDeletion(
      [flowId],
      client.id,
      engagement?.id,
      'manual',
      user?.id,
      flowToDelete
    );
  };

  const handleViewFlowDetails = (flowId: string, phase: string): void => {
    navigate(`/collection/progress/${flowId}`);
  };

  return {
    deletingFlows,
    setDeletingFlows,
    hasJustDeleted,
    setHasJustDeleted,
    deletionState,
    deletionActions,
    handleContinueFlow,
    handleDeleteFlow,
    handleViewFlowDetails,
  };
};
