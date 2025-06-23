import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { apiCall } from '../config/api';

// Unified Discovery Flow State Interface
interface UnifiedDiscoveryFlowState {
  // Core identification
  flow_id: string;
  session_id: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  
  // CrewAI Flow state management
  current_phase: string;
  phase_completion: Record<string, boolean>;
  crew_status: Record<string, any>;
  
  // Phase-specific data
  raw_data: any[];
  field_mappings: Record<string, any>;
  cleaned_data: any[];
  asset_inventory: Record<string, any>;
  dependencies: Record<string, any>;
  technical_debt: Record<string, any>;
  
  // Flow control
  status: string;
  progress_percentage: number;
  errors: any[];
  warnings: string[];
  
  // Timestamps
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

// Current Flow Response Interface
interface CurrentFlowResponse {
  has_current_flow: boolean;
  flow_id?: string;
  session_id?: string;
  current_phase?: string;
  status?: string;
  progress_percentage?: number;
  started_at?: string;
  updated_at?: string;
  message?: string;
  timestamp: string;
}

// Flow Initialization Parameters
interface FlowInitializationParams {
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  raw_data: any[];
  metadata: Record<string, any>;
  configuration: Record<string, any>;
}

// Phase Execution Parameters
interface PhaseExecutionParams {
  phase: string;
  data: any;
  configuration: Record<string, any>;
}

export const useUnifiedDiscoveryFlow = (providedFlowId?: string | null) => {
  const { user, client, engagement, getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();
  
  // Current flow tracking - use provided flow ID if available, otherwise auto-detect
  const [currentFlowId, setCurrentFlowId] = useState<string | null>(providedFlowId || null);
  
  // Auto-detect current flow query (only when no flow ID is provided)
  const currentFlowQuery = useQuery<CurrentFlowResponse>({
    queryKey: ['current-discovery-flow', client?.id, engagement?.id],
    queryFn: async () => {
      const response = await apiCall('/api/v1/unified-discovery/flow/current', {
        method: 'GET',
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get current flow: ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!client && !!engagement && !providedFlowId, // Only auto-detect when no flow ID provided
    refetchInterval: (data, query) => {
      // Stop polling if there's an error
      if (query.state.error) {
        console.log('🛑 Stopping current flow polling due to error:', query.state.error);
        return false;
      }
      // Continue polling every 10 seconds if successful
      return 10000;
    },
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: (failureCount, error) => {
      // Retry up to 3 times for network errors
      return failureCount < 3;
    },
    onSuccess: (data) => {
      // Auto-set current flow ID when flow is detected (only if no provided flow ID)
      if (!providedFlowId && data.has_current_flow && data.flow_id && data.flow_id !== currentFlowId) {
        console.log(`🔄 Auto-detected current flow ID: ${data.flow_id}`);
        setCurrentFlowId(data.flow_id);
      } else if (!providedFlowId && !data.has_current_flow && currentFlowId) {
        console.log('ℹ️ No current flow detected, clearing flow ID');
        setCurrentFlowId(null);
      }
    },
    onError: (error) => {
      console.error('Current flow detection error:', error);
    }
  });

  // Update flow ID when provided flow ID changes
  useEffect(() => {
    if (providedFlowId !== undefined && providedFlowId !== currentFlowId) {
      console.log(`🔄 Using provided flow ID: ${providedFlowId}`);
      setCurrentFlowId(providedFlowId);
    }
  }, [providedFlowId, currentFlowId]);

  // Single flow state query with real-time updates (using flow_id)
  const flowQuery = useQuery<UnifiedDiscoveryFlowState>({
    queryKey: ['unified-discovery-flow', client?.id, engagement?.id, currentFlowId],
    queryFn: async () => {
      if (!currentFlowId) {
        throw new Error('No active flow ID');
      }
      
      const response = await apiCall(`/api/v1/unified-discovery/flow/by-id/${currentFlowId}`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        if (response.status === 404) {
          // Flow not found - clear the current flow ID and stop polling
          console.warn(`⚠️ Flow not found: ${currentFlowId}. Clearing flow ID.`);
          setCurrentFlowId(null);
          throw new Error(`Flow not found: ${currentFlowId}`);
        }
        throw new Error(`Failed to fetch flow status: ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!client && !!engagement && !!currentFlowId,
    refetchInterval: (data, query) => {
      // Stop polling if there's an error (like 404)
      if (query.state.error) {
        console.log('🛑 Stopping polling due to error:', query.state.error);
        return false;
      }
      // Continue polling every 5 seconds if successful
      return 5000;
    },
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: (failureCount, error) => {
      // Don't retry 404 errors (flow not found)
      if (error?.message?.includes('Flow not found') || error?.message?.includes('404')) {
        console.log('🛑 Not retrying 404 error for flow:', currentFlowId);
        return false;
      }
      // Retry other errors up to 3 times
      return failureCount < 3;
    },
    onError: (error) => {
      console.error('Flow query error:', error);
      // If it's a 404 error, clear the flow ID
      if (error?.message?.includes('Flow not found') || error?.message?.includes('404')) {
        console.log('🔄 Clearing flow ID due to 404 error');
        setCurrentFlowId(null);
      }
    }
  });

  // Health check query
  const healthQuery = useQuery({
    queryKey: ['unified-discovery-health'],
    queryFn: async () => {
      const response = await apiCall('/api/v1/unified-discovery/flow/health', {
        method: 'GET',
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`);
      }
      
      return response.json();
    },
    refetchInterval: 30000, // Health check every 30 seconds
    enabled: !!client && !!engagement
  });

  // Initialize flow mutation
  const initializeFlowMutation = useMutation({
    mutationFn: async (params: FlowInitializationParams) => {
      const response = await apiCall('/api/v1/unified-discovery/flow/initialize', {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to initialize flow: ${response.statusText}`);
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      // Set current flow ID for tracking
      setCurrentFlowId(data.flow_id);
      
      // Invalidate and refetch flow state
      queryClient.invalidateQueries({ 
        queryKey: ['unified-discovery-flow', client?.id, engagement?.id] 
      });
      queryClient.invalidateQueries({ 
        queryKey: ['current-discovery-flow', client?.id, engagement?.id] 
      });
    },
    onError: (error) => {
      console.error('Flow initialization failed:', error);
    }
  });
  
  // Execute specific phase mutation
  const executePhase = useMutation({
    mutationFn: async (params: PhaseExecutionParams) => {
      if (!currentFlowId) {
        throw new Error('No active flow ID for phase execution');
      }
      
      const response = await apiCall(`/api/v1/unified-discovery/flow/execute/${params.phase}`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          flow_id: currentFlowId,
          data: params.data,
          configuration: params.configuration
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to execute phase ${params.phase}: ${response.statusText}`);
      }
      
      return response.json();
    },
    onSuccess: () => {
      // Invalidate flow state to trigger refresh
      queryClient.invalidateQueries({ 
        queryKey: ['unified-discovery-flow', client?.id, engagement?.id, currentFlowId] 
      });
    }
  });

  // Convenience functions
  const initializeFlow = useCallback(async (params: Omit<FlowInitializationParams, 'client_account_id' | 'engagement_id' | 'user_id'>) => {
    if (!client || !engagement || !user) {
      throw new Error('Missing required context');
    }
    
    return initializeFlowMutation.mutateAsync({
      ...params,
      client_account_id: client.id,
      engagement_id: engagement.id,
      user_id: user.id
    });
  }, [client, engagement, user, initializeFlowMutation]);

  const executeFlowPhase = useCallback(async (phase: string, data: any = {}, configuration: Record<string, any> = {}) => {
    return executePhase.mutateAsync({ phase, data, configuration });
  }, [executePhase]);

  // Get data for a specific phase
  const getPhaseData = useCallback((phase: string) => {
    const state = flowQuery.data;
    if (!state) return null;
    
    switch (phase) {
      case 'data_import':
      case 'raw_data':
        return state.raw_data;
      case 'field_mapping':
        return state.field_mappings;
      case 'data_cleansing':
        return state.cleaned_data;
      case 'asset_inventory':
        return state.asset_inventory;
      case 'dependency_analysis':
        return state.dependencies;
      case 'tech_debt_analysis':
        return state.technical_debt;
      default:
        return null;
    }
  }, [flowQuery.data]);
  
  // Get phase completion status
  const isPhaseComplete = useCallback((phase: string) => {
    return flowQuery.data?.phase_completion?.[phase] || false;
  }, [flowQuery.data]);
  
  // Get crew status for a phase
  const getCrewStatus = useCallback((phase: string) => {
    return flowQuery.data?.crew_status?.[phase] || null;
  }, [flowQuery.data]);
  
  // Check if flow is ready for next phase
  const canProceedToPhase = useCallback((phase: string) => {
    const state = flowQuery.data;
    if (!state) return false;
    
    const phaseOrder = [
      'data_import',
      'field_mapping',
      'data_cleansing',
      'asset_inventory',
      'dependency_analysis',
      'tech_debt_analysis'
    ];
    
    const currentIndex = phaseOrder.indexOf(phase);
    if (currentIndex <= 0) return true; // First phase or invalid phase
    
    // Check if previous phase is complete
    const previousPhase = phaseOrder[currentIndex - 1];
    return state.phase_completion[previousPhase] || false;
  }, [flowQuery.data]);
  
  // Manual refresh function
  const refreshFlow = useCallback(() => {
    return flowQuery.refetch();
  }, [flowQuery]);
  
  // Reset flow state (for testing/development)
  const resetFlow = useCallback(() => {
    setCurrentFlowId(null);
    queryClient.removeQueries({ 
      queryKey: ['unified-discovery-flow', client?.id, engagement?.id] 
    });
    queryClient.removeQueries({ 
      queryKey: ['current-discovery-flow', client?.id, engagement?.id] 
    });
  }, [queryClient, client, engagement]);

  // Force set flow ID (for URL-based navigation)
  const setFlowId = useCallback((flowId: string | null) => {
    if (flowId !== currentFlowId) {
      console.log(`🔄 Manually setting flow ID: ${flowId}`);
      setCurrentFlowId(flowId);
    }
  }, [currentFlowId]);
  
  return {
    // Flow state
    flowState: flowQuery.data,
    currentFlow: currentFlowQuery.data,
    isLoading: flowQuery.isLoading || currentFlowQuery.isLoading,
    error: flowQuery.error || currentFlowQuery.error,
    isHealthy: healthQuery.data?.status === 'healthy',
    
    // Flow control
    initializeFlow,
    executeFlowPhase,
    refreshFlow,
    resetFlow,
    setFlowId,
    
    // Phase helpers
    getPhaseData,
    isPhaseComplete,
    getCrewStatus,
    canProceedToPhase,
    
    // Current state
    currentPhase: flowQuery.data?.current_phase || currentFlowQuery.data?.current_phase || 'initialization',
    progress: flowQuery.data?.progress_percentage || currentFlowQuery.data?.progress_percentage || 0,
    status: flowQuery.data?.status || currentFlowQuery.data?.status || 'idle',
    
    // Session management
    flowId: currentFlowId,
    hasActiveFlow: !!currentFlowId || !!currentFlowQuery.data?.has_current_flow,
    hasCurrentFlow: currentFlowQuery.data?.has_current_flow || false,
    
    // Mutation states
    isInitializing: initializeFlowMutation.isPending,
    isExecutingPhase: executePhase.isPending,
    
    // Real-time updates
    lastUpdated: flowQuery.data?.updated_at || currentFlowQuery.data?.updated_at,
    
    // Error handling
    errors: flowQuery.data?.errors || [],
    warnings: flowQuery.data?.warnings || []
  };
}; 