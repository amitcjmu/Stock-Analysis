import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useToast } from '../use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '../../config/api';
import { useDiscoveryFlowState } from './useDiscoveryFlowState';

// Types
interface DependencyData {
  cross_application_mapping: {
    cross_app_dependencies: any[];
    application_clusters: any[];
    dependency_graph: { nodes: any[]; edges: any[] };
    suggested_patterns: any[];
    confidence_scores: Record<string, number>;
  };
  app_server_mapping: {
    hosting_relationships: any[];
    suggested_mappings: any[];
    confidence_scores: Record<string, number>;
  };
  session_id: string;
  crew_completion_status: Record<string, boolean>;
}

const DEFAULT_DEPENDENCY_DATA: DependencyData = {
  cross_application_mapping: {
    cross_app_dependencies: [],
    application_clusters: [],
    dependency_graph: { nodes: [], edges: [] },
    suggested_patterns: [],
    confidence_scores: {}
  },
  app_server_mapping: {
    hosting_relationships: [],
    suggested_mappings: [],
    confidence_scores: {}
  },
  session_id: '',
  crew_completion_status: {}
};

export const useDependencyLogic = () => {
  const location = useLocation();
  const { user, client, engagement } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Local state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeView, setActiveView] = useState<'app-server' | 'app-app'>('app-server');
  const uploadProcessedRef = useRef(false);

  // Get discovery flow state to access dependency data
  const { flowState, isLoading: isFlowStateLoading, error: flowStateError } = useDiscoveryFlowState();

  // Fallback dependency data from the main dependencies endpoint (if flow state not available)
  const { data: fallbackDependencyData } = useQuery({
    queryKey: ['dependency-analysis-fallback', client?.id, engagement?.id],
    queryFn: async () => {
      const response = await apiCall('/discovery/dependencies', {
        method: 'GET'
      });
      return response;
    },
    enabled: !!client?.id && !!engagement?.id && !flowState,
    staleTime: 30000, // 30 seconds
    retry: 1
  });

  // Extract dependency data from flow state or fallback
  const dependencyData = useMemo(() => {
    // Try flow state first (preferred)
    if (flowState?.phase_data) {
      const phaseData = flowState.phase_data;
      
      return {
        cross_application_mapping: {
          cross_app_dependencies: phaseData.app_app_dependencies?.communication_patterns || [],
          application_clusters: phaseData.app_app_dependencies?.application_clusters || [],
          dependency_graph: phaseData.app_app_dependencies?.dependency_graph || { nodes: [], edges: [] },
          suggested_patterns: phaseData.app_app_dependencies?.suggested_patterns || [],
          confidence_scores: phaseData.app_app_dependencies?.confidence_scores || {}
        },
        app_server_mapping: {
          hosting_relationships: phaseData.app_server_dependencies?.hosting_relationships || [],
          suggested_mappings: phaseData.app_server_dependencies?.suggested_mappings || [],
          confidence_scores: phaseData.app_server_dependencies?.confidence_scores || {}
        },
        session_id: flowState.session_id || '',
        crew_completion_status: flowState.phase_completion || {}
      };
    }
    
    // Fallback to direct API data
    if (fallbackDependencyData?.data) {
      const data = fallbackDependencyData.data;
      
      return {
        cross_application_mapping: {
          cross_app_dependencies: data.cross_application_mapping?.cross_app_dependencies || [],
          application_clusters: data.cross_application_mapping?.application_clusters || [],
          dependency_graph: data.cross_application_mapping?.dependency_graph || { nodes: [], edges: [] },
          suggested_patterns: data.cross_application_mapping?.suggested_patterns || [],
          confidence_scores: data.cross_application_mapping?.confidence_scores || {}
        },
        app_server_mapping: {
          hosting_relationships: [],
          suggested_mappings: [],
          confidence_scores: {}
        },
        session_id: '',
        crew_completion_status: {}
      };
    }
    
    return DEFAULT_DEPENDENCY_DATA;
  }, [flowState, fallbackDependencyData]);

  // Initialize from navigation state (from previous Discovery pages)
  useEffect(() => {
    const handleFlowContinuation = async () => {
      if (!client || !engagement) return;

      const state = location.state as any;
      
      if (state?.from_discovery_flow && !uploadProcessedRef.current) {
        uploadProcessedRef.current = true;
        
        toast({
          title: "🚀 Dependency Analysis",
          description: "Loading dependency analysis data...",
        });
      }
    };

    handleFlowContinuation();
  }, [location.state, client, engagement, toast]);

  // Analyze dependencies function
  const analyzeDependencies = useCallback(async () => {
    if (!client?.id || !engagement?.id) {
      toast({
        title: "❌ Missing Context",
        description: "Please select a client and engagement first.",
        variant: "destructive"
      });
      return;
    }

    try {
      setIsAnalyzing(true);
      
      toast({
        title: "🔄 Refreshing Dependencies",
        description: `Refreshing ${activeView} dependency data...`
      });

      // Invalidate the query to refetch data
      queryClient.invalidateQueries({ queryKey: ['dependency-analysis', client.id, engagement.id] });

      toast({
        title: "✅ Refresh Complete",
        description: "Dependency data has been refreshed."
      });

    } catch (error) {
      console.error('Failed to refresh dependencies:', error);
      toast({
        title: "❌ Refresh Failed",
        description: "Could not refresh dependency data. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [client, engagement, activeView, queryClient, toast]);

  // Check if we can continue to next phase
  const canContinueToNextPhase = useCallback(() => {
    if (!dependencyData) return false;

    const appServerComplete = dependencyData.app_server_mapping.hosting_relationships.length > 0;
    const crossAppComplete = dependencyData.cross_application_mapping.cross_app_dependencies.length > 0;

    return appServerComplete || crossAppComplete; // At least one type should be complete
  }, [dependencyData]);

  return {
    dependencyData,
    isLoading: isFlowStateLoading,
    error: flowStateError,
    isAnalyzing,
    analyzeDependencies,
    activeView,
    setActiveView,
    canContinueToNextPhase
  };
}; 