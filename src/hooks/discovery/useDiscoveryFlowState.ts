import { useState, useCallback, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../use-toast';
import { apiCall, apiCallWithFallback } from '../../config/api';
import { FlowState } from '../../types/discovery';

const POLLING_INTERVAL = 5000;
const STALE_TIME = 30000;

export const useDiscoveryFlowState = () => {
  const { user, client, engagement, getAuthHeaders } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const location = useLocation();

  const flowStateQuery = useQuery<FlowState>({
    queryKey: ['discovery-flow-state', client?.id, engagement?.id],
    queryFn: async () => {
      const headers = getAuthHeaders();
      const response = await apiCallWithFallback(`/api/v1/discovery/flow/status`, { headers });
      
      if (!response.ok) {
        console.error('Failed to fetch flow state:', response);
        return null;
      }
      
      const data = await response.json();
      return data?.flow_state || null;
    },
    enabled: !!client && !!engagement,
    refetchInterval: POLLING_INTERVAL,
    staleTime: STALE_TIME,
  });

  const initializeFlow = useMutation({
    mutationFn: async (params: { 
        client_account_id: string; 
        engagement_id: string; 
        user_id: string;
        raw_data: any[];
        metadata: Record<string, any>;
        configuration: Record<string, any>;
    }) => {
      const headers = getAuthHeaders();
      return apiCall('/api/v1/discovery/flow/run', {
        method: 'POST',
        headers,
        body: JSON.stringify(params),
      });
    },
    onSuccess: (data) => {
      toast({
        title: "✅ Discovery Flow Initialized",
        description: `Flow session ${data.session_id} has started.`,
      });
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    },
    onError: (error) => {
      toast({
        title: "❌ Flow Initialization Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const executePhase = useMutation({
    mutationFn: async (params: {
      phase: string;
      session_id: string;
      additional_config?: Record<string, any>;
    }) => {
      const headers = getAuthHeaders();
      return apiCall(`/api/v1/discovery/flow/execute-phase`, {
          method: 'POST',
          headers,
          body: JSON.stringify(params),
      });
    },
    onSuccess: (data) => {
      toast({
        title: `✅ Phase ${data.phase} Execution Started`,
        description: "Agents are now processing the task.",
      });
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    },
    onError: (error) => {
      toast({
        title: "❌ Phase Execution Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Effect to handle initialization from navigation state (e.g., from Data Import)
  useEffect(() => {
    const state = location.state as any;
    if (state?.trigger_discovery_flow && client?.id && engagement?.id && user?.id) {
        initializeFlow.mutate({
            client_account_id: client.id,
            engagement_id: engagement.id,
            user_id: user.id,
            raw_data: state.raw_data || [],
            metadata: state.metadata || {},
            configuration: state.configuration || {}
        });
        // Clear state to prevent re-triggering
        window.history.replaceState({}, document.title)
    }
  }, [location.state, client, engagement, user, initializeFlow]);


  return {
    flowState: flowStateQuery.data,
    isLoading: flowStateQuery.isLoading,
    error: flowStateQuery.error,
    initializeFlow,
    executePhase,
    refetchFlowState: flowStateQuery.refetch,
  };
}; 