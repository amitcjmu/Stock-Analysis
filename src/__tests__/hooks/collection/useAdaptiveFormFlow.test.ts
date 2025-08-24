/**
 * Tests for useAdaptiveFormFlow hook to verify infinite loading fixes
 */

import { renderHook, waitFor } from '@testing-library/react';
import { vi, expect, describe, it, beforeEach } from 'vitest';
import { useAdaptiveFormFlow } from '@/hooks/collection/useAdaptiveFormFlow';
import { collectionFlowApi } from '@/services/api/collection-flow';

// Mock the API
vi.mock('@/services/api/collection-flow');
const mockedCollectionFlowApi = vi.mocked(collectionFlowApi);

// Mock toast and navigation
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() })
}));

vi.mock('react-router-dom', () => ({
  useSearchParams: () => [new URLSearchParams()]
}));

// Mock auth context
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    setCurrentFlow: vi.fn(),
    user: { role: 'analyst' }
  })
}));

// Mock collection flow management
vi.mock('@/hooks/collection/useCollectionFlowManagement', () => ({
  useCollectionFlowManagement: () => ({
    continueFlow: vi.fn(),
    deleteFlow: vi.fn()
  }),
  useIncompleteCollectionFlows: () => ({
    data: [],
    isLoading: false
  })
}));

// Mock form data transformation
vi.mock('@/utils/collection/formDataTransformation', () => ({
  convertQuestionnairesToFormData: vi.fn(),
  validateFormDataStructure: vi.fn(() => true),
  createFallbackFormData: vi.fn(() => ({
    formId: 'fallback',
    sections: [],
    totalFields: 0,
    requiredFields: 0
  }))
}));

describe('useAdaptiveFormFlow - Infinite Loading Fixes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should timeout after 10 seconds and use fallback form', async () => {
    // Mock API responses to simulate timeout
    mockedCollectionFlowApi.createFlow.mockResolvedValue({
      id: 'test-flow-1',
      status: 'active'
    } as any);

    mockedCollectionFlowApi.executeFlowPhase.mockResolvedValue({
      phase: 'initialization',
      status: 'running'
    } as any);

    mockedCollectionFlowApi.getFlowStatus.mockResolvedValue({
      status: 'running',
      current_phase: 'gap_analysis'
    } as any);

    // Mock questionnaires to never return results (simulate timeout)
    mockedCollectionFlowApi.getFlowQuestionnaires.mockRejectedValue(
      new Error('Not ready yet')
    );

    const { result } = renderHook(() =>
      useAdaptiveFormFlow({
        applicationId: 'test-app',
        autoInitialize: true
      })
    );

    // Should start loading
    expect(result.current.isLoading).toBe(true);
    expect(result.current.formData).toBe(null);

    // Wait for timeout (should be less than 15 seconds total)
    await waitFor(
      () => {
        expect(result.current.formData).not.toBe(null);
        expect(result.current.isLoading).toBe(false);
      },
      { timeout: 15000 } // Give extra time for test environment
    );

    // Should have fallback form data
    expect(result.current.formData).toBeDefined();
    expect(result.current.error).toBe(null); // No error since fallback was used
  });

  it('should handle API errors gracefully and provide fallback', async () => {
    // Mock API to throw error
    mockedCollectionFlowApi.createFlow.mockRejectedValue(
      new Error('Service unavailable')
    );

    const { result } = renderHook(() =>
      useAdaptiveFormFlow({
        applicationId: 'test-app',
        autoInitialize: true
      })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should provide fallback form when service fails
    expect(result.current.formData).toBeDefined();
    expect(result.current.error).toBe(null); // Error handled gracefully with fallback
  });

  it('should stop loading when questionnaires are received', async () => {
    // Mock successful flow creation
    mockedCollectionFlowApi.createFlow.mockResolvedValue({
      id: 'test-flow-1',
      status: 'active'
    } as any);

    mockedCollectionFlowApi.executeFlowPhase.mockResolvedValue({
      phase: 'initialization',
      status: 'running'
    } as any);

    // Mock questionnaires available after 2 seconds
    let callCount = 0;
    mockedCollectionFlowApi.getFlowQuestionnaires.mockImplementation(async () => {
      callCount++;
      if (callCount < 3) {
        throw new Error('Not ready');
      }
      return [{
        id: 'q1',
        flow_id: 'test-flow-1',
        title: 'Test Questionnaire',
        questions: []
      }];
    });

    const { result } = renderHook(() =>
      useAdaptiveFormFlow({
        applicationId: 'test-app',
        autoInitialize: true
      })
    );

    // Should start loading
    expect(result.current.isLoading).toBe(true);

    // Wait for questionnaires to be loaded
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.formData).toBeDefined();
    });

    // Should have real form data, not fallback
    expect(result.current.questionnaires).toHaveLength(1);
  });

  it('should handle 409 conflicts without infinite loops', async () => {
    // Mock 409 conflict error
    mockedCollectionFlowApi.createFlow.mockRejectedValue({
      status: 409,
      message: 'Multiple active collection flows detected'
    });

    const { result } = renderHook(() =>
      useAdaptiveFormFlow({
        applicationId: 'test-app',
        autoInitialize: true
      })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should have error (not fallback for conflicts)
    expect(result.current.error).toBeDefined();
    expect(result.current.error?.message).toContain('Multiple active');
    expect(result.current.formData).toBe(null);
  });

  it('should clear loading state even when errors occur', async () => {
    // Mock permission error
    mockedCollectionFlowApi.createFlow.mockRejectedValue({
      status: 403,
      message: 'Permission denied'
    });

    const { result } = renderHook(() =>
      useAdaptiveFormFlow({
        applicationId: 'test-app',
        autoInitialize: true
      })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Loading should be false regardless of error
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeDefined();
  });
});
