import { useState, useCallback } from 'react';
import { useDiscoveryFlowV2 } from './useDiscoveryFlowV2';

export const useTechDebtLogic = (flowId?: string) => {
  // Use the V2 discovery flow
  const {
    flow,
    isLoading,
    error,
    updatePhase,
    refresh
  } = useDiscoveryFlowV2(flowId);

  // Local UI state
  const [activeView, setActiveView] = useState<'debt-scores' | 'modernization'>('debt-scores');

  // Extract tech debt analysis data from flow state
  const techDebtData = {
    debt_scores: flow?.results?.tech_debt_analysis?.debt_scores || flow?.tech_debt_analysis?.debt_scores || {},
    modernization_recommendations: flow?.results?.tech_debt_analysis?.modernization_recommendations || flow?.tech_debt_analysis?.modernization_recommendations || [],
    risk_assessments: flow?.results?.tech_debt_analysis?.risk_assessments || flow?.tech_debt_analysis?.risk_assessments || {},
    six_r_preparation: flow?.results?.tech_debt_analysis?.six_r_preparation || flow?.tech_debt_analysis?.six_r_preparation || {},
    session_id: flow?.flow_id,
    crew_completion_status: flow?.phases || {},
    analysis_progress: {
      total_assets: flow?.results?.tech_debt_analysis?.total_assets || flow?.tech_debt_analysis?.total_assets || 0,
      analyzed_assets: flow?.results?.tech_debt_analysis?.analyzed_assets || flow?.tech_debt_analysis?.analyzed_assets || 0,
      completion_percentage: flow?.progress_percentage || 0
    },
    // Add additional tech debt data from flow state
    debt_categories: flow?.results?.tech_debt_analysis?.debt_categories || flow?.tech_debt_analysis?.debt_categories || [],
    modernization_priorities: flow?.results?.tech_debt_analysis?.modernization_priorities || flow?.tech_debt_analysis?.modernization_priorities || [],
    technology_stack_analysis: flow?.results?.tech_debt_analysis?.technology_stack_analysis || flow?.tech_debt_analysis?.technology_stack_analysis || {},
    migration_complexity_scores: flow?.results?.tech_debt_analysis?.migration_complexity_scores || flow?.tech_debt_analysis?.migration_complexity_scores || {},
    cost_benefit_analysis: flow?.results?.tech_debt_analysis?.cost_benefit_analysis || flow?.tech_debt_analysis?.cost_benefit_analysis || {},
    recommendations: flow?.results?.tech_debt_analysis?.recommendations || flow?.tech_debt_analysis?.recommendations || []
  };

  // Loading and analyzing states
  const isAnalyzing = isLoading;

  // Action handlers
  const analyzeTechDebt = useCallback(async () => {
    if (flow?.flow_id) {
      await updatePhase('tech_debt_analysis', { trigger_analysis: true });
    }
  }, [flow, updatePhase]);

  const canContinueToNextPhase = useCallback(() => {
    return flow?.phases?.tech_debt_analysis === true || flow?.phases?.tech_debt_completed === true;
  }, [flow]);

  return {
    techDebtData,
    isLoading,
    error,
    isAnalyzing,
    analyzeTechDebt,
    activeView,
    setActiveView,
    canContinueToNextPhase
  };
}; 