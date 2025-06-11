import React, { useState, useCallback, useMemo } from 'react';
import { useQueryClient, useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { 
  AlertCircle, 
  Clock, 
  Play, 
  Brain, 
  RotateCw, 
  Settings, 
  Save, 
  CheckCircle, 
  Download, 
  ChevronLeft, 
  ChevronRight,
  Plus,
  Trash2,
  Archive,
  BarChart2,
  ListChecks,
  RefreshCw,
  Check,
  X,
  Sliders,
  HelpCircle,
  CheckSquare,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Info,
  Loader2,
  MoreHorizontal,
  PlusCircle,
  Search,
  Settings2,
  Share2,
  Tag,
  Upload,
  User,
  XCircle,
  Zap,
  FileText
} from 'lucide-react';

// Hooks
import { useAuth } from '@/hooks/useAuth';
import { useApplications } from '@/hooks/useApplications';
import { useSixRAnalysis } from '@/hooks/useSixRAnalysis';
import { useAnalysisQueue } from '@/hooks/useAnalysisQueue';

// Types
import { 
  Application,
  SixRParameters,
  SixRRecommendation,
  QuestionResponse,
  AnalysisProgress,
  Analysis,
  AnalysisQueueItem
} from '@/types/assessment';

// Components
import { 
  ParameterSliders,
  QualifyingQuestions,
  AnalysisProgressDisplay,
  RecommendationDisplay,
  AnalysisHistory,
  Sidebar
} from '@/components/assessment';

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

  const {
    analysisState: state,
    isLoading: isAnalysisLoading,
    error: analysisError,
    initializeAnalysis,
    updateParameters,
    answerQuestions,
    acceptRecommendation,
    iterateAnalysis
  } = useSixRAnalysis(selectedApplicationIds);

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
    selectedApplicationIds.includes(app.id)
  );

  // Error handling
  if (appsError) {
    toast.error('Failed to load applications');
  }
  if (analysisError) {
    toast.error('Analysis error: ' + (analysisError.message || 'Unknown error'));
  }
  
  // Handlers
  const handleSelectApplications = useCallback((selected: Application[]) => {
    setSelectedApplicationIds(selected.map(app => app.id));
  }, []);
  
  const handleTabChange = useCallback((tab: string) => {
    setCurrentTab(tab);
    setManualNavigation(true);
  }, []);
  
  const handleStartAnalysis = useCallback(async () => {
    if (selectedApplicationIds.length === 0) {
      toast.error('Please select at least one application');
      return;
    }
    
    setCurrentTab('parameters');
    await initializeAnalysis();
  }, [selectedApplicationIds, initializeAnalysis]);
  
  const handleUpdateParameters = useCallback((params: SixRParameters) => {
    updateParameters(params);
  }, [updateParameters]);
  
  const handleAnswerQuestions = useCallback((responses: QuestionResponse[]) => {
    answerQuestions(responses);
  }, [answerQuestions]);
  
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
  
  const handleCreateQueueItem = useCallback(async (request: any) => {
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
    <div className="flex h-screen">
      <Sidebar>
        {/* Navigation */}
        <nav className="space-y-2">
          <button
            onClick={() => handleTabChange('selection')}
            className={`w-full text-left px-4 py-2 rounded ${
              currentTab === 'selection' ? 'bg-blue-100 text-blue-800' : ''
            }`}
          >
            Application Selection
          </button>
          {/* Add other navigation buttons */}
        </nav>
      </Sidebar>

      <main className="flex-1 overflow-auto">
        <div className="p-6">
          {/* Tab content */}
          {currentTab === 'selection' && (
            <ApplicationSelector
              applications={applications}
              selectedApplications={selectedApplications}
              onSelectionChange={handleSelectApplications}
              onStartAnalysis={handleStartAnalysis}
            />
          )}

          {currentTab === 'parameters' && state.parameters && (
            <ParameterSliders
              parameters={state.parameters}
              onChange={handleUpdateParameters}
            />
          )}

          {currentTab === 'questions' && state.questions && (
            <QualifyingQuestions
              questions={state.questions}
              onResponse={handleAnswerQuestions}
            />
          )}

          {currentTab === 'progress' && state.progress && (
            <AnalysisProgressDisplay progress={state.progress} />
          )}

          {currentTab === 'recommendation' && state.recommendation && (
            <RecommendationDisplay
              recommendation={state.recommendation}
              onAccept={handleAcceptRecommendation}
              onReject={handleIterateAnalysis}
            />
          )}

          {currentTab === 'history' && (
            <AnalysisHistory
              analyses={state.analysisHistory || []}
              onSelect={(analysis) => {/* Handle selection */}}
              onCompare={(ids) => {/* Handle comparison */}}
              onExport={(ids, format) => {/* Handle export */}}
              onDelete={(id) => {/* Handle deletion */}}
              onArchive={(id) => {/* Handle archival */}}
              onViewDetails={(id) => {/* Handle viewing details */}}
            />
          )}
        </div>
      </main>
    </div>
  );
};

export default Treatment;
