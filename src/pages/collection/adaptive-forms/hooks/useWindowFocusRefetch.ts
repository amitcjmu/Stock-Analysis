/**
 * Custom hook for handling window focus refetch logic
 * Extracted from AdaptiveForms.tsx
 *
 * This hook ensures data is refetched when user returns from navigation
 * (e.g., application selection page), maintaining data freshness
 */

import { useEffect } from "react";

interface UseWindowFocusRefetchProps {
  activeFlowId: string | null;
  isLoadingFlow: boolean;
  refetchCollectionFlow: () => Promise<void>;
  enabled?: boolean;
}

/**
 * Hook to refetch collection flow data when window regains focus
 * Critical for detecting application selection updates when navigating back
 */
export const useWindowFocusRefetch = ({
  activeFlowId,
  isLoadingFlow,
  refetchCollectionFlow,
  enabled = true,
}: UseWindowFocusRefetchProps): void => {
  useEffect(() => {
    if (!enabled) return;

    const handleWindowFocus = async () => {
      if (activeFlowId && !isLoadingFlow) {
        console.log(
          "🔄 Window focused - refetching collection flow data to check for application updates"
        );
        await refetchCollectionFlow();
      }
    };

    window.addEventListener("focus", handleWindowFocus);
    return () => {
      window.removeEventListener("focus", handleWindowFocus);
    };
  }, [activeFlowId, isLoadingFlow, refetchCollectionFlow, enabled]);
};
