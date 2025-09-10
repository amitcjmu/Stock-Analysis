import { useState, useCallback, useMemo } from 'react'
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';
import { masterFlowService } from '../../services/api/masterFlowService';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';

export const useInventoryLogic = (flowId?: string): JSX.Element => {
  const { client, engagement } = useAuth();

  // Use the unified discovery flow
  const {
    flowState: flow,
    isLoading,
    error,
    executeFlowPhase: updatePhase,
    refreshFlow: refresh
  } = useUnifiedDiscoveryFlow(flowId);

  // Extract assets from flow state
  const assets = flow?.asset_inventory?.assets || [];

  // Local UI state for filters, pagination, etc.
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [filters, setFilters] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);

  // Get asset inventory data from unified flow (now from assets table)
  const flowAssets = assets || [];
  const summary = { total: flowAssets.length };
  interface Asset {
    asset_type?: string;
    [key: string]: unknown;
  }

  const typedFlowAssets = flowAssets as Asset[];

  const inventoryProgress = useMemo(() => ({
    total_assets: typedFlowAssets.length,
    classified_assets: typedFlowAssets.filter((asset: Asset) => asset.asset_type).length,
    classification_accuracy: typedFlowAssets.length > 0 ? (typedFlowAssets.filter((asset: Asset) => asset.asset_type).length / typedFlowAssets.length) * 100 : 0
  }), [typedFlowAssets]);

  // Get real classification summary from backend
  const { data: classificationSummary, isLoading: isClassificationLoading } = useQuery({
    queryKey: ['classification-summary', flowId, client?.id],
    queryFn: async () => {
      if (!flowId || !client?.id) return null;
      try {
        const flowStatus = await masterFlowService.getFlowStatus(flowId, client.id, engagement?.id);
        return flowStatus.metadata?.classification_summary || null;
      } catch (error) {
        console.error('Failed to get classification summary:', error);
        return null;
      }
    },
    enabled: !!flowId && !!client?.id,
    staleTime: 30000
  });

  // Get real CrewAI insights from backend
  const { data: crewaiInsights, isLoading: isInsightsLoading } = useQuery({
    queryKey: ['crewai-insights', flowId, client?.id],
    queryFn: async () => {
      if (!flowId || !client?.id) return null;
      try {
        const flowStatus = await masterFlowService.getFlowStatus(flowId, client.id, engagement?.id);
        return flowStatus.metadata?.crewai_insights || null;
      } catch (error) {
        console.error('Failed to get CrewAI insights:', error);
        return null;
      }
    },
    enabled: !!flowId && !!client?.id,
    staleTime: 30000
  });

  // Enhanced asset classification data with real counts
  const assetClassification = {
    total: classificationSummary?.total_assets || summary.total,
    servers: classificationSummary?.by_type?.servers || 0,
    applications: classificationSummary?.by_type?.applications || 0,
    databases: classificationSummary?.by_type?.databases || 0,
    devices: classificationSummary?.by_type?.devices || 0,
    virtual_machines: classificationSummary?.by_type?.virtual_machines || 0,
    containers: classificationSummary?.by_type?.containers || 0,
    other: classificationSummary?.by_type?.other || 0,
    accuracy: classificationSummary?.classification_accuracy || inventoryProgress.classification_accuracy
  };

  // Enhanced insights with real CrewAI data
  const insights = {
    recommendations: crewaiInsights || [],
    patterns: {
      infrastructure_analysis: crewaiInsights?.find(i => i.category === 'Infrastructure Intelligence')?.recommendations,
      migration_readiness: crewaiInsights?.find(i => i.category === 'Migration Intelligence')?.recommendations,
      risk_assessment: crewaiInsights?.find(i => i.category === 'Risk Intelligence')?.recommendations
    },
    confidence_scores: {
      overall: crewaiInsights?.reduce((acc, insight) => acc + insight.confidence_score, 0) / (crewaiInsights?.length || 1) || 85.0
    }
  };

  // Pagination
  const pagination = {
    currentPage,
    pageSize,
    total: summary.total || 0,
    totalPages: Math.ceil((summary.total || 0) / pageSize)
  };

  // Loading states
  const isFlowStateLoading = isLoading || isClassificationLoading || isInsightsLoading;
  const isAnalyzing = isLoading;
  const lastUpdated = new Date();

  // Error states
  const flowStateError = error;

  // Action handlers
  const handleTriggerInventoryAnalysis = useCallback(async () => {
    if (flow?.flow_id) {
      await updatePhase('asset_inventory', { trigger_agent: true }); // Now uses persistent agents
    }
  }, [flow, updatePhase]);

  const handleCompleteInventoryAndTriggerParallelAnalysis = useCallback(async () => {
    if (flow?.flow_id) {
      // Complete inventory and automatically trigger parallel dependencies + tech debt analysis
      await updatePhase('inventory_completed', {
        trigger_parallel_analysis: true,
        execute_dependencies_and_tech_debt: true
      });
    }
  }, [flow, updatePhase]);

  const fetchAssets = useCallback(async () => {
    refresh();
  }, [refresh]);

  const fetchInsights = useCallback(async () => {
    // Refresh is handled by React Query automatically
  }, []);

  // Enhanced handlers with real data integration
  const canContinueToNextPhase = useCallback(() => {
    return flow?.next_phase && inventoryProgress.total_assets > 0;
  }, [flow, inventoryProgress]);

  const handleContinueToNextPhase = useCallback(async () => {
    if (flow?.flow_id && canContinueToNextPhase()) {
      // Trigger the parallel analysis phase
      await handleCompleteInventoryAndTriggerParallelAnalysis();
    }
  }, [flow, canContinueToNextPhase, handleCompleteInventoryAndTriggerParallelAnalysis]);

  return {
    // Flow data with enhanced real data
    flow,
    flowAssets,
    summary,
    inventoryProgress,
    assetClassification, // Enhanced with real classification counts
    insights, // Enhanced with real CrewAI insights
    pagination,

    // Loading states
    isFlowStateLoading,
    isAnalyzing,
    lastUpdated,

    // Error states
    flowStateError,

    // UI state
    currentPage,
    setCurrentPage,
    pageSize,
    filters,
    setFilters,
    searchTerm,
    setSearchTerm,
    selectedAssets,
    setSelectedAssets,

    // Actions
    handleTriggerInventoryAnalysis,
    handleCompleteInventoryAndTriggerParallelAnalysis,
    fetchAssets,
    fetchInsights,
    canContinueToNextPhase,
    handleContinueToNextPhase,

    // Flow progression
    isInventoryComplete: flow?.inventory_completed || false,
    isDependencyAnalysisComplete: flow?.dependencies_completed || false,
    isTechDebtAnalysisComplete: flow?.tech_debt_completed || false,
    nextPhase: flow?.next_phase || null
  };
};
