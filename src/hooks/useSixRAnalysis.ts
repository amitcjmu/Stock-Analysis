import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'sonner';
import { 
  sixrApi, 
  type CreateAnalysisRequest, 
  type UpdateParametersRequest,
  type SubmitQuestionsRequest,
  type IterateAnalysisRequest,
  type BulkAnalysisRequest,
  type ApiError
} from '../lib/api/sixr';
import { 
  SixRParameters, 
  QualifyingQuestion, 
  QuestionResponse, 
  SixRRecommendation,
  AnalysisProgressType,
  AnalysisHistoryItem,
  BulkAnalysisJob,
  BulkAnalysisResult,
  BulkAnalysisSummary
} from '../components/sixr';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { AnalysisProgress, Analysis } from '@/types/assessment';

// State interfaces
export interface AnalysisState {
  // Current analysis
  currentAnalysisId: number | null;
  analysisStatus: 'idle' | 'pending' | 'in_progress' | 'completed' | 'failed' | 'requires_input';
  
  // Analysis data
  parameters: SixRParameters;
  qualifyingQuestions: QualifyingQuestion[];
  questionResponses: QuestionResponse[];
  currentRecommendation: SixRRecommendation | null;
  analysisProgress: AnalysisProgressType | null;
  
  // Iteration tracking
  iterationNumber: number;
  iterationHistory: IterationHistoryItem[];
  
  // History and bulk
  analysisHistory: AnalysisHistoryItem[];
  bulkJobs: BulkAnalysisJob[];
  bulkResults: BulkAnalysisResult[];
  bulkSummary: BulkAnalysisSummary;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  optimisticUpdates: Map<string, any>;
}

export interface IterationHistoryItem {
  iteration: number;
  parameters: SixRParameters;
  responses: QuestionResponse[];
  recommendation: SixRRecommendation | null;
  timestamp: Date;
  notes?: string;
}

export interface UseSixRAnalysisOptions {
  autoLoadHistory?: boolean;
  enableOptimisticUpdates?: boolean;
  cacheTimeout?: number;
  maxIterationHistory?: number;
}

export interface AnalysisActions {
  // Analysis lifecycle
  createAnalysis: (request: CreateAnalysisRequest) => Promise<number | null>;
  loadAnalysis: (analysisId: number) => Promise<void>;
  refreshAnalysis: () => Promise<void>;
  resetAnalysis: () => void;
  
  // Parameter management
  updateParameters: (parameters: Partial<SixRParameters>, triggerReanalysis?: boolean) => Promise<void>;
  updateParametersLocal: (parameters: Partial<SixRParameters>) => void;
  resetParameters: () => void;
  
  // Question handling
  loadQualifyingQuestions: (analysisId: number) => Promise<void>;
  submitQuestionResponse: (questionId: string, response: any) => void;
  submitAllQuestions: (isPartial?: boolean) => Promise<void>;
  
  // Analysis control
  startAnalysis: () => Promise<void>;
  iterateAnalysis: (notes?: string) => Promise<void>;
  acceptRecommendation: () => Promise<void>;
  rejectRecommendation: () => Promise<void>;
  
  // History management
  loadAnalysisHistory: (filters?: any) => Promise<void>;
  deleteAnalysis: (analysisId: number) => Promise<void>;
  archiveAnalysis: (analysisId: number) => Promise<void>;
  exportAnalyses: (analysisIds: number[], format: 'csv' | 'pdf' | 'json') => Promise<void>;
  
  // Bulk analysis
  createBulkAnalysis: (request: BulkAnalysisRequest) => Promise<string | null>;
  loadBulkJobs: () => Promise<void>;
  controlBulkJob: (jobId: string, action: 'start' | 'pause' | 'cancel' | 'retry') => Promise<void>;
  deleteBulkJob: (jobId: string) => Promise<void>;
  exportBulkResults: (jobId: string, format: 'csv' | 'pdf' | 'json') => Promise<void>;
  
  // Utility
  clearError: () => void;
  refreshData: () => Promise<void>;
  cleanup: () => void;
}

const defaultParameters: SixRParameters = {
  business_value: 5,
  technical_complexity: 5,
  migration_urgency: 5,
  compliance_requirements: 5,
  cost_sensitivity: 5,
  risk_tolerance: 5,
  innovation_priority: 5,
  application_type: 'custom'
};

const defaultBulkSummary: BulkAnalysisSummary = {
  total_jobs: 0,
  active_jobs: 0,
  completed_jobs: 0,
  failed_jobs: 0,
  total_applications_processed: 0,
  average_confidence: 0,
  strategy_distribution: {},
  processing_time_stats: { min: 0, max: 0, average: 0, total: 0 }
};

export const useSixRAnalysis = (options: UseSixRAnalysisOptions = {}): [AnalysisState, AnalysisActions] => {
  const {
    autoLoadHistory = false,
    maxIterationHistory = 10
  } = options;

  // Simple state - no complex dependencies
  const [state, setState] = useState<AnalysisState>({
    currentAnalysisId: null,
    analysisStatus: 'idle',
    parameters: defaultParameters,
    qualifyingQuestions: [],
    questionResponses: [],
    currentRecommendation: null,
    analysisProgress: null,
    iterationNumber: 1,
    iterationHistory: [],
    analysisHistory: [],
    bulkJobs: [],
    bulkResults: [],
    bulkSummary: defaultBulkSummary,
    isLoading: false,
    error: null,
    optimisticUpdates: new Map()
  });

  // Load analysis data from API
  const loadAnalysis = useCallback(async (analysisId: number) => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      // Clear cache to ensure fresh data
      sixrApi.clearCache();
      
      const analysis = await sixrApi.getAnalysis(analysisId);
      console.log(`Loading analysis ${analysisId}:`, {
        status: analysis.status,
        progress: analysis.progress_percentage,
        hasRecommendation: !!analysis.recommendation
      });
      
      setState(prev => ({
        ...prev,
        currentAnalysisId: analysis.analysis_id,
        analysisStatus: analysis.status,
        parameters: analysis.parameters,
        currentRecommendation: analysis.recommendation,
        iterationNumber: analysis.current_iteration || 1,
        analysisProgress: analysis.progress_percentage !== undefined ? {
          analysisId: analysis.analysis_id,
          status: analysis.status === 'in_progress' ? 'in_progress' : 
                  analysis.status === 'completed' ? 'completed' :
                  analysis.status === 'failed' ? 'failed' : 
                  analysis.status === 'pending' ? 'pending' : 'pending',
          overallProgress: analysis.progress_percentage,
          currentStep: analysis.status === 'in_progress' ? 'processing' : undefined,
          steps: [
            {
              id: 'discovery',
              name: 'Application Discovery',
              description: 'Analyzing application data and dependencies',
              status: analysis.progress_percentage > 0 ? 'completed' : 'pending',
              progress: Math.min(100, analysis.progress_percentage * 3)
            },
            {
              id: 'analysis',
              name: '6R Strategy Analysis',
              description: 'Evaluating migration strategies using AI agents',
              status: analysis.progress_percentage > 30 ? (analysis.progress_percentage >= 100 ? 'completed' : 'in_progress') : 'pending',
              progress: Math.max(0, Math.min(100, (analysis.progress_percentage - 30) * 2))
            },
            {
              id: 'validation',
              name: 'Recommendation Validation',
              description: 'Validating and finalizing recommendations',
              status: analysis.progress_percentage >= 100 ? 'completed' : 'pending',
              progress: analysis.progress_percentage >= 100 ? 100 : 0
            }
          ],
          iterationNumber: analysis.current_iteration || 1,
          startTime: new Date(analysis.created_at),
          endTime: analysis.status === 'completed' ? new Date(analysis.updated_at) : undefined
        } : null,
        isLoading: false
      }));
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load analysis';
      setState(prev => ({ ...prev, error: errorMessage, isLoading: false }));
    }
  }, []);

  // Polling mechanism for active analyses with anti-spam safeguards
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const consecutiveErrors = useRef<number>(0);
  const lastSuccessfulPoll = useRef<number>(0);
  
  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    // DISABLED: No automatic polling - use manual refresh only
    console.log('🔇 DISABLED: 6R Analysis polling disabled - use manual refresh instead');
  }, [state.currentAnalysisId, state.analysisStatus, loadAnalysis]);
  
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
      consecutiveErrors.current = 0; // Reset error count when stopping
    }
  }, []);

  // Start/stop polling based on analysis status with intelligent conditions
  useEffect(() => {
    if (state.currentAnalysisId && (state.analysisStatus === 'pending' || state.analysisStatus === 'in_progress')) {
      console.log(`Starting polling for analysis ${state.currentAnalysisId} (30-second intervals)`);
      startPolling();
    } else {
      console.log('Stopping polling - analysis completed or no active analysis');
      stopPolling();
    }

    // Cleanup on unmount
    return () => stopPolling();
  }, [state.currentAnalysisId, state.analysisStatus, startPolling, stopPolling]);

  // Refresh current analysis data
  const refreshAnalysis = useCallback(async () => {
    if (state.currentAnalysisId) {
      console.log(`Refreshing analysis ${state.currentAnalysisId}...`);
      await loadAnalysis(state.currentAnalysisId);
    } else {
      console.log('No current analysis to refresh');
    }
  }, [state.currentAnalysisId, loadAnalysis]);

  // Refresh current analysis data (alias for compatibility)
  const refreshData = useCallback(async () => {
    await refreshAnalysis();
  }, [refreshAnalysis]);

  // Simple actions without complex dependencies
  const createAnalysis = useCallback(async (request: CreateAnalysisRequest): Promise<number | null> => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const analysisId = await sixrApi.createAnalysis(request);
      const analysis = await sixrApi.getAnalysis(analysisId);
      
      setState(prev => ({
        ...prev,
        currentAnalysisId: analysis.analysis_id,
        analysisStatus: analysis.status,
        parameters: analysis.parameters,
        iterationNumber: analysis.current_iteration || 1,
        isLoading: false
      }));
      
      toast.success('Analysis created successfully');
      return analysisId;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create analysis';
      setState(prev => ({ ...prev, error: errorMessage, isLoading: false }));
      return null;
    }
  }, []);

  const resetAnalysis = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentAnalysisId: null,
      analysisStatus: 'idle',
      parameters: defaultParameters,
      qualifyingQuestions: [],
      questionResponses: [],
      currentRecommendation: null,
      analysisProgress: null,
      iterationNumber: 1,
      iterationHistory: [],
      error: null
    }));
  }, []);

  const updateParametersLocal = useCallback((parameters: Partial<SixRParameters>) => {
    console.log('🔍 updateParametersLocal called with:', parameters);
    setState(prev => {
      const newState = {
        ...prev,
        parameters: { ...prev.parameters, ...parameters }
      };
      console.log('🔍 Updated state parameters:', newState.parameters);
      return newState;
    });
  }, []);

  const submitQuestionResponse = useCallback((questionId: string, response: any) => {
    const newResponse: QuestionResponse = {
      question_id: questionId,
      response,
      confidence: 0.8,
      source: 'user_input',
      timestamp: new Date()
    };

    setState(prev => {
      const filtered = prev.questionResponses.filter(r => r.question_id !== questionId);
      return {
        ...prev,
        questionResponses: [...filtered, newResponse]
      };
    });
  }, []);

  // Load analysis history from API
  const loadAnalysisHistory = useCallback(async (filters?: any) => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const history = await sixrApi.getAnalysisHistory(filters);
      console.log('Loaded analysis history:', history.length, 'items');
      
      setState(prev => ({
        ...prev,
        analysisHistory: history,
        isLoading: false
      }));
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load analysis history';
      setState(prev => ({ ...prev, error: errorMessage, isLoading: false }));
    }
  }, []);

  // Accept recommendation and update application status
  const acceptRecommendation = useCallback(async () => {
    if (!state.currentAnalysisId || !state.currentRecommendation) {
      return;
    }

    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      // TODO: Implement backend endpoint to accept recommendation
      // For now, just mark as accepted locally
      console.log('Accepting recommendation for analysis:', state.currentAnalysisId);
      
      // Reload analysis history to reflect the accepted recommendation
      await loadAnalysisHistory();
      
      setState(prev => ({ ...prev, isLoading: false }));
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to accept recommendation';
      setState(prev => ({ ...prev, error: errorMessage, isLoading: false }));
      throw error;
    }
  }, [state.currentAnalysisId, state.currentRecommendation, loadAnalysisHistory]);

  // Auto-load history on mount if enabled
  useEffect(() => {
    if (autoLoadHistory) {
      console.log('Auto-loading analysis history...');
      loadAnalysisHistory();
    }
  }, [autoLoadHistory, loadAnalysisHistory]);

  // Analysis iteration
  const iterateAnalysis = useCallback(async (notes?: string): Promise<void> => {
    if (!state.currentAnalysisId) {
      throw new Error('No active analysis to iterate');
    }

    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      // Call the iterate API endpoint with the correct signature
      const result = await sixrApi.iterateAnalysis(
        state.currentAnalysisId, 
        notes || 'Refining analysis based on updated parameters'
      );
      
      // Update state with new iteration
      setState(prev => ({
        ...prev,
        iterationNumber: result.current_iteration || (prev.iterationNumber + 1),
        analysisStatus: result.status,
        currentRecommendation: result.recommendation || null,
        analysisProgress: {
          analysisId: state.currentAnalysisId,
          status: result.status === 'completed' ? 'completed' : 'in_progress',
          overallProgress: result.progress_percentage || 0,
          currentStep: result.status === 'completed' ? 'Analysis Complete' : 'Processing iteration...',
          estimatedCompletion: result.estimated_completion ? new Date(result.estimated_completion) : new Date(Date.now() + 5 * 60 * 1000),
          steps: [
            { id: 'init', name: 'Initialize Iteration', status: 'completed', progress: 100 },
            { id: 'analyze', name: 'Analyze Parameters', status: result.status === 'completed' ? 'completed' : 'in_progress', progress: result.progress_percentage || 0 },
            { id: 'recommend', name: 'Generate Recommendation', status: result.recommendation ? 'completed' : 'pending', progress: result.recommendation ? 100 : 0 },
            { id: 'validate', name: 'Validate Results', status: result.status === 'completed' ? 'completed' : 'pending', progress: result.status === 'completed' ? 100 : 0 }
          ],
          iterationNumber: result.current_iteration || (prev.iterationNumber + 1)
        },
        isLoading: false
      }));
      
      toast.success(`Analysis iteration ${result.current_iteration || state.iterationNumber + 1} ${result.status === 'completed' ? 'completed' : 'started'}`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to iterate analysis';
      setState(prev => ({ ...prev, error: errorMessage, isLoading: false }));
      throw error;
    }
  }, [state.currentAnalysisId, state.iterationNumber]);

  // Simplified actions object
  const actions: AnalysisActions = {
    createAnalysis,
    loadAnalysis,
    refreshAnalysis,
    resetAnalysis,
    updateParameters: async () => {},
    updateParametersLocal,
    resetParameters: () => setState(prev => ({ ...prev, parameters: defaultParameters })),
    loadQualifyingQuestions: async () => {},
    submitQuestionResponse,
    submitAllQuestions: async () => {},
    startAnalysis: async () => {},
    iterateAnalysis,
    acceptRecommendation,
    rejectRecommendation: async () => {},
    loadAnalysisHistory,
    deleteAnalysis: async () => {},
    archiveAnalysis: async () => {},
    exportAnalyses: async () => {},
    createBulkAnalysis: async () => null,
    loadBulkJobs: async () => {},
    controlBulkJob: async () => {},
    deleteBulkJob: async () => {},
    exportBulkResults: async () => {},
    clearError: () => setState(prev => ({ ...prev, error: null })),
    refreshData,
    cleanup: () => stopPolling()
  };

  return [state, actions];
}; 