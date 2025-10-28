import React from 'react'
import { useState } from 'react'
import { useCallback, useMemo } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { AlertCircle, Clock, Play, Brain, RotateCw, Settings, Save, CheckCircle, Download, ChevronLeft, ChevronRight, Plus, Trash2, Archive, BarChart2, ListChecks, RefreshCw, Check, X, Sliders, HelpCircle, CheckSquare, AlertTriangle, ArrowRight, ArrowLeft, ChevronDown, ChevronUp, ExternalLink, Info, MoreHorizontal, PlusCircle, Search, Settings2, Share2, Tag, Upload, User, XCircle, Zap, FileText } from 'lucide-react'
import { Loader2 } from 'lucide-react'

// Hooks
import { useAuth } from '@/contexts/AuthContext';
import { useApplications } from '@/hooks/useApplications';
import { useSixRAnalysis } from '@/hooks/useSixRAnalysis';
import { useAnalysisQueue } from '@/hooks/useAnalysisQueue';

// Types
import type { SixRParameters, Application} from '@/types/assessment';
import { SixRRecommendation, QuestionResponse, AnalysisProgress as AnalysisProgressType, AnalysisQueueItem } from '@/types/assessment'
import { Analysis } from '@/types/assessment'

// Components
import { AnalysisProgress as AnalysisProgressComponent } from '@/components/assessment'
import { ParameterSliders, QualifyingQuestions, RecommendationDisplay, AnalysisHistory } from '@/components/assessment'
import { ApplicationSelector, Tier1GapFillingModal } from '@/components/sixr';
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// Two-Tier Inline Gap-Filling (PR #816)
import type { SixRAnalysisResponse } from '@/lib/api/sixr';
import { sixrApi } from '@/lib/api/sixr';

// Main component
export const Treatment: React.FC = () => {
  // Local UI state
  const [currentTab, setCurrentTab] = useState<string>('selection');
  const [selectedApplicationIds, setSelectedApplicationIds] = useState<string[]>([]);
  const [manualNavigation, setManualNavigation] = useState<boolean>(false);
  const [showApplicationType, setShowApplicationType] = useState<'all' | 'selected'>('all');

  // Two-Tier Inline Gap-Filling modal state (PR #816)
  const [showGapModal, setShowGapModal] = useState(false);
  const [blockedAnalysis, setBlockedAnalysis] = useState<SixRAnalysisResponse | null>(null);

  // Hooks
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Query Hooks
  const {
    applications = [],
    isLoading: isLoadingApps,
    error: appsError,
    refetch: refetchApplications
  } = useApplications();

  const [state, actions] = useSixRAnalysis({ autoLoadHistory: false });
const { isLoading: isAnalysisLoading, error: analysisError } = state;
const { updateParameters, submitQuestionResponse, acceptRecommendation, iterateAnalysis } = actions;

  const {
    queues: analysisQueues,
    isLoading: isLoadingQueues,
    createQueue,
    startQueue,
    pauseQueue,
    cancelQueue,
    retryQueue,
    deleteQueue,
    exportResults
  } = useAnalysisQueue();

  // Selected applications derived from IDs
  const selectedApplications = applications.filter(app =>
    selectedApplicationIds.includes(String(app.id))
  );

  // Error handling
  if (appsError) {
    toast.error('Failed to load applications');
  }
  if (analysisError) {
    toast.error('Analysis error: ' + (analysisError.message || 'Unknown error'));
  }

  // Handlers - Bug #813 fix: Already using string[] (UUIDs), no conversion needed
  const handleSelectApplications = useCallback((selectedIds: string[]) => {
    // Already UUID strings from ApplicationSelector
    setSelectedApplicationIds(selectedIds);
  }, []);

  const handleTabChange = useCallback(
    (tab: string) => {
      setCurrentTab(tab);
      setManualNavigation(true);

      // Bug #814: Load history when user clicks History tab
      if (tab === 'history' && state.analysisHistory.length === 0 && !state.isLoading) {
        actions.loadAnalysisHistory();
      }
    },
    [state.analysisHistory.length, state.isLoading, actions]
  );

  // Start analysis handler - Bug #813 fix: Changed appIds from number[] to string[] (UUIDs)
  // PR #816: Extended to handle blocked status and show Tier 1 gap-filling modal
  const handleStartAnalysis = useCallback(async (appIds: string[], queueName?: string) => {
    try {
      console.log('Starting analysis for:', appIds, 'with queue name:', queueName);

      // Create analysis using the SixR API - returns full response object (PR #816)
      const analysis = await actions.createAnalysis({
        application_ids: appIds,
        parameters: state.parameters,
        queue_name: queueName || `Analysis ${Date.now()}`
      });

      if (analysis) {
        // Check if analysis is blocked by Tier 1 gaps (PR #816)
        if (analysis.status === 'requires_input' && analysis.tier1_gaps_by_asset) {
          console.log('Analysis blocked by Tier 1 gaps:', analysis.tier1_gaps_by_asset);
          setBlockedAnalysis(analysis);
          setShowGapModal(true);
          // Toast is skipped by createAnalysis when status is requires_input
        } else {
          // Normal flow - analysis started successfully
          toast.success(`Analysis started for ${appIds.length} applications`);
          // Switch to progress tab to show the analysis progress
          setCurrentTab('progress');
        }
      } else {
        toast.error('Failed to start analysis');
      }
    } catch (error) {
      console.error('Failed to start analysis:', error);
      toast.error('Failed to start analysis: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  }, [actions, state.parameters]);

  // PR #816: Handle submission of inline gap answers
  const handleSubmitGapAnswers = useCallback(async (assetId: string, answers: Record<string, string>) => {
    if (!blockedAnalysis) return;

    try {
      const result = await sixrApi.submitInlineAnswers(blockedAnalysis.analysis_id.toString(), {
        asset_id: assetId,
        answers
      });

      console.log('Inline answers submitted:', result);

      // If all gaps filled and analysis can proceed
      if (result.can_proceed && result.remaining_tier1_gaps === 0) {
        toast.success('All required information collected. Starting analysis...');
        setShowGapModal(false);
        setBlockedAnalysis(null);
        // Switch to progress tab
        setCurrentTab('progress');
      } else {
        // More gaps remain
        toast.info(`${result.remaining_tier1_gaps} asset(s) still need information`);
      }
    } catch (error) {
      console.error('Failed to submit gap answers:', error);
      toast.error('Failed to submit answers: ' + (error instanceof Error ? error.message : 'Unknown error'));
      throw error; // Re-throw so modal can handle it
    }
  }, [blockedAnalysis]);

  const handleUpdateParameters = useCallback((params: SixRParameters) => {
    updateParameters(params);
  }, [updateParameters]);

  // Removed: handleAnswerQuestions (answerQuestions not available in AnalysisActions)

  const handleAcceptRecommendation = useCallback(async () => {
    try {
      await acceptRecommendation();
      toast.success('Recommendation accepted successfully');
      setCurrentTab('history');
    } catch (error) {
      toast.error('Failed to accept recommendation');
    }
  }, [acceptRecommendation]);

  const handleIterateAnalysis = useCallback(() => {
    iterateAnalysis();
    setCurrentTab('parameters');
  }, [iterateAnalysis]);

  const handleCreateQueueItem = useCallback(async (request: unknown) => {
    try {
      const newQueue = await createQueue({
        name: `Analysis ${Date.now()}`,
        applicationIds: selectedApplicationIds
      });
      toast.success('Analysis queue created successfully');
      return newQueue;
    } catch (error) {
      toast.error('Failed to create analysis queue');
      throw error;
    }
  }, [selectedApplicationIds, createQueue]);

  // Loading states
  if (isLoadingApps || isLoadingQueues) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading treatment data...</p>
        </div>
      </div>
    );
  }

  // Main render
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Context Breadcrumbs */}
            <ContextBreadcrumbs />

            {/* Page header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">6R Treatment Planning</h1>
              <p className="text-gray-600">Analyze applications and determine optimal migration strategies</p>
            </div>

            {/* Tab navigation */}
            <div className="mb-6">
              <nav className="flex space-x-4">
            <button
              onClick={() => handleTabChange('selection')}
              className={`px-4 py-2 rounded-lg font-medium ${
                currentTab === 'selection'
                  ? 'bg-blue-100 text-blue-800'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Application Selection
            </button>
            <button
              onClick={() => handleTabChange('parameters')}
              className={`px-4 py-2 rounded-lg font-medium ${
                currentTab === 'parameters'
                  ? 'bg-blue-100 text-blue-800'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              disabled={selectedApplicationIds.length === 0}
            >
              Parameters
            </button>
            <button
              onClick={() => handleTabChange('progress')}
              className={`px-4 py-2 rounded-lg font-medium ${
                currentTab === 'progress'
                  ? 'bg-blue-100 text-blue-800'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              disabled={!state.analysisProgress}
            >
              Progress
            </button>
            <button
              onClick={() => handleTabChange('history')}
              className={`px-4 py-2 rounded-lg font-medium ${
                currentTab === 'history'
                  ? 'bg-blue-100 text-blue-800'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              History
            </button>
              </nav>
            </div>

            {/* Content */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {/* Tab content */}
          {currentTab === 'selection' && (
            <ApplicationSelector
              applications={applications}
              selectedApplications={selectedApplicationIds}
              onSelectionChange={handleSelectApplications}
              onStartAnalysis={handleStartAnalysis}
            />
          )}

          {currentTab === 'parameters' && state.parameters && (
            <ParameterSliders
              parameters={state.parameters}
              onParametersChange={updateParameters}
            />
          )}

          {currentTab === 'questions' && state.qualifyingQuestions && (
            <QualifyingQuestions
              questions={state.qualifyingQuestions}
              responses={state.questionResponses}
              onResponseChange={submitQuestionResponse}
              onSubmit={() => {}}
            />
          )}

          {currentTab === 'progress' && (
            <>
              {state.analysisProgress ? (
                <AnalysisProgressComponent progress={state.analysisProgress} />
              ) : (
                <div className="flex flex-col items-center justify-center p-12 space-y-6">
                  <div className="animate-pulse">
                    <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  </div>

                  <div className="text-center space-y-2">
                    <h3 className="text-xl font-semibold text-gray-900">
                      Analysis in Progress
                    </h3>
                    <p className="text-gray-600 max-w-md">
                      Your 6R assessment is being analyzed. This may take several minutes depending on the complexity of your applications.
                    </p>
                  </div>

                  <button
                    onClick={() => actions.refreshAnalysis?.()}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm flex items-center gap-2"
                  >
                    <RefreshCw className="w-5 h-5" />
                    Refresh Progress
                  </button>

                  <p className="text-sm text-gray-500">
                    Automatic updates are disabled. Click "Refresh Progress" to see the latest status.
                  </p>
                </div>
              )}
            </>
          )}

          {currentTab === 'recommendation' && state.currentRecommendation && (
            <RecommendationDisplay
              recommendation={state.currentRecommendation}
              onAccept={acceptRecommendation}
              onReject={iterateAnalysis}
            />
          )}

          {currentTab === 'history' && (
            <AnalysisHistory
              analyses={state.analysisHistory || []}
              // TODO: Implement these handlers as needed
              onSelect={() => {}}
              onCompare={() => {}}
              onExport={() => {}}
              onDelete={() => {}}
              onArchive={() => {}}
              onViewDetails={() => {}}
            />
          )}
            </div>
          </div>
        </main>

        {/* Two-Tier Inline Gap-Filling Modal (PR #816) */}
        {showGapModal && blockedAnalysis?.tier1_gaps_by_asset && (
          <Tier1GapFillingModal
            isOpen={showGapModal}
            onClose={() => {
              setShowGapModal(false);
              setBlockedAnalysis(null);
            }}
            analysisId={blockedAnalysis.analysis_id.toString()}
            tier1_gaps_by_asset={blockedAnalysis.tier1_gaps_by_asset}
            onSubmit={handleSubmitGapAnswers}
          />
        )}
      </div>
    </div>
  );
};

export default Treatment;
