import { useState, useCallback } from 'react';
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

export const useDiscoveryFlowState = () => {
  const [currentFlowId, setCurrentFlowId] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Get flow state using CrewAI Event Listener API (proper flow tracking)
  const { data: flowState, isLoading, error } = useQuery<DiscoveryFlowState>({
    queryKey: ['discovery-flow-state', currentFlowId],
    queryFn: async (): Promise<DiscoveryFlowState> => {
      // Use flow_id (from flow creation) as primary identifier
      if (!currentFlowId) {
        throw new Error('No flow ID available for status tracking');
      }

      console.log('🔍 Fetching flow status using CrewAI Event Listener API for flow_id:', currentFlowId);

      try {
        // Use the new event-based flow status endpoint
        const response = await apiCall(`/api/v1/discovery/flow/status/${currentFlowId}`, {
          method: 'GET',
        });

        console.log('✅ Flow status response from Event Listener:', response);

        if (response.status === 'not_found') {
          console.log('⚠️ Flow not found in Event Listener, checking available flows:', response.available_flows);
          throw new Error(`Flow ${currentFlowId} not found or not yet started`);
        }

        // Transform event listener response to DiscoveryFlowState format
        const transformedState: DiscoveryFlowState = {
          session_id: currentSessionId || currentFlowId,
          flow_fingerprint: currentFlowId,
          client_account_id: 'demo-client',
          engagement_id: 'demo-engagement', 
          user_id: 'demo-user',
          current_phase: response.current_phase || 'initialization',
          phase_completion: response.completed_phases?.reduce((acc: Record<string, boolean>, phase: string) => {
            acc[phase] = true;
            return acc;
          }, {}) || {},
          crew_status: response.recent_events?.reduce((acc: Record<string, any>, event: any) => {
            if (event.crew_name) {
              acc[event.crew_name] = {
                status: event.status,
                progress: response.progress || 0,
                last_activity: event.timestamp
              };
            }
            return acc;
          }, {}) || {},
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
          completion_percentage: response.progress || 0,
          estimated_remaining_time: response.duration_seconds ? `${Math.ceil(response.duration_seconds / 60)} minutes` : 'Calculating...',
          overall_status: response.status === 'completed' ? 'completed' : 
                        response.status === 'running' ? 'in_progress' : 
                        response.status === 'error' ? 'failed' : 'initializing'
        };

        return transformedState;

      } catch (error) {
        console.error('❌ Error fetching flow status:', error);
        
        // Check for active flows as fallback
        try {
          const activeFlowsResponse = await apiCall('/api/v1/discovery/flow/active', {
            method: 'GET',
          });
          
          console.log('🔍 Available active flows:', activeFlowsResponse);
          
          if (activeFlowsResponse.active_flows?.length > 0) {
            // Try to use the most recent active flow
            const latestFlow = activeFlowsResponse.flow_details?.[0];
            if (latestFlow) {
              console.log('🔄 Using latest active flow:', latestFlow.flow_id);
              setCurrentFlowId(latestFlow.flow_id);
            }
          }
        } catch (activeFlowError) {
          console.error('❌ Error checking active flows:', activeFlowError);
        }

        throw error;
      }
    },
    enabled: !!currentFlowId,
    refetchInterval: 2000, // Poll every 2 seconds for real-time updates
    refetchIntervalInBackground: true,
    retry: 3,
    retryDelay: 1000,
  });

  // Get flow events for debugging and detailed monitoring
  const { data: flowEvents } = useQuery({
    queryKey: ['discovery-flow-events', currentFlowId],
    queryFn: async () => {
      if (!currentFlowId) return [];
      
      console.log('🔍 Fetching flow events for flow_id:', currentFlowId);
      
      const response = await apiCall(`/api/v1/discovery/flow/events/${currentFlowId}?limit=20`, {
        method: 'GET',
      });
      
      console.log('📊 Flow events:', response.events);
      return response.events || [];
    },
    enabled: !!currentFlowId,
    refetchInterval: 5000, // Refresh events every 5 seconds
  });

  // Functions to manage flow identifiers
  const setFlowId = useCallback((flowId: string | null) => {
    console.log('🆔 Setting flow ID (from flow creation):', flowId);
    setCurrentFlowId(flowId);
  }, []);

  const setSessionId = useCallback((sessionId: string | null) => {
    console.log('🆔 Setting session ID (legacy compatibility):', sessionId);
    setCurrentSessionId(sessionId);
  }, []);

  // Set flow identifier from flow creation response
  const setFlowIdentifiers = useCallback((response: { flow_id?: string; session_id?: string; flow_fingerprint?: string }) => {
    console.log('🆔 Setting flow identifiers from response:', response);
    
    // Use flow_id as primary identifier for event tracking
    const flowId = response.flow_id;
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
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
      
      // Additional logging for debugging
      console.log('Flow ID for event tracking:', data.flow_id);
      console.log('Session ID for compatibility:', data.session_id);
      console.log('Event tracking will use flow_id as primary identifier');
    },
    onError: (error) => {
      console.error('❌ Discovery Flow initialization failed:', error);
    },
  });

  return {
    // State
    flowState,
    flowEvents,
    isLoading,
    error,
    currentFlowId,
    currentSessionId,
    
    // Actions
    initializeFlow,
    setFlowId,
    setSessionId,
    setFlowIdentifiers,
    
    // Helper functions
    invalidateState: () => queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] }),
    refreshState: () => queryClient.refetchQueries({ queryKey: ['discovery-flow-state'] }),
    
    // Event tracking helpers
    getFlowEvents: () => flowEvents || [],
    isEventTrackingActive: () => !!currentFlowId,
  };
}; 