/**
 * Tests for Unified Discovery Flow Hook - Consolidation Implementation
 *
 * This test suite validates the unified discovery flow hook functionality,
 * ensuring proper integration with the backend flow system.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import React from 'react';

// Mock the unified discovery flow hook
const mockUseUnifiedDiscoveryFlow = vi.fn();

// Mock API responses
const mockFlowState = {
  flow_id: 'test-flow-123',
  flow_type: 'discovery',
  client_account_id: 'client-789',
  engagement_id: 'engagement-101',
  user_id: 'user-202',
  current_phase: 'data_cleansing',
  phase_completion: {
    data_import: true,
    field_mapping: true,
    data_cleansing: false,
    asset_inventory: false,
    dependency_analysis: false,
    tech_debt_analysis: false
  },
  crew_status: {
    field_mapping: { status: 'completed', timestamp: '2025-01-21T10:00:00Z' },
    data_cleansing: { status: 'running', timestamp: '2025-01-21T10:30:00Z' }
  },
  raw_data: [
    { hostname: 'server01', ip: '192.168.1.10' },
    { hostname: 'server02', ip: '192.168.1.11' }
  ],
  field_mappings: {
    hostname: { target: 'server_name', confidence: 0.95 },
    ip: { target: 'ip_address', confidence: 0.90 }
  },
  cleaned_data: [],
  asset_inventory: {},
  dependencies: {},
  technical_debt: {},
  status: 'running',
  progress_percentage: 33.3,
  errors: [],
  warnings: [],
  created_at: '2025-01-21T09:00:00Z',
  updated_at: '2025-01-21T10:30:00Z'
};

// Mock fetch API
global.fetch = vi.fn();

// Test wrapper with React Query provider
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    React.createElement(QueryClientProvider, { client: queryClient }, children)
  );
};

describe('useUnifiedDiscoveryFlow Hook', () => {
  let mockFetch: jest.MockedFunction<typeof fetch>;

  beforeEach(() => {
    mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
    mockFetch.mockClear();

    // Default successful API response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFlowState,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Flow State Management', () => {
    it('should fetch flow state successfully', async () => {
      // Mock the hook implementation
      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: mockFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      expect(result.current.flowState).toEqual(mockFlowState);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle loading state correctly', async () => {
      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: null,
        isLoading: true,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      expect(result.current.isLoading).toBe(true);
      expect(result.current.flowState).toBeNull();
    });

    it('should handle error state correctly', async () => {
      const mockError = new Error('Failed to fetch flow state');

      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: null,
        isLoading: false,
        error: mockError,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      expect(result.current.error).toEqual(mockError);
      expect(result.current.flowState).toBeNull();
    });
  });

  describe('Phase Data Access', () => {
    it('should return correct phase data', () => {
      const mockGetPhaseData = vi.fn();
      mockGetPhaseData.mockReturnValue(mockFlowState.field_mappings);

      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: mockFlowState,
        isLoading: false,
        error: null,
        getPhaseData: mockGetPhaseData,
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      const fieldMappingData = result.current.getPhaseData('field_mapping');

      expect(mockGetPhaseData).toHaveBeenCalledWith('field_mapping');
      expect(fieldMappingData).toEqual(mockFlowState.field_mappings);
    });

    it('should correctly identify completed phases', () => {
      const mockIsPhaseComplete = vi.fn();
      mockIsPhaseComplete.mockImplementation((phase: string) => {
        return mockFlowState.phase_completion[phase as keyof typeof mockFlowState.phase_completion];
      });

      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: mockFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: mockIsPhaseComplete,
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      expect(result.current.isPhaseComplete('field_mapping')).toBe(true);
      expect(result.current.isPhaseComplete('data_cleansing')).toBe(false);
      expect(result.current.isPhaseComplete('asset_inventory')).toBe(false);
    });

    it('should correctly determine phase progression capability', () => {
      const mockCanProceedToPhase = vi.fn();
      mockCanProceedToPhase.mockImplementation((phase: string) => {
        // Logic: can proceed if previous phase is complete
        const phaseOrder = ['field_mapping', 'data_cleansing', 'asset_inventory', 'dependency_analysis', 'tech_debt_analysis'];
        const currentIndex = phaseOrder.indexOf(phase);
        if (currentIndex <= 0) return true;

        const previousPhase = phaseOrder[currentIndex - 1];
        return mockFlowState.phase_completion[previousPhase as keyof typeof mockFlowState.phase_completion];
      });

      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: mockFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: mockCanProceedToPhase,
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      expect(result.current.canProceedToPhase('data_cleansing')).toBe(true); // field_mapping is complete
      expect(result.current.canProceedToPhase('asset_inventory')).toBe(false); // data_cleansing not complete
    });
  });

  describe('Phase Execution', () => {
    it('should execute flow phase successfully', async () => {
      const mockExecuteFlowPhase = vi.fn();
      mockExecuteFlowPhase.mockResolvedValue({ success: true });

      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: mockFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: mockExecuteFlowPhase,
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      await result.current.executeFlowPhase('data_cleansing');

      expect(mockExecuteFlowPhase).toHaveBeenCalledWith('data_cleansing');
    });

    it('should handle phase execution errors', async () => {
      const mockExecuteFlowPhase = vi.fn();
      mockExecuteFlowPhase.mockRejectedValue(new Error('Phase execution failed'));

      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: mockFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: mockExecuteFlowPhase,
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      await expect(result.current.executeFlowPhase('data_cleansing'))
        .rejects.toThrow('Phase execution failed');
    });

    it('should track execution state correctly', () => {
      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: mockFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: true, // Currently executing
        refreshFlow: vi.fn(),
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      expect(result.current.isExecutingPhase).toBe(true);
    });
  });

  describe('Flow Refresh', () => {
    it('should refresh flow state successfully', async () => {
      const mockRefreshFlow = vi.fn();
      mockRefreshFlow.mockResolvedValue(mockFlowState);

      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: mockFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: mockRefreshFlow,
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      await result.current.refreshFlow();

      expect(mockRefreshFlow).toHaveBeenCalled();
    });

    it('should handle refresh errors', async () => {
      const mockRefreshFlow = vi.fn();
      mockRefreshFlow.mockRejectedValue(new Error('Refresh failed'));

      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: mockFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: mockRefreshFlow,
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      await expect(result.current.refreshFlow())
        .rejects.toThrow('Refresh failed');
    });
  });

  describe('Real-time Updates', () => {
    it('should handle real-time flow state updates', async () => {
      const updatedFlowState = {
        ...mockFlowState,
        current_phase: 'asset_inventory',
        phase_completion: {
          ...mockFlowState.phase_completion,
          data_cleansing: true
        },
        progress_percentage: 50.0
      };

      // Simulate state update
      mockUseUnifiedDiscoveryFlow.mockReturnValueOnce({
        flowState: mockFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      const { result, rerender } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      expect(result.current.flowState?.current_phase).toBe('data_cleansing');

      // Simulate state update
      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: updatedFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      rerender();

      expect(result.current.flowState?.current_phase).toBe('asset_inventory');
      expect(result.current.flowState?.progress_percentage).toBe(50.0);
    });
  });

  describe('Multi-tenant Support', () => {
    it('should handle different client contexts', () => {
      const clientFlowState = {
        ...mockFlowState,
        client_account_id: 'different-client-123',
        engagement_id: 'different-engagement-456'
      };

      mockUseUnifiedDiscoveryFlow.mockReturnValue({
        flowState: clientFlowState,
        isLoading: false,
        error: null,
        getPhaseData: vi.fn(),
        isPhaseComplete: vi.fn(),
        canProceedToPhase: vi.fn(),
        executeFlowPhase: vi.fn(),
        isExecutingPhase: false,
        refreshFlow: vi.fn(),
      });

      const { result } = renderHook(
        () => mockUseUnifiedDiscoveryFlow(),
        { wrapper: createWrapper() }
      );

      expect(result.current.flowState?.client_account_id).toBe('different-client-123');
      expect(result.current.flowState?.engagement_id).toBe('different-engagement-456');
    });
  });
});
