import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, ArrowLeft } from 'lucide-react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import RawDataTable from '../../components/discovery/RawDataTable';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import QualityDashboard from '../../components/discovery/data-cleansing/QualityDashboard';
import DataCleansingHeader from '../../components/discovery/data-cleansing/DataCleansingHeader';
import QualityIssuesSummary from '../../components/discovery/data-cleansing/QualityIssuesSummary';
import RecommendationsSummary from '../../components/discovery/data-cleansing/RecommendationsSummary';
import ActionFeedback from '../../components/discovery/data-cleansing/ActionFeedback';
import { useDataCleansing } from '../../hooks/useDataCleansing';
import { getFieldHighlight } from '../../utils/dataCleansingUtils';

const DataCleansing = () => {
  const navigate = useNavigate();
  
  // Use the custom hook for all business logic
  const {
    // State
    rawData,
    qualityMetrics,
    qualityIssues,
    agentRecommendations,
    agentAnalysis,
    isLoading,
    isAnalyzing,
    agentRefreshTrigger,
    selectedIssue,
    selectedRecommendation,
    actionFeedback,
    
    // Actions
    setSelectedIssue,
    setSelectedRecommendation,
    handleFixIssue,
    handleApplyRecommendation,
    handleRefreshAnalysis
  } = useDataCleansing();

  // Navigation handlers
  const handleContinueToInventory = () => {
    navigate('/discovery/inventory', {
      state: {
        fromDataCleansing: true,
        cleanedData: rawData,
        qualityMetrics: qualityMetrics,
        agentAnalysis: agentAnalysis
      }
    });
  };

  const handleBackToAttributeMapping = () => {
    navigate('/discovery/attribute-mapping');
  };

  // Enhanced field highlighting function that passes all necessary data
  const getEnhancedFieldHighlight = (fieldName: string, assetId: string) => {
    return getFieldHighlight(
      fieldName,
      assetId,
      rawData,
      qualityIssues,
      agentRecommendations,
      selectedIssue,
      selectedRecommendation
    );
  };

  // Agent panel handlers
  const handleQuestionAnswered = (questionId: string, response: string) => {
    console.log('Cleansing question answered:', questionId, response);
    // Handle dependency mapping clarifications
    if (response.includes('dependency') || response.includes('related')) {
      // Update raw data to include dependency mappings
      // This would typically trigger a re-analysis
      console.log('Dependency mapping confirmed, would trigger re-analysis');
    }
  };

  const handleClassificationUpdate = (itemId: string, newClassification: string) => {
    console.log('Data classification updated:', itemId, newClassification);
    // Update quality metrics based on classification
    if (newClassification === 'good_data') {
      console.log('Asset marked as good data, would update metrics');
    }
  };

  const handleInsightAction = (insightId: string, action: string) => {
    console.log('Cleansing insight action:', insightId, action);
    // Apply agent recommendations for data quality improvement
    if (action === 'helpful') {
      console.log('Applying agent recommendations for quality improvement');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <div className="flex h-full">
          {/* Main Content Area */}
          <div className="flex-1 overflow-y-auto">
            <main className="p-8">
              <div className="max-w-4xl mx-auto">
                {/* Header with Breadcrumbs */}
                <div className="mb-8">
                  <div className="mb-4">
                    <ContextBreadcrumbs showContextSelector={true} />
                  </div>
                  
                  {/* DataCleansingHeader component already handles the main header */}
                  <DataCleansingHeader
                    isAnalyzing={isAnalyzing}
                    rawDataLength={rawData.length}
                    onRefreshAnalysis={handleRefreshAnalysis}
                  />
                </div>

                {/* Action Feedback */}
                {actionFeedback && (
                  <ActionFeedback feedback={actionFeedback} />
                )}

                {/* Quality Dashboard */}
                <QualityDashboard 
                  metrics={qualityMetrics} 
                  isLoading={isLoading}
                />

                {/* Compact Quality Summary & Recommendations */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                  {/* Quality Issues Summary */}
                  <QualityIssuesSummary
                    qualityIssues={qualityIssues}
                    selectedIssue={selectedIssue}
                    onIssueSelect={setSelectedIssue}
                    onFixIssue={handleFixIssue}
                  />

                  {/* Recommendations Summary */}
                  <RecommendationsSummary
                    agentRecommendations={agentRecommendations}
                    selectedRecommendation={selectedRecommendation}
                    onRecommendationSelect={setSelectedRecommendation}
                    onApplyRecommendation={handleApplyRecommendation}
                  />
                </div>

                {/* Enhanced Raw Data Table with Highlighting */}
                {rawData.length > 0 && (
                  <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-xl font-semibold text-gray-900">Data Preview</h2>
                      <div className="flex items-center space-x-4 text-sm">
                        {selectedIssue && (
                          <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-red-100 border border-red-300 rounded"></div>
                            <span>Selected Issue Field</span>
                          </div>
                        )}
                        {selectedRecommendation && (
                          <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-blue-100 border border-blue-300 rounded"></div>
                            <span>Recommendation Fields</span>
                          </div>
                        )}
                        <span className="text-gray-600">
                          Showing {Math.min(rawData.length, 10)} of {rawData.length} assets
                        </span>
                      </div>
                    </div>
                    <RawDataTable
                      data={rawData}
                      title="Asset Data for Quality Review"
                      pageSize={10}
                      showLegend={false}
                      getFieldHighlight={getEnhancedFieldHighlight}
                    />
                  </div>
                )}

                {/* Navigation */}
                <div className="flex justify-between items-center">
                  <button
                    onClick={handleBackToAttributeMapping}
                    className="flex items-center space-x-2 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    <ArrowLeft className="h-5 w-5" />
                    <span>Back to Attribute Mapping</span>
                  </button>

                  <button
                    onClick={handleContinueToInventory}
                    disabled={qualityMetrics.completion_percentage < 60}
                    className={`flex items-center space-x-2 px-6 py-3 rounded-lg text-lg font-medium transition-colors ${
                      qualityMetrics.completion_percentage >= 60
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    <span>Continue to Asset Inventory</span>
                    <ArrowRight className="h-5 w-5" />
                  </button>
                </div>
                
                {qualityMetrics.completion_percentage < 60 && (
                  <p className="text-center text-sm text-gray-600 mt-2">
                    Achieve at least 60% data quality to proceed
                  </p>
                )}
              </div>
            </main>
          </div>

          {/* Agent Interaction Sidebar */}
          <div className="w-96 border-l border-gray-200 bg-gray-50 overflow-y-auto">
            <div className="p-4 space-y-4">
              {/* Agent Clarification Panel */}
              <AgentClarificationPanel 
                pageContext="data-cleansing"
                refreshTrigger={agentRefreshTrigger}
                isProcessing={isAnalyzing}
                onQuestionAnswered={handleQuestionAnswered}
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                pageContext="data-cleansing"
                refreshTrigger={agentRefreshTrigger}
                isProcessing={isAnalyzing}
                onClassificationUpdate={handleClassificationUpdate}
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                pageContext="data-cleansing"
                refreshTrigger={agentRefreshTrigger}
                isProcessing={isAnalyzing}
                onInsightAction={handleInsightAction}
              />

              {/* Help Card for Agent Panels - Only show if no quality issues */}
              {qualityIssues.length === 0 && agentRecommendations.length === 0 && (
                <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
                  <h3 className="font-medium text-blue-900 mb-2 flex items-center">
                    <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                    Agent Assistance
                  </h3>
                  <div className="text-sm text-blue-800 space-y-2">
                    <p>AI agents are analyzing your data quality and will provide:</p>
                    <ul className="space-y-1 ml-4">
                      <li>• <strong>Clarifications</strong> for ambiguous data</li>
                      <li>• <strong>Classifications</strong> for data quality</li>
                      <li>• <strong>Insights</strong> for improvement opportunities</li>
                    </ul>
                    <p className="text-xs mt-2 text-blue-600">
                      Refresh analysis or interact with quality issues to trigger more agent activity.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataCleansing; 