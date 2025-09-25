import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import {
  useDataCleansingStats,
  useDataCleansingAnalysis,
  useTriggerDataCleansing
} from '../useDataCleansingQueries';
import * as dataCleansingService from '../../../services/dataCleansingService';

// Mock the service
vi.mock('../../../services/dataCleansingService');

describe('useDataCleansingQueries', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    });
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  describe('useDataCleansingStats', () => {
    it('should fetch data cleansing stats when flowId is provided', async () => {
      const mockStats = {
        total_records: 100,
        total_fields: 10,
        fields_mapped: 8,
        fields_unmapped: 2,
        quality_score: 85.5
      };

      vi.mocked(dataCleansingService.getDataCleansingStats).mockResolvedValue(mockStats);

      const { result } = renderHook(
        () => useDataCleansingStats('test-flow-id'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockStats);
      expect(dataCleansingService.getDataCleansingStats).toHaveBeenCalledWith('test-flow-id');
    });

    it('should not fetch when flowId is not provided', () => {
      const { result } = renderHook(
        () => useDataCleansingStats(null),
        { wrapper }
      );

      expect(result.current.isIdle).toBe(true);
      expect(dataCleansingService.getDataCleansingStats).not.toHaveBeenCalled();
    });

    it('should have correct query key structure', () => {
      const flowId = 'test-flow-123';
      const { result } = renderHook(
        () => useDataCleansingStats(flowId),
        { wrapper }
      );

      // Query key should be ['dataCleansing', 'stats', flowId]
      const queryKey = queryClient.getQueryCache().findAll()[0]?.queryKey;
      expect(queryKey).toEqual(['dataCleansing', 'stats', flowId]);
    });
  });

  describe('useDataCleansingAnalysis', () => {
    it('should fetch data cleansing analysis when flowId is provided', async () => {
      const mockAnalysis = {
        flow_id: 'test-flow-id',
        analysis_timestamp: '2025-01-18T12:00:00Z',
        total_records: 100,
        quality_score: 89.0,
        issues_found: [],
        recommendations: [],
        processing_status: 'completed',
        source: 'agent' as const
      };

      vi.mocked(dataCleansingService.getDataCleansingAnalysis).mockResolvedValue(mockAnalysis);

      const { result } = renderHook(
        () => useDataCleansingAnalysis('test-flow-id'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockAnalysis);
      expect(dataCleansingService.getDataCleansingAnalysis).toHaveBeenCalledWith('test-flow-id');
    });

    it('should handle source field correctly', async () => {
      const mockAnalysisWithFallback = {
        flow_id: 'test-flow-id',
        analysis_timestamp: '2025-01-18T12:00:00Z',
        total_records: 50,
        quality_score: 75.0,
        issues_found: [],
        recommendations: [],
        processing_status: 'completed_without_agents',
        source: 'fallback' as const
      };

      vi.mocked(dataCleansingService.getDataCleansingAnalysis).mockResolvedValue(mockAnalysisWithFallback);

      const { result } = renderHook(
        () => useDataCleansingAnalysis('test-flow-id'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.source).toBe('fallback');
      expect(result.current.data?.processing_status).toBe('completed_without_agents');
    });
  });

  describe('useTriggerDataCleansing', () => {
    it('should trigger data cleansing mutation', async () => {
      const mockResponse = {
        flow_id: 'test-flow-id',
        status: 'success',
        analysis: {
          flow_id: 'test-flow-id',
          quality_score: 92.0,
          processing_status: 'completed',
          source: 'agent' as const
        }
      };

      vi.mocked(dataCleansingService.triggerDataCleansing).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useTriggerDataCleansing(),
        { wrapper }
      );

      await result.current.mutateAsync({ flowId: 'test-flow-id' });

      expect(dataCleansingService.triggerDataCleansing).toHaveBeenCalledWith('test-flow-id');
    });

    it('should invalidate related queries on success', async () => {
      const mockResponse = {
        flow_id: 'test-flow-id',
        status: 'success',
        analysis: {
          flow_id: 'test-flow-id',
          quality_score: 92.0,
          processing_status: 'completed',
          source: 'agent' as const
        }
      };

      vi.mocked(dataCleansingService.triggerDataCleansing).mockResolvedValue(mockResponse);

      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(
        () => useTriggerDataCleansing(),
        { wrapper }
      );

      await result.current.mutateAsync({ flowId: 'test-flow-id' });

      await waitFor(() => {
        expect(invalidateSpy).toHaveBeenCalledWith({
          queryKey: ['dataCleansing']
        });
      });
    });

    it('should handle mutation errors gracefully', async () => {
      const error = new Error('Network error');
      vi.mocked(dataCleansingService.triggerDataCleansing).mockRejectedValue(error);

      const { result } = renderHook(
        () => useTriggerDataCleansing(),
        { wrapper }
      );

      await expect(result.current.mutateAsync({ flowId: 'test-flow-id' })).rejects.toThrow('Network error');
    });
  });

  describe('Query key and enabled semantics', () => {
    it('should disable queries when flowId is undefined', () => {
      const { result: statsResult } = renderHook(
        () => useDataCleansingStats(undefined),
        { wrapper }
      );

      const { result: analysisResult } = renderHook(
        () => useDataCleansingAnalysis(undefined),
        { wrapper }
      );

      expect(statsResult.current.isIdle).toBe(true);
      expect(analysisResult.current.isIdle).toBe(true);
    });

    it('should enable queries when flowId is provided', () => {
      const { result: statsResult } = renderHook(
        () => useDataCleansingStats('valid-flow-id'),
        { wrapper }
      );

      const { result: analysisResult } = renderHook(
        () => useDataCleansingAnalysis('valid-flow-id'),
        { wrapper }
      );

      // Queries should be enabled and start fetching
      expect(statsResult.current.isIdle).toBe(false);
      expect(analysisResult.current.isIdle).toBe(false);
    });
  });
});
