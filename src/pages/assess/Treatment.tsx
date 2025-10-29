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
import { useAnalysisQueue } from '@/hooks/useAnalysisQueue';

// Types
import type { SixRParameters, Application} from '@/types/assessment';
import type { SixRRecommendation, QuestionResponse, AnalysisProgress as AnalysisProgressType, AnalysisQueueItem } from '@/types/assessment'
import type { Analysis } from '@/types/assessment'

// Components (restored from git history for backward compatibility)
import { ParameterSliders, AnalysisHistory } from '@/components/assessment'
// Note: Phase 5 - ApplicationSelector and Tier1GapFillingModal removed (from deleted sixr components)
// TODO: Replace ParameterSliders and AnalysisHistory with Assessment Flow equivalents
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// Assessment Flow API (Migration Phase 3 - Issue #839)
import { assessmentFlowApi } from '@/lib/api/assessmentFlow';
import type { AssessmentFlowStatusResponse } from '@/lib/api/assessmentFlow';

// Main component
export const Treatment: React.FC = () => {
  // Local UI state
  const [currentTab, setCurrentTab] = useState<string>('selection');
  const [selectedApplicationIds, setSelectedApplicationIds] = useState<string[]>([]);
  const [manualNavigation, setManualNavigation] = useState<boolean>(false);
  const [showApplicationType, setShowApplicationType] = useState<'all' | 'selected'>('all');

  // Two-Tier Inline Gap-Filling modal state (PR #816) - DEPRECATED
  // TODO: Remove gap filling modal logic in favor of Assessment Flow's built-in pause point handling
  const [showGapModal, setShowGapModal] = useState(false);
  const [blockedAnalysis, setBlockedAnalysis] = useState<AssessmentFlowStatusResponse | null>(null);

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

  // Assessment Flow state (replaces useSixRAnalysis per Migration Phase 3)
  const [parameters, setParameters] = React.useState<SixRParameters>({
    business_value: 5,
    technical_complexity: 5,
    migration_urgency: 5,
    compliance_requirements: 5,
    cost_sensitivity: 5,
    risk_tolerance: 5,
    innovation_priority: 5,
  });
  const [analysisHistory, setAnalysisHistory] = React.useState<Analysis[]>([]);
  const [isAnalysisLoading, setIsAnalysisLoading] = React.useState(false);
  const [analysisError, setAnalysisError] = React.useState<Error | null>(null);

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

      // Load history when user clicks History tab
      if (tab === 'history' && analysisHistory.length === 0 && !isAnalysisLoading) {
        // TODO: Implement loadAnalysisHistory with Assessment Flow API
        console.log('Loading analysis history - to be implemented with Assessment Flow');
      }
    },
    [analysisHistory.length, isAnalysisLoading]
  );

  // Start analysis handler - Migration Phase 3 (Issue #839)
  // Updated to use Assessment Flow API instead of deprecated sixrApi
  const handleStartAnalysis = useCallback(async (appIds: string[], queueName?: string) => {
    try {
      setIsAnalysisLoading(true);
      setAnalysisError(null);
      console.log('Starting assessment flow for:', appIds, 'with flow name:', queueName);

      // Create assessment flow using the new Assessment Flow API
      const flowId = await assessmentFlowApi.createAssessmentFlow({
        selected_application_ids: appIds,
        flow_name: queueName || `Assessment ${Date.now()}`,
        parameters: {
          business_value: parameters.business_value,
          technical_complexity: parameters.technical_complexity,
          migration_urgency: parameters.migration_urgency,
          compliance_requirements: parameters.compliance_requirements,
          cost_sensitivity: parameters.cost_sensitivity,
          risk_tolerance: parameters.risk_tolerance,
          innovation_priority: parameters.innovation_priority
        }
      });

      if (flowId) {
        toast.success(`Assessment flow started for ${appIds.length} applications`);
        // Navigate to assessment flow page
        navigate(`/assessment/${flowId}/architecture`);
      } else {
        toast.error('Failed to start assessment flow');
      }
    } catch (error) {
      console.error('Failed to start assessment flow:', error);
      setAnalysisError(error instanceof Error ? error : new Error('Unknown error'));
      toast.error('Failed to start assessment flow: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setIsAnalysisLoading(false);
    }
  }, [parameters, navigate]);

  // DEPRECATED - PR #816 gap filling logic
  // Assessment Flow handles pause points natively via asset_application_resolution phase
  const handleSubmitGapAnswers = useCallback(async (assetId: string, answers: Record<string, string>) => {
    // This functionality is deprecated - Assessment Flow handles gaps via pause points
    console.warn('handleSubmitGapAnswers is deprecated. Use Assessment Flow pause points instead.');
    toast.info('Please use the Assessment Flow to resolve asset gaps');
    setShowGapModal(false);
    setBlockedAnalysis(null);
  }, []);

  const handleUpdateParameters = useCallback((params: SixRParameters) => {
    setParameters(params);
  }, []);

  const handleAcceptRecommendation = useCallback(async () => {
    try {
      // TODO: Implement backend endpoint to accept recommendation via Assessment Flow API
      console.log('Accepting recommendation - to be implemented with Assessment Flow');
      toast.success('Recommendation accepted successfully');
      setCurrentTab('history');
    } catch (error) {
      toast.error('Failed to accept recommendation');
    }
  }, []);

  const handleIterateAnalysis = useCallback(() => {
    // Assessment Flow handles iterations differently - this is deprecated
    console.warn('handleIterateAnalysis is deprecated with Assessment Flow');
    setCurrentTab('parameters');
  }, []);

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
              disabled={selectedApplicationIds.length === 0}
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
            <div className="p-6">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  <strong>Phase 5 Note:</strong> ApplicationSelector component removed as part of 6R Analysis deprecation.
                  <br />
                  <strong>Action Required (Phase 6):</strong> Replace with Assessment Flow application selection UI.
                </p>
              </div>
              {/* TODO Phase 6: Replace with Assessment Flow ApplicationSelector equivalent */}
              {/* <ApplicationSelector
                applications={applications}
                selectedApplications={selectedApplicationIds}
                onSelectionChange={handleSelectApplications}
                onStartAnalysis={handleStartAnalysis}
              /> */}
            </div>
          )}

          {currentTab === 'parameters' && (
            <ParameterSliders
              parameters={parameters}
              onParametersChange={handleUpdateParameters}
            />
          )}

          {currentTab === 'progress' && (
            <div className="flex flex-col items-center justify-center p-12 space-y-6">
              <div className="animate-pulse">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
              </div>

              <div className="text-center space-y-2">
                <h3 className="text-xl font-semibold text-gray-900">
                  Assessment Flow in Progress
                </h3>
                <p className="text-gray-600 max-w-md">
                  Your assessment is being processed by the Assessment Flow. Navigate to the Assessment Flow page to see detailed progress.
                </p>
              </div>

              <button
                onClick={() => toast.info('Assessment flow progress available in the Assessment page')}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm flex items-center gap-2"
              >
                <RefreshCw className="w-5 h-5" />
                View Assessment Progress
              </button>

              <p className="text-sm text-gray-500">
                This tab is deprecated. Use the Assessment Flow page for real-time progress tracking.
              </p>
            </div>
          )}

          {currentTab === 'history' && (
            <AnalysisHistory
              analyses={analysisHistory || []}
              // TODO: Implement these handlers with Assessment Flow API
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

        {/* DEPRECATED - Two-Tier Inline Gap-Filling Modal (PR #816) */}
        {/* Assessment Flow handles gaps via asset_application_resolution phase */}
        {/* Kept for backward compatibility but should be removed in future */}
      </div>
    </div>
  );
};

export default Treatment;
