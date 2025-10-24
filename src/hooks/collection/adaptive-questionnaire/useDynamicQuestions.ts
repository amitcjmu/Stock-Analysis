/**
 * React Query hooks for dynamic question filtering
 * Handles asset-type-specific questions with agent-based pruning
 */

import { useQuery, useMutation } from "@tanstack/react-query";
import { collectionFlowApi } from "@/services/api/collection-flow";
import type {
  DynamicQuestionsRequest,
  DynamicQuestionsResponse,
  DependencyChangeRequest,
  DependencyChangeResponse,
} from "@/services/api/collection-flow";

export interface UseFilteredQuestionsOptions {
  child_flow_id: string;
  asset_id: string;
  asset_type: string;
  include_answered?: boolean;
  refresh_agent_analysis?: boolean;
  enabled?: boolean;
  /**
   * Polling interval in milliseconds when agent analysis is running
   * Default: 5000 (5 seconds)
   */
  pollingInterval?: number;
}

/**
 * Hook for getting filtered questions with optional agent pruning
 * Automatically polls when agent analysis is in progress
 */
export const useFilteredQuestions = ({
  child_flow_id,
  asset_id,
  asset_type,
  include_answered = false,
  refresh_agent_analysis = false,
  enabled = true,
  pollingInterval = 5000,
}: UseFilteredQuestionsOptions): ReturnType<typeof useQuery<DynamicQuestionsResponse, Error>> => {
  const queryResult = useQuery<DynamicQuestionsResponse, Error>({
    queryKey: [
      "filtered-questions",
      child_flow_id,
      asset_id,
      asset_type,
      include_answered,
      refresh_agent_analysis,
    ],
    queryFn: () =>
      collectionFlowApi.getFilteredQuestions({
        child_flow_id,
        asset_id,
        asset_type,
        include_answered,
        refresh_agent_analysis,
      }),
    enabled: enabled && !!child_flow_id && !!asset_id && !!asset_type,
    // Poll when agent status is not completed or fallback
    refetchInterval: (data) => {
      if (!data) return false;
      // Continue polling if agent is still working
      if (data.agent_status === "not_requested") {
        return pollingInterval;
      }
      return false; // Stop polling when completed or fallback
    },
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: false,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
  });

  return queryResult;
};

/**
 * Hook for handling dependency changes
 * Determines which questions should reopen when a critical field changes
 */
export const useDependencyChange = (): ReturnType<typeof useMutation<DependencyChangeResponse, Error, DependencyChangeRequest>> => {
  return useMutation<DependencyChangeResponse, Error, DependencyChangeRequest>({
    mutationFn: (request) => collectionFlowApi.handleDependencyChange(request),
    onSuccess: (data) => {
      if (data.reopened_question_ids.length > 0) {
        console.log(
          `🔄 Reopened ${data.reopened_question_ids.length} questions due to: ${data.reason}`
        );
      }
    },
    onError: (error) => {
      console.error("❌ Dependency change handling failed:", error);
    },
  });
};
