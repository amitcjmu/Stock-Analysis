import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';
import type { ApiError } from '../../types/shared/api-types';

/**
 * Unified hook for fetching latest import data
 * Provides centralized caching and prevents duplicate API calls
 */
export const useLatestImport = (enabled = true): JSX.Element => {
  const { user, getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['latest-import', user?.id],
    queryFn: async () => {
      const response = await apiCall('/api/v1/data-import/latest-import', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });
      return response;
    },
    enabled: enabled && !!user?.id,
    staleTime: 2 * 60 * 1000, // Consider data fresh for 2 minutes
    cacheTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
    retry: (failureCount, error) => {
      // Don't retry on 429 (Too Many Requests) or authentication errors
      const err = error as ApiError | { status?: number };
      if (err?.status === 429 || err?.status === 401 || err?.status === 403) {
        return false;
      }
      return failureCount < 2; // Only retry twice
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000), // Exponential backoff, max 5s
  });
};
