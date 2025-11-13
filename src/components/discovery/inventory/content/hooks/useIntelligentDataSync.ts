import React, { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

// Local interface definition to avoid circular imports
interface UnifiedDiscoveryFlowState {
  flow_id: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  current_phase: string;
  phase_completion: Record<string, boolean>;
  phase_state?: Record<string, unknown>;
  crew_status: Record<string, any>;
  raw_data: any[];
  field_mappings: Record<string, any>;
  cleaned_data: any[];
  asset_inventory: Record<string, any>;
  dependencies: Record<string, any>;
  technical_debt: Record<string, any>;
  agent_insights: any[];
  status: string;
  progress_percentage: number;
  errors: string[];
  warnings: string[];
  created_at: string;
  updated_at: string;
}

interface UseIntelligentDataSyncProps {
  flowId?: string;
  flow: UnifiedDiscoveryFlowState | null;
  clientId?: number;
  engagementId?: number;
  assetsLength: number;
  assetsLoading: boolean;
  refetchAssets: () => Promise<any>;
  refreshFlow: () => Promise<any>;
}

interface ConflictDetectionState {
  hasCheckedForConflicts: boolean;
  lastConflictCheck: number;
  conflictCheckInterval: NodeJS.Timeout | null;
}

/**
 * Intelligent data synchronization hook that replaces forced page reloads
 * with proper React Query state management and smart polling
 */
export const useIntelligentDataSync = ({
  flowId,
  flow,
  clientId,
  engagementId,
  assetsLength,
  assetsLoading,
  refetchAssets,
  refreshFlow
}: UseIntelligentDataSyncProps) => {
  const queryClient = useQueryClient();

  // State for conflict detection
  const conflictStateRef = useRef<ConflictDetectionState>({
    hasCheckedForConflicts: false,
    lastConflictCheck: 0,
    conflictCheckInterval: null
  });

  // Smart query invalidation strategy
  const invalidateRelevantQueries = useCallback(async () => {
    if (!flowId || !clientId || !engagementId) return;

    console.log('🔄 [DataSync] Invalidating relevant queries...');

    // Invalidate flow state query
    await queryClient.invalidateQueries({
      queryKey: ['unifiedDiscoveryFlow', flowId, clientId, engagementId],
      refetchType: 'active'
    });

    // Invalidate assets queries for both view modes
    await queryClient.invalidateQueries({
      queryKey: ['discovery-assets'],
      refetchType: 'active'
    });

    // Trigger manual refetch for immediate updates
    await Promise.all([
      refetchAssets(),
      refreshFlow()
    ]);
  }, [queryClient, flowId, clientId, engagementId, refetchAssets, refreshFlow]);

  // Smart conflict detection with intelligent polling
  const startConflictDetectionPolling = useCallback(() => {
    if (conflictStateRef.current.conflictCheckInterval) {
      return; // Already polling
    }

    console.log('🔍 [DataSync] Starting intelligent conflict detection polling...');

    const pollForConflicts = async () => {
      const now = Date.now();
      const timeSinceLastCheck = now - conflictStateRef.current.lastConflictCheck;

      // Only check every 10 seconds to avoid excessive API calls
      if (timeSinceLastCheck < 10000) {
        return;
      }

      conflictStateRef.current.lastConflictCheck = now;

      try {
        // Check if we're in a state where conflicts might exist
        const isInAssetInventoryPhase = flow?.current_phase === 'asset_inventory';
        const hasNoAssets = assetsLength === 0;
        const hasRawData = flow?.raw_data && flow.raw_data.length > 0;
        const noConflictsFlag = !flow?.phase_state?.conflict_resolution_pending;

        console.log('🔍 [DataSync] Conflict detection check:', {
          isInAssetInventoryPhase,
          hasNoAssets,
          hasRawData,
          noConflictsFlag,
          shouldCheck: isInAssetInventoryPhase && hasNoAssets && hasRawData && noConflictsFlag
        });

        if (isInAssetInventoryPhase && hasNoAssets && hasRawData && noConflictsFlag) {
          console.log('🔄 [DataSync] Potential conflicts detected, refreshing data...');
          await invalidateRelevantQueries();
        }
      } catch (error) {
        console.error('❌ [DataSync] Error during conflict detection:', error);
      }
    };

    // Start polling every 15 seconds
    conflictStateRef.current.conflictCheckInterval = setInterval(pollForConflicts, 15000);

    // Initial check after 5 seconds
    setTimeout(pollForConflicts, 5000);
  }, [flow, assetsLength, invalidateRelevantQueries]);

  // Stop conflict detection polling
  const stopConflictDetectionPolling = useCallback(() => {
    if (conflictStateRef.current.conflictCheckInterval) {
      console.log('🛑 [DataSync] Stopping conflict detection polling...');
      clearInterval(conflictStateRef.current.conflictCheckInterval);
      conflictStateRef.current.conflictCheckInterval = null;
    }
  }, []);

  // Main effect for intelligent data synchronization
  useEffect(() => {
    if (!flowId || !flow || assetsLoading) {
      return;
    }

    console.log('🔄 [DataSync] Setting up intelligent data sync:', {
      flowId,
      currentPhase: flow.current_phase,
      assetsLength,
      hasRawData: !!(flow.raw_data && flow.raw_data.length > 0),
      conflictFlag: flow.phase_state?.conflict_resolution_pending
    });

    // Check if we need to start conflict detection polling
    const isInAssetInventoryPhase = flow.current_phase === 'asset_inventory';
    const hasNoAssets = assetsLength === 0;
    const hasRawData = flow.raw_data && flow.raw_data.length > 0;
    const noConflictsFlag = !flow.phase_state?.conflict_resolution_pending;

    if (isInAssetInventoryPhase && hasNoAssets && hasRawData && noConflictsFlag) {
      // Start intelligent polling instead of forced refresh
      startConflictDetectionPolling();
    } else {
      // Stop polling if conditions are no longer met
      stopConflictDetectionPolling();
    }

    // Cleanup on unmount or dependency change
    return () => {
      stopConflictDetectionPolling();
    };
  }, [flowId, flow, assetsLength, assetsLoading, startConflictDetectionPolling, stopConflictDetectionPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopConflictDetectionPolling();
    };
  }, [stopConflictDetectionPolling]);

  return {
    invalidateRelevantQueries,
    startConflictDetectionPolling,
    stopConflictDetectionPolling
  };
};
