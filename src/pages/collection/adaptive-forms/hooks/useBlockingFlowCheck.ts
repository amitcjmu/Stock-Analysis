/**
 * useBlockingFlowCheck Hook
 * Checks for incomplete flows that would block new collection processes
 */

import { useMemo } from 'react';
import {
  useIncompleteCollectionFlows,
  useCollectionFlowManagement,
} from '@/hooks/collection/useCollectionFlowManagement';

interface CollectionFlow {
  flow_id?: string;
  id?: string;
  progress?: number;
  current_phase?: string;
  collection_config?: {
    selected_application_ids?: string[];
    applications?: string[];
    application_ids?: string[];
    has_applications?: boolean;
  };
}

interface UseBlockingFlowCheckProps {
  flowId: string | null;
}

interface UseBlockingFlowCheckReturn {
  skipIncompleteCheck: boolean;
  checkingFlows: boolean;
  hasBlockingFlows: boolean;
  shouldAutoInitialize: boolean;
  incompleteFlows: CollectionFlow[];
  blockingFlows: CollectionFlow[];
  refetchFlows: () => void;
  deleteFlow: ReturnType<typeof useCollectionFlowManagement>['deleteFlow'];
  isDeleting: ReturnType<typeof useCollectionFlowManagement>['isDeleting'];
}

/**
 * Hook for checking incomplete flows and determining if auto-initialization should occur
 */
export const useBlockingFlowCheck = ({
  flowId,
}: UseBlockingFlowCheckProps): UseBlockingFlowCheckReturn => {
  // Check for incomplete flows that would block new collection processes
  // Skip checking if we're continuing a specific flow (flowId provided)
  const skipIncompleteCheck = !!flowId;
  const {
    data: incompleteFlows = [],
    isLoading: checkingFlows,
    refetch: refetchFlows,
  } = useIncompleteCollectionFlows(); // Always call the hook to maintain consistent hook order

  // Use collection flow management hook for flow operations
  const { deleteFlow, isDeleting } = useCollectionFlowManagement();

  // Calculate autoInitialize value
  const hasBlockingFlows = !skipIncompleteCheck && incompleteFlows.length > 0;
  const shouldAutoInitialize = !checkingFlows && (!hasBlockingFlows || !!flowId);

  // Filter out the current flow and flows being deleted from the blocking check
  const blockingFlows = useMemo(() => {
    if (skipIncompleteCheck) return [];

    return incompleteFlows.filter((flow) => {
      const id = String(flow.flow_id || flow.id || '');
      const normalizedFlowId = String(flowId || '');
      if (flowId && id === normalizedFlowId) {
        return false;
      }
      return id !== normalizedFlowId;
    });
  }, [skipIncompleteCheck, incompleteFlows, flowId]);

  return {
    skipIncompleteCheck,
    checkingFlows,
    hasBlockingFlows,
    shouldAutoInitialize,
    incompleteFlows,
    blockingFlows,
    refetchFlows,
    deleteFlow,
    isDeleting,
  };
};
