/**
 * useCacheInvalidation Hook
 * Manages cache invalidation for collection flow queries
 *
 * CRITICAL: Ensures AdaptiveForms fetches updated data after selection
 */

import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

interface UseCacheInvalidationReturn {
  invalidateCollectionFlowCache: (flowId: string) => Promise<void>;
}

/**
 * Hook for managing cache invalidation after data updates
 */
export const useCacheInvalidation = (): UseCacheInvalidationReturn => {
  const queryClient = useQueryClient();

  const invalidateCollectionFlowCache = useCallback(
    async (flowId: string) => {
      // CRITICAL: Invalidate collection flow cache so AdaptiveForms fetches updated data
      await queryClient.invalidateQueries({
        queryKey: ["collection-flow", flowId],
        exact: true,
      });

      // Also invalidate any related collection flow queries
      await queryClient.invalidateQueries({
        queryKey: ["collection-flows"],
      });

      console.log(
        `✅ Cache invalidated for flow ${flowId} after application selection`,
      );
    },
    [queryClient],
  );

  return {
    invalidateCollectionFlowCache,
  };
};
