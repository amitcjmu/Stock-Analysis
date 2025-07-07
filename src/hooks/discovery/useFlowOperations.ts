import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { masterFlowService } from '@/services/api/masterFlowService';
import { useToast } from '@/components/ui/use-toast';
import { useNavigate } from 'react-router-dom';
import { getDiscoveryPhaseRoute } from '@/config/flowRoutes';
import { apiCall } from '@/config/api';
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
export const useIncompleteFlowDetectionV2 = () => {
  const { client, engagement } = useAuth();
  
  return useQuery({
    queryKey: ['incomplete-flows', client?.id, engagement?.id],
    queryFn: async () => {
      try {
        // Use proper UUIDs from auth context with demo fallbacks
        const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
        const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";
        
        // Try the active flows endpoint first
        const response = await masterFlowService.getActiveFlows(clientAccountId, engagementId, 'discovery');
        console.log('Active flows response:', response);
        const allFlows = Array.isArray(response) ? response : (response.flows || []);
        
        // Filter for incomplete flows (not completed or failed)
        const incompleteFlows = allFlows.filter((flow: any) => 
          flow.status !== 'completed' && 
          flow.status !== 'failed' &&
          flow.status !== 'error'
        ).map((flow: any, index: number) => {
          // Generate a demo-pattern UUID as fallback if no flow ID exists
          // Uses the demo pattern: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX
          const generateDemoFallbackUuid = (index: number) => {
            const indexPadded = index.toString().padStart(8, '0');
            const timestamp = Date.now().toString().slice(-12).padStart(12, '0');
            return `${indexPadded}-def0-def0-def0-${timestamp}`;
          };
          
          const fallbackId = generateDemoFallbackUuid(index);
          
          return ({
            flowId: flow.master_flow_id || flow.flowId || flow.flow_id || fallbackId,
            flow_id: flow.master_flow_id || flow.flowId || flow.flow_id || fallbackId, // Add flow_id for component compatibility
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
        });
        });
        
        console.log('Transformed incomplete flows:', incompleteFlows);
        return {
          flows: incompleteFlows
        };
      } catch (error) {
        console.warn('Failed to fetch active flows, returning empty list:', error);
        return { flows: [] };
      }
    },
    staleTime: 30000,
    refetchInterval: false,
    enabled: !!client?.id // Only run query when we have a client ID
  });
};

// Hook for resuming flows
export const useFlowResumptionV2 = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const navigate = useNavigate();
  const { client, engagement } = useAuth();
  
  return useMutation({
    mutationFn: async (flowId: string) => {
      const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
      const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";
      
      // Use masterFlowService for resuming flows
      return await masterFlowService.resumeFlow(flowId, clientAccountId, engagementId);
    },
    onSuccess: (data, flowId) => {
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-flows'] });
      
      toast({
        title: "Flow Resumed",
        description: "The discovery flow has been resumed successfully.",
      });
      
      // Navigate to the appropriate page based on the flow's current phase
      if (data.current_phase) {
        const route = getDiscoveryPhaseRoute(data.current_phase, flowId);
        navigate(route);
      }
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.message || "Failed to resume flow",
        variant: "destructive",
      });
    }
  });
};

// Hook for deleting flows
export const useFlowDeletionV2 = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { client, engagement } = useAuth();
  
  return useMutation({
    mutationFn: async (flowId: string) => {
      const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
      const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";
      
      // Use masterFlowService for deletion (proper unified API)
      return await masterFlowService.deleteFlow(flowId, clientAccountId, engagementId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-flows'] });
      
      toast({
        title: "Flow Deleted",
        description: "The discovery flow has been deleted successfully.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.message || "Failed to delete flow",
        variant: "destructive",
      });
    }
  });
};

// Hook for bulk flow operations
export const useBulkFlowOperationsV2 = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { client, engagement } = useAuth();
  const [isDeleting, setIsDeleting] = useState(false);
  
  const bulkDelete = useMutation({
    mutationFn: async (params: { flow_ids: string[] } | string[]) => {
      // Support both formats for compatibility
      const flowIds = Array.isArray(params) ? params : params.flow_ids;
      setIsDeleting(true);
      const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
      const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";
      
      try {
        const results = await Promise.all(
          flowIds.map(async flowId => {
            try {
              // Use masterFlowService for all deletions
              await masterFlowService.deleteFlow(flowId, clientAccountId, engagementId);
              return { flowId, success: true };
            } catch (error) {
              return { flowId, error };
            }
          })
        );
        return results;
      } finally {
        setIsDeleting(false);
      }
    },
    onSuccess: (results) => {
      const successCount = results.filter(r => !r.error).length;
      const failureCount = results.filter(r => r.error).length;
      
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-flows'] });
      
      if (successCount > 0) {
        toast({
          title: "Flows Deleted",
          description: `Successfully deleted ${successCount} flow(s)${failureCount > 0 ? `, ${failureCount} failed` : ''}.`,
        });
      }
      
      if (failureCount > 0) {
        toast({
          title: "Some Deletions Failed",
          description: `Failed to delete ${failureCount} flow(s).`,
          variant: "destructive",
        });
      }
    },
    onError: (error: any) => {
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