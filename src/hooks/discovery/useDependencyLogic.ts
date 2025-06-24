import { useState, useCallback } from 'react';
import { useDiscoveryFlowV2 } from './useDiscoveryFlowV2';

export const useDependencyLogic = (flowId?: string) => {
  // Use the V2 discovery flow
  const {
    flow,
    isLoading,
    error,
    updatePhase,
    refresh
  } = useDiscoveryFlowV2(flowId);

  // Local UI state
  const [activeView, setActiveView] = useState<'app-server' | 'app-app'>('app-server');

  // Get dependency analysis data from V2 flow
  const dependencyData = {
    cross_application_mapping: [],
    app_server_mapping: [],
    session_id: flow?.flow_id,
    crew_completion_status: flow?.phases || {},
    analysis_progress: {
      total_applications: 0,
      mapped_dependencies: 0,
      completion_percentage: flow?.progress_percentage || 0
    }
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
    return flow?.phases?.dependency_analysis === true;
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