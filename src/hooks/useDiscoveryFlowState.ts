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

  // Get flow state with comprehensive monitoring using flow fingerprint as primary ID
  const { data: flowState, isLoading, error } = useQuery<DiscoveryFlowState>({
    queryKey: ['discovery-flow-state', currentFlowId, currentSessionId],
    queryFn: async (): Promise<DiscoveryFlowState> => {
      // Use flow_id (fingerprint) as primary identifier, session_id as fallback
      const identifier = currentFlowId || currentSessionId;
      
      if (!identifier) {
        throw new Error('No flow ID or session ID available');
      }

      console.log('🔍 Fetching Discovery Flow status for identifier:', identifier);
      console.log('🔍 Flow ID (fingerprint):', currentFlowId);
      console.log('🔍 Session ID (fallback):', currentSessionId);

      try {
        // Try comprehensive dashboard endpoint first with the identifier
        try {
          const response = await apiCall(`/api/v1/discovery/flow/ui/dashboard-data/${identifier}`);
          console.log('✅ Successfully fetched dashboard data:', response);
          
          // Transform dashboard data to full flow state
          return {
            session_id: currentSessionId || identifier,
            flow_fingerprint: currentFlowId || response.flow_fingerprint || identifier,
            client_account_id: response.dashboard_data?.session_info?.client_account_id || '',
            engagement_id: response.dashboard_data?.session_info?.engagement_id || '',
            user_id: response.dashboard_data?.session_info?.user_id || '',
            current_phase: response.dashboard_data?.overview?.current_phase || 'field_mapping',
            completion_percentage: response.dashboard_data?.overview?.completion || 0,
            estimated_remaining_time: response.dashboard_data?.overview?.estimated_remaining || '',
            overall_status: response.dashboard_data?.overview?.status || 'initializing',
            
            // Crew status from cards
            crew_status: response.dashboard_data?.crew_cards?.reduce((acc: any, card: any) => {
              acc[card.crew_name] = {
                status: card.status,
                manager: card.manager,
                progress: card.progress,
                agents: card.agents,
                key_metrics: card.key_metrics
              };
              return acc;
            }, {}),
            
            // Phase completion tracking
            phase_completion: response.dashboard_data?.crew_cards?.reduce((acc: any, card: any) => {
              acc[card.crew_name] = card.status === 'completed';
              return acc;
            }, {}),
            
            // Memory and collaboration
            shared_memory_id: response.dashboard_data?.memory_visualization?.memory_id || '',
            collaboration_activities: response.dashboard_data?.collaboration_network?.activities || [],
            memory_analytics: response.dashboard_data?.memory_visualization || {},
            
            // Performance metrics
            agent_performance_metrics: response.dashboard_data?.performance_charts || {},
            performance_analytics: response.dashboard_data?.performance_charts || {},
            
            // Default values for other fields
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
            data_quality_metrics: {},
            app_server_dependencies: {},
            app_app_dependencies: {},
            technical_debt_assessment: {},
            discovery_summary: {},
            assessment_flow_package: {},
            agent_collaboration_map: {},
            overall_plan: {},
            crew_coordination: {},
            planning_status: {},
            success_criteria_tracking: {},
            knowledge_base_status: {},
            errors: [],
            warnings: []
          } as DiscoveryFlowState;
          
        } catch (dashboardError) {
          console.log('⚠️ Dashboard endpoint failed, trying status endpoint:', dashboardError);
          
          // Fallback to status endpoint
          const statusResponse = await apiCall(`/api/v1/discovery/flow/agentic-analysis/status-public?session_id=${identifier}`);
          console.log('✅ Successfully fetched status data:', statusResponse);
          
          return {
            session_id: currentSessionId || identifier,
            flow_fingerprint: currentFlowId || statusResponse.flow_fingerprint || identifier,
            client_account_id: statusResponse.session_info?.client_account_id || '',
            engagement_id: statusResponse.session_info?.engagement_id || '',
            user_id: statusResponse.session_info?.user_id || '',
            current_phase: statusResponse.current_phase || 'field_mapping',
            completion_percentage: statusResponse.completion_percentage || 0,
            estimated_remaining_time: statusResponse.estimated_remaining || '',
            overall_status: statusResponse.overall_status || 'initializing',
            crew_status: statusResponse.crew_status || {},
            phase_completion: statusResponse.phase_completion || {},
            shared_memory_id: statusResponse.shared_memory_status?.memory_id || '',
            collaboration_activities: statusResponse.agent_collaboration_activities || [],
            memory_analytics: statusResponse.shared_memory_status || {},
            agent_performance_metrics: statusResponse.performance_metrics || {},
            performance_analytics: statusResponse.performance_metrics || {},
            
            // Default values for other fields
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
            data_quality_metrics: {},
            app_server_dependencies: {},
            app_app_dependencies: {},
            technical_debt_assessment: {},
            discovery_summary: {},
            assessment_flow_package: {},
            agent_collaboration_map: {},
            overall_plan: {},
            crew_coordination: {},
            planning_status: {},
            success_criteria_tracking: {},
            knowledge_base_status: {},
            errors: [],
            warnings: []
          } as DiscoveryFlowState;
        }
        
      } catch (statusError) {
        console.log('⚠️ Status endpoint also failed, trying active flows:', statusError);
        
        // Try active flows endpoint as final fallback
        try {
          const activeResponse = await apiCall('/api/v1/discovery/flow/active');
          console.log('✅ Successfully fetched active flows:', activeResponse);
          
          // Find our flow in active flows by either flow_id or session_id
          const activeFlow = activeResponse.active_flows?.find((flow: any) => 
            flow.session_id === identifier || 
            flow.flow_id === identifier ||
            flow.flow_fingerprint === identifier
          );
          
          if (activeFlow) {
            return {
              session_id: currentSessionId || activeFlow.session_id || identifier,
              flow_fingerprint: currentFlowId || activeFlow.flow_fingerprint || activeFlow.flow_id || identifier,
              client_account_id: activeFlow.client_account_id || '',
              engagement_id: activeFlow.engagement_id || '',
              user_id: activeFlow.user_id || '',
              current_phase: activeFlow.current_phase || 'field_mapping',
              completion_percentage: activeFlow.completion_percentage || 0,
              estimated_remaining_time: activeFlow.estimated_remaining || '',
              overall_status: activeFlow.status || 'in_progress',
              crew_status: activeFlow.crew_status || {},
              phase_completion: activeFlow.phase_completion || {},
              shared_memory_id: activeFlow.shared_memory_id || '',
              collaboration_activities: [],
              memory_analytics: {},
              agent_performance_metrics: {},
              performance_analytics: {},
              
              // Default values for other fields
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
              data_quality_metrics: {},
              app_server_dependencies: {},
              app_app_dependencies: {},
              technical_debt_assessment: {},
              discovery_summary: {},
              assessment_flow_package: {},
              agent_collaboration_map: {},
              overall_plan: {},
              crew_coordination: {},
              planning_status: {},
              success_criteria_tracking: {},
              knowledge_base_status: {},
              errors: [],
              warnings: []
            } as DiscoveryFlowState;
          }
        } catch (activeError) {
          console.log('⚠️ Active flows endpoint also failed:', activeError);
        }
        
        // Create mock state when no active flow found
        console.log('🔧 Creating mock active flow state');
        return {
          session_id: currentSessionId || identifier,
          flow_fingerprint: currentFlowId || identifier,
          client_account_id: '',
          engagement_id: '',
          user_id: '',
          current_phase: 'field_mapping',
          completion_percentage: 0,
          estimated_remaining_time: 'Calculating...',
          overall_status: 'initializing',
          phase_completion: { field_mapping: false },
          crew_status: { field_mapping: 'active' },
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
          data_quality_metrics: {},
          app_server_dependencies: {},
          app_app_dependencies: {},
          technical_debt_assessment: {},
          discovery_summary: {},
          assessment_flow_package: {},
          agent_collaboration_map: {},
          shared_memory_id: '',
          overall_plan: {},
          crew_coordination: {},
          collaboration_activities: [],
          memory_analytics: {},
          agent_performance_metrics: {},
          performance_analytics: {},
          planning_status: {},
          success_criteria_tracking: {},
          knowledge_base_status: {},
          errors: [],
          warnings: []
        } as DiscoveryFlowState;
        
      }
    },
    enabled: !!currentFlowId || !!currentSessionId,
    refetchInterval: 10000, // Poll every 10 seconds for real-time updates
    refetchIntervalInBackground: false,
    retry: 1,
    staleTime: 5000,
  });

  // Functions to manage flow and session identifiers
  const setFlowId = useCallback((flowId: string | null) => {
    console.log('🆔 Setting flow ID (fingerprint):', flowId);
    setCurrentFlowId(flowId);
  }, []);

  const setSessionId = useCallback((sessionId: string | null) => {
    console.log('🆔 Setting session ID:', sessionId);
    setCurrentSessionId(sessionId);
  }, []);

  // Set both identifiers from flow creation response
  const setFlowIdentifiers = useCallback((response: { flow_id?: string; session_id?: string; flow_fingerprint?: string }) => {
    console.log('🆔 Setting flow identifiers from response:', response);
    
    // Prefer flow_fingerprint, then flow_id, then session_id for flow identification
    const flowId = response.flow_fingerprint || response.flow_id;
    const sessionId = response.session_id;
    
    if (flowId) {
      setCurrentFlowId(flowId);
      console.log('✅ Set flow ID (fingerprint):', flowId);
    }
    
    if (sessionId) {
      setCurrentSessionId(sessionId);
      console.log('✅ Set session ID:', sessionId);
    }
  }, []);

  // Initialize Discovery Flow with updated response handling
  const initializeFlow = useMutation({
    mutationFn: async (params: InitializeFlowParams) => {
      console.log('🚀 Initializing Discovery Flow with params:', params);
      
      const response = await apiCall('/api/v1/discovery/flow/run-redesigned', {
        method: 'POST',
        body: JSON.stringify({
          headers: Object.keys(params.raw_data[0] || {}),
          sample_data: params.raw_data,
          filename: params.metadata.filename || 'discovery_flow_data.json',
          options: params.configuration || {}
        }),
      });
      
      console.log('✅ Discovery Flow initialization response:', response);
      
      // Extract and set identifiers from response
      setFlowIdentifiers(response);
      
      return response;
    },
    onSuccess: (data) => {
      console.log('✅ Discovery Flow initialized successfully:', data);
      
      // Invalidate and refetch the flow state
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
      
      // Additional logging for debugging
      console.log('Flow ID (fingerprint):', data.flow_fingerprint || data.flow_id);
      console.log('Session ID:', data.session_id);
      console.log('Architecture:', data.architecture);
      console.log('Next phase:', data.next_phase);
    },
    onError: (error) => {
      console.error('❌ Discovery Flow initialization failed:', error);
    },
  });

  // Add mutation functions for all 6 crews
  const executeFieldMappingCrewMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await apiCall(`/api/v1/discovery/flow/crews/field-mapping/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          options: {
            use_shared_memory: true,
            apply_knowledge_base: true,
            enable_collaboration: true,
            confidence_threshold: 0.8
          }
        })
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    }
  });

  const executeDataCleansingCrewMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await apiCall(`/api/v1/discovery/flow/crews/data-cleansing/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    }
  });

  const executeInventoryBuildingCrewMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await apiCall(`/api/v1/discovery/flow/crews/inventory-building/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    }
  });

  const executeAppServerDependencyCrewMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await apiCall(`/api/v1/discovery/flow/crews/app-server-dependency/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    }
  });

  const executeAppAppDependencyCrewMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await apiCall(`/api/v1/discovery/flow/crews/app-app-dependency/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    }
  });

  const executeTechnicalDebtCrewMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await apiCall(`/api/v1/discovery/flow/crews/technical-debt/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
    }
  });

  // Enhanced crew status function
  const getCrewStatus = useCallback(async (sessionId: string, crewName: string) => {
    try {
      const response = await apiCall(`/api/v1/discovery/flow/crews/${crewName}/details/${sessionId}`);
      return response;
    } catch (error) {
      console.error(`Failed to get crew status for ${crewName}:`, error);
      return null;
    }
  }, []);

  // Memory and collaboration monitoring
  const getMemoryStatus = useCallback(async (sessionId: string) => {
    try {
      const response = await apiCall(`/api/v1/discovery/flow/memory/status/${sessionId}`);
      return response;
    } catch (error) {
      console.error('Failed to get memory status:', error);
      return null;
    }
  }, []);

  const getCollaborationTracking = useCallback(async (sessionId: string) => {
    try {
      const response = await apiCall(`/api/v1/discovery/flow/collaboration/tracking/${sessionId}`);
      return response;
    } catch (error) {
      console.error('Failed to get collaboration tracking:', error);
      return null;
    }
  }, []);

  const getAgentPerformance = useCallback(async (sessionId: string) => {
    try {
      const response = await apiCall(`/api/v1/discovery/flow/agents/performance/${sessionId}`);
      return response;
    } catch (error) {
      console.error('Failed to get agent performance:', error);
      return null;
    }
  }, []);

  return {
    // State
    flowState,
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
    
    // Crew execution functions
    executeFieldMappingCrew: executeFieldMappingCrewMutation.mutateAsync,
    executeDataCleansingCrew: executeDataCleansingCrewMutation.mutateAsync,
    executeInventoryBuildingCrew: executeInventoryBuildingCrewMutation.mutateAsync,
    executeAppServerDependencyCrew: executeAppServerDependencyCrewMutation.mutateAsync,
    executeAppAppDependencyCrew: executeAppAppDependencyCrewMutation.mutateAsync,
    executeTechnicalDebtCrew: executeTechnicalDebtCrewMutation.mutateAsync,
    
    // Status and monitoring
    getCrewStatus,
    getMemoryStatus,
    getCollaborationTracking,
    getAgentPerformance,
    
    // Loading states
    isInitializing: initializeFlow.isPending,
    isExecutingCrew: executeFieldMappingCrewMutation.isPending || 
                     executeDataCleansingCrewMutation.isPending || 
                     executeInventoryBuildingCrewMutation.isPending ||
                     executeAppServerDependencyCrewMutation.isPending ||
                     executeAppAppDependencyCrewMutation.isPending ||
                     executeTechnicalDebtCrewMutation.isPending
  };
}; 