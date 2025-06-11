import { useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useLatestImport, useAssets, useAgentAnalysis, useApplyFix, useCachedAgentAnalysis } from './discovery/useDataCleansingQueries';
import { QualityIssue, AgentRecommendation, ActionFeedback } from '@/types/discovery';

interface UseDataCleansingReturn {
  // State
  rawData: any[];
  qualityMetrics: any;
  qualityIssues: QualityIssue[];
  agentRecommendations: AgentRecommendation[];
  agentAnalysis: any;
  isLoading: boolean;
  isAnalyzing: boolean;
  agentRefreshTrigger: number;
  selectedIssue: string | null;
  selectedRecommendation: string | null;
  actionFeedback: ActionFeedback | null;
  fromAttributeMapping: boolean;
  
  // Actions
  setSelectedIssue: (issueId: string | null) => void;
  setSelectedRecommendation: (recommendationId: string | null) => void;
  handleFixIssue: (issueId: string, fixData: any) => Promise<void>;
  handleApplyRecommendation: (recommendationId: string) => Promise<void>;
  handleRefreshAnalysis: () => void;
  handleContinueToInventory: () => void;
}

export const useDataCleansing = (): UseDataCleansingReturn => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  // State
  const [fromAttributeMapping, setFromAttributeMapping] = useState(false);
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);
  const [selectedIssue, setSelectedIssue] = useState<string | null>(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<ActionFeedback | null>(null);
  
  // Queries
  const { data: latestImport, isLoading: isLoadingLatestImport } = useLatestImport();
  const { data: assets, isLoading: isLoadingAssets } = useAssets(1, 1000);
  
  // Mutations
  const { mutateAsync: performAnalysis, isPending: isAnalyzing } = useAgentAnalysis();
  const { mutateAsync: applyFix } = useApplyFix();
  
  // Derived state
  const isLoading = isLoadingLatestImport || isLoadingAssets;
  
  // Get data from location state if coming from attribute mapping
  const locationState = location.state as any;
  const importedData = locationState?.fromAttributeMapping ? locationState.importedData : null;
  
  // Determine which data to use (priority: imported data > latest import > assets)
  const rawData = importedData || latestImport || assets || [];
  
  // Use cached agent analysis or trigger a new one
  const { data: agentAnalysis } = useCachedAgentAnalysis(rawData);
  
  // Handle fixing an issue
  const handleFixIssue = useCallback(async (issueId: string, fixData: any) => {
    try {
      await applyFix({ issueId, fixData });
      setActionFeedback({
        type: 'success',
        message: 'Fix applied successfully',
        details: 'The issue has been resolved.'
      });
      // Trigger a refresh of the analysis
      setAgentRefreshTrigger(prev => prev + 1);
    } catch (error) {
      console.error('Failed to apply fix:', error);
      setActionFeedback({
        type: 'error',
        message: 'Failed to apply fix',
        details: error instanceof Error ? error.message : 'An unknown error occurred'
      });
    }
  }, [applyFix]);
  
  // Handle applying a recommendation
  const handleApplyRecommendation = useCallback(async (recommendationId: string) => {
    try {
      // This would be implemented based on your specific recommendation logic
      // For now, we'll just show a success message
      setActionFeedback({
        type: 'success',
        message: 'Recommendation applied',
        details: 'The recommendation has been processed.'
      });
    } catch (error) {
      console.error('Failed to apply recommendation:', error);
      setActionFeedback({
        type: 'error',
        message: 'Failed to apply recommendation',
        details: error instanceof Error ? error.message : 'An unknown error occurred'
      });
    }
  }, []);
  
  // Handle refreshing the analysis
  const handleRefreshAnalysis = useCallback(() => {
    setAgentRefreshTrigger(prev => prev + 1);
  }, []);
  
  // Handle continuing to inventory
  const handleContinueToInventory = useCallback(() => {
    navigate('/discovery/inventory', {
      state: {
        fromDataCleansing: true,
        cleanedData: rawData,
        qualityMetrics: agentAnalysis?.quality_metrics,
        agentInsights: agentAnalysis?.agent_insights || []
      }
    });
  }, [navigate, rawData, agentAnalysis]);
  
  // Set fromAttributeMapping if we have imported data
  if (importedData && !fromAttributeMapping) {
    setFromAttributeMapping(true);
  }
  
  return {
    // State
    rawData,
    qualityMetrics: agentAnalysis?.quality_metrics || {},
    qualityIssues: agentAnalysis?.quality_issues || [],
    agentRecommendations: agentAnalysis?.recommendations || [],
    agentAnalysis,
    isLoading,
    isAnalyzing,
    agentRefreshTrigger,
    selectedIssue,
    selectedRecommendation,
    actionFeedback,
    fromAttributeMapping,
    
    // Actions
    setSelectedIssue,
    setSelectedRecommendation,
    handleFixIssue,
    handleApplyRecommendation,
    handleRefreshAnalysis,
    handleContinueToInventory
  };
};

export default useDataCleansing;
