import { useState, useCallback } from 'react';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';

export const useDependencyLogic = () => {
  // Use the unified discovery flow
  const {
    flowState,
    isLoading,
    error,
    getPhaseData,
    isPhaseComplete,
    canProceedToPhase,
    executeFlowPhase,
    isExecutingPhase,
    refreshFlow
  } = useUnifiedDiscoveryFlow();

  // Local UI state
  const [activeView, setActiveView] = useState<'app-server' | 'app-app'>('app-server');

  // Get dependency analysis data from unified flow
  const dependencyData = getPhaseData('dependency_analysis') || {
    cross_application_mapping: [],
    app_server_mapping: [],
    session_id: flowState?.session_id,
    crew_completion_status: {},
    analysis_progress: {
      total_applications: 0,
      mapped_dependencies: 0,
      completion_percentage: 0
    }
  };

  // Loading and analyzing states
  const isAnalyzing = isExecutingPhase;

  // Action handlers
  const analyzeDependencies = useCallback(async () => {
    await executeFlowPhase('dependency_analysis');
  }, [executeFlowPhase]);

  const canContinueToNextPhase = useCallback(() => {
    return canProceedToPhase('tech_debt_analysis');
  }, [canProceedToPhase]);

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