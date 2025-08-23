import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { masterFlowService } from '@/services/api/masterFlowService';
import { useToast } from '@/components/ui/use-toast';
import { useNavigate } from 'react-router-dom';
import { getDiscoveryPhaseRoute } from '@/config/flowRoutes';
import type { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';
import type { FlowContinuationResponse } from '@/types/api/flow-continuation';

// Type definitions
export interface IncompleteFlow {
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
export const useIncompleteFlowDetection = (): unknown => {
  const { client, engagement } = useAuth();

  return useQuery({
    queryKey: ['incomplete-flows', client?.id, engagement?.id],
    queryFn: async () => {
      try {
        // Log only in development
        if (process.env.NODE_ENV === 'development') {
          console.debug('Fetching incomplete flows for:', { client: client?.id, engagement: engagement?.id });
        }

        // Require proper UUIDs from auth context
        if (!client?.id || !engagement?.id) {
          // This is expected when context is not yet loaded
          return { flows: [] };
        }

        const clientAccountId = client.id;
        const engagementId = engagement.id;

        // Try the active flows endpoint first
        // Call getActiveFlows API
        const response = await masterFlowService.getActiveFlows(clientAccountId, engagementId, 'discovery');
        // Process response
        const allFlows = Array.isArray(response) ? response : (response.flows || []);
        // Filter flows

        // Filter for incomplete flows (match backend logic: not completed, cancelled, or deleted)
        const incompleteFlows = allFlows.filter((flow: unknown) =>
          flow.status !== 'completed' &&
          flow.status !== 'cancelled' &&
          flow.status !== 'deleted'
        ).map((flow: unknown) => {
          // Get the flow ID from various possible fields
          const flowId = flow.master_flow_id || flow.flowId || flow.flow_id;

          // If no flow ID exists, skip this flow silently (common for flows in initial state)
          if (!flowId) {
            // Only log in development mode to reduce console noise
            if (process.env.NODE_ENV === 'development') {
              console.debug('Flow missing ID, skipping:', flow);
            }
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
          created_at: flow.createdAt || flow.created_at || flow.startTime || null,
          updated_at: flow.updatedAt || flow.updated_at || flow.lastUpdated || null,
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

        // Return filtered flows
        return {
          flows: incompleteFlows
        };
      } catch (error) {
        console.error('Failed to fetch active flows:', error);
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
export const useFlowResumption = (): unknown => {
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
    onSuccess: (response, flowId) => {
      console.log('🎉 [DEBUG] Flow resumption mutation success:', { response, flowId });

      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-flows'] });

      // Extract the flow continuation data
      const data = response.data as FlowContinuationResponse;

      // Display the intelligent agent's user guidance
      if (data.user_guidance) {
        // Show the primary message from the agent
        toast({
          title: "Agent Guidance",
          description: data.user_guidance.primary_message,
          duration: 8000, // Show for longer so user can read
        });

        // If there are specific user actions, show them too
        if (data.user_guidance.user_actions && data.user_guidance.user_actions.length > 0) {
          setTimeout(() => {
            toast({
              title: "Required Actions",
              description: data.user_guidance.user_actions.join("\n"),
              duration: 10000,
            });
          }, 1000);
        }

        // Log the full guidance for debugging
        console.log('🤖 Agent Guidance:', {
          primary: data.user_guidance.primary_message,
          actions: data.user_guidance.action_items,
          userActions: data.user_guidance.user_actions,
          systemActions: data.user_guidance.system_actions
        });
      } else {
        // Fallback to generic message if no guidance
        toast({
          title: "Flow Resumed",
          description: "The discovery flow has been resumed successfully.",
        });
      }

      // Navigate based on routing context or current phase
      if (data.routing_context) {
        console.log('📍 [DEBUG] Using routing context:', data.routing_context);
        navigate(data.routing_context.target_page);
      } else if (data.current_phase) {
        const route = getDiscoveryPhaseRoute(data.current_phase, flowId);
        console.log('📍 [DEBUG] Navigating to phase route:', route);
        navigate(route);
      } else {
        console.log('📍 [DEBUG] No routing info, defaulting to attribute mapping');
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
export const useFlowDeletion = (): unknown => {
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
export const useBulkFlowOperations = (): unknown => {
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

// Backward compatibility exports
export const useIncompleteFlowDetectionV2 = useIncompleteFlowDetection;
export const useFlowResumptionV2 = useFlowResumption;
export const useFlowDeletionV2 = useFlowDeletion;
export const useBulkFlowOperationsV2 = useBulkFlowOperations;
