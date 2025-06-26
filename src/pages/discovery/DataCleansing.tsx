import React from 'react';
import { useParams } from 'react-router-dom';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import EnhancedAgentOrchestrationPanel from '../../components/discovery/EnhancedAgentOrchestrationPanel';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import Sidebar from '../../components/Sidebar';

// Data Cleansing Components
import DataCleansingHeader from '../../components/discovery/data-cleansing/DataCleansingHeader';
import DataCleansingProgressDashboard from '../../components/discovery/data-cleansing/DataCleansingProgressDashboard';
import QualityIssuesPanel from '../../components/discovery/data-cleansing/QualityIssuesPanel';
import CleansingRecommendationsPanel from '../../components/discovery/data-cleansing/CleansingRecommendationsPanel';
import DataCleansingNavigationButtons from '../../components/discovery/data-cleansing/DataCleansingNavigationButtons';
import DataCleansingStateProvider from '../../components/discovery/data-cleansing/DataCleansingStateProvider';

// Hooks
import { useDiscoveryFlowV2 } from '../../hooks/discovery/useDiscoveryFlowV2';
import { useDataCleansingFlowDetection } from '../../hooks/discovery/useDiscoveryFlowAutoDetection';
import { useAuth } from '../../contexts/AuthContext';
import { useDataCleansingAnalysis } from '../../hooks/useDataCleansingAnalysis';

const DataCleansing: React.FC = () => {
  const { user } = useAuth();
  
  // Use the new auto-detection hook for consistent flow detection
  const {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
    isFlowListLoading,
    hasEffectiveFlow
  } = useDataCleansingFlowDetection();
  
  // V2 Discovery flow hook with auto-detected flow ID
  const {
    flow,
    isLoading,
    error,
    updatePhase,
    isUpdating,
    progressPercentage,
    currentPhase,
    completedPhases,
    nextPhase,
    refresh
  } = useDiscoveryFlowV2(effectiveFlowId);

  // Use real data cleansing analysis hook
  const {
    data: cleansingAnalysis,
    isLoading: isCleansingLoading,
    error: cleansingError,
    refetch: refetchCleansing
  } = useDataCleansingAnalysis();

  // Combine flow data with real cleansing analysis
  const qualityIssues = cleansingAnalysis?.quality_issues || [];
  const agentRecommendations = cleansingAnalysis?.recommendations || [];
  const cleansingProgress = {
    total_records: cleansingAnalysis?.metrics?.total_records || 0,
    quality_score: cleansingAnalysis?.metrics?.quality_score || 0,
    completion_percentage: cleansingAnalysis?.metrics?.completion_percentage || 0,
    cleaned_records: cleansingAnalysis?.metrics?.cleaned_records || 0,
    issues_resolved: cleansingAnalysis?.metrics?.quality_issues_resolved || 0,
    crew_completion_status: cleansingAnalysis?.processing_status?.phase || 'pending'
  };

  // Handle data cleansing execution
  const handleTriggerDataCleansingCrew = async () => {
    try {
      console.log('🧹 Triggering data cleansing phase...');
      await updatePhase('data_cleansing', { action: 'start_cleansing' });
      // Refresh the data after triggering
      setTimeout(() => {
        refetchCleansing();
      }, 2000);
    } catch (error) {
      console.error('Failed to execute data cleansing phase:', error);
    }
  };

  // Navigation handlers
  const handleBackToAttributeMapping = () => {
    // Navigate back to attribute mapping
    window.history.back();
  };

  const handleContinueToInventory = () => {
    // Navigate to asset inventory
    window.location.href = '/discovery/inventory';
  };

  // Determine state conditions - use real data cleansing analysis
  const hasError = !!(error || cleansingError);
  const errorMessage = error?.message || cleansingError?.message;
  const hasData = !!(qualityIssues.length > 0 || agentRecommendations.length > 0 || cleansingProgress.total_records > 0);
  const isAnalyzing = isUpdating;
  const isLoadingData = isLoading || isCleansingLoading || isFlowListLoading;

  // Get data cleansing specific data from V2 flow (keep for compatibility)
  const isDataCleansingComplete = completedPhases.includes('data_cleansing');
  const canContinueToInventory = completedPhases.includes('data_cleansing') || cleansingProgress.completion_percentage >= 80;

  // Debug info for flow detection
  console.log('🔍 DataCleansing flow detection:', {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    hasEffectiveFlow,
    totalFlowsAvailable: flowList?.length || 0
  });

  return (
    <DataCleansingStateProvider
      isLoading={isLoadingData}
      hasError={hasError}
      errorMessage={errorMessage}
      hasData={hasData}
      onBackToAttributeMapping={handleBackToAttributeMapping}
      onTriggerAnalysis={handleTriggerDataCleansingCrew}
      isAnalyzing={isAnalyzing}
    >
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>

            <DataCleansingHeader 
              totalRecords={cleansingProgress.total_records}
              qualityScore={cleansingProgress.quality_score}
              completionPercentage={cleansingProgress.completion_percentage}
              issuesCount={qualityIssues.length}
              recommendationsCount={agentRecommendations.length}
              isAnalyzing={isAnalyzing}
              isLoading={isLoadingData}
              onRefresh={refetchCleansing}
              onTriggerAnalysis={handleTriggerDataCleansingCrew}
            />

            <DataCleansingProgressDashboard 
              progress={{
                ...cleansingProgress,
                crew_completion_status: {}
              }}
              isLoading={isLoadingData}
            />

            {flow?.flow_id && (
              <div className="mb-6">
                <EnhancedAgentOrchestrationPanel
                  sessionId={flow.flow_id}
                  flowState={flow}
                />
              </div>
            )}

            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
              <div className="xl:col-span-3 space-y-6">
                <QualityIssuesPanel 
                  qualityIssues={qualityIssues}
                  onResolveIssue={(issueId) => {
                    console.log('Resolving issue:', issueId);
                    // Implementation for resolving issues
                  }}
                  isLoading={isLoadingData}
                />

                <CleansingRecommendationsPanel 
                  recommendations={agentRecommendations}
                  onApplyRecommendation={(recommendationId) => {
                    console.log('Applying recommendation:', recommendationId);
                    // Implementation for applying recommendations
                  }}
                  isLoading={isLoadingData}
                />

                <DataCleansingNavigationButtons 
                  canContinue={canContinueToInventory}
                  onBackToAttributeMapping={handleBackToAttributeMapping}
                  onContinueToInventory={handleContinueToInventory}
                />
              </div>

              <div className="xl:col-span-1 space-y-6">
                <AgentClarificationPanel 
                  pageContext="data-cleansing"
                  refreshTrigger={0}
                  onQuestionAnswered={(questionId, response) => {
                    console.log('Data cleansing question answered:', questionId, response);
                    refetchCleansing();
                  }}
                />

                <DataClassificationDisplay 
                  pageContext="data-cleansing"
                  refreshTrigger={0}
                  onClassificationUpdate={(itemId, newClassification) => {
                    console.log('Data cleansing classification updated:', itemId, newClassification);
                    refetchCleansing();
                  }}
                />

                <AgentInsightsSection 
                  pageContext="data-cleansing"
                  refreshTrigger={0}
                  onInsightAction={(insightId, action) => {
                    console.log('Data cleansing insight action:', insightId, action);
                    if (action === 'apply_insight') {
                      refetchCleansing();
                    }
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </DataCleansingStateProvider>
  );
};

export default DataCleansing; 