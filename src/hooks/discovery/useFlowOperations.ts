import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { masterFlowService } from '@/services/api/masterFlowService';
import { useToast } from '@/components/ui/use-toast';
import { useNavigate } from 'react-router-dom';
import type { getDiscoveryPhaseRoute } from '@/config/flowRoutes';
import type { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

// Type definitions
export interface IncompleteFlowV2 {
  flowId: string;
  status: string;
  current_phase: string;
  next_phase?: string;
  phases_completed: string[];
  progress: number;
  created_at: string;
  updated_at: string;
  error?: string;
  client_account_id?: string;
  engagement_id?: string;
}

// Hook to detect incomplete flows
export const useIncompleteFlowDetectionV2 = (): unknown => {
  const { client, engagement } = useAuth();

  return useQuery({
    queryKey: ['incomplete-flows', client?.id, engagement?.id],
    queryFn: async () => {
      try {
        console.log('🔍 [DEBUG] Fetching incomplete flows for:', { client: client?.id, engagement: engagement?.id });

        // Require proper UUIDs from auth context
        if (!client?.id || !engagement?.id) {
          console.warn('❌ [DEBUG] Missing client or engagement context for flow operations');
          return { flows: [] };
        }

        const clientAccountId = client.id;
        const engagementId = engagement.id;

        // Try the active flows endpoint first
        console.log('🔍 [DEBUG] Calling getActiveFlows with:', { clientAccountId, engagementId, flowType: 'discovery' });
        const response = await masterFlowService.getActiveFlows(clientAccountId, engagementId, 'discovery');
        console.log('✅ [DEBUG] Active flows response:', response);
        const allFlows = Array.isArray(response) ? response : (response.flows || []);
        console.log('📋 [DEBUG] All flows found:', allFlows.length);

        // Filter for incomplete flows (not completed or failed)
        const incompleteFlows = allFlows.filter((flow: unknown) =>
          flow.status !== 'completed' &&
          flow.status !== 'failed' &&
          flow.status !== 'error'
        ).map((flow: unknown) => {
          // Get the flow ID from various possible fields
          const flowId = flow.master_flow_id || flow.flowId || flow.flow_id;

          // If no flow ID exists, log an error and skip this flow
          if (!flowId) {
            console.error('❌ [DEBUG] Flow missing ID, skipping:', flow);
            return null;
          }

          return ({
            flowId: flowId,
            flow_id: flowId, // Add flow_id for component compatibility
            status: flow.status,
          current_phase: flow.currentPhase || flow.current_phase || 'unknown',
          next_phase: flow.nextPhase || flow.next_phase,
          phases_completed: flow.phasesCompleted || flow.phases_completed || [],
          progress: flow.progress || flow.progress_percentage || 0,
          progress_percentage: flow.progress_percentage || flow.progress || 0,
          created_at: flow.createdAt || flow.created_at,
          updated_at: flow.updatedAt || flow.updated_at,
          error: flow.error,
          client_account_id: flow.client_account_id,
          engagement_id: flow.engagement_id,
          // Additional fields for compatibility
          flow_name: flow.flowType || 'Discovery Flow',
          flow_description: flow.metadata?.description || '',
          can_resume: flow.status !== 'failed',
          // Add agent_insights field to prevent undefined errors
          agent_insights: flow.agent_insights || [],
          // Add deletion_impact field to prevent undefined errors in BatchDeletionConfirmDialog
          deletion_impact: flow.deletion_impact || {
            data_to_delete: {
              workflow_state: 1,
              import_sessions: 0,
              field_mappings: 0,
              assets: 0,
              dependencies: 0,
              shared_memory_refs: 0
            },
            estimated_cleanup_time: '30s'
          },
        });
        }).filter(flow => flow !== null); // Remove flows without IDs

        console.log('📋 [DEBUG] Transformed incomplete flows:', incompleteFlows);
        console.log('📋 [DEBUG] Final result:', { flows: incompleteFlows });
        return {
          flows: incompleteFlows
        };
      } catch (error) {
        console.error('❌ [DEBUG] Failed to fetch active flows, returning empty list:', error);
        return { flows: [] };
      }
    },
    staleTime: 30000,
    refetchInterval: false,
    enabled: !!client?.id && !!engagement?.id, // Only run query when we have proper context
    retry: false, // Don't retry failed requests to avoid console spam
    refetchOnWindowFocus: false // Don't refetch when window gains focus
  });
};

// Hook for resuming flows
export const useFlowResumptionV2 = (): unknown => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const navigate = useNavigate();
  const { client, engagement } = useAuth();

  return useMutation({
    mutationFn: async (flowId: string) => {
      console.log('🔄 [DEBUG] Flow resumption called with:', { flowId, client: client?.id, engagement: engagement?.id });

      // Require proper UUIDs from auth context
      if (!client?.id || !engagement?.id) {
        console.error('❌ [DEBUG] Missing client or engagement context for flow resumption');
        throw new Error('Missing client or engagement context for flow resumption');
      }

      try {
        // Use masterFlowService for resuming flows
        const result = await masterFlowService.resumeFlow(flowId, client.id, engagement.id);
        console.log('✅ [DEBUG] Flow resumption successful:', result);
        return result;
      } catch (error) {
        console.error('❌ [DEBUG] Flow resumption failed:', error);
        throw error;
      }
    },
    onSuccess: (data, flowId) => {
      console.log('🎉 [DEBUG] Flow resumption mutation success:', { data, flowId });

      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-flows'] });

      toast({
        title: "Flow Resumed",
        description: "The discovery flow has been resumed successfully.",
      });

      // Navigate to the appropriate page based on the flow's current phase
      if (data.current_phase) {
        const route = getDiscoveryPhaseRoute(data.current_phase, flowId);
        console.log('📍 [DEBUG] Navigating to:', route);
        navigate(route);
      } else {
        console.log('📍 [DEBUG] No current_phase in response, navigating to attribute mapping');
        const route = getDiscoveryPhaseRoute('field_mapping', flowId);
        navigate(route);
      }
    },
    onError: (error: unknown) => {
      console.error('❌ [DEBUG] Flow resumption mutation error:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to resume flow",
        variant: "destructive",
      });
    }
  });
};

// Hook for deleting flows
// @deprecated Use useFlowDeletion from '@/hooks/useFlowDeletion' instead
export const useFlowDeletionV2 = (): unknown => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { client, engagement } = useAuth();

  console.warn('⚠️ useFlowDeletionV2 is deprecated. Use useFlowDeletion for centralized user-approval deletion system.');

  return useMutation({
    mutationFn: async (flowId: string) => {
      // Require proper UUIDs from auth context
      if (!client?.id || !engagement?.id) {
        throw new Error('Missing client or engagement context for flow deletion');
      }

      // Show warning that direct deletion is deprecated
      toast({
        title: "⚠️ Deprecated Deletion Method",
        description: "This deletion method is deprecated. Please use the new user-approval flow deletion system.",
        variant: "destructive",
      });

      throw new Error('Direct flow deletion is deprecated. Use the new user-approval deletion system.');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-flows'] });
    },
    onError: (error: unknown) => {
      toast({
        title: "Error",
        description: error.message || "Failed to delete flow",
        variant: "destructive",
      });
    }
  });
};

// Hook for bulk flow operations
// @deprecated Use useFlowDeletion from '@/hooks/useFlowDeletion' instead
export const useBulkFlowOperationsV2 = (): unknown => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { client, engagement } = useAuth();
  const [isDeleting, setIsDeleting] = useState(false);

  console.warn('⚠️ useBulkFlowOperationsV2 is deprecated. Use useFlowDeletion for centralized user-approval deletion system.');

  const bulkDelete = useMutation({
    mutationFn: async (params: { flow_ids: string[] } | string[]) => {
      // Show warning that direct deletion is deprecated
      toast({
        title: "⚠️ Deprecated Bulk Deletion Method",
        description: "This bulk deletion method is deprecated. Please use the new user-approval flow deletion system.",
        variant: "destructive",
      });

      throw new Error('Direct bulk flow deletion is deprecated. Use the new user-approval deletion system.');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-flows'] });
    },
    onError: (error: unknown) => {
      toast({
        title: "Error",
        description: error.message || "Failed to delete flows",
        variant: "destructive",
      });
    }
  });

  return {
    bulkDelete: {
      mutate: bulkDelete.mutate,
      mutateAsync: bulkDelete.mutateAsync,
      isLoading: isDeleting,
      isError: bulkDelete.isError,
      error: bulkDelete.error
    }
  };
};
