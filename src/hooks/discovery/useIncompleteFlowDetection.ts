import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import { useToast } from '@/hooks/use-toast';

export interface IncompleteFlow {
  session_id: string;
  current_phase: string;
  status: 'running' | 'paused' | 'failed';
  progress_percentage: number;
  phase_completion: Record<string, boolean>;
  agent_insights: Array<{
    phase: string;
    insight: string;
    confidence: number;
    timestamp: string;
  }>;
  created_at: string;
  updated_at: string;
  can_resume: boolean;
  deletion_impact: {
    flow_phase: string;
    data_to_delete: Record<string, number>;
    estimated_cleanup_time: string;
  };
  flow_management_info?: {
    estimated_remaining_time: string;
    next_phase: string;
    completion_percentage: number;
    resumption_possible: boolean;
  };
}

export interface FlowDetectionResult {
  flows: IncompleteFlow[];
  total_count: number;
  can_start_new_flow: boolean;
  blocking_flows: IncompleteFlow[];
}

export interface BulkDeleteRequest {
  session_ids: string[];
  force_delete?: boolean;
}

export interface BulkDeleteResult {
  batch_results: Array<{
    session_id: string;
    success: boolean;
    result?: any;
    error?: string;
  }>;
  total_processed: number;
  successful: number;
  failed: number;
}

/**
 * Hook for detecting incomplete CrewAI discovery flows
 * Provides real-time monitoring and flow state management
 */
export const useIncompleteFlowDetection = () => {
  const { client, engagement } = useAuth();
  
  return useQuery({
    queryKey: ['incomplete-flows', client?.id, engagement?.id],
    queryFn: async (): Promise<FlowDetectionResult> => {
      const response = await apiCall('/discovery/flows/incomplete');
      return response;
    },
    enabled: !!client?.id && !!engagement?.id,
    refetchInterval: 30000, // Check every 30 seconds for real-time updates
    staleTime: 10000, // Consider data stale after 10 seconds
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * Hook for validating if new flow can be started
 */
export const useNewFlowValidation = () => {
  const { client, engagement } = useAuth();
  
  return useQuery({
    queryKey: ['flow-validation', 'can-start-new', client?.id, engagement?.id],
    queryFn: async (): Promise<{ can_start: boolean; blocking_flows?: IncompleteFlow[]; reason?: string }> => {
      const response = await apiCall('/discovery/flows/validation/can-start-new');
      return response;
    },
    enabled: !!client?.id && !!engagement?.id,
    staleTime: 5000, // Fresh data for validation
  });
};

/**
 * Hook for getting detailed flow information
 */
export const useFlowDetails = (sessionId: string | null) => {
  return useQuery({
    queryKey: ['flow-details', sessionId],
    queryFn: async (): Promise<IncompleteFlow> => {
      if (!sessionId) throw new Error('Session ID required');
      const response = await apiCall(`/discovery/flows/${sessionId}/details`);
      return response;
    },
    enabled: !!sessionId,
    staleTime: 15000,
  });
};

/**
 * Hook for resuming CrewAI flows
 */
export const useFlowResumption = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: async (sessionId: string) => {
      // Prepare the request body
      const requestBody = {
        resume_context: {},
        force_resume: false
      };
      
      console.log('🔄 Flow resumption request:', {
        sessionId,
        endpoint: `/discovery/flows/${sessionId}/resume`,
        body: requestBody
      });
      
      // Make the API call with explicit body handling
      try {
        const response = await apiCall(`/discovery/flows/${sessionId}/resume`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestBody)
        });
        
        console.log('✅ Flow resumption response:', response);
        return response;
      } catch (error) {
        console.error('❌ Flow resumption error:', error);
        throw error;
      }
    },
    onSuccess: (data, sessionId) => {
      // Invalidate incomplete flows query to refresh UI
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['flow-validation'] });
      
      // Determine next phase and navigate appropriately
      const nextPhase = data?.next_phase || data?.current_phase;
      
      // ✅ Include session ID in phase routes
      const phaseRoutes = {
        'data_import': `/discovery/import/${sessionId}`,
        'field_mapping': `/discovery/attribute-mapping/${sessionId}`,
        'data_cleansing': `/discovery/data-cleansing/${sessionId}`,
        'asset_inventory': `/discovery/inventory/${sessionId}`,
        'dependency_analysis': `/discovery/dependencies/${sessionId}`,
        'tech_debt': `/discovery/tech-debt/${sessionId}`
      };
      
      const nextRoute = phaseRoutes[nextPhase as keyof typeof phaseRoutes] || '/discovery/enhanced-dashboard';
      
      toast({
        title: "Flow Resumed Successfully",
        description: `Discovery flow has been resumed. Redirecting to ${nextPhase?.replace('_', ' ')} phase...`,
        variant: "default",
      });
      
      // Navigate to the appropriate phase after a short delay
      setTimeout(() => {
        window.location.href = nextRoute;
      }, 2000);
    },
    onError: (error: any, sessionId) => {
      console.error('Flow resumption failed:', error);
      
      toast({
        title: "Flow Resumption Failed",
        description: error?.message || `Failed to resume flow ${sessionId.substring(0, 8)}...`,
        variant: "destructive",
      });
    }
  });
};

/**
 * Hook for deleting individual CrewAI flows
 */
export const useFlowDeletion = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: async (sessionId: string) => {
      return await apiCall(`/discovery/flows/${sessionId}`, {
        method: 'DELETE'
      });
    },
    onSuccess: (data, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['flow-validation'] });
      
      toast({
        title: "Flow Deleted Successfully",
        description: `Discovery flow and all associated data have been permanently removed.`,
        variant: "default",
      });
    },
    onError: (error: any, sessionId) => {
      toast({
        title: "Flow Deletion Failed",
        description: error?.message || `Failed to delete flow ${sessionId.substring(0, 8)}...`,
        variant: "destructive",
      });
    }
  });
};

/**
 * Hook for bulk operations on multiple flows
 */
export const useBulkFlowOperations = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: async (request: BulkDeleteRequest): Promise<BulkDeleteResult> => {
      return await apiCall('/discovery/flows/bulk-operations', {
        method: 'POST',
        body: JSON.stringify(request)
      });
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['flow-validation'] });
      
      const { successful, failed, total_processed } = data;
      
      if (failed === 0) {
        toast({
          title: "Bulk Operation Completed",
          description: `Successfully processed ${successful} of ${total_processed} flows.`,
          variant: "default",
        });
      } else {
        toast({
          title: "Bulk Operation Completed with Errors",
          description: `${successful} succeeded, ${failed} failed out of ${total_processed} flows.`,
          variant: "destructive",
        });
      }
    },
    onError: (error: any) => {
      toast({
        title: "Bulk Operation Failed",
        description: error?.message || "Failed to process bulk operation",
        variant: "destructive",
      });
    }
  });
};

/**
 * Hook for real-time flow monitoring
 * Provides WebSocket-like updates for active flows
 */
export const useFlowMonitoring = (sessionIds: string[]) => {
  const queryClient = useQueryClient();
  
  return useQuery({
    queryKey: ['flow-monitoring', sessionIds],
    queryFn: async () => {
      // Poll multiple flows for status updates
      const promises = sessionIds.map(sessionId => 
        apiCall(`/discovery/flows/${sessionId}/details`).catch(() => null)
      );
      const results = await Promise.all(promises);
      return results.filter(Boolean);
    },
    enabled: sessionIds.length > 0,
    refetchInterval: 10000, // More frequent updates for active monitoring
    staleTime: 5000,
  });
}; 