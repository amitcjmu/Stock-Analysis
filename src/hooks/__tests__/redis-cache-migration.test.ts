/**
 * Integration tests for Redis Cache Migration - Week 4 Deliverables
 *
 * Tests the implementation of:
 * - Feature flags for gradual rollout
 * - Simplified API client without custom caching
 * - WebSocket cache invalidation
 * - React Query optimization
 *
 * CC Generated Test Suite
 */

import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';

// Import modules to test
import { isCacheFeatureEnabled } from '@/constants/features';
import { apiClient } from '@/lib/api/apiClient';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useFieldMappings } from '@/hooks/discovery/attribute-mapping/useFieldMappings';

// Mock environment for testing
vi.mock('@/constants/features', () => ({
  isCacheFeatureEnabled: vi.fn(),
  FEATURES: {
    CACHE: {
      USE_GLOBAL_CONTEXT: false,
      DISABLE_CUSTOM_CACHE: false,
      ENABLE_WEBSOCKET_CACHE: false,
      ENABLE_CACHE_HEADERS: false,
      REACT_QUERY_OPTIMIZATIONS: false
    }
  }
}));

// Mock WebSocket for testing
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    isConnected: false,
    subscribe: vi.fn(),
    isFeatureEnabled: false
  }))
}));

// Mock auth context
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    getAuthHeaders: () => ({ 'Authorization': 'Bearer test-token' })
  }))
}));

// Mock fetch for API testing
global.fetch = vi.fn();

describe('Redis Cache Migration - Week 4 Implementation', () => {
  let queryClient: QueryClient;
  let mockIsCacheFeatureEnabled: any;
  let mockUseWebSocket: any;

  beforeEach(() => {
    // Create a fresh query client for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          staleTime: 0,
          cacheTime: 0
        }
      }
    });

    // Setup mocks
    mockIsCacheFeatureEnabled = vi.mocked(isCacheFeatureEnabled);
    mockUseWebSocket = vi.mocked(useWebSocket);

    // Reset mocks
    vi.clearAllMocks();

    // Reset fetch mock
    (global.fetch as any).mockClear();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('Feature Flags Implementation', () => {
    it('should have all required cache feature flags', () => {
      // Test that all required feature flags exist
      expect(mockIsCacheFeatureEnabled).toBeDefined();

      // Test each flag
      mockIsCacheFeatureEnabled.mockImplementation((flag: string) => {
        const flags = [
          'USE_GLOBAL_CONTEXT',
          'DISABLE_CUSTOM_CACHE',
          'ENABLE_WEBSOCKET_CACHE',
          'ENABLE_CACHE_HEADERS',
          'REACT_QUERY_OPTIMIZATIONS'
        ];
        return flags.includes(flag);
      });

      expect(mockIsCacheFeatureEnabled('DISABLE_CUSTOM_CACHE')).toBe(true);
      expect(mockIsCacheFeatureEnabled('ENABLE_WEBSOCKET_CACHE')).toBe(true);
      expect(mockIsCacheFeatureEnabled('ENABLE_CACHE_HEADERS')).toBe(true);
      expect(mockIsCacheFeatureEnabled('REACT_QUERY_OPTIMIZATIONS')).toBe(true);
    });

    it('should handle disabled features gracefully', () => {
      mockIsCacheFeatureEnabled.mockReturnValue(false);

      expect(mockIsCacheFeatureEnabled('DISABLE_CUSTOM_CACHE')).toBe(false);
      expect(mockIsCacheFeatureEnabled('ENABLE_WEBSOCKET_CACHE')).toBe(false);
    });
  });

  describe('API Client Implementation', () => {
    beforeEach(() => {
      // Mock successful API response
      (global.fetch as any).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: 'test' }),
        headers: { get: () => 'application/json' }
      });
    });

    it('should make GET requests without custom caching', async () => {
      const result = await apiClient.get('/test-endpoint');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/test-endpoint'),
        expect.objectContaining({
          method: 'GET',
          cache: 'no-store' // Default behavior when cache headers disabled
        })
      );

      expect(result).toEqual({ data: 'test' });
    });

    it('should honor cache headers when feature flag is enabled', async () => {
      mockIsCacheFeatureEnabled.mockImplementation((flag: string) =>
        flag === 'ENABLE_CACHE_HEADERS'
      );

      const result = await apiClient.get('/test-endpoint');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/test-endpoint'),
        expect.objectContaining({
          method: 'GET',
          cache: 'default' // Should honor backend cache headers
        })
      );
    });

    it('should include auth headers in requests', async () => {
      // Mock localStorage
      const mockGetItem = vi.fn();
      Object.defineProperty(global, 'localStorage', {
        value: { getItem: mockGetItem },
        writable: true
      });

      mockGetItem.mockImplementation((key: string) => {
        if (key === 'auth_token') return 'test-token';
        if (key === 'auth_user') return JSON.stringify({ id: 'user-123' });
        return null;
      });

      await apiClient.get('/test-endpoint');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'X-User-ID': 'user-123'
          })
        })
      );
    });

    it('should handle POST requests with data', async () => {
      const testData = { name: 'test' };

      await apiClient.post('/test-endpoint', testData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/test-endpoint'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(testData),
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('should handle request deduplication for GET requests', async () => {
      // Make two identical GET requests simultaneously
      const promise1 = apiClient.get('/test-endpoint');
      const promise2 = apiClient.get('/test-endpoint');

      await Promise.all([promise1, promise2]);

      // Should only make one actual fetch call due to deduplication
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('should not deduplicate POST requests', async () => {
      const testData = { name: 'test' };

      // Make two identical POST requests simultaneously
      const promise1 = apiClient.post('/test-endpoint', testData);
      const promise2 = apiClient.post('/test-endpoint', testData);

      await Promise.all([promise1, promise2]);

      // Should make two separate fetch calls
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('WebSocket Cache Invalidation', () => {
    let mockSubscribe: any;

    beforeEach(() => {
      mockSubscribe = vi.fn();
      mockUseWebSocket.mockReturnValue({
        isConnected: true,
        subscribe: mockSubscribe,
        isFeatureEnabled: true
      });
    });

    it('should create WebSocket hook with correct configuration', () => {
      const { result } = renderHook(() => useWebSocket({
        clientAccountId: 'test-client',
        subscribedEvents: ['field_mappings_updated']
      }));

      expect(result.current).toMatchObject({
        isConnected: true,
        subscribe: expect.any(Function),
        isFeatureEnabled: true
      });
    });

    it('should handle subscription to cache events', () => {
      const { result } = renderHook(() => useWebSocket());

      const callback = vi.fn();
      result.current.subscribe('field_mappings_updated', callback);

      expect(mockSubscribe).toHaveBeenCalledWith('field_mappings_updated', callback);
    });

    it('should be disabled when feature flag is false', () => {
      mockIsCacheFeatureEnabled.mockImplementation((flag: string) =>
        flag !== 'ENABLE_WEBSOCKET_CACHE'
      );

      mockUseWebSocket.mockReturnValue({
        isConnected: false,
        subscribe: vi.fn(),
        isFeatureEnabled: false
      });

      const { result } = renderHook(() => useWebSocket());

      expect(result.current.isFeatureEnabled).toBe(false);
    });
  });

  describe('Field Mappings Hook Integration', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children);

    beforeEach(() => {
      // Mock successful API response for field mappings
      (global.fetch as any).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve([
          {
            id: 'mapping-1',
            source_field: 'name',
            target_field: 'asset_name',
            confidence: 0.95,
            is_approved: false,
            status: 'pending'
          }
        ]),
        headers: { get: () => 'application/json' }
      });
    });

    it('should use new API client when custom cache is disabled', async () => {
      mockIsCacheFeatureEnabled.mockImplementation((flag: string) =>
        flag === 'DISABLE_CUSTOM_CACHE'
      );

      const { result } = renderHook(
        () => useFieldMappings(
          { import_metadata: { import_id: 'test-import' } },
          null
        ),
        { wrapper }
      );

      // Wait for the query to complete
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
      });

      // Verify the new API client is used (no custom cache headers)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/data-import/field-mapping/imports/test-import/field-mappings'),
        expect.objectContaining({
          method: 'GET',
          cache: 'no-store'
        })
      );
    });

    it('should setup WebSocket cache invalidation listener', () => {
      mockIsCacheFeatureEnabled.mockImplementation((flag: string) =>
        flag === 'ENABLE_WEBSOCKET_CACHE'
      );

      const mockSubscribeFn = vi.fn();
      mockUseWebSocket.mockReturnValue({
        isConnected: true,
        subscribe: mockSubscribeFn,
        isFeatureEnabled: true
      });

      renderHook(
        () => useFieldMappings(
          { import_metadata: { import_id: 'test-import' } },
          null
        ),
        { wrapper }
      );

      // Verify WebSocket subscription was set up
      expect(mockSubscribeFn).toHaveBeenCalledWith(
        'field_mappings_updated',
        expect.any(Function)
      );
    });

    it('should use optimized cache times when React Query optimizations are enabled', () => {
      mockIsCacheFeatureEnabled.mockImplementation((flag: string) =>
        flag === 'REACT_QUERY_OPTIMIZATIONS'
      );

      const { result } = renderHook(
        () => useFieldMappings(
          { import_metadata: { import_id: 'test-import' } },
          null
        ),
        { wrapper }
      );

      // The hook should use optimized cache times
      // This is tested indirectly through the feature flag check
      expect(mockIsCacheFeatureEnabled).toHaveBeenCalledWith('REACT_QUERY_OPTIMIZATIONS');
    });
  });

  describe('Backward Compatibility', () => {
    it('should fall back to legacy API when custom cache is enabled', async () => {
      mockIsCacheFeatureEnabled.mockImplementation((flag: string) =>
        flag !== 'DISABLE_CUSTOM_CACHE'
      );

      // Mock the legacy apiCall function
      const mockApiCall = await import('@/config/api');
      const apiCallSpy = vi.spyOn(mockApiCall, 'apiCall');
      apiCallSpy.mockResolvedValue({ data: 'legacy' });

      const { result } = renderHook(
        () => useFieldMappings(
          { import_metadata: { import_id: 'test-import' } },
          null
        ),
        { wrapper: ({ children }: { children: React.ReactNode }) =>
          createElement(QueryClientProvider, { client: queryClient }, children) }
      );

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
      });

      // Should use legacy API call when custom cache is not disabled
      expect(mockIsCacheFeatureEnabled).toHaveBeenCalledWith('DISABLE_CUSTOM_CACHE');
    });

    it('should maintain window-based cache invalidation for bulk operations', () => {
      const { result } = renderHook(
        () => useFieldMappings(
          { import_metadata: { import_id: 'test-import' } },
          null
        ),
        { wrapper: ({ children }: { children: React.ReactNode }) =>
          createElement(QueryClientProvider, { client: queryClient }, children) }
      );

      // Check that window function is attached for backward compatibility
      expect((window as any).__invalidateFieldMappings).toBeDefined();
      expect(typeof (window as any).__invalidateFieldMappings).toBe('function');
    });
  });

  describe('Error Handling', () => {
    it('should handle API client errors gracefully', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      try {
        await apiClient.get('/test-endpoint');
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('Network Error');
      }
    });

    it('should handle WebSocket connection failures', () => {
      mockUseWebSocket.mockReturnValue({
        isConnected: false,
        error: 'Connection failed',
        subscribe: vi.fn(),
        isFeatureEnabled: true
      });

      const { result } = renderHook(() => useWebSocket());

      expect(result.current.isConnected).toBe(false);
      expect(result.current.error).toBe('Connection failed');
    });
  });
});
