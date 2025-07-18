/* eslint-disable @typescript-eslint/no-explicit-any */
import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useSixRAnalysis } from '../useSixRAnalysis';
import { sixrApi } from '../../lib/api/sixr';
import { useSixRWebSocket } from '../useSixRWebSocket';

// Mock the API client
vi.mock('../../lib/api/sixr', () => ({
  sixrApi: {
    createAnalysis: vi.fn(),
    getAnalysis: vi.fn(),
    updateParameters: vi.fn(),
    submitQuestions: vi.fn(),
    iterateAnalysis: vi.fn(),
    getRecommendation: vi.fn(),
    getAnalysisHistory: vi.fn(),
    deleteAnalysis: vi.fn(),
    archiveAnalysis: vi.fn(),
    exportAnalysis: vi.fn(),
    createBulkAnalysis: vi.fn(),
    getBulkJobs: vi.fn(),
    controlBulkJob: vi.fn(),
    deleteBulkJob: vi.fn(),
    exportBulkResults: vi.fn(),
    getBulkSummary: vi.fn(),
    cleanup: vi.fn()
  }
}));

// Mock the WebSocket hook
vi.mock('../useSixRWebSocket', () => ({
  useSixRWebSocket: vi.fn(() => ({
    isConnected: true,
    lastMessage: null,
    sendMessage: vi.fn(),
    subscribe: vi.fn(),
    unsubscribe: vi.fn()
  }))
}));

// Mock toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn()
  }
}));

describe('useSixRAnalysis', () => {
  const mockWebSocketHook = {
    isConnected: true,
    lastMessage: null,
    sendMessage: vi.fn(),
    subscribe: vi.fn(),
    unsubscribe: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useSixRWebSocket as any).mockReturnValue(mockWebSocketHook);
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => useSixRAnalysis());
    const [state] = result.current;

    expect(state.currentAnalysisId).toBeNull();
    expect(state.analysisStatus).toBe('idle');
    expect(state.parameters.business_value).toBe(5);
    expect(state.parameters.application_type).toBe('custom');
    expect(state.qualifyingQuestions).toEqual([]);
    expect(state.questionResponses).toEqual([]);
    expect(state.currentRecommendation).toBeNull();
    expect(state.analysisProgress).toBeNull();
    expect(state.iterationNumber).toBe(1);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('creates analysis successfully', async () => {
    const mockResponse = {
      analysis_id: 123,
      status: 'created',
      estimated_duration: 300
    };

    (sixrApi.createAnalysis as any).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useSixRAnalysis());
    const [, actions] = result.current;

    await act(async () => {
      const analysisId = await actions.createAnalysis({
        application_ids: [1, 2, 3],
        parameters: {
          business_value: 7,
          technical_complexity: 5,
          migration_urgency: 6,
          compliance_requirements: 4,
          cost_sensitivity: 5,
          risk_tolerance: 6,
          innovation_priority: 8,
          application_type: 'custom'
        }
      });

      expect(analysisId).toBe(123);
    });

    const [state] = result.current;
    expect(state.currentAnalysisId).toBe(123);
    expect(state.analysisStatus).toBe('configuring');
    expect(state.iterationNumber).toBe(1);
  });

  it('handles API errors gracefully', async () => {
    const mockError = new Error('API Error');
    (sixrApi.createAnalysis as any).mockRejectedValue(mockError);

    const { result } = renderHook(() => useSixRAnalysis());
    const [, actions] = result.current;

    await act(async () => {
      try {
        await actions.createAnalysis({
          application_ids: [1],
          parameters: {}
        });
      } catch (error) {
        expect(error).toBe(mockError);
      }
    });

    const [state] = result.current;
    expect(state.error).toBe('API Error');
    expect(state.isLoading).toBe(false);
  });

  it('updates parameters with optimistic updates', async () => {
    (sixrApi.updateParameters as any).mockResolvedValue({
      success: true,
      message: 'Parameters updated'
    });

    const { result } = renderHook(() => useSixRAnalysis());
    
    // Set up initial state
    act(() => {
      const [state, actions] = result.current;
      // Simulate having an active analysis
      (state as any).currentAnalysisId = 123;
    });

    const [, actions] = result.current;

    await act(async () => {
      await actions.updateParameters({
        business_value: 8,
        innovation_priority: 9
      });
    });

    const [state] = result.current;
    expect(state.parameters.business_value).toBe(8);
    expect(state.parameters.innovation_priority).toBe(9);
  });

  it('handles parameter update failures with rollback', async () => {
    const mockError = new Error('Update failed');
    (sixrApi.updateParameters as any).mockRejectedValue(mockError);

    const { result } = renderHook(() => useSixRAnalysis());
    
    // Set up initial state with analysis ID
    act(() => {
      const [state] = result.current;
      (state as any).currentAnalysisId = 123;
    });

    const [, actions] = result.current;

    await act(async () => {
      await actions.updateParameters({
        business_value: 8
      });
    });

    const [state] = result.current;
    // Should rollback to original value
    expect(state.parameters.business_value).toBe(5);
    expect(state.error).toBe('Update failed');
  });

  it('submits question responses correctly', async () => {
    (sixrApi.submitQuestions as any).mockResolvedValue({
      success: true,
      message: 'Questions submitted'
    });

    const { result } = renderHook(() => useSixRAnalysis());
    
    // Set up initial state
    act(() => {
      const [state] = result.current;
      (state as any).currentAnalysisId = 123;
    });

    const [, actions] = result.current;

    // Add a question response
    act(() => {
      actions.submitQuestionResponse('app_type', 'custom');
    });

    await act(async () => {
      await actions.submitAllQuestions(false);
    });

    const [state] = result.current;
    expect(state.analysisStatus).toBe('analyzing');
    expect(state.questionResponses).toHaveLength(1);
    expect(state.questionResponses[0].question_id).toBe('app_type');
    expect(state.questionResponses[0].response).toBe('custom');
  });

  it('handles WebSocket messages correctly', async () => {
    const mockMessage = {
      type: 'analysis_progress',
      analysis_id: 123,
      data: {
        progress: 50,
        step: 'processing',
        status: 'in_progress'
      }
    };

    const { result } = renderHook(() => useSixRAnalysis());
    
    // Set up initial state
    act(() => {
      const [state] = result.current;
      (state as any).currentAnalysisId = 123;
      (state as any).analysisProgress = {
        analysisId: 123,
        status: 'in_progress',
        overallProgress: 0,
        steps: [
          { id: 'processing', status: 'pending', progress: 0 }
        ]
      };
    });

    // Simulate WebSocket message
    act(() => {
      const mockOnMessage = (useSixRWebSocket as any).mock.calls[0][0].onMessage;
      mockOnMessage(mockMessage);
    });

    const [state] = result.current;
    expect(state.analysisProgress?.overallProgress).toBe(50);
    expect(state.analysisProgress?.currentStep).toBe('processing');
  });

  it('handles analysis completion via WebSocket', async () => {
    const mockRecommendation = {
      recommended_strategy: 'refactor',
      confidence_score: 0.85,
      strategy_scores: [],
      key_factors: [],
      assumptions: [],
      next_steps: []
    };

    const mockMessage = {
      type: 'analysis_complete',
      analysis_id: 123,
      data: {
        recommendation: mockRecommendation,
        application_name: 'Test App',
        application_id: 1,
        department: 'IT'
      }
    };

    const { result } = renderHook(() => useSixRAnalysis());
    
    // Set up initial state
    act(() => {
      const [state] = result.current;
      (state as any).currentAnalysisId = 123;
      (state as any).iterationNumber = 1;
      (state as any).parameters = {
        business_value: 7,
        technical_complexity: 5,
        migration_urgency: 6,
        compliance_requirements: 4,
        cost_sensitivity: 5,
        risk_tolerance: 6,
        innovation_priority: 8,
        application_type: 'custom'
      };
    });

    // Simulate WebSocket message
    act(() => {
      const mockOnMessage = (useSixRWebSocket as any).mock.calls[0][0].onMessage;
      mockOnMessage(mockMessage);
    });

    const [state] = result.current;
    expect(state.analysisStatus).toBe('completed');
    expect(state.currentRecommendation).toEqual(mockRecommendation);
    expect(state.analysisHistory).toHaveLength(1);
    expect(state.analysisHistory[0].recommended_strategy).toBe('refactor');
  });

  it('loads analysis history on mount', async () => {
    const mockHistory = [
      {
        id: 1,
        application_name: 'Test App 1',
        application_id: 1,
        department: 'IT',
        analysis_date: new Date(),
        analyst: 'User 1',
        status: 'completed',
        recommended_strategy: 'refactor',
        confidence_score: 0.85,
        iteration_count: 1,
        estimated_effort: 'medium',
        estimated_timeline: '3-6 months',
        estimated_cost_impact: 'moderate',
        parameters: {},
        key_factors: [],
        next_steps: []
      }
    ];

    (sixrApi.getAnalysisHistory as any).mockResolvedValue(mockHistory);
    (sixrApi.getBulkJobs as any).mockResolvedValue([]);
    (sixrApi.getBulkSummary as any).mockResolvedValue({
      total_jobs: 0,
      active_jobs: 0,
      completed_jobs: 0,
      failed_jobs: 0,
      total_applications_processed: 0,
      average_confidence: 0,
      strategy_distribution: {},
      processing_time_stats: { min: 0, max: 0, average: 0, total: 0 }
    });

    const { result } = renderHook(() => useSixRAnalysis({ autoLoadHistory: true }));

    await waitFor(() => {
      const [state] = result.current;
      expect(state.analysisHistory).toEqual(mockHistory);
    });
  });

  it('creates bulk analysis job', async () => {
    const mockJobResponse = {
      job_id: 'job-123',
      message: 'Bulk analysis job created'
    };

    (sixrApi.createBulkAnalysis as any).mockResolvedValue(mockJobResponse);
    (sixrApi.getBulkJobs as any).mockResolvedValue([]);
    (sixrApi.getBulkSummary as any).mockResolvedValue({
      total_jobs: 1,
      active_jobs: 1,
      completed_jobs: 0,
      failed_jobs: 0,
      total_applications_processed: 0,
      average_confidence: 0,
      strategy_distribution: {},
      processing_time_stats: { min: 0, max: 0, average: 0, total: 0 }
    });

    const { result } = renderHook(() => useSixRAnalysis());
    const [, actions] = result.current;

    await act(async () => {
      const jobId = await actions.createBulkAnalysis({
        name: 'Test Bulk Job',
        description: 'Test bulk analysis',
        application_ids: [1, 2, 3],
        priority: 'medium',
        parameters: {
          parallel_limit: 3,
          retry_failed: true,
          auto_approve_high_confidence: false,
          confidence_threshold: 0.8
        }
      });

      expect(jobId).toBe('job-123');
    });
  });

  it('controls bulk analysis jobs', async () => {
    (sixrApi.controlBulkJob as any).mockResolvedValue({
      success: true,
      message: 'Job started'
    });

    const { result } = renderHook(() => useSixRAnalysis());
    
    // Set up initial bulk jobs state
    act(() => {
      const [state] = result.current;
      (state as any).bulkJobs = [
        {
          id: 'job-123',
          name: 'Test Job',
          status: 'paused',
          priority: 'medium',
          application_ids: [1, 2, 3],
          created_at: new Date(),
          progress: {
            total: 3,
            completed: 1,
            failed: 0,
            in_progress: 1
          }
        }
      ];
    });

    const [, actions] = result.current;

    await act(async () => {
      await actions.controlBulkJob('job-123', 'start');
    });

    const [state] = result.current;
    expect(state.bulkJobs[0].status).toBe('running');
  });

  it('exports analysis results', async () => {
    const mockBlob = new Blob(['test data'], { type: 'text/csv' });
    (sixrApi.exportAnalysis as any).mockResolvedValue(mockBlob);

    // Mock URL.createObjectURL and related functions
    const mockCreateObjectURL = vi.fn(() => 'blob:mock-url');
    const mockRevokeObjectURL = vi.fn();
    const mockClick = vi.fn();
    const mockAppendChild = vi.fn();
    const mockRemoveChild = vi.fn();

    Object.defineProperty(window, 'URL', {
      value: {
        createObjectURL: mockCreateObjectURL,
        revokeObjectURL: mockRevokeObjectURL
      }
    });

    Object.defineProperty(document, 'createElement', {
      value: vi.fn(() => ({
        href: '',
        download: '',
        click: mockClick
      }))
    });

    Object.defineProperty(document.body, 'appendChild', { value: mockAppendChild });
    Object.defineProperty(document.body, 'removeChild', { value: mockRemoveChild });

    const { result } = renderHook(() => useSixRAnalysis());
    const [, actions] = result.current;

    await act(async () => {
      await actions.exportAnalyses([1, 2, 3], 'csv');
    });

    expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob);
    expect(mockClick).toHaveBeenCalled();
    expect(mockRevokeObjectURL).toHaveBeenCalled();
  });

  it('resets analysis state correctly', () => {
    const { result } = renderHook(() => useSixRAnalysis());
    
    // Set up some state
    act(() => {
      const [state] = result.current;
      (state as any).currentAnalysisId = 123;
      (state as any).analysisStatus = 'completed';
      (state as any).currentRecommendation = { recommended_strategy: 'refactor' };
    });

    const [, actions] = result.current;

    act(() => {
      actions.resetAnalysis();
    });

    const [state] = result.current;
    expect(state.currentAnalysisId).toBeNull();
    expect(state.analysisStatus).toBe('idle');
    expect(state.currentRecommendation).toBeNull();
    expect(state.iterationNumber).toBe(1);
  });

  it('handles iteration tracking correctly', async () => {
    (sixrApi.iterateAnalysis as any).mockResolvedValue({
      success: true,
      iteration_number: 2,
      message: 'Iteration started'
    });

    const { result } = renderHook(() => useSixRAnalysis());
    
    // Set up initial state
    act(() => {
      const [state] = result.current;
      (state as any).currentAnalysisId = 123;
      (state as any).iterationNumber = 1;
    });

    const [, actions] = result.current;

    await act(async () => {
      await actions.iterateAnalysis('Refining based on feedback');
    });

    const [state] = result.current;
    expect(state.iterationNumber).toBe(2);
    expect(state.analysisStatus).toBe('analyzing');
    expect(state.currentRecommendation).toBeNull();
  });

  it('cleans up resources on unmount', () => {
    const { result, unmount } = renderHook(() => useSixRAnalysis());
    
    // Set up some state
    act(() => {
      const [state] = result.current;
      (state as any).currentAnalysisId = 123;
    });

    unmount();

    expect(sixrApi.cleanup).toHaveBeenCalled();
    expect(mockWebSocketHook.unsubscribe).toHaveBeenCalledWith(123);
  });

  it('handles concurrent operations correctly', async () => {
    (sixrApi.updateParameters as any).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    const { result } = renderHook(() => useSixRAnalysis());
    
    // Set up initial state
    act(() => {
      const [state] = result.current;
      (state as any).currentAnalysisId = 123;
    });

    const [, actions] = result.current;

    // Start multiple concurrent operations
    const promises = [
      actions.updateParameters({ business_value: 8 }),
      actions.updateParameters({ technical_complexity: 3 }),
      actions.updateParameters({ innovation_priority: 9 })
    ];

    await act(async () => {
      await Promise.all(promises);
    });

    const [state] = result.current;
    // Last update should win
    expect(state.parameters.innovation_priority).toBe(9);
  });

  it('validates required analysis ID for operations', async () => {
    const { result } = renderHook(() => useSixRAnalysis());
    const [, actions] = result.current;

    // Try to update parameters without an active analysis
    await act(async () => {
      try {
        await actions.updateParameters({ business_value: 8 });
      } catch (error) {
        expect(error.message).toBe('No active analysis');
      }
    });
  });

  it('handles optimistic updates with proper rollback', async () => {
    const mockError = new Error('Network error');
    (sixrApi.updateParameters as any).mockRejectedValue(mockError);

    const { result } = renderHook(() => useSixRAnalysis({ enableOptimisticUpdates: true }));
    
    // Set up initial state
    act(() => {
      const [state] = result.current;
      (state as any).currentAnalysisId = 123;
    });

    const [, actions] = result.current;

    await act(async () => {
      await actions.updateParameters({ business_value: 8 });
    });

    const [state] = result.current;
    // Should rollback to original value on error
    expect(state.parameters.business_value).toBe(5);
    expect(state.error).toBe('Network error');
  });
}); 