import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { 
  ParameterSliders, 
  QualifyingQuestions, 
  RecommendationDisplay, 
  AnalysisProgress, 
  ApplicationSelector,
  AnalysisHistory,
  BulkAnalysis,
  type SixRParameters,
  type QualifyingQuestion,
  type QuestionResponse,
  type SixRRecommendation,
  type AnalysisProgressType,
  type Application,
  type AnalysisHistoryItem,
  type BulkAnalysisJob,
  type BulkAnalysisResult,
  type BulkAnalysisSummary,
  type AnalysisQueue
} from '../../components/sixr';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Separator } from '../../components/ui/separator';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Save, 
  Download, 
  Settings,
  Brain,
  Target,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  Users,
  FileText,
  BarChart3
} from 'lucide-react';
import { toast } from 'sonner';
import { useSixRAnalysis } from '@/hooks/useSixRAnalysis';
import { apiCall, API_CONFIG } from '@/config/api';
import { Tooltip, TooltipContent, TooltipTrigger } from '../../components/ui/tooltip';
import { Slider } from '../../components/ui/slider';

// Load applications from the discovery phase for 6R analysis
const loadApplicationsFromBackend = async (): Promise<Application[]> => {
  try {
    const data = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.APPLICATIONS);
    
    // Transform the response to match our Application interface
    return data.applications.map((app: any) => ({
      id: app.id,
      name: app.name,
      description: app.description || `${app.original_asset_type || 'Application'} - ${app.techStack || 'Unknown Technology'}`,
      department: app.department || 'Unknown',
      business_unit: app.business_unit || app.department || 'Unknown',
      criticality: (app.criticality || 'medium').toLowerCase() as 'low' | 'medium' | 'high' | 'critical',
      complexity_score: app.complexity_score || 5,
      technology_stack: app.techStack ? app.techStack.split(', ') : ['Unknown'],
      application_type: app.application_type || 'custom',
      environment: app.environment || 'Unknown',
      sixr_ready: app.sixr_ready,
      migration_complexity: app.migration_complexity,
      original_asset_type: app.original_asset_type,
      asset_id: app.asset_id,
      analysis_status: 'not_analyzed' as const,
      user_count: undefined,
      data_volume: undefined,
      compliance_requirements: [],
      dependencies: [],
      last_updated: undefined,
      recommended_strategy: undefined,
      confidence_score: undefined
    }));
  } catch (error) {
    console.error('Failed to load applications:', error);
    // Return empty array so UI shows no data state instead of crashing
    return [];
  }
};

const Treatment = () => {
  // State management using the custom hook
  const [state, actions] = useSixRAnalysis({ autoLoadHistory: true });
  
  // Local UI state
  const [currentTab, setCurrentTab] = useState('selection');
  const [selectedApplications, setSelectedApplications] = useState<number[]>([]);
  const [manualNavigation, setManualNavigation] = useState(false);
  
  // Queue management state
  const [analysisQueues, setAnalysisQueues] = useState<AnalysisQueue[]>([]);
  const [currentQueueName, setCurrentQueueName] = useState<string>('');

  // Application state management
  const [applications, setApplications] = useState<Application[]>([]);

  // Load applications on component mount
  useEffect(() => {
    const loadApps = async () => {
      const apps = await loadApplicationsFromBackend();
      setApplications(apps);
    };
    loadApps();
  }, []);

  // Auto-navigate to results when analysis completes
  useEffect(() => {
    if (state.analysisStatus === 'completed' && state.currentRecommendation && currentTab === 'progress') {
      console.log('Analysis completed, navigating to results');
      setCurrentTab('results');
      toast.success('Analysis completed! View your 6R recommendation.');
    }
  }, [state.analysisStatus, state.currentRecommendation, currentTab]);

  // Auto-navigate based on analysis status - DISABLED due to conflicts
  // useEffect(() => {
  //   console.log('Auto-navigation useEffect triggered:', {
  //     analysisStatus: state.analysisStatus,
  //     currentAnalysisId: state.currentAnalysisId,
  //     currentTab,
  //     manualNavigation
  //   });
  //   
  //   // TEMPORARILY DISABLED - auto-navigation is causing conflicts
  //   return;
  //   
  //   // Don't auto-navigate if we're in manual navigation mode
  //   if (manualNavigation) {
  //     console.log('Skipping auto-navigation due to manual navigation');
  //     return;
  //   }
  //   
  //   if (state.analysisStatus === 'pending' && currentTab === 'selection') {
  //     console.log('Auto-navigating to parameters tab');
  //     setCurrentTab('parameters');
  //   } else if (state.analysisStatus === 'in_progress' && currentTab !== 'progress') {
  //     console.log('Auto-navigating to progress tab');
  //     setCurrentTab('progress');
  //   } else if (state.analysisStatus === 'requires_input' && currentTab !== 'questions') {
  //     // Agents need additional input - show questions
  //     console.log('Auto-navigating to questions tab');
  //     setCurrentTab('questions');
  //     toast.info('AI agents need additional information to improve their recommendations');
  //   } else if (state.analysisStatus === 'completed' && currentTab !== 'results') {
  //     console.log('Auto-navigating to results tab');
  //     setCurrentTab('results');
  //   } else if (!state.currentAnalysisId && currentTab !== 'selection' && currentTab !== 'history' && currentTab !== 'bulk') {
  //     // Reset to selection tab when no active analysis
  //     console.log('Auto-navigating back to selection tab');
  //     setCurrentTab('selection');
  //   }
  // }, [state.analysisStatus, state.currentAnalysisId, currentTab, manualNavigation]);

  // Ensure qualifying questions are available
  // useEffect(() => {
  //   if (state.qualifyingQuestions.length === 0) {
  //     // Use mock questions when no analysis-specific questions are loaded
  //     actions.updateParametersLocal({ ...state.parameters });
  //   }
  // }, [state.qualifyingQuestions.length, actions, state.parameters]);

  // Event handlers
  const handleApplicationSelection = (selectedIds: number[]) => {
    setSelectedApplications(selectedIds);
  };

  const handleStartAnalysis = async (applicationIds: number[], queueName?: string) => {
    if (applicationIds.length === 0) {
      toast.error('Please select at least one application');
      return;
    }

    try {
      // Create a new queue entry
      const newQueue: AnalysisQueue = {
        id: `queue-${Date.now()}`,
        name: queueName || `Analysis ${new Date().toLocaleString()}`,
        applications: applicationIds,
        status: 'pending',
        created_at: new Date(),
        priority: analysisQueues.length + 1,
        estimated_duration: applicationIds.length * 1800 // 30 minutes per app
      };
      
      // Add to queues
      setAnalysisQueues(prev => [newQueue, ...prev]);
      setCurrentQueueName(newQueue.name);
      
      const analysisId = await actions.createAnalysis({
        application_ids: applicationIds,
        parameters: state.parameters
      });
      
      if (analysisId) {
        // Update queue status
        setAnalysisQueues(prev => prev.map(queue => 
          queue.id === newQueue.id 
            ? { ...queue, status: 'in_progress' }
            : queue
        ));
        
        setCurrentTab('parameters');
        toast.success(`Started analysis configuration for ${applicationIds.length} application(s) in queue: ${newQueue.name}`);
      } else {
        // Remove queue if analysis creation failed
        setAnalysisQueues(prev => prev.filter(queue => queue.id !== newQueue.id));
        toast.error('Failed to create analysis - no ID returned');
      }
    } catch (error) {
      console.error('Error starting analysis:', error);
      toast.error(`Failed to start analysis: ${error.message}`);
    }
  };

  const handleQueueAction = async (queueId: string, action: 'start' | 'pause' | 'cancel') => {
    setAnalysisQueues(prev => prev.map(queue => 
      queue.id === queueId 
        ? { 
            ...queue, 
            status: action === 'start' ? 'in_progress' : 
                   action === 'pause' ? 'paused' : 'pending'
          }
        : queue
    ));
    
    toast.success(`Queue ${action}ed successfully`);
  };

  const handleParametersChange = (newParameters: SixRParameters) => {
    // Update local state only, don't trigger reanalysis until Save is clicked
    actions.updateParametersLocal(newParameters);
  };

  const handleParametersSave = async () => {
    try {
      if (state.currentAnalysisId) {
        // Update existing analysis parameters and trigger initial analysis
        await actions.updateParameters(state.parameters, true);
        toast.success('Parameters saved. Starting initial analysis...');
        setCurrentTab('progress');
      } else {
        // Create new analysis with parameters and start initial processing
        if (selectedApplications.length === 0) {
          toast.error('Please select at least one application');
          setCurrentTab('selection');
          return;
        }
        
        const analysisId = await actions.createAnalysis({
          application_ids: selectedApplications,
          parameters: state.parameters
        });
        
        if (analysisId) {
          // Load the analysis data to start polling
          await actions.loadAnalysis(analysisId);
          toast.success('Analysis started. Processing parameters...');
          setCurrentTab('progress');
        }
      }
    } catch (error) {
      toast.error(`Failed to save parameters: ${error.message}`);
    }
  };

  const handleQuestionResponse = (questionId: string, response: any) => {
    actions.submitQuestionResponse(questionId, response);
  };

  const handleQuestionsSubmit = async (responses: QuestionResponse[], isPartial?: boolean) => {
    try {
      if (!state.currentAnalysisId) {
        toast.error('No active analysis. Please start from the parameters section.');
        setCurrentTab('parameters');
        return;
      }

      await actions.submitAllQuestions(isPartial || false);
      
      if (!isPartial) {
        setCurrentTab('progress');
        toast.success('Additional information submitted. Continuing analysis...');
      } else {
        toast.success('Progress saved');
      }
    } catch (error) {
      toast.error(`Failed to submit questions: ${error.message}`);
    }
  };

  const handleAcceptRecommendation = async () => {
    if (!state.currentAnalysisId || !state.currentRecommendation) {
      return;
    }

    try {
      await actions.acceptRecommendation();
      
      // Update the application status in the local state
      if (selectedApplications.length > 0) {
        setApplications(prev => prev.map(app => 
          selectedApplications.includes(app.id) 
            ? {
                ...app,
                analysis_status: 'completed',
                recommended_strategy: state.currentRecommendation?.recommended_strategy,
                confidence_score: state.currentRecommendation?.confidence_score
              }
            : app
        ));
      }
      
      toast.success('Recommendation accepted and saved');
      setCurrentTab('selection');
      actions.resetAnalysis();
    } catch (error) {
      toast.error(`Failed to accept recommendation: ${error.message}`);
    }
  };

  const handleRejectRecommendation = () => {
    setCurrentTab('parameters');
    toast.info('Adjust parameters and iterate the analysis');
  };

  const handleIterateAnalysis = async () => {
    if (!state.currentAnalysisId) {
      return;
    }

    try {
      await actions.iterateAnalysis('Refining analysis based on updated parameters');
      setCurrentTab('progress');
      toast.success('Starting analysis iteration...');
    } catch (error) {
      toast.error(`Failed to iterate analysis: ${error.message}`);
    }
  };

  const handleBulkAnalysis = async (request: any) => {
    try {
      const jobId = await actions.createBulkAnalysis(request);
      toast.success(`Bulk analysis job created: ${jobId}`);
    } catch (error) {
      toast.error(`Failed to create bulk analysis: ${error.message}`);
    }
  };

  const handleExportAnalyses = async (analysisIds: number[], format: 'csv' | 'pdf' | 'json') => {
    try {
      await actions.exportAnalyses(analysisIds, format);
      toast.success(`Export completed in ${format.toUpperCase()} format`);
    } catch (error) {
      toast.error(`Failed to export analyses: ${error.message}`);
    }
  };

  // Get current application being analyzed
  const currentApplication = selectedApplications.length > 0 
    ? applications.find(app => app.id === selectedApplications[0])
    : null;

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    6R Treatment Analysis
                    {currentApplication && (
                      <span className="ml-2 text-lg font-medium text-blue-600">
                        - {currentApplication.name}
                      </span>
                    )}
                  </h1>
                  <p className="text-gray-600">AI-powered migration strategy analysis using CrewAI agents</p>
                </div>
                
                {/* Header Actions */}
                {state.currentAnalysisId && (
                  <div className="flex items-center space-x-3">
                    <Button
                      variant="outline"
                      onClick={() => actions.refreshAnalysis()}
                      disabled={state.isLoading}
                      className="flex items-center space-x-2"
                    >
                      <RotateCcw className="h-4 w-4" />
                      <span>Refresh</span>
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => actions.resetAnalysis()}
                      disabled={state.isLoading}
                      className="flex items-center space-x-2"
                    >
                      <RotateCcw className="h-4 w-4" />
                      <span>Reset</span>
                    </Button>
                    <Button
                      onClick={() => {
                        if (currentTab === 'parameters') {
                          handleParametersSave();
                        } else if (currentTab === 'questions') {
                          handleQuestionsSubmit(state.questionResponses, true);
                        } else {
                          toast.info('No changes to save');
                        }
                      }}
                      disabled={
                        state.isLoading || 
                        (currentTab === 'questions' && Object.keys(state.questionResponses).length === 0)
                      }
                      className="flex items-center space-x-2"
                    >
                      <Save className="h-4 w-4" />
                      <span>
                        {currentTab === 'parameters' ? 'Start Analysis' : 'Save'}
                      </span>
                    </Button>
                  </div>
                )}
              </div>
              
              {/* Status Banner */}
              {state.currentAnalysisId && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {state.analysisStatus === 'pending' && <Settings className="h-5 w-5 text-blue-600" />}
                      {state.analysisStatus === 'in_progress' && <Brain className="h-5 w-5 text-blue-600 animate-pulse" />}
                      {state.analysisStatus === 'completed' && <CheckCircle className="h-5 w-5 text-green-600" />}
                      <div>
                        <p className="text-blue-800 font-medium">
                          {state.analysisStatus === 'pending' && 'Configuring Analysis Parameters'}
                          {state.analysisStatus === 'in_progress' && 'AI Analysis in Progress'}
                          {state.analysisStatus === 'completed' && 'Analysis Complete'}
                        </p>
                        <p className="text-blue-600 text-sm">
                          {currentApplication && `Application ID: ${state.currentAnalysisId} • Iteration ${state.iterationNumber}`}
                        </p>
                      </div>
                    </div>
                    {state.analysisStatus === 'in_progress' && (
                      <Badge variant="outline" className="bg-blue-100 text-blue-700">
                        <Zap className="h-3 w-3 mr-1" />
                        CrewAI Active
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Main Content */}
            <div className="space-y-6">
              {/* Progress Tabs */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Target className="h-5 w-5" />
                    <span>Analysis Workflow</span>
                    {currentApplication && (
                      <span className="text-base font-normal text-blue-600">
                        - {currentApplication.name}
                      </span>
                    )}
                  </CardTitle>
                  <CardDescription>
                    Follow the steps below to complete your 6R migration strategy analysis
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs value={currentTab} onValueChange={setCurrentTab}>
                    <TabsList className="grid w-full grid-cols-7">
                      <TabsTrigger value="selection" className="flex items-center space-x-2">
                        <Users className="h-5 w-5" />
                        <span>Selection</span>
                      </TabsTrigger>
                      <TabsTrigger value="parameters" className="flex items-center space-x-2">
                        <Settings className="h-5 w-5" />
                        <span>Parameters</span>
                      </TabsTrigger>
                      <TabsTrigger value="questions" className="flex items-center space-x-2">
                        <FileText className="h-5 w-5" />
                        <span>Questions</span>
                        {state.qualifyingQuestions.length > 0 && (
                          <Badge variant="destructive" className="ml-1 h-5 w-5 p-0 text-xs">
                            {state.qualifyingQuestions.length}
                          </Badge>
                        )}
                      </TabsTrigger>
                      <TabsTrigger value="progress" className="flex items-center space-x-2">
                        <BarChart3 className="h-5 w-5" />
                        <span>Progress</span>
                      </TabsTrigger>
                      <TabsTrigger value="results" className="flex items-center space-x-2">
                        <CheckCircle className="h-5 w-5" />
                        <span>Results</span>
                      </TabsTrigger>
                      <TabsTrigger value="history" className="flex items-center space-x-2">
                        <RotateCcw className="h-5 w-5" />
                        <span>History</span>
                      </TabsTrigger>
                      <TabsTrigger value="bulk" className="flex items-center space-x-2">
                        <Download className="h-5 w-5" />
                        <span>Bulk</span>
                      </TabsTrigger>
                    </TabsList>

                    <div className="mt-6">
                      <TabsContent value="selection" className="space-y-6">
                        <ApplicationSelector
                          applications={applications}
                          selectedApplications={selectedApplications}
                          onSelectionChange={handleApplicationSelection}
                          onStartAnalysis={handleStartAnalysis}
                          maxSelections={1}
                          showQueue={false}
                        />
                      </TabsContent>

                      <TabsContent value="parameters" className="space-y-6">
                        <ParameterSliders
                          parameters={state.parameters}
                          onParametersChange={handleParametersChange}
                          onSave={handleParametersSave}
                          disabled={state.isLoading}
                          showApplicationType={true}
                        />
                        
                        {state.iterationNumber > 1 && (
                          <div className="flex justify-end space-x-2">
                            <Button onClick={handleIterateAnalysis} disabled={state.isLoading}>
                              <Play className="w-4 h-4 mr-2" />
                              Start Iteration {state.iterationNumber}
                            </Button>
                          </div>
                        )}
                      </TabsContent>

                      <TabsContent value="questions" className="space-y-6">
                        {state.qualifyingQuestions.length > 0 ? (
                          <QualifyingQuestions
                            questions={state.qualifyingQuestions}
                            responses={state.questionResponses}
                            onResponseChange={handleQuestionResponse}
                            onSubmit={handleQuestionsSubmit}
                            disabled={state.isLoading}
                            showProgress={true}
                          />
                        ) : (
                          <Card>
                            <CardContent className="pt-6">
                              <div className="text-center py-8">
                                <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-gray-900 mb-2">
                                  No Additional Questions Needed
                                </h3>
                                <p className="text-gray-600 mb-4">
                                  The AI agents have sufficient information from your parameters to make confident recommendations.
                                </p>
                                <p className="text-sm text-gray-500">
                                  If agents need additional clarification during analysis, they will generate specific questions here.
                                </p>
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </TabsContent>

                      <TabsContent value="progress" className="space-y-6">
                        {state.analysisProgress && (
                          <AnalysisProgress
                            progress={state.analysisProgress}
                            onPause={() => toast.info('Pause functionality coming soon')}
                            onResume={() => toast.info('Resume functionality coming soon')}
                            onCancel={() => actions.resetAnalysis()}
                            onRetry={() => actions.refreshData()}
                            onRefresh={() => actions.refreshAnalysis()}
                          />
                        )}
                      </TabsContent>

                      <TabsContent value="results" className="space-y-6">
                        {state.currentRecommendation && (
                          <RecommendationDisplay
                            recommendation={state.currentRecommendation}
                            iterationNumber={state.iterationNumber}
                            onAccept={handleAcceptRecommendation}
                            onReject={handleRejectRecommendation}
                            onIterate={handleIterateAnalysis}
                          />
                        )}
                      </TabsContent>

                      <TabsContent value="history" className="space-y-6">
                        <div className="flex items-center justify-between mb-4">
                          <div>
                            <h3 className="text-lg font-medium">Analysis History</h3>
                            <p className="text-sm text-gray-600">View and manage your completed analyses</p>
                          </div>
                          <Button
                            variant="outline"
                            onClick={() => actions.loadAnalysisHistory()}
                            disabled={state.isLoading}
                            className="flex items-center space-x-2"
                          >
                            <RotateCcw className="h-4 w-4" />
                            <span>Refresh</span>
                          </Button>
                        </div>
                        <AnalysisHistory
                          analyses={state.analysisHistory}
                          onCompare={(ids) => console.log('Compare analyses:', ids)}
                          onExport={handleExportAnalyses}
                          onDelete={(id) => actions.deleteAnalysis(id)}
                          onArchive={(id) => actions.archiveAnalysis(id)}
                          onViewDetails={(id) => {
                            // Load the analysis and navigate to results
                            actions.loadAnalysis(id);
                            setCurrentTab('results');
                            toast.info(`Viewing analysis ${id}`);
                          }}
                        />
                      </TabsContent>

                      <TabsContent value="bulk" className="space-y-6">
                        <BulkAnalysis
                          jobs={state.bulkJobs}
                          results={state.bulkResults}
                          summary={state.bulkSummary}
                          onCreateJob={handleBulkAnalysis}
                          onStartJob={(jobId) => actions.controlBulkJob(jobId, 'start')}
                          onPauseJob={(jobId) => actions.controlBulkJob(jobId, 'pause')}
                          onCancelJob={(jobId) => actions.controlBulkJob(jobId, 'cancel')}
                          onRetryJob={(jobId) => actions.controlBulkJob(jobId, 'retry')}
                          onDeleteJob={(jobId) => actions.deleteBulkJob(jobId)}
                          onExportResults={(jobId, format) => actions.exportBulkResults(jobId, format)}
                        />
                      </TabsContent>
                    </div>
                  </Tabs>
                </CardContent>
              </Card>

              {/* Quick Actions */}
              {state.currentAnalysisId === null && (
                <Card>
                  <CardHeader>
                    <CardTitle>Quick Actions</CardTitle>
                    <CardDescription>
                      Common tasks and shortcuts for 6R analysis
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
                        <Download className="h-6 w-6" />
                        <span>Export Results</span>
                      </Button>
                      <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
                        <RotateCcw className="h-6 w-6" />
                        <span>View History</span>
                      </Button>
                      <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
                        <Settings className="h-6 w-6" />
                        <span>Settings</span>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Workflow Navigation */}
              {(state.currentAnalysisId || currentTab === 'selection' || selectedApplications.length > 0) && (
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-center">
                      <div className="text-sm text-gray-600">
                        {currentTab === 'selection' && 'Select applications to analyze'}
                        {currentTab === 'parameters' && 'Configure analysis parameters'}
                        {currentTab === 'questions' && 'Answer additional questions from AI agents'}
                        {currentTab === 'progress' && 'Analysis in progress...'}
                        {currentTab === 'results' && 'Review recommendations'}
                        {currentTab === 'history' && 'View analysis history'}
                        {currentTab === 'bulk' && 'Manage bulk analysis'}
                      </div>
                      <div className="flex space-x-3">
                        {/* Previous Button */}
                        {currentTab !== 'selection' && currentTab !== 'progress' && (
                          <Button
                            variant="outline"
                            onClick={() => {
                              if (currentTab === 'parameters') setCurrentTab('selection');
                              else if (currentTab === 'questions') setCurrentTab('parameters');
                              else if (currentTab === 'results') setCurrentTab('questions');
                              else if (currentTab === 'history') setCurrentTab('results');
                              else if (currentTab === 'bulk') setCurrentTab('history');
                            }}
                            disabled={state.isLoading}
                          >
                            Previous
                          </Button>
                        )}

                        {/* Save and Continue Button */}
                        {currentTab === 'parameters' && (
                          <Button
                            onClick={() => {
                              if (state.currentAnalysisId) {
                                // Update parameters and start analysis
                                handleParametersSave();
                              } else {
                                // Navigate to progress to show analysis starting
                                setCurrentTab('progress');
                                toast.success('Starting analysis with current parameters...');
                              }
                            }}
                            disabled={state.isLoading}
                            data-testid="save-parameters-btn"
                            className="bg-blue-600 hover:bg-blue-700"
                          >
                            <Save className="w-4 h-4 mr-2" />
                            Start Analysis
                          </Button>
                        )}

                        {currentTab === 'questions' && (
                          <Button
                            onClick={() => handleQuestionsSubmit(state.questionResponses, false)}
                            disabled={state.isLoading || Object.keys(state.questionResponses).length === 0}
                            data-testid="submit-questions-btn"
                            className="bg-blue-600 hover:bg-blue-700"
                          >
                            <Play className="w-4 h-4 mr-2" />
                            Continue Analysis
                          </Button>
                        )}

                        {currentTab === 'results' && state.currentRecommendation && (
                          <div className="flex space-x-2">
                            <Button
                              variant="outline"
                              onClick={handleRejectRecommendation}
                              disabled={state.isLoading}
                              data-testid="reject-recommendation-btn"
                            >
                              Adjust Parameters
                            </Button>
                            <Button
                              onClick={handleAcceptRecommendation}
                              disabled={state.isLoading}
                              data-testid="accept-recommendation-btn"
                              className="bg-green-600 hover:bg-green-700"
                            >
                              <CheckCircle className="w-4 h-4 mr-2" />
                              Accept & Save
                            </Button>
                          </div>
                        )}

                        {/* Next Button for other tabs */}
                        {(currentTab === 'selection' || currentTab === 'history' || currentTab === 'bulk') && (
                          <Button
                            onClick={() => {
                              if (currentTab === 'selection' && selectedApplications.length > 0) {
                                handleStartAnalysis(selectedApplications);
                              } else if (currentTab === 'history') {
                                setCurrentTab('bulk');
                              } else if (currentTab === 'bulk') {
                                setCurrentTab('selection');
                              }
                            }}
                            disabled={
                              state.isLoading || 
                              (currentTab === 'selection' && selectedApplications.length === 0)
                            }
                            data-testid="start-analysis-btn"
                            className="bg-blue-600 hover:bg-blue-700"
                          >
                            {currentTab === 'selection' ? 'Start Analysis' : 'Next'}
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default Treatment;
