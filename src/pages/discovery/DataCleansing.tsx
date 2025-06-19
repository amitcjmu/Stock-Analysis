import React from 'react';
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
import { useDataCleansingLogic } from '../../hooks/discovery/useDataCleansingLogic';
import { useDataCleansingNavigation } from '../../hooks/discovery/useDataCleansingNavigation';

const DataCleansing: React.FC = () => {
  // Custom hooks for business logic
  const {
    cleansingData,
    qualityIssues,
    agentRecommendations,
    cleansingProgress,
    flowState,
    isCleansingLoading,
    isFlowStateLoading,
    isAnalyzing,
    cleansingError,
    flowStateError,
    handleTriggerDataCleansingCrew,
    handleResolveIssue,
    handleApplyRecommendation,
    refetchCleansing,
    canContinueToInventory,
  } = useDataCleansingLogic();

  // Navigation logic
  const { handleBackToAttributeMapping, handleContinueToInventory } = useDataCleansingNavigation(
    flowState,
    cleansingProgress
  );

  // Determine state conditions
  const isLoading = (isFlowStateLoading && !flowState) || isCleansingLoading;
  const hasError = !!(flowStateError || cleansingError);
  const errorMessage = flowStateError?.message || cleansingError?.message;
  const hasData = !!(cleansingData?.quality_issues?.length);

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
              issuesCount={cleansingData?.statistics?.issues_count || qualityIssues.length}
              recommendationsCount={cleansingData?.statistics?.recommendations_count || agentRecommendations.length}
              isAnalyzing={isAnalyzing}
              isLoading={isCleansingLoading}
              onRefresh={refetchCleansing}
              onTriggerAnalysis={handleTriggerDataCleansingCrew}
            />

            <DataCleansingProgressDashboard 
              progress={cleansingProgress}
              isLoading={isCleansingLoading}
            />

            {flowState?.session_id && (
              <div className="mb-6">
                <EnhancedAgentOrchestrationPanel
                  sessionId={flowState.session_id}
                  flowState={flowState}
                />
              </div>
            )}

            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
              <div className="xl:col-span-3 space-y-6">
                <QualityIssuesPanel 
                  qualityIssues={qualityIssues}
                  onResolveIssue={handleResolveIssue}
                  isLoading={isCleansingLoading}
                />

                <CleansingRecommendationsPanel 
                  recommendations={agentRecommendations}
                  onApplyRecommendation={handleApplyRecommendation}
                  isLoading={isCleansingLoading}
                />

                <DataCleansingNavigationButtons 
                  canContinue={canContinueToInventory()}
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