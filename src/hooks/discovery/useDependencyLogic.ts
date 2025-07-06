import { useState, useCallback } from 'react';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';

export const useDependencyLogic = (flowId?: string) => {
  // Use the unified discovery flow
  const {
    flowState: flow,
    isLoading,
    error,
    executeFlowPhase: updatePhase,
    refreshFlow: refresh
  } = useUnifiedDiscoveryFlow(flowId);

  // Local UI state
  const [activeView, setActiveView] = useState<'app-server' | 'app-app'>('app-server');

  // Extract dependency analysis data from flow state
  const dependencyData = {
    cross_application_mapping: flow?.results?.dependency_analysis?.cross_application_mapping || flow?.dependency_analysis?.cross_application_mapping || [],
    app_server_mapping: flow?.results?.dependency_analysis?.app_server_mapping || flow?.dependency_analysis?.app_server_mapping || [],
    flow_id: flow?.flow_id,
    crew_completion_status: flow?.phases || {},
    analysis_progress: {
      total_applications: flow?.results?.dependency_analysis?.total_applications || flow?.dependency_analysis?.total_applications || 0,
      mapped_dependencies: flow?.results?.dependency_analysis?.mapped_dependencies || flow?.dependency_analysis?.mapped_dependencies || 0,
      completion_percentage: flow?.progress_percentage || 0
    },
    // Add additional dependency data from flow state
    dependency_relationships: flow?.results?.dependency_analysis?.dependency_relationships || flow?.dependency_analysis?.dependency_relationships || [],
    dependency_matrix: flow?.results?.dependency_analysis?.dependency_matrix || flow?.dependency_analysis?.dependency_matrix || {},
    critical_dependencies: flow?.results?.dependency_analysis?.critical_dependencies || flow?.dependency_analysis?.critical_dependencies || [],
    orphaned_assets: flow?.results?.dependency_analysis?.orphaned_assets || flow?.dependency_analysis?.orphaned_assets || [],
    dependency_complexity_score: flow?.results?.dependency_analysis?.complexity_score || flow?.dependency_analysis?.complexity_score || 0,
    recommendations: flow?.results?.dependency_analysis?.recommendations || flow?.dependency_analysis?.recommendations || []
  };

  // Loading and analyzing states
  const isAnalyzing = isLoading;

  // Action handlers
  const analyzeDependencies = useCallback(async () => {
    if (flow?.flow_id) {
      await updatePhase('dependency_analysis', { trigger_analysis: true });
    }
  }, [flow, updatePhase]);

  const canContinueToNextPhase = useCallback(() => {
    return flow?.phases?.dependency_analysis === true || flow?.phases?.dependencies_completed === true;
  }, [flow]);

  return {
    dependencyData,
    isLoading,
    error,
    isAnalyzing,
    analyzeDependencies,
    activeView,
    setActiveView,
    canContinueToNextPhase
  };
}; 