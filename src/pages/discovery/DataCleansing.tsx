import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { ArrowRight, ArrowLeft, RefreshCw, Zap, Brain, Users, Activity, Database, CheckCircle, XCircle } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '../../config/api';

// CrewAI Discovery Flow Integration
import { useDiscoveryFlowState } from '../../hooks/useDiscoveryFlowState';
import { useDataCleansingAnalysis } from '../../hooks/useDataCleansingAnalysis';

// Components
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import NoDataPlaceholder from '../../components/NoDataPlaceholder';
import EnhancedAgentOrchestrationPanel from '../../components/discovery/EnhancedAgentOrchestrationPanel';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import Sidebar from '../../components/Sidebar';

// Types
interface DataCleansingProgress {
  total_records: number;
  cleaned_records: number;
  quality_score: number;
  completion_percentage: number;
  issues_resolved: number;
  crew_completion_status: Record<string, boolean>;
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
  status: 'pending' | 'resolved' | 'ignored';
}

interface CleansingRecommendation {
  id: string;
  type: string;
  title: string;
  description: string;
  confidence: number;
  priority: 'high' | 'medium' | 'low';
  fields: string[];
  agent_source: string;
  implementation_steps: string[];
  status: 'pending' | 'applied' | 'rejected';
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
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [issueStatuses, setIssueStatuses] = useState<Record<string, 'pending' | 'resolved' | 'ignored'>>({});
  const [recommendationStatuses, setRecommendationStatuses] = useState<Record<string, 'pending' | 'applied' | 'rejected'>>({});

  // Track if we've already processed from attribute mapping
  const uploadProcessedRef = useRef(false);

  // Use the data cleansing analysis hook as primary data source (similar to AttributeMapping)
  const { 
    data: cleansingData, 
    isLoading: isCleansingLoading, 
    error: cleansingError,
    refetch: refetchCleansing
  } = useDataCleansingAnalysis();

  // Discovery Flow State Integration (secondary, for compatibility)
  const {
    flowState,
    isLoading: isFlowStateLoading,
    error: flowStateError,
    initializeFlow,
    executePhase
  } = useDiscoveryFlowState();

  // Convert cleansing data to display format
  const qualityIssues = useMemo(() => {
    if (!cleansingData?.quality_issues) return [];
    
    return cleansingData.quality_issues.map(issue => ({
      ...issue,
      status: issueStatuses[issue.id] || issue.status
    }));
  }, [cleansingData, issueStatuses]);

  const agentRecommendations = useMemo(() => {
    if (!cleansingData?.recommendations) return [];
    
    return cleansingData.recommendations.map(rec => ({
      ...rec,
      status: recommendationStatuses[rec.id] || rec.status
    }));
  }, [cleansingData, recommendationStatuses]);

  // Calculate cleansing progress
  const cleansingProgress = useMemo(() => {
    if (!cleansingData?.statistics && !cleansingData?.metrics) {
      return { 
        total_records: 0, 
        cleaned_records: 0, 
        quality_score: 0, 
        completion_percentage: 0,
        issues_resolved: 0,
        crew_completion_status: {}
      };
    }
    
    const stats = cleansingData.statistics || cleansingData.metrics;
    return {
      total_records: stats.total_records || 0,
      cleaned_records: cleansingData.metrics?.cleaned_records || 0,
      quality_score: stats.quality_score || stats.data_quality_score || 0,
      completion_percentage: stats.completion_percentage || 0,
      issues_resolved: cleansingData.metrics?.quality_issues_resolved || 0,
      crew_completion_status: {
        data_cleansing: stats.completion_percentage >= 80
      }
    };
  }, [cleansingData]);

  // Initialize from navigation state (from Attribute Mapping)
  useEffect(() => {
    const handleNavigationFromAttributeMapping = async () => {
      if (!client || !engagement) return;
      
      const state = location.state as any;
      
      // Check if coming from attribute mapping phase
      if (state?.from_phase === 'field_mapping' && state?.flow_session_id && !uploadProcessedRef.current) {
        console.log('🚀 Arrived from Attribute Mapping, initializing Data Cleansing phase');
        console.log('📋 Navigation state:', {
          flow_session_id: state.flow_session_id,
          mapping_progress: state.mapping_progress,
          from_phase: state.from_phase
        });
        
        // Mark as processed to prevent re-processing
        uploadProcessedRef.current = true;
        
        try {
          setIsAnalyzing(true);
          
          toast({
            title: "🚀 Data Cleansing Phase Started",
            description: "Initializing Data Quality Manager and Standardization Specialist...",
          });

          // Execute data cleansing phase if we have flow state
          if (state.flow_session_id) {
            await executePhase('data_cleansing', { 
              session_id: state.flow_session_id,
              previous_phase: 'field_mapping',
              mapping_progress: state.mapping_progress,
              client_account_id: client.id,
              engagement_id: engagement.id
            });
          }

          // Trigger cleansing data fetch
          setTimeout(() => {
            refetchCleansing();
          }, 2000);

          toast({
            title: "✅ Data Cleansing Analysis Started",
            description: "Crew is analyzing data quality issues and standardization opportunities.",
          });

        } catch (error) {
          console.error('❌ Failed to initialize Data Cleansing phase:', error);
          toast({
            title: "❌ Phase Initialization Failed",
            description: "Could not start Data Cleansing phase. Please try manually triggering analysis.",
            variant: "destructive"
          });
        } finally {
          setIsAnalyzing(false);
        }
        
        return;
      }
      
      // Check if cleansing data is already available
      if (cleansingData?.quality_issues?.length > 0) {
        console.log('✅ Data cleansing analysis already available:', cleansingData.quality_issues.length, 'issues found');
        return;
      }
      
      console.log('ℹ️ No cleansing data available. User can manually trigger analysis if needed.');
    };
    
    handleNavigationFromAttributeMapping();
  }, [client, engagement, executePhase, toast, refetchCleansing, cleansingData, location.state]);

  // Manual trigger for data cleansing analysis
  const handleTriggerDataCleansingCrew = useCallback(async () => {
    try {
      setIsAnalyzing(true);
      toast({
        title: "🤖 Triggering Data Cleansing Analysis",
        description: "Starting data quality analysis and standardization review...",
      });

      // Check if we need to initialize Discovery Flow first
      if (!flowState?.session_id && !cleansingData?.quality_issues?.length) {
        toast({
          title: "🚀 Initializing Discovery Flow for Data Cleansing",
          description: "Setting up Discovery Flow for data quality analysis...",
        });

        // Get data from latest import or navigation state
        const state = location.state as any;
        let rawData = [];
        
        try {
          const latestImportResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT);
          rawData = latestImportResponse?.data || [];
        } catch (error) {
          console.warn('Could not load latest import:', error);
        }
        
        if (rawData.length === 0) {
          toast({
            title: "❌ No Data Available",
            description: "Please complete field mapping first before running data cleansing analysis.",
            variant: "destructive"
          });
          return;
        }

        // Initialize Discovery Flow for data cleansing
        await initializeFlow.mutateAsync({
          client_account_id: client!.id,
          engagement_id: engagement!.id,
          user_id: user?.id || 'anonymous',
          raw_data: rawData,
          metadata: {
            source: 'data_cleansing_manual_trigger',
            filename: state?.filename || 'cleansing_data.csv',
            previous_phase: 'field_mapping'
          },
          configuration: {
            enable_field_mapping: false, // Already completed
            enable_data_cleansing: true,
            enable_inventory_building: false,
            enable_dependency_analysis: false,
            enable_technical_debt_analysis: false,
            confidence_threshold: 0.7
          }
        });
        
        console.log('✅ Discovery Flow initialized for data cleansing analysis');
      }

      // Refetch cleansing data to trigger new analysis
      await refetchCleansing();

      toast({
        title: "✅ Analysis Complete", 
        description: "Data cleansing analysis has been completed.",
      });
    } catch (error) {
      console.error('Failed to trigger data cleansing analysis:', error);
      toast({
        title: "❌ Analysis Failed",
        description: "Data cleansing analysis encountered an error. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [refetchCleansing, toast, flowState, cleansingData, initializeFlow, client, engagement, user, location.state]);

  // Handle issue resolution
  const handleResolveIssue = useCallback(async (issueId: string, action: 'resolve' | 'ignore') => {
    const issue = qualityIssues.find(i => i.id === issueId);
    if (!issue) return;

    // Immediately update local state for instant UI feedback
    setIssueStatuses(prev => ({
      ...prev,
      [issueId]: action === 'resolve' ? 'resolved' : 'ignored'
    }));

    try {
      console.log(`🔧 ${action}ing issue:`, issue);
      
      // Use agent learning endpoint for issue resolution
      const response = await apiCall('/api/v1/agents/discovery/learning/agent-learning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learning_type: 'data_quality_issue_resolution',
          action: action,
          issue_data: {
            field: issue.field,
            issue_type: issue.issue_type,
            severity: issue.severity,
            resolution: action === 'resolve' ? 'fixed' : 'acknowledged'
          }
        })
      });

      if (response.status === 'success') {
        toast({
          title: action === 'resolve' ? 'Issue Resolved' : 'Issue Ignored',
          description: `Quality issue "${issue.field}" has been ${action}d.`
        });
        
        // Refresh the cleansing data
        await refetchCleansing();
        
        // Invalidate related queries
        queryClient.invalidateQueries({ queryKey: ['data-cleansing-analysis'] });
      } else {
        throw new Error(response.message || 'Failed to update issue');
      }
      
    } catch (error) {
      console.error(`❌ Error ${action}ing issue:`, error);
      
      // Revert the local state on error
      setIssueStatuses(prev => ({
        ...prev,
        [issueId]: 'pending'
      }));
      
      toast({
        title: 'Error',
        description: `Failed to ${action} issue. Please try again.`,
        variant: 'destructive'
      });
    }
  }, [qualityIssues, toast, refetchCleansing, queryClient]);

  // Handle recommendation application
  const handleApplyRecommendation = useCallback(async (recommendationId: string, action: 'apply' | 'reject') => {
    const recommendation = agentRecommendations.find(r => r.id === recommendationId);
    if (!recommendation) return;

    // Immediately update local state for instant UI feedback
    setRecommendationStatuses(prev => ({
      ...prev,
      [recommendationId]: action === 'apply' ? 'applied' : 'rejected'
    }));

    try {
      console.log(`🔧 ${action}ing recommendation:`, recommendation);
      
      // Use agent learning endpoint for recommendation handling
      const response = await apiCall('/api/v1/agents/discovery/learning/agent-learning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learning_type: 'data_cleansing_recommendation',
          action: action,
          recommendation_data: {
            type: recommendation.type,
            title: recommendation.title,
            fields: recommendation.fields,
            priority: recommendation.priority
          }
        })
      });

      if (response.status === 'success') {
        toast({
          title: action === 'apply' ? 'Recommendation Applied' : 'Recommendation Rejected',
          description: `Cleansing recommendation "${recommendation.title}" has been ${action === 'apply' ? 'applied' : 'rejected'}.`
        });
        
        // Refresh the cleansing data
        await refetchCleansing();
        
        // Invalidate related queries
        queryClient.invalidateQueries({ queryKey: ['data-cleansing-analysis'] });
      } else {
        throw new Error(response.message || 'Failed to update recommendation');
      }
      
    } catch (error) {
      console.error(`❌ Error ${action}ing recommendation:`, error);
      
      // Revert the local state on error
      setRecommendationStatuses(prev => ({
        ...prev,
        [recommendationId]: 'pending'
      }));
      
      toast({
        title: 'Error',
        description: `Failed to ${action} recommendation. Please try again.`,
        variant: 'destructive'
      });
    }
  }, [agentRecommendations, toast, refetchCleansing, queryClient]);

  // Check if can continue to next phase
  const canContinueToInventory = () => {
    return flowState?.phase_completion?.data_cleansing || 
           (cleansingProgress.completion_percentage >= 60 && cleansingProgress.quality_score >= 70);
  };

  // Show loading state while initializing
  if ((isFlowStateLoading && !flowState) || isCleansingLoading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Brain className="h-12 w-12 text-blue-600 animate-pulse mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {isCleansingLoading ? 'Loading Data Cleansing Analysis' : 'Initializing Data Cleansing Flow'}
            </h2>
            <p className="text-gray-600">
              {isCleansingLoading ? 'Fetching data quality analysis...' : 'Setting up Data Quality Manager and Standardization Specialist...'}
            </p>
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
              <Button 
                onClick={() => navigate('/discovery/attribute-mapping')}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Return to Attribute Mapping</span>
              </Button>
            }
          />
        </div>
      </div>
    );
  }

  // Show no data state
  if (!cleansingData?.quality_issues?.length && !isCleansingLoading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <NoDataPlaceholder
            title="No Data Available"
            description="No data available for data cleansing analysis. Please ensure data has been imported and field mapping is complete."
            actions={
              <div className="flex flex-col sm:flex-row gap-3">
                <Button 
                  onClick={() => navigate('/discovery/attribute-mapping')}
                  className="flex items-center space-x-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  <span>Go to Attribute Mapping</span>
                </Button>
                <Button 
                  onClick={handleTriggerDataCleansingCrew}
                  disabled={isAnalyzing}
                  variant="outline"
                  className="flex items-center space-x-2"
                >
                  {isAnalyzing ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Zap className="h-4 w-4" />
                  )}
                  <span>{isAnalyzing ? 'Analyzing...' : 'Trigger Analysis'}</span>
                </Button>
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

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          {/* Context Breadcrumbs */}
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Database className="h-8 w-8 text-green-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Data Cleansing & Quality Analysis</h1>
                <p className="text-gray-600">
                  {cleansingData?.statistics?.total_records 
                    ? `${cleansingData.statistics.total_records} records analyzed with ${cleansingData.statistics.issues_count} quality issues found and ${cleansingData.statistics.recommendations_count} improvement recommendations` 
                    : 'AI-powered data quality analysis and standardization recommendations'
                  }
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Quality Score */}
              {cleansingData?.statistics?.quality_score && (
                <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium ${
                  cleansingData.statistics.quality_score >= 80 ? 'bg-green-100 text-green-800 border border-green-200' : 
                  cleansingData.statistics.quality_score >= 60 ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                  'bg-red-100 text-red-800 border border-red-200'
                }`}>
                  <Activity className="h-4 w-4" />
                  <span>{cleansingData.statistics.quality_score}% Quality Score</span>
                </div>
              )}
              
              {/* Completion Status */}
              {cleansingData?.statistics?.completion_percentage && (
                <div className="flex items-center space-x-2 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                  <span className="font-medium">{cleansingData.statistics.completion_percentage}% Complete</span>
                </div>
              )}
              
              {/* Manual Refresh Button */}
              <Button
                onClick={() => refetchCleansing()}
                disabled={isCleansingLoading}
                variant="outline"
                className="flex items-center space-x-2"
              >
                {isCleansingLoading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                <span>Refresh Analysis</span>
              </Button>
              
              {/* Crew Analysis Button */}
              <Button
                onClick={handleTriggerDataCleansingCrew}
                disabled={isAnalyzing}
                className="flex items-center space-x-2"
              >
                {isAnalyzing ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
                <span>{isAnalyzing ? 'Analyzing...' : 'Trigger Analysis'}</span>
              </Button>
            </div>
          </div>

          {/* Progress Dashboard */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Records</p>
                  <p className="text-2xl font-bold text-gray-900">{cleansingProgress.total_records}</p>
                </div>
                <Database className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Quality Score</p>
                  <p className="text-2xl font-bold text-gray-900">{cleansingProgress.quality_score}%</p>
                </div>
                <Activity className={`h-8 w-8 ${cleansingProgress.quality_score >= 80 ? 'text-green-600' : cleansingProgress.quality_score >= 60 ? 'text-yellow-600' : 'text-red-600'}`} />
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Issues Found</p>
                  <p className="text-2xl font-bold text-gray-900">{qualityIssues.length}</p>
                </div>
                <XCircle className="h-8 w-8 text-red-600" />
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Completion</p>
                  <p className="text-2xl font-bold text-gray-900">{cleansingProgress.completion_percentage}%</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
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

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Main Content */}
            <div className="xl:col-span-3 space-y-6">
              {/* Quality Issues */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Quality Issues</h3>
                  <p className="text-sm text-gray-600">
                    {qualityIssues.length} data quality issues identified by the Data Quality Manager
                  </p>
                </div>
                <div className="p-6">
                  {qualityIssues.length === 0 ? (
                    <div className="text-center py-8">
                      <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                      <p className="text-gray-600">No quality issues found. Data quality looks good!</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {qualityIssues.map((issue) => (
                        <div key={issue.id} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                  issue.severity === 'high' ? 'bg-red-100 text-red-800' :
                                  issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-blue-100 text-blue-800'
                                }`}>
                                  {issue.severity.toUpperCase()}
                                </span>
                                <span className="text-sm font-medium text-gray-900">{issue.field}</span>
                                <span className="text-xs text-gray-500">({issue.affected_records} records)</span>
                              </div>
                              <p className="text-sm text-gray-700 mb-2">{issue.description}</p>
                              <p className="text-xs text-gray-500 italic">{issue.recommendation}</p>
                              <p className="text-xs text-blue-600 mt-1">Source: {issue.agent_source}</p>
                            </div>
                            <div className="flex space-x-2 ml-4">
                              <Button
                                size="sm"
                                onClick={() => handleResolveIssue(issue.id, 'resolve')}
                                disabled={issue.status !== 'pending'}
                                className={issue.status === 'resolved' ? 'bg-green-600' : ''}
                              >
                                {issue.status === 'resolved' ? 'Resolved' : 'Resolve'}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleResolveIssue(issue.id, 'ignore')}
                                disabled={issue.status !== 'pending'}
                              >
                                {issue.status === 'ignored' ? 'Ignored' : 'Ignore'}
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Agent Recommendations */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Cleansing Recommendations</h3>
                  <p className="text-sm text-gray-600">
                    {agentRecommendations.length} improvement recommendations from the Data Standardization Specialist
                  </p>
                </div>
                <div className="p-6">
                  {agentRecommendations.length === 0 ? (
                    <div className="text-center py-8">
                      <Brain className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                      <p className="text-gray-600">No recommendations yet. Trigger analysis to get AI-powered suggestions.</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {agentRecommendations.map((rec) => (
                        <div key={rec.id} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                  rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                                  rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-green-100 text-green-800'
                                }`}>
                                  {rec.priority.toUpperCase()}
                                </span>
                                <span className="text-sm font-medium text-gray-900">{rec.title}</span>
                                <span className="text-xs text-gray-500">({Math.round(rec.confidence * 100)}% confidence)</span>
                              </div>
                              <p className="text-sm text-gray-700 mb-2">{rec.description}</p>
                              <div className="text-xs text-gray-600">
                                <p><strong>Fields:</strong> {rec.fields.join(', ')}</p>
                                <p><strong>Steps:</strong></p>
                                <ul className="list-disc list-inside ml-2 space-y-1">
                                  {rec.implementation_steps.map((step, idx) => (
                                    <li key={idx}>{step}</li>
                                  ))}
                                </ul>
                              </div>
                              <p className="text-xs text-blue-600 mt-1">Source: {rec.agent_source}</p>
                            </div>
                            <div className="flex space-x-2 ml-4">
                              <Button
                                size="sm"
                                onClick={() => handleApplyRecommendation(rec.id, 'apply')}
                                disabled={rec.status !== 'pending'}
                                className={rec.status === 'applied' ? 'bg-green-600' : ''}
                              >
                                {rec.status === 'applied' ? 'Applied' : 'Apply'}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleApplyRecommendation(rec.id, 'reject')}
                                disabled={rec.status !== 'pending'}
                              >
                                {rec.status === 'rejected' ? 'Rejected' : 'Reject'}
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Navigation Buttons */}
              <div className="flex justify-between">
                <Button
                  onClick={() => navigate('/discovery/attribute-mapping')}
                  variant="outline"
                  className="flex items-center space-x-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  <span>Back to Attribute Mapping</span>
                </Button>

                {canContinueToInventory() && (
                  <Button
                    onClick={() => navigate('/discovery/inventory', {
                      replace: true,
                      state: {
                        flow_session_id: flowState?.session_id || `session-${Date.now()}`,
                        from_phase: 'data_cleansing',
                        cleansing_progress: cleansingProgress,
                        client_account_id: client?.id,
                        engagement_id: engagement?.id,
                        user_id: user?.id
                      }
                    })}
                    className="flex items-center space-x-2 bg-green-600 hover:bg-green-700"
                  >
                    <span>Continue to Inventory</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>

            {/* Right Sidebar - Agent UI Bridge */}
            <div className="xl:col-span-1 space-y-6">
              {/* Agent Clarification Panel */}
              <AgentClarificationPanel 
                pageContext="data-cleansing"
                refreshTrigger={0}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Data cleansing question answered:', questionId, response);
                  refetchCleansing();
                }}
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                pageContext="data-cleansing"
                refreshTrigger={0}
                onClassificationUpdate={(itemId, newClassification) => {
                  console.log('Data cleansing classification updated:', itemId, newClassification);
                  refetchCleansing();
                }}
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                pageContext="data-cleansing"
                refreshTrigger={0}
                onInsightAction={(insightId, action) => {
                  console.log('Data cleansing insight action:', insightId, action);
                  if (action === 'apply_insight') {
                    console.log('Applying agent data cleansing insights');
                    refetchCleansing();
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataCleansing; 