/**
 * useCollectionFlowQuery Hook
 * Fetches collection flow details and application selection status
 */

import { useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { debugLog, debugWarn, debugError } from '@/utils/debug';

interface CollectionFlowConfig {
  selected_application_ids?: string[];
  applications?: string[];
  application_ids?: string[];
  has_applications?: boolean;
}

interface CollectionFlow {
  flow_id?: string;
  id?: string;
  progress?: number;
  current_phase?: string;
  collection_config?: CollectionFlowConfig;
}

interface UseCollectionFlowQueryProps {
  activeFlowId: string | null;
}

interface UseCollectionFlowQueryReturn {
  currentCollectionFlow: CollectionFlow | null;
  isLoadingFlow: boolean;
  refetchCollectionFlow: () => void;
  hasApplicationsSelected: (flow: CollectionFlow | null) => boolean;
}

/**
 * Hook for querying collection flow details and application selection
 */
export const useCollectionFlowQuery = ({
  activeFlowId,
}: UseCollectionFlowQueryProps): UseCollectionFlowQueryReturn => {
  // Check if the current Collection flow has application selection
  const { data: currentCollectionFlow, isLoading: isLoadingFlow, refetch: refetchCollectionFlow } = useQuery({
    queryKey: ['collection-flow', activeFlowId],
    queryFn: async () => {
      if (!activeFlowId) return null;
      try {
        debugLog('🔍 Fetching collection flow details for application check:', activeFlowId);
        return await apiCall(`/collection/flows/${activeFlowId}`);
      } catch (error) {
        debugError('Failed to fetch collection flow:', error);
        return null;
      }
    },
    enabled: !!activeFlowId,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  });

  // Function to detect if applications are selected in the collection flow
  const hasApplicationsSelected = useCallback((collectionFlow: CollectionFlow | null): boolean => {
    if (!collectionFlow) return false;

    const config = collectionFlow.collection_config || {};
    const selectedApps =
      config.selected_application_ids ||
      config.applications ||
      config.application_ids ||
      [];

    const hasApps = Array.isArray(selectedApps) && selectedApps.length > 0;
    const hasAppsFlag = config.has_applications === true;

    return hasApps || hasAppsFlag;
  }, []);

  return {
    currentCollectionFlow: currentCollectionFlow || null,
    isLoadingFlow,
    refetchCollectionFlow,
    hasApplicationsSelected,
  };
};
