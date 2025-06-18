import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '../config/api';

// Discovery Flow State interface matching backend
interface DiscoveryFlowState {
  session_id: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  current_phase: string;
  phase_completion: Record<string, boolean>;
  crew_status: Record<string, any>;
  field_mappings: {
    mappings: Record<string, any>;
    confidence_scores: Record<string, number>;
    unmapped_fields: string[];
    validation_results: Record<string, any>;
    agent_insights: Record<string, any>;
  };
  raw_data: any[];
  cleaned_data: any[];
  asset_inventory: Record<string, any>;
  agent_collaboration_map: Record<string, string[]>;
  shared_memory_id: string;
  shared_memory_reference?: any;
  overall_plan: Record<string, any>;
  crew_coordination: Record<string, any>;
  errors: any[];
  warnings: any[];
}

interface InitializeFlowParams {
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  raw_data: any[];
  metadata: Record<string, any>;
}

export const useDiscoveryFlowState = () => {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Get flow state
  const { data: flowState, isLoading, error } = useQuery({
    queryKey: ['discovery-flow-state', currentSessionId],
    queryFn: async () => {
      if (!currentSessionId) return null;
      
      const response = await apiCall(`/api/v1/discovery/flow/${currentSessionId}/state`);
      return response as DiscoveryFlowState;
    },
    enabled: !!currentSessionId,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: (data) => {
      // Auto-refresh if flow is active
      if (data?.current_phase && data.current_phase !== 'completed') {
        return 10 * 1000; // 10 seconds
      }
      return false;
    }
  });

  // Initialize flow
  const initializeFlowMutation = useMutation({
    mutationFn: async (params: InitializeFlowParams) => {
      const response = await apiCall('/api/v1/discovery/flow/initialize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      return response;
    },
    onSuccess: (data) => {
      if (data.session_id) {
        setCurrentSessionId(data.session_id);
        queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
      }
    }
  });

  // Execute Field Mapping Crew
  const executeFieldMappingCrewMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await apiCall(`/api/v1/discovery/flow/${sessionId}/crews/field-mapping/execute`, {
        method: 'POST'
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    }
  });

  // Execute Data Cleansing Crew
  const executeDataCleansingCrewMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await apiCall(`/api/v1/discovery/flow/${sessionId}/crews/data-cleansing/execute`, {
        method: 'POST'
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    }
  });

  // Execute Inventory Building Crew
  const executeInventoryBuildingCrewMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await apiCall(`/api/v1/discovery/flow/${sessionId}/crews/inventory-building/execute`, {
        method: 'POST'
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    }
  });

  // Get crew status
  const getCrewStatus = useCallback(async (sessionId: string, crewName: string) => {
    try {
      const response = await apiCall(`/api/v1/discovery/flow/${sessionId}/crews/${crewName}/status`);
      return response;
    } catch (error) {
      console.error(`Failed to get crew status for ${crewName}:`, error);
      return null;
    }
  }, []);

  // Set session ID for existing flows
  const setSessionId = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
  }, []);

  return {
    flowState,
    isLoading,
    error,
    currentSessionId,
    setSessionId,
    initializeFlow: initializeFlowMutation.mutateAsync,
    executeFieldMappingCrew: executeFieldMappingCrewMutation.mutateAsync,
    executeDataCleansingCrew: executeDataCleansingCrewMutation.mutateAsync,
    executeInventoryBuildingCrew: executeInventoryBuildingCrewMutation.mutateAsync,
    getCrewStatus,
    isInitializing: initializeFlowMutation.isPending,
    isExecutingCrew: executeFieldMappingCrewMutation.isPending || 
                     executeDataCleansingCrewMutation.isPending || 
                     executeInventoryBuildingCrewMutation.isPending
  };
}; 