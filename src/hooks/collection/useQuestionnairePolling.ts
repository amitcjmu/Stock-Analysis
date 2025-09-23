/**
 * Custom hook for handling questionnaire polling with completion status
 *
 * Implements the new polling logic from questionnaire-generation-fix-plan.md:
 * - Poll every 5 seconds when completion_status === 'pending'
 * - Stop polling when status is 'ready', 'fallback', or 'failed'
 * - Display appropriate UI states based on completion_status
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { collectionFlowApi } from '@/services/api/collection-flow';
import type { AdaptiveQuestionnaireResponse } from '@/services/api/collection-flow';

export interface QuestionnairePollingState {
  questionnaires: AdaptiveQuestionnaireResponse[];
  isPolling: boolean;
  error: Error | null;
  completionStatus: "pending" | "ready" | "fallback" | "failed" | null;
  statusLine: string | null;
}

export interface QuestionnairePollingOptions {
  flowId: string;
  enabled?: boolean;
  onReady?: (questionnaires: AdaptiveQuestionnaireResponse[]) => void;
  onFallback?: (questionnaires: AdaptiveQuestionnaireResponse[]) => void;
  onFailed?: (error: string) => void;
}

export const useQuestionnairePolling = ({
  flowId,
  enabled = true,
  onReady,
  onFallback,
  onFailed
}: QuestionnairePollingOptions): QuestionnairePollingState => {
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [completionStatus, setCompletionStatus] = useState<"pending" | "ready" | "fallback" | "failed" | null>(null);
  const [statusLine, setStatusLine] = useState<string | null>(null);
  const callbacksRef = useRef({ onReady, onFallback, onFailed });

  // Update callbacks ref when they change
  useEffect(() => {
    callbacksRef.current = { onReady, onFallback, onFailed };
  }, [onReady, onFallback, onFailed]);

  // Function to fetch questionnaires and check completion status
  const fetchQuestionnaires = useCallback(async (): Promise<AdaptiveQuestionnaireResponse[]> => {
    if (!flowId) {
      throw new Error('Flow ID is required');
    }

    try {
      const questionnaires = await collectionFlowApi.getFlowQuestionnaires(flowId);
      console.log('📋 Fetched questionnaires:', questionnaires);

      // Check completion status from the first questionnaire
      if (questionnaires.length > 0) {
        const status = questionnaires[0].completion_status;
        const statusMessage = questionnaires[0].status_line;

        setCompletionStatus(status);
        setStatusLine(statusMessage || null);

        console.log(`📊 Questionnaire completion status: ${status}`, {
          statusLine: statusMessage,
          questionnaireCount: questionnaires.length
        });

        // Handle different completion statuses
        switch (status) {
          case 'ready':
            setIsPolling(false);
            setError(null);
            callbacksRef.current.onReady?.(questionnaires);
            break;

          case 'fallback':
            setIsPolling(false);
            setError(null);
            callbacksRef.current.onFallback?.(questionnaires);
            break;

          case 'failed': {
            setIsPolling(false);
            const errorMessage = statusMessage || 'Questionnaire generation failed';
            setError(new Error(errorMessage));
            callbacksRef.current.onFailed?.(errorMessage);
            break;
          }

          case 'pending':
            // Continue polling
            setIsPolling(true);
            setError(null);
            break;

          default:
            console.warn('Unknown completion status:', status);
            setIsPolling(false);
            break;
        }
      } else {
        // No questionnaires found - could mean still generating or error
        setCompletionStatus('pending');
        setStatusLine('Generating questionnaire...');
        setIsPolling(true);
      }

      return questionnaires;
    } catch (err) {
      console.error('❌ Failed to fetch questionnaires:', err);

      // Handle specific error cases
      if (err && typeof err === 'object' && 'code' in err) {
        const error = err as { code: string; status?: number };
        if (error.code === 'no_applications_selected' && error.status === 422) {
          // This is a specific error case, not a polling failure
          throw err;
        }
      }

      setError(err as Error);
      setIsPolling(false);
      setCompletionStatus('failed');
      setStatusLine('Failed to fetch questionnaire status');
      throw err;
    }
  }, [flowId]);

  // Use React Query for data fetching with conditional polling
  const {
    data: questionnaires = [],
    isLoading,
    refetch
  } = useQuery({
    queryKey: ['questionnaires', flowId],
    queryFn: fetchQuestionnaires,
    enabled: enabled && !!flowId,
    // Polling configuration based on completion status
    refetchInterval: (data, query) => {
      // Only poll if status is pending
      if (completionStatus === 'pending' && isPolling) {
        return 5000; // Poll every 5 seconds
      }
      return false; // Stop polling
    },
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    // Keep data for 30 seconds to prevent unnecessary re-fetching
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000, // 5 minutes cache time
    retry: (failureCount, error) => {
      // Don't retry on specific errors
      if (error && typeof error === 'object' && 'code' in error) {
        const typedError = error as { code: string; status?: number };
        if (typedError.code === 'no_applications_selected' && typedError.status === 422) {
          return false;
        }
      }
      // Retry up to 3 times for other errors
      return failureCount < 3;
    }
  });

  // Start polling when enabled and we have a flow ID
  useEffect(() => {
    if (enabled && flowId && !questionnaires.length) {
      console.log('🔄 Starting questionnaire polling for flow:', flowId);
      setIsPolling(true);
      setError(null);
      setCompletionStatus('pending');
      setStatusLine('Checking questionnaire status...');
    }
  }, [enabled, flowId, questionnaires.length]);

  // Expose method to manually trigger a status check
  const checkStatus = useCallback(() => {
    if (flowId) {
      refetch();
    }
  }, [flowId, refetch]);

  return {
    questionnaires,
    isPolling: isPolling || isLoading,
    error,
    completionStatus,
    statusLine
  };
};
