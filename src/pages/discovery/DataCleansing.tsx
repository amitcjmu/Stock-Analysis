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

const DataCleansing: React.FC = () => {
  const { flowId: urlFlowId } = useParams<{ flowId?: string }>();
  
  // V2 Discovery flow hook - pass flowId if available from URL
  const {
    flow,
    isLoading,
    error,
    updatePhase,
    isUpdating,
    progressPercentage,
    currentPhase,
    completedPhases,
    nextPhase
  } = useDiscoveryFlowV2(urlFlowId);

  // Get data cleansing specific data from V2 flow
  const cleansingData = flow?.phases?.data_cleansing ? { quality_issues: [], recommendations: [] } : null;
  const isDataCleansingComplete = completedPhases.includes('data_cleansing');
  const canContinueToInventory = completedPhases.includes('data_cleansing');

  // Handle data cleansing execution
  const handleTriggerDataCleansingCrew = async () => {
    try {
      await updatePhase('data_cleansing', { action: 'start_cleansing' });
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

  // Derived state for compatibility with existing components
  const qualityIssues = (cleansingData && !Array.isArray(cleansingData)) ? (cleansingData.quality_issues || []) : [];
  const agentRecommendations = (cleansingData && !Array.isArray(cleansingData)) ? (cleansingData.recommendations || []) : [];
  const cleansingProgress = {
    total_records: (cleansingData && !Array.isArray(cleansingData)) ? (cleansingData.total_records || 0) : 0,
    quality_score: (cleansingData && !Array.isArray(cleansingData)) ? (cleansingData.quality_score || 0) : 0,
    completion_percentage: isDataCleansingComplete ? 100 : 0,
    cleaned_records: 0,
    issues_resolved: 0,
    crew_completion_status: 'pending'
  };

  // Handle issue resolution
  const handleResolveIssue = async (issueId: string) => {
    console.log('Resolving issue:', issueId);
    // Implementation for resolving issues
  };

  // Handle recommendation application
  const handleApplyRecommendation = async (recommendationId: string) => {
    console.log('Applying recommendation:', recommendationId);
    // Implementation for applying recommendations
  };

  // Refresh function
  const refetchCleansing = () => {
    // Refresh flow state
    return Promise.resolve();
  };

  // Determine state conditions
  const hasError = !!error;
  const errorMessage = error?.message;
  const hasData = !!(Array.isArray(cleansingData) ? cleansingData.length : cleansingData?.quality_issues?.length);
  const isAnalyzing = isUpdating;

  return (
    <DataCleansingStateProvider
      isLoading={isLoading}
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
              isLoading={isLoading}
              onRefresh={refetchCleansing}
              onTriggerAnalysis={handleTriggerDataCleansingCrew}
            />

            <DataCleansingProgressDashboard 
              progress={{
                ...cleansingProgress,
                crew_completion_status: {}
              }}
              isLoading={isLoading}
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
                  onResolveIssue={handleResolveIssue}
                  isLoading={isLoading}
                />

                <CleansingRecommendationsPanel 
                  recommendations={agentRecommendations}
                  onApplyRecommendation={handleApplyRecommendation}
                  isLoading={isLoading}
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