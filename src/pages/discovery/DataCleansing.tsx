import React, { useCallback, useMemo, useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowRight, ArrowLeft, RefreshCw, Zap, Brain, Users, Activity, Database } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { useQueryClient } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '@/config/api';

// CrewAI Discovery Flow Integration
// Removed WebSocket dependency - using HTTP polling instead
import { useDiscoveryFlowState } from '@/hooks/useDiscoveryFlowState';

// Components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import RawDataTable from '@/components/discovery/RawDataTable';
import AgentClarificationPanel from '@/components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '@/components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '@/components/discovery/AgentInsightsSection';
import QualityDashboard from '@/components/discovery/data-cleansing/QualityDashboard';
import DataCleansingHeader from '@/components/discovery/data-cleansing/DataCleansingHeader';
import QualityIssuesSummary from '@/components/discovery/data-cleansing/QualityIssuesSummary';
import RecommendationsSummary from '@/components/discovery/data-cleansing/RecommendationsSummary';
import ActionFeedback from '@/components/discovery/data-cleansing/ActionFeedback';
import EnhancedAgentOrchestrationPanel from '@/components/discovery/EnhancedAgentOrchestrationPanel';
import NoDataPlaceholder from '@/components/NoDataPlaceholder';
import { getFieldHighlight } from '@/utils/dataCleansingUtils';
import { logger } from '@/utils/logger';

// Types from Discovery Flow State
interface DiscoveryFlowState {
  session_id: string;
  client_account_id: string;
  engagement_id: string;
  current_phase: string;
  phase_completion: Record<string, boolean>;
  crew_status: Record<string, any>;
  field_mappings: {
    mappings: Record<string, any>;
    confidence_scores: Record<string, number>;
    unmapped_fields: string[];
    validation_results: Record<string, any>;
    agent_insights: Record<string, any>;
  };
  cleaned_data: any[];
  data_quality_metrics: Record<string, any>;
  raw_data: any[];
  shared_memory_id: string;
}

interface QualityIssue {
  id: string;
  field: string;
  issue_type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  affected_records: number;
  recommendation: string;
  agent_source: string;
}

interface AgentRecommendation {
  id: string;
  type: string;
  title: string;
  description: string;
  confidence: number;
  priority: string;
  fields: string[];
  agent_source: string;
  implementation_steps: string[];
}

interface ActionFeedback {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  details?: string;
}

const DataCleansing: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, client, engagement, session } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Local state
  const [selectedIssue, setSelectedIssue] = useState<string | null>(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<ActionFeedback | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Discovery Flow State Integration - TEMPORARILY SIMPLIFIED to prevent infinite loops
  const {
    flowState,
    isLoading: isFlowStateLoading,
    error: flowStateError
    // TEMPORARILY DISABLED: initializeFlow, executeDataCleansingCrew, getCrewStatus
  } = useDiscoveryFlowState();

  // Real-time monitoring via HTTP polling (no WebSocket needed)
  const isPollingActive = !!flowState && flowState.overall_status === 'in_progress';

  // Derived state from Discovery Flow
  const rawData = useMemo(() => {
    return flowState?.raw_data || [];
  }, [flowState]);

  const qualityMetrics = useMemo(() => {
    return flowState?.data_quality_metrics || {
      completion_percentage: 0,
      issues_resolved: 0,
      total_issues: 0,
      quality_score: 0
    };
  }, [flowState]);

  // Quality Issues from Discovery Flow State
  const qualityIssues = useMemo(() => {
    if (!flowState?.crew_status?.data_cleansing?.quality_issues) return [];
    
    return flowState.crew_status.data_cleansing.quality_issues.map((issue: any, index: number) => ({
      id: `issue-${index}`,
      field: issue.field || 'unknown',
      issue_type: issue.type || 'data_quality',
      severity: issue.severity || 'medium',
      description: issue.description || 'Data quality issue detected',
      affected_records: issue.affected_records || 0,
      recommendation: issue.recommendation || 'Review and clean data',
      agent_source: issue.agent_source || 'Data Quality Manager'
    }));
  }, [flowState]);

  // Agent Recommendations from Discovery Flow State
  const agentRecommendations = useMemo(() => {
    if (!flowState?.crew_status?.data_cleansing?.recommendations) return [];
    
    return flowState.crew_status.data_cleansing.recommendations.map((rec: any, index: number) => ({
      id: `recommendation-${index}`,
      type: rec.type || 'data_cleansing',
      title: rec.title || 'Data Quality Improvement',
      description: rec.description || 'Improve data quality',
      confidence: rec.confidence || 0.8,
      priority: rec.priority || 'medium',
      fields: rec.fields || [],
      agent_source: rec.agent_source || 'Data Standardization Specialist',
      implementation_steps: rec.implementation_steps || []
    }));
  }, [flowState]);

  // Initialize Discovery Flow on component mount if needed - TEMPORARILY DISABLED to prevent infinite loops
  useEffect(() => {
    // TEMPORARILY DISABLED - this was causing infinite API calls
    // Only initialize flow if explicitly passed from navigation
    const state = location.state as any;
    
    if (state?.flow_session_id && state?.flow_state) {
      console.log('✅ Using existing Discovery Flow session from navigation:', state.flow_session_id);
      // Could set flow state here if needed
    } else {
      console.log('⚠️ Data Cleansing accessed directly - no flow state available');
      // Show message to user to start from attribute mapping
    }
  }, [location.state]);

  // Execute Data Cleansing Crew Analysis
  const handleTriggerDataCleansingCrew = useCallback(async () => {
    if (!flowState?.session_id) {
      toast({
        title: "Flow Not Ready",
        description: "Discovery Flow must be initialized first",
        variant: "destructive"
      });
      return;
    }
    
    try {
      setIsAnalyzing(true);
      toast({
        title: "🤖 Data Cleansing Crew Activated",
        description: "Manager coordinating Quality Expert and Standardization Specialist...",
      });

      await executeDataCleansingCrew(flowState.session_id);

      toast({
        title: "✅ Data Cleansing Crew Complete", 
        description: "Agents have completed data quality analysis with shared insights.",
      });
    } catch (error) {
      console.error('Failed to execute Data Cleansing Crew:', error);
      toast({
        title: "❌ Crew Execution Failed",
        description: "Data Cleansing Crew encountered an error. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [flowState, executeDataCleansingCrew, toast]);

  // Handle fixing an issue
  const handleFixIssue = useCallback(async (issueId: string, fixData: any) => {
    if (!flowState?.session_id) return;
    
    try {
      // Send fix action to Discovery Flow for shared memory update
      await apiCall(`/api/v1/discovery/flow/${flowState.session_id}/agent-learning`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learning_type: 'data_quality_fix',
          crew: 'data_cleansing',
          agent: 'Data Quality Manager',
          issue_id: issueId,
          fix_applied: fixData,
          context: {
            shared_memory_id: flowState.shared_memory_id
          }
        })
      });

      setActionFeedback({
        type: 'success',
        message: 'Fix applied successfully',
        details: 'The issue has been resolved and shared with crew memory.'
      });
      
      // Refresh flow state
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
      
    } catch (error) {
      console.error('Error handling fix issue:', error);
      setActionFeedback({
        type: 'error',
        message: 'Failed to apply fix',
        details: error instanceof Error ? error.message : 'An unknown error occurred'
      });
    }
  }, [flowState, toast, queryClient]);

  // Handle applying a recommendation
  const handleApplyRecommendation = useCallback(async (recommendationId: string) => {
    if (!flowState?.session_id) return;
    
    const recommendation = agentRecommendations.find(r => r.id === recommendationId);
    if (!recommendation) return;

    try {
      // Send recommendation action to Discovery Flow
      await apiCall(`/api/v1/discovery/flow/${flowState.session_id}/agent-learning`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learning_type: 'recommendation_applied',
          crew: 'data_cleansing',
          agent: recommendation.agent_source,
          recommendation_id: recommendationId,
          recommendation_details: {
            type: recommendation.type,
            title: recommendation.title,
            fields: recommendation.fields
          },
          context: {
            shared_memory_id: flowState.shared_memory_id
          }
        })
      });

      setActionFeedback({
        type: 'success',
        message: 'Recommendation applied',
        details: 'The recommendation has been processed and shared with crew memory.'
      });
      
      // Refresh flow state
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
      
    } catch (error) {
      console.error('Error applying recommendation:', error);
      setActionFeedback({
        type: 'error',
        message: 'Failed to apply recommendation',
        details: error instanceof Error ? error.message : 'An unknown error occurred'
      });
    }
  }, [flowState, agentRecommendations, toast, queryClient]);

  // Handle refreshing the analysis
  const handleRefreshAnalysis = useCallback(() => {
    if (flowState?.session_id) {
      handleTriggerDataCleansingCrew();
    }
  }, [flowState, handleTriggerDataCleansingCrew]);

  // Handle continuing to inventory
  const handleContinueToInventory = useCallback(() => {
    if (!flowState?.session_id) return;
    
    navigate('/discovery/inventory', {
      state: {
        flow_session_id: flowState.session_id,
        flow_state: flowState,
        from_phase: 'data_cleansing'
      }
    });
  }, [flowState, navigate]);

  // Navigation handler
  const handleBackToAttributeMapping = useCallback(() => {
    if (flowState?.session_id) {
      navigate('/discovery/attribute-mapping', {
        state: {
          flow_session_id: flowState.session_id,
          flow_state: flowState,
          from_phase: 'data_cleansing'
        }
      });
    } else {
      navigate('/discovery/attribute-mapping');
    }
  }, [flowState, navigate]);

  // Agent panel handlers
  const handleQuestionAnswered = useCallback((questionId: string, response: string) => {
    logger.info('Cleansing question answered:', { questionId, response });
    // Handle dependency mapping clarifications
    if (response.includes('dependency') || response.includes('related')) {
      logger.debug('Dependency mapping confirmed, would trigger re-analysis');
      handleRefreshAnalysis();
    }
  }, [handleRefreshAnalysis]);

  const handleClassificationUpdate = useCallback((itemId: string, newClassification: string) => {
    logger.info('Data classification updated:', { itemId, newClassification });
    // In a real implementation, this would update the classification
    // and potentially trigger a re-analysis
  }, []);

  const handleInsightAction = useCallback((insightId: string, action: string) => {
    logger.info('Cleansing insight action:', { insightId, action });
    // Apply agent recommendations for data quality improvement
    if (action === 'helpful') {
      logger.debug('Applying agent recommendations for quality improvement');
    }
  }, []);

  // Memoized field highlighting function
  const getEnhancedFieldHighlight = useCallback((fieldName: string, assetId: string) => {
    return getFieldHighlight(
      fieldName,
      assetId,
      rawData,
      qualityIssues,
      agentRecommendations,
      selectedIssue,
      selectedRecommendation
    );
  }, [rawData, qualityIssues, agentRecommendations, selectedIssue, selectedRecommendation]);

  // Check if can continue to next phase
  const canContinueToInventory = () => {
    return flowState?.phase_completion?.data_cleansing || 
           qualityMetrics.completion_percentage >= 60;
  };

  // Show loading state while initializing
  if (isFlowStateLoading && !flowState) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Brain className="h-12 w-12 text-green-600 animate-pulse mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Initializing Discovery Flow</h2>
            <p className="text-gray-600">Setting up Data Cleansing Crew and shared memory...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (flowStateError) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <NoDataPlaceholder
            title="Discovery Flow Error"
            description={`Failed to initialize Discovery Flow: ${flowStateError.message}`}
            actions={
              <div className="flex space-x-3">
                <button 
                  onClick={() => navigate('/discovery/attribute-mapping')}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Database className="h-4 w-4" />
                  <span>Return to Attribute Mapping</span>
                </button>
              </div>
            }
          />
        </div>
      </div>
    );
  }

  // Show no data state
  if (!flowState?.raw_data?.length) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <NoDataPlaceholder
            title="No Data Available"
            description="No data available for data cleansing analysis. Please ensure you have completed field mapping first."
            actions={
              <div className="flex space-x-3">
                <button 
                  onClick={() => navigate('/discovery/attribute-mapping')}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Database className="h-4 w-4" />
                  <span>Go to Attribute Mapping</span>
                </button>
                <button 
                  onClick={() => navigate('/discovery/cmdb-import')}
                  className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  <Database className="h-4 w-4" />
                  <span>Import Data</span>
                </button>
              </div>
            }
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          {/* Context Breadcrumbs */}
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <RefreshCw className="h-8 w-8 text-green-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Data Cleansing</h1>
                <p className="text-gray-600">CrewAI Data Cleansing Crew Analysis</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Real-time Status */}
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                isPollingActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
              }`}>
                <Activity className="h-4 w-4" />
                <span>{isPollingActive ? 'Live Monitoring' : 'Monitoring Ready'}</span>
              </div>
              
              {/* Crew Analysis Button */}
              <button
                onClick={handleTriggerDataCleansingCrew}
                disabled={isAnalyzing || !flowState?.session_id}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
                <span>{isAnalyzing ? 'Crew Active' : 'Trigger Data Cleansing Crew'}</span>
              </button>
            </div>
          </div>

          {/* Enhanced Agent Orchestration Panel */}
          {flowState?.session_id && (
            <div className="mb-6">
              <EnhancedAgentOrchestrationPanel
                sessionId={flowState.session_id}
                flowState={flowState}
              />
            </div>
          )}

          {/* Action Feedback */}
          {actionFeedback && (
            <ActionFeedback feedback={actionFeedback} />
          )}

          {/* Quality Dashboard */}
          <QualityDashboard 
            metrics={qualityMetrics} 
            isLoading={isAnalyzing}
          />

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Main Content */}
            <div className="xl:col-span-3">
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

                {canContinueToInventory() && (
                  <button
                    onClick={handleContinueToInventory}
                    className="flex items-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    <span>Continue to Asset Inventory</span>
                    <ArrowRight className="h-5 w-5" />
                  </button>
                )}
              </div>
              
              {!canContinueToInventory() && (
                <div className="text-center mt-4">
                  <p className="text-sm text-gray-600">
                    Complete data cleansing analysis to proceed to inventory building
                  </p>
                </div>
              )}
            </div>

            {/* Right Sidebar - Agent Interaction Panel */}
            <div className="xl:col-span-1 space-y-6">
              {/* Agent Clarification Panel */}
              <AgentClarificationPanel 
                pageContext="data-cleansing"
                refreshTrigger={isAnalyzing ? 1 : 0}
                isProcessing={isAnalyzing}
                onQuestionAnswered={handleQuestionAnswered}
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                pageContext="data-cleansing"
                refreshTrigger={isAnalyzing ? 1 : 0}
                isProcessing={isAnalyzing}
                onClassificationUpdate={handleClassificationUpdate}
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                pageContext="data-cleansing"
                refreshTrigger={isAnalyzing ? 1 : 0}
                isProcessing={isAnalyzing}
                onInsightAction={handleInsightAction}
              />

              {/* Help Card for Agent Panels */}
              {qualityIssues.length === 0 && agentRecommendations.length === 0 && (
                <div className="bg-green-50 rounded-lg border border-green-200 p-4">
                  <h3 className="font-medium text-green-900 mb-2 flex items-center">
                    <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                    Data Cleansing Crew
                  </h3>
                  <div className="text-sm text-green-800 space-y-2">
                    <p>AI agents will analyze data quality and provide:</p>
                    <ul className="space-y-1 ml-4">
                      <li>• <strong>Quality Issues</strong> identification and fixes</li>
                      <li>• <strong>Standardization</strong> recommendations</li>
                      <li>• <strong>Validation</strong> rules and enforcement</li>
                    </ul>
                    <div className="mt-3 pt-2 border-t border-green-200">
                      <p className="text-xs text-green-700">
                        Phase 2 of 6 in Discovery Flow
                      </p>
                    </div>
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