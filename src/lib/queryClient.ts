import { QueryClient } from '@tanstack/react-query';
import type { ApiError } from '@/types/shared/api-types';
import { isCacheFeatureEnabled } from '@/constants/features';

// Optimal cache times for different endpoint types
const CACHE_TIMES = {
  // User context and auth - short cache time as it changes frequently
  USER_CONTEXT: {
    staleTime: 30 * 1000, // 30 seconds
    cacheTime: 2 * 60 * 1000, // 2 minutes
  },

  // Field mappings - medium cache time, updated via WebSocket
  FIELD_MAPPINGS: {
    staleTime: 2 * 60 * 1000, // 2 minutes
    cacheTime: 5 * 60 * 1000, // 5 minutes
  },

  // Asset inventory - longer cache time, bulk operations
  ASSET_INVENTORY: {
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  },

  // Static data - very long cache time
  STATIC_DATA: {
    staleTime: 30 * 60 * 1000, // 30 minutes
    cacheTime: 60 * 60 * 1000, // 1 hour
  },

  // Default cache times
  DEFAULT: {
    staleTime: 2 * 60 * 1000, // 2 minutes
    cacheTime: 5 * 60 * 1000, // 5 minutes
  }
};

// Get cache configuration based on query key
const getCacheConfig = (queryKey: unknown[]) => {
  const key = queryKey[0] as string;

  if (key.includes('user') || key.includes('auth') || key.includes('context')) {
    return CACHE_TIMES.USER_CONTEXT;
  }

  if (key.includes('field-mapping') || key.includes('attribute-mapping')) {
    return CACHE_TIMES.FIELD_MAPPINGS;
  }

  if (key.includes('asset') || key.includes('inventory') || key.includes('discovery')) {
    return CACHE_TIMES.ASSET_INVENTORY;
  }

  if (key.includes('template') || key.includes('config') || key.includes('reference')) {
    return CACHE_TIMES.STATIC_DATA;
  }

  return CACHE_TIMES.DEFAULT;
};

// Create query client with optimized configuration
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Dynamic cache times based on query type
      staleTime: (context) => {
        if (isCacheFeatureEnabled('REACT_QUERY_OPTIMIZATIONS') && context?.queryKey) {
          return getCacheConfig(context.queryKey).staleTime;
        }
        return CACHE_TIMES.DEFAULT.staleTime;
      },

      // Conservative refetch settings to rely on WebSocket invalidation
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      refetchOnMount: true,

      // Optimized retry logic
      retry: (failureCount: number, error: ApiError & { status?: number; isAuthError?: boolean }) => {
        // Don't retry on authentication errors
        if (error?.status === 401 || error?.isAuthError) {
          return false;
        }

        // Don't retry on client errors (4xx except 429)
        if (error?.status >= 400 && error?.status < 500 && error?.status !== 429) {
          return false;
        }

        // Retry rate-limited requests with longer delays
        if (error?.status === 429) {
          return failureCount < 2; // Only 2 retries for rate limits
        }

        // Retry up to 3 times for other errors
        return failureCount < 3;
      },

      // Exponential backoff with jitter
      retryDelay: (attemptIndex: number, error: ApiError & { status?: number }) => {
        // Longer delays for rate limits
        if (error?.status === 429) {
          return Math.min(5000 * 2 ** attemptIndex, 60000); // 5s, 10s, 20s max
        }

        // Standard exponential backoff with jitter
        const baseDelay = 1000 * 2 ** attemptIndex;
        const jitter = Math.random() * 500; // Add up to 500ms jitter
        return Math.min(baseDelay + jitter, 30000);
      },

      // Network mode for offline support
      networkMode: 'online',

      // Meta data for tracking
      meta: {
        source: 'api-client-v2'
      }
    },

    mutations: {
      // Don't retry mutations by default
      retry: false,

      // Network mode for mutations
      networkMode: 'online',

      // Meta data for tracking
      meta: {
        source: 'api-client-v2'
      }
    }
  },
});

// Helper function to get cache configuration for specific query types
export const getQueryConfig = (queryType: keyof typeof CACHE_TIMES) => {
  return CACHE_TIMES[queryType];
};

// Helper function to invalidate queries by pattern
export const invalidateQueriesByPattern = async (pattern: string) => {
  await queryClient.invalidateQueries({
    predicate: (query) => {
      const queryKey = query.queryKey[0] as string;
      return queryKey.includes(pattern);
    }
  });
};

// Helper function to clear stale queries
export const clearStaleQueries = () => {
  queryClient.removeQueries({
    predicate: (query) => {
      const now = Date.now();
      const config = getCacheConfig(query.queryKey);
      return query.state.dataUpdatedAt + config.cacheTime < now;
    }
  });
};
