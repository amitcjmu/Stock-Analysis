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
  flow_id: string;
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
        const allFlows = Array.isArray(response) ? response : (response.flows || []);
        
        // Filter for incomplete flows (not completed or failed)
        const incompleteFlows = allFlows.filter((flow: any) => 
          flow.status !== 'completed' && 
          flow.status !== 'failed' &&
          flow.status !== 'error'
        );
        
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
  
  return useMutation({
    mutationFn: async (flowId: string) => {
      return await apiCall(`/api/v1/discovery/flow/${flowId}/resume`, {
        method: 'POST',
        body: JSON.stringify({
          field_mappings: {},
          notes: 'Resuming incomplete flow'
        })
      });
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
  
  return useMutation({
    mutationFn: async (flowId: string) => {
      try {
        // First try to delete from discovery flows
        return await apiCall(`/api/v1/discovery/flow/${flowId}`, {
          method: 'DELETE'
        });
      } catch (error) {
        // If that fails, try master flows API as fallback
        console.warn('Discovery flow delete failed, trying master flows API');
        return await apiCall(`/api/v1/flows/${flowId}`, {
          method: 'DELETE'
        });
      }
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
  const [isDeleting, setIsDeleting] = useState(false);
  
  const bulkDelete = useMutation({
    mutationFn: async (flowIds: string[]) => {
      setIsDeleting(true);
      try {
        const results = await Promise.all(
          flowIds.map(async flowId => {
            try {
              // First try discovery flow endpoint
              return await apiCall(`/api/v1/discovery/flow/${flowId}`, { method: 'DELETE' });
            } catch (error) {
              try {
                // Fallback to master flows API
                return await apiCall(`/api/v1/flows/${flowId}`, { method: 'DELETE' });
              } catch (fallbackError) {
                return { flowId, error: fallbackError };
              }
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
    mutate: bulkDelete.mutate,
    mutateAsync: bulkDelete.mutateAsync,
    isLoading: isDeleting,
    isError: bulkDelete.isError,
    error: bulkDelete.error
  };
};