import { useMutation, useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';

interface ThinkEscalationRequest {
  agent_id: string;
  context: Record<string, any>;
  complexity_level?: string;
  page_data?: Record<string, any>;
}

interface PonderEscalationRequest {
  agent_id: string;
  context: Record<string, any>;
  collaboration_type?: string;
  page_data?: Record<string, any>;
}

interface EscalationResponse {
  success: boolean;
  escalation_id: string;
  crew_type?: string;
  collaboration_strategy?: any;
  status: string;
  estimated_duration: string;
  message: string;
  progress_endpoint: string;
  collaboration_details?: any;
}

interface EscalationStatus {
  success: boolean;
  escalation_id: string;
  flow_id: string;
  status: string;
  progress: number;
  current_phase: string;
  crew_activity: any[];
  preliminary_insights: any[];
  estimated_completion?: string;
  error?: string;
  started_at?: string;
  updated_at?: string;
  collaboration_details?: any;
  results?: any;
  insights_generated?: any[];
  recommendations?: any[];
}

export const useCrewEscalation = (flowId: string) => {
  
  // Think escalation mutation
  const thinkMutation = useMutation({
    mutationFn: async (request: ThinkEscalationRequest): Promise<EscalationResponse> => {
      const response = await apiCall(`/api/v1/discovery/${flowId}/escalate/dependencies/think`, {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return response;
    },
  });

  // Ponder More escalation mutation  
  const ponderMutation = useMutation({
    mutationFn: async (request: PonderEscalationRequest): Promise<EscalationResponse> => {
      const response = await apiCall(`/api/v1/discovery/${flowId}/escalate/dependencies/ponder`, {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return response;
    },
  });

  // Get escalation status
  const getEscalationStatus = async (escalationId: string): Promise<EscalationStatus | null> => {
    try {
      const response = await apiCall(`/api/v1/discovery/${flowId}/escalation/${escalationId}/status`);
      return response;
    } catch (error) {
      console.error('Failed to get escalation status:', error);
      return null;
    }
  };

  // Get flow escalation status
  const { data: flowEscalationStatus, isLoading: isLoadingFlowStatus } = useQuery({
    queryKey: ['flow-escalation-status', flowId],
    queryFn: async () => {
      const response = await apiCall(`/api/v1/discovery/${flowId}/escalation/status`);
      return response;
    },
    refetchInterval: 5000, // Refresh every 5 seconds
    enabled: !!flowId,
  });

  // Cancel escalation mutation
  const cancelEscalationMutation = useMutation({
    mutationFn: async (escalationId: string) => {
      const response = await apiCall(`/api/v1/discovery/${flowId}/escalation/${escalationId}`, {
        method: 'DELETE',
      });
      return response;
    },
  });

  // Convenience methods
  const triggerThink = async (request: ThinkEscalationRequest): Promise<EscalationResponse> => {
    return thinkMutation.mutateAsync(request);
  };

  const triggerPonderMore = async (request: PonderEscalationRequest): Promise<EscalationResponse> => {
    return ponderMutation.mutateAsync(request);
  };

  const cancelEscalation = async (escalationId: string) => {
    return cancelEscalationMutation.mutateAsync(escalationId);
  };

  return {
    // Think functionality
    triggerThink,
    isThinking: thinkMutation.isPending,
    thinkError: thinkMutation.error?.message,
    thinkData: thinkMutation.data,

    // Ponder More functionality  
    triggerPonderMore,
    isPondering: ponderMutation.isPending,
    ponderError: ponderMutation.error?.message,
    ponderData: ponderMutation.data,

    // Status and monitoring
    getEscalationStatus,
    flowEscalationStatus,
    isLoadingFlowStatus,

    // Cancellation
    cancelEscalation,
    isCancelling: cancelEscalationMutation.isPending,

    // Combined states
    isProcessing: thinkMutation.isPending || ponderMutation.isPending,
    hasError: !!thinkMutation.error || !!ponderMutation.error,
    error: thinkMutation.error?.message || ponderMutation.error?.message,
  };
}; 