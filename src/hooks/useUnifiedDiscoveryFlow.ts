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

// Phase execution parameters
interface PhaseExecutionParams {
  phase: string;
  data?: any;
  configuration?: Record<string, any>;
}

// Flow initialization parameters
interface FlowInitializationParams {
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  raw_data: any[];
  metadata?: Record<string, any>;
  configuration?: Record<string, any>;
}

export const useUnifiedDiscoveryFlow = () => {
  const { user, client, engagement, getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();
  
  // Current session tracking
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  
  // Single flow state query with real-time updates
  const flowQuery = useQuery<UnifiedDiscoveryFlowState>({
    queryKey: ['unified-discovery-flow', client?.id, engagement?.id, currentSessionId],
    queryFn: async () => {
      if (!currentSessionId) {
        throw new Error('No active session');
      }
      
      const response = await apiCall(`/api/v1/unified-discovery/flow/status/${currentSessionId}`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch flow status: ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!client && !!engagement && !!currentSessionId,
    refetchInterval: 5000, // Real-time updates every 5 seconds
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
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
      // Set current session ID for tracking
      setCurrentSessionId(data.session_id);
      
      // Invalidate and refetch flow state
      queryClient.invalidateQueries({ 
        queryKey: ['unified-discovery-flow', client?.id, engagement?.id] 
      });
    },
    onError: (error) => {
      console.error('Flow initialization failed:', error);
    }
  });
  
  // Execute specific phase mutation
  const executePhase = useMutation({
    mutationFn: async (params: PhaseExecutionParams) => {
      if (!currentSessionId) {
        throw new Error('No active session for phase execution');
      }
      
      const response = await apiCall(`/api/v1/unified-discovery/flow/execute/${params.phase}`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: currentSessionId,
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
        queryKey: ['unified-discovery-flow', client?.id, engagement?.id, currentSessionId] 
      });
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
        throw new Error('Health check failed');
      }
      
      return response.json();
    },
    refetchInterval: 30000, // Health check every 30 seconds
    retry: 3
  });
  
  // Initialize flow with default parameters
  const initializeFlow = useCallback(async (rawData: any[], metadata: Record<string, any> = {}) => {
    if (!client || !engagement || !user) {
      throw new Error('Missing required authentication context');
    }
    
    const params: FlowInitializationParams = {
      client_account_id: client.id,
      engagement_id: engagement.id,
      user_id: user.id,
      raw_data: rawData,
      metadata,
      configuration: {}
    };
    
    return initializeFlowMutation.mutateAsync(params);
  }, [client, engagement, user, initializeFlowMutation]);
  
  // Execute specific phase with data
  const executeFlowPhase = useCallback(async (phase: string, data?: any, configuration?: Record<string, any>) => {
    return executePhase.mutateAsync({ phase, data, configuration });
  }, [executePhase]);
  
  // Get phase-specific data helpers
  const getPhaseData = useCallback((phase: string) => {
    const state = flowQuery.data;
    if (!state) return null;
    
    switch (phase) {
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
    setCurrentSessionId(null);
    queryClient.removeQueries({ 
      queryKey: ['unified-discovery-flow', client?.id, engagement?.id] 
    });
  }, [queryClient, client, engagement]);
  
  return {
    // Flow state
    flowState: flowQuery.data,
    isLoading: flowQuery.isLoading,
    error: flowQuery.error,
    isHealthy: healthQuery.data?.status === 'healthy',
    
    // Flow control
    initializeFlow,
    executeFlowPhase,
    refreshFlow,
    resetFlow,
    
    // Phase helpers
    getPhaseData,
    isPhaseComplete,
    getCrewStatus,
    canProceedToPhase,
    
    // Current state
    currentPhase: flowQuery.data?.current_phase || 'initialization',
    progress: flowQuery.data?.progress_percentage || 0,
    status: flowQuery.data?.status || 'idle',
    
    // Session management
    sessionId: currentSessionId,
    hasActiveSession: !!currentSessionId,
    
    // Mutation states
    isInitializing: initializeFlowMutation.isPending,
    isExecutingPhase: executePhase.isPending,
    
    // Real-time updates
    lastUpdated: flowQuery.data?.updated_at,
    
    // Error handling
    errors: flowQuery.data?.errors || [],
    warnings: flowQuery.data?.warnings || []
  };
}; 