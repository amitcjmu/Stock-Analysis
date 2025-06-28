import { useMutation, useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useRef } from 'react';

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
  const consecutiveErrors = useRef<number>(0);
  const maxConsecutiveErrors = 3;
  
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

  // Get flow escalation status with enhanced error handling
  const { data: flowEscalationStatus, isLoading: isLoadingFlowStatus } = useQuery({
    queryKey: ['flow-escalation-status', flowId],
    queryFn: async () => {
      try {
        const response = await apiCall(`/api/v1/discovery/${flowId}/escalation/status`);
        consecutiveErrors.current = 0; // Reset on success
        return response;
      } catch (err: any) {
        consecutiveErrors.current += 1;
        console.error(`❌ Flow escalation status fetch error (attempt ${consecutiveErrors.current}):`, err);
        
        // Handle 404 errors gracefully - flow may not exist
        if (err.status === 404 || err.response?.status === 404) {
          console.warn(`🚫 Flow ${flowId} escalation status not found, stopping polling`);
          return null;
        }
        
        // Stop polling after max consecutive errors
        if (consecutiveErrors.current >= maxConsecutiveErrors) {
          console.warn(`🚫 Stopping flow escalation status polling after ${maxConsecutiveErrors} consecutive failures`);
        }
        
        throw err;
      }
    },
    refetchInterval: consecutiveErrors.current >= maxConsecutiveErrors ? false : 5000, // Stop polling on errors
    enabled: !!flowId,
    retry: (failureCount, error) => {
      // Don't retry 404 errors (flow doesn't exist)
      if (error && ('status' in error && error.status === 404)) {
        console.warn(`🚫 Flow ${flowId} not found, stopping retries`);
        return false;
      }
      
      // Don't retry if error message indicates flow not found
      if (error && error.message && error.message.includes('not found')) {
        console.warn(`🚫 Flow ${flowId} not found (from message), stopping retries`);
        return false;
      }
      
      return failureCount < 2 && consecutiveErrors.current < maxConsecutiveErrors;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    refetchOnReconnect: false,
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

  // Reset error state function
  const resetErrorState = () => {
    consecutiveErrors.current = 0;
    console.log(`🔄 Reset error state for flow escalation ${flowId}`);
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

    // Error management
    consecutiveErrors: consecutiveErrors.current,
    isPollingDisabled: consecutiveErrors.current >= maxConsecutiveErrors,
    resetErrorState,

    // Combined states
    isProcessing: thinkMutation.isPending || ponderMutation.isPending,
    hasError: !!thinkMutation.error || !!ponderMutation.error,
    error: thinkMutation.error?.message || ponderMutation.error?.message,
  };
}; 