import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '../config/api';

// Discovery Flow State interface matching backend
interface DiscoveryFlowState {
  session_id: string;
  flow_fingerprint?: string;  // Add CrewAI fingerprint support
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
  
  // Add missing fields from the full architecture
  data_quality_metrics: Record<string, any>;
  app_server_dependencies: Record<string, any>;
  app_app_dependencies: Record<string, any>;
  technical_debt_assessment: Record<string, any>;
  discovery_summary: Record<string, any>;
  assessment_flow_package: Record<string, any>;
  
  // Real-time agent monitoring
  agent_performance_metrics: Record<string, any>;
  collaboration_activities: any[];
  memory_analytics: Record<string, any>;
  knowledge_base_status: Record<string, any>;
  
  // Planning and intelligence
  planning_status: Record<string, any>;
  success_criteria_tracking: Record<string, any>;
  performance_analytics: Record<string, any>;
  
  // Completion and status
  completion_percentage: number;
  estimated_remaining_time: string;
  overall_status: 'initializing' | 'in_progress' | 'completed' | 'failed' | 'paused';
}

interface InitializeFlowParams {
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  raw_data: any[];
  metadata: Record<string, any>;
  
  // Add configuration options from the documentation
  configuration?: {
    enable_field_mapping?: boolean;
    enable_data_cleansing?: boolean;
    enable_inventory_building?: boolean;
    enable_dependency_analysis?: boolean;
    enable_technical_debt_analysis?: boolean;
    parallel_execution?: boolean;
    memory_sharing?: boolean;
    knowledge_integration?: boolean;
    confidence_threshold?: number;
  };
}

export interface FlowEvent {
  event_type: string;
  timestamp: string;
  data: any;
}

const initialState: DiscoveryFlowState = {
  session_id: '',
  flow_fingerprint: undefined,
  client_account_id: '',
  engagement_id: '',
  user_id: '',
  current_phase: 'initialization',
  phase_completion: {},
  crew_status: {},
  field_mappings: {
    mappings: {},
    confidence_scores: {},
    unmapped_fields: [],
    validation_results: {},
    agent_insights: {}
  },
  raw_data: [],
  cleaned_data: [],
  asset_inventory: {},
  agent_collaboration_map: {},
  shared_memory_id: '',
  shared_memory_reference: null,
  overall_plan: {},
  crew_coordination: {},
  errors: [],
  warnings: [],
  
  // Add missing required fields
  data_quality_metrics: {},
  app_server_dependencies: {},
  app_app_dependencies: {},
  technical_debt_assessment: {},
  discovery_summary: {},
  assessment_flow_package: {},
  
  // Real-time monitoring fields
  agent_performance_metrics: {},
  collaboration_activities: [],
  memory_analytics: {},
  knowledge_base_status: {},
  
  // Planning and intelligence fields
  planning_status: {},
  success_criteria_tracking: {},
  performance_analytics: {},
  
  // Status and completion fields
  completion_percentage: 0,
  estimated_remaining_time: 'Calculating...',
  overall_status: 'initializing'
};

export const useDiscoveryFlowState = () => {
  const [flowState, setFlowState] = useState<DiscoveryFlowState>(initialState);
  const [currentFlowId, setCurrentFlowId] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const queryClient = useQueryClient();

     // Query for flow status using event-based approach - DISABLED temporarily due to missing endpoints
   const { data: flowStatus, isLoading: isStatusLoading, error: statusError } = useQuery({
     queryKey: ['discovery-flow-status', flowState.flow_fingerprint],
     queryFn: async () => {
       // DISABLED: These endpoints don't exist yet
       // if (!flowState.flow_fingerprint) return null;
       // 
       // const response = await apiCall(`/api/v1/discovery/flow/status/${flowState.flow_fingerprint}`, {
       //   method: 'GET',
       // });
       // if (!response.ok) {
       //   throw new Error('Failed to fetch flow status');
       // }
       // return response.json();
       return null; // Return null to prevent API calls
     },
     enabled: false, // DISABLED until endpoints are implemented
     refetchInterval: false, // Disabled
     staleTime: Infinity, // Never refetch
   });

  // Query for flow events (for debugging/detailed monitoring) - DISABLED temporarily
  const { data: flowEvents } = useQuery({
    queryKey: ['discovery-flow-events', flowState.flow_fingerprint],
    queryFn: async () => {
      // DISABLED: These endpoints don't exist yet
      // if (!flowState.flow_fingerprint) return [];
      // 
      // const response = await apiCall(`/api/v1/discovery/flow/events/${flowState.flow_fingerprint}`, {
      //   method: 'GET',
      // });
      // if (!response.ok) {
      //   return []; // Graceful fallback if events not available
      // }
      // return response.json();
      return []; // Return empty array to prevent API calls
    },
    enabled: false, // DISABLED until endpoints are implemented
    refetchInterval: false, // Disabled
  });

  // Query for active flows (fallback discovery)
  const { data: activeFlows } = useQuery({
    queryKey: ['discovery-active-flows'],
    queryFn: async () => {
      const response = await apiCall('/api/v1/discovery/flow/active', {
        method: 'GET',
      });
      if (!response.ok) {
        return [];
      }
      return response.json();
    },
    enabled: false, // DISABLED: No automatic active flow discovery
    staleTime: Infinity, // Never automatically consider data stale
    refetchInterval: false, // DISABLED: No automatic polling
    refetchOnWindowFocus: false, // DISABLED: No refetch on focus
    refetchOnMount: false, // DISABLED: No refetch on mount
    refetchOnReconnect: false // DISABLED: No refetch on reconnect
  });

     // Update flow state when status changes
   useEffect(() => {
     if (flowStatus && typeof flowStatus === 'object') {
       const status = flowStatus as any; // Type assertion for API response
       setFlowState(prev => ({
         ...prev,
         flow_fingerprint: status.flow_fingerprint || prev.flow_fingerprint,
         session_id: status.session_id || prev.session_id,
         current_phase: status.current_phase || prev.current_phase,
         completion_percentage: status.completion_percentage || prev.completion_percentage,
         crew_status: status.crew_status || prev.crew_status,
         errors: status.errors || prev.errors,
         warnings: status.warnings || prev.warnings,
         overall_status: status.overall_status || prev.overall_status
       }));
     }
   }, [flowStatus]);

     // Auto-discover active flows if no flow_fingerprint set
   useEffect(() => {
     if (!flowState.flow_fingerprint && activeFlows && Array.isArray(activeFlows) && activeFlows.length > 0) {
       const latestFlow = activeFlows[0] as any; // Type assertion for API response
       setFlowState(prev => ({
         ...prev,
         flow_fingerprint: latestFlow.flow_fingerprint || prev.flow_fingerprint,
         session_id: latestFlow.session_id || prev.session_id,
         current_phase: latestFlow.current_phase || prev.current_phase,
         completion_percentage: latestFlow.completion_percentage || 0,
         overall_status: latestFlow.overall_status || 'running'
       }));
     }
   }, [activeFlows, flowState.flow_fingerprint]);

  // Functions to manage flow identifiers
  const setFlowId = useCallback((flowId: string | null) => {
    console.log('🆔 Setting flow ID (from flow creation):', flowId);
    setCurrentFlowId(flowId);
  }, []);

  const setSessionId = useCallback((sessionId: string | null) => {
    console.log('�� Setting session ID (legacy compatibility):', sessionId);
    setCurrentSessionId(sessionId);
  }, []);

  // Set flow identifier from flow creation response
  const setFlowIdentifiers = useCallback((response: { flow_fingerprint?: string; session_id?: string }) => {
    console.log('🆔 Setting flow identifiers from response:', response);
    
    // Use flow_fingerprint as primary identifier for event tracking
    const flowId = response.flow_fingerprint;
    const sessionId = response.session_id;
    
    if (flowId) {
      setCurrentFlowId(flowId);
      console.log('✅ Set flow ID for event tracking:', flowId);
    }
    
    if (sessionId) {
      setCurrentSessionId(sessionId);
      console.log('✅ Set session ID for compatibility:', sessionId);
    }
  }, []);

  // Initialize Discovery Flow with event tracking support
  const initializeFlow = useMutation({
    mutationFn: async (params: InitializeFlowParams) => {
      console.log('🚀 Initializing Discovery Flow with CrewAI Event Listener support:', params);
      
      const response = await apiCall('/api/v1/discovery/flow/run-redesigned', {
        method: 'POST',
        body: JSON.stringify({
          headers: Object.keys(params.raw_data[0] || {}),
          sample_data: params.raw_data,
          filename: params.metadata.filename || 'discovery_flow_data.json',
          options: params.configuration || {}
        }),
      });
      
      console.log('✅ Discovery Flow initialization response with flow tracking:', response);
      
      // Extract and set identifiers for event tracking
      setFlowIdentifiers(response);
      
      return response;
    },
    onSuccess: (data) => {
      console.log('✅ Discovery Flow initialized with event tracking:', data);
      
      // Invalidate and refetch the flow state to start event tracking
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-status'] });
      
      // Additional logging for debugging
      console.log('Flow ID for event tracking:', data.flow_fingerprint);
      console.log('Session ID for compatibility:', data.session_id);
      console.log('Event tracking will use flow_fingerprint as primary identifier');
    },
    onError: (error) => {
      console.error('❌ Discovery Flow initialization failed:', error);
    },
  });

  const executePhase = useCallback(async (phase: string, data: any) => {
    try {
      if (!flowState.flow_fingerprint) {
        throw new Error('No active flow to execute phase');
      }

      const response = await apiCall(`/api/v1/discovery/flow/${flowState.flow_fingerprint}/execute/${phase}`, {
        method: 'POST',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to execute phase: ${phase}`);
      }

      const result = await response.json();
      
      // Status will be updated automatically via polling
      return result;
    } catch (error) {
      setFlowState(prev => ({
        ...prev,
        errors: [...prev.errors, error instanceof Error ? error.message : 'Unknown error'],
        warnings: [...prev.warnings, error instanceof Error ? error.message : 'Unknown error'],
        overall_status: 'failed'
      }));
      throw error;
    }
  }, [flowState.flow_fingerprint]);

  const resetFlow = useCallback(() => {
    setFlowState(initialState);
    queryClient.removeQueries({ queryKey: ['discovery-flow-status'] });
    queryClient.removeQueries({ queryKey: ['discovery-flow-events'] });
  }, [queryClient]);

  return {
    flowState,
    flowEvents: flowEvents || [],
    isLoading: isStatusLoading,
    error: statusError,
    currentFlowId,
    currentSessionId,
    initializeFlow,
    setFlowId,
    setSessionId,
    setFlowIdentifiers,
    executePhase,
    resetFlow,
    invalidateState: () => queryClient.invalidateQueries({ queryKey: ['discovery-flow-status'] }),
    refreshState: () => queryClient.refetchQueries({ queryKey: ['discovery-flow-status'] }),
    getFlowEvents: () => flowEvents || [],
    isEventTrackingActive: !!flowState.flow_fingerprint,
  };
}; 