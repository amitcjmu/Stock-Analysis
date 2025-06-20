import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '../use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { useDiscoveryFlowState } from './useDiscoveryFlowState';
import { 
  DependencyData, 
  DependencyAnalysisResponse,
  DependencyCreateResponse,
  DependencyUpdateResponse,
  AppServerMapping,
  CrossApplicationMapping
} from '../../types/dependency';
import { apiCall } from '../../config/api';

// This file is being completely rewritten to follow the correct architectural pattern
// observed in other discovery modules like Inventory. It will manage its own state
// and call its own dedicated API endpoints, rather than relying on the central
// discovery flow state for its core data.

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
  const { toast } = useToast();
  const { client, engagement, getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeView, setActiveView] = useState<'app-server' | 'app-app'>('app-server');

  // Fetch dependency data
  const { 
    data: dependencyResponse,
    isLoading,
    error,
    refetch: refetchDependencies
  } = useQuery<DependencyAnalysisResponse>({
    queryKey: ['dependencies', client?.id, engagement?.id],
    queryFn: async () => {
      const headers = getAuthHeaders();
      const response = await apiCall('/api/v1/discovery/dependencies/analysis', {
        method: 'GET',
        headers
      }) as DependencyAnalysisResponse;
      
      return response || { 
        success: true,
        message: 'No dependencies found',
        data: DEFAULT_DEPENDENCY_DATA
      };
    },
    enabled: !!client && !!engagement
  });

  // Analyze dependencies
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
      const headers = getAuthHeaders();
      
      await apiCall('/api/v1/discovery/dependencies/analyze', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          dependency_type: activeView,
          client_account_id: client.id,
          engagement_id: engagement.id
        })
      });

      toast({
        title: "✅ Analysis Started",
        description: "Dependency analysis is in progress..."
      });

      // Poll for results
      const pollInterval = setInterval(async () => {
        const result = await refetchDependencies();
        const isComplete = activeView === 'app-server' 
          ? result?.data?.app_server_mapping?.hosting_relationships?.length > 0
          : result?.data?.cross_application_mapping?.cross_app_dependencies?.length > 0;

        if (isComplete) {
          clearInterval(pollInterval);
          setIsAnalyzing(false);
          toast({
            title: "✅ Analysis Complete",
            description: "Dependency analysis has been completed."
          });
        }
      }, 2000);

      // Cleanup interval after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        setIsAnalyzing(false);
      }, 300000);

    } catch (error) {
      console.error('Failed to analyze dependencies:', error);
      setIsAnalyzing(false);
      toast({
        title: "❌ Analysis Failed",
        description: "Could not complete dependency analysis. Please try again.",
        variant: "destructive"
      });
    }
  }, [client, engagement, activeView, toast, refetchDependencies, getAuthHeaders]);

  // Check if we can continue to next phase
  const canContinueToNextPhase = useCallback(() => {
    if (!dependencyResponse?.data) return false;

    const appServerComplete = dependencyResponse.data.app_server_mapping.hosting_relationships.length > 0;
    const crossAppComplete = dependencyResponse.data.cross_application_mapping.cross_app_dependencies.length > 0;

    return appServerComplete && crossAppComplete;
  }, [dependencyResponse]);

  return {
    dependencyData: dependencyResponse?.data || DEFAULT_DEPENDENCY_DATA,
    isLoading,
    error,
    isAnalyzing,
    analyzeDependencies,
    activeView,
    setActiveView,
    canContinueToNextPhase
  };
}; 