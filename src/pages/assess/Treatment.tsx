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
import { ApplicationSelector } from '@/components/sixr';
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// Main component
export const Treatment: React.FC = () => {
  // Local UI state
  const [currentTab, setCurrentTab] = useState<string>('selection');
  const [selectedApplicationIds, setSelectedApplicationIds] = useState<string[]>([]);
  const [manualNavigation, setManualNavigation] = useState<boolean>(false);
  const [showApplicationType, setShowApplicationType] = useState<'all' | 'selected'>('all');

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

  const [state, actions] = useSixRAnalysis(selectedApplicationIds);
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

  // Handlers
  const handleSelectApplications = useCallback((selectedIds: string[] | number[]) => {
    // Convert to strings for consistency
    const stringIds = selectedIds.map(id => String(id));
    setSelectedApplicationIds(stringIds);
  }, []);

  const handleTabChange = useCallback((tab: string) => {
    setCurrentTab(tab);
    setManualNavigation(true);
  }, []);

  // Removed: handleStartAnalysis (initializeAnalysis not available in AnalysisActions)

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
              selectedApplications={selectedApplicationIds.map(id => parseInt(id, 10)).filter(id => !isNaN(id))}
              onSelectionChange={handleSelectApplications}
              onStartAnalysis={(appIds, queueName) => {
                // TODO: Implement analysis start logic
                console.log('Starting analysis for:', appIds, 'with queue name:', queueName);
                toast.success(`Starting analysis for ${appIds.length} applications`);
              }}
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

          {currentTab === 'progress' && state.analysisProgress && (
            <AnalysisProgressComponent progress={state.analysisProgress} />
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
      </div>
    </div>
  );
};

export default Treatment;
