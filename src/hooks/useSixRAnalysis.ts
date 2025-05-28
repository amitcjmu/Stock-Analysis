import { useState, useCallback, useEffect, useRef } from 'react';
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
    maxIterationHistory = 10
  } = options;

  // Polling ref to track intervals
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

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
      
      const analysis = await sixrApi.getAnalysis(analysisId);
      
      setState(prev => ({
        ...prev,
        currentAnalysisId: analysis.analysis_id,
        analysisStatus: analysis.status,
        parameters: analysis.parameters,
        currentRecommendation: analysis.recommendation,
        iterationNumber: analysis.current_iteration || 1,
        analysisProgress: analysis.progress_percentage ? {
          analysisId: analysis.analysis_id,
          status: analysis.status,
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

  // Refresh current analysis data
  const refreshData = useCallback(async () => {
    if (state.currentAnalysisId) {
      await loadAnalysis(state.currentAnalysisId);
    }
  }, [state.currentAnalysisId, loadAnalysis]);

  // Start polling when analysis is in progress
  useEffect(() => {
    if (state.currentAnalysisId && (state.analysisStatus === 'pending' || state.analysisStatus === 'in_progress')) {
      console.log(`Starting polling for analysis ${state.currentAnalysisId} with status ${state.analysisStatus}`);
      
      // Start polling every 2 seconds
      pollingIntervalRef.current = setInterval(async () => {
        try {
          console.log(`Polling analysis ${state.currentAnalysisId}...`);
          const analysis = await sixrApi.getAnalysis(state.currentAnalysisId!);
          console.log(`Polling result:`, { 
            id: analysis.analysis_id, 
            status: analysis.status, 
            progress: analysis.progress_percentage,
            hasRecommendation: !!analysis.recommendation 
          });
          
          setState(prev => ({
            ...prev,
            analysisStatus: analysis.status,
            currentRecommendation: analysis.recommendation || prev.currentRecommendation,
            analysisProgress: analysis.progress_percentage ? {
              analysisId: analysis.analysis_id,
              status: analysis.status,
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
            } : prev.analysisProgress
          }));
          
          // Stop polling if analysis is complete
          if (analysis.status === 'completed' || analysis.status === 'failed') {
            console.log(`Analysis ${analysis.analysis_id} completed with status: ${analysis.status}`);
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
          }
        } catch (error) {
          console.error('Polling error:', error);
        }
      }, 2000);
      
      return () => {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      };
    } else {
      // Stop polling when analysis is complete or not active
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }
  }, [state.currentAnalysisId, state.analysisStatus]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

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
    // Clear polling when resetting
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    
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
    setState(prev => ({
      ...prev,
      parameters: { ...prev.parameters, ...parameters }
    }));
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

  // Simplified actions object
  const actions: AnalysisActions = {
    createAnalysis,
    loadAnalysis,
    resetAnalysis,
    updateParameters: async () => {},
    updateParametersLocal,
    resetParameters: () => setState(prev => ({ ...prev, parameters: defaultParameters })),
    loadQualifyingQuestions: async () => {},
    submitQuestionResponse,
    submitAllQuestions: async () => {},
    startAnalysis: async () => {},
    iterateAnalysis: async () => {},
    acceptRecommendation: async () => {},
    rejectRecommendation: async () => {},
    loadAnalysisHistory: async () => {},
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
    cleanup: () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }
  };

  return [state, actions];
}; 