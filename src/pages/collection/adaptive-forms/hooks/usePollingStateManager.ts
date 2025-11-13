/**
 * usePollingStateManager Hook
 * Manages HTTP polling for real-time updates during workflow initialization
 */

import { useCollectionStatePolling } from '@/hooks/collection/useCollectionStatePolling';
import { toast } from '@/components/ui/use-toast';
import type { CollectionFormData } from '@/components/collection/types';
import { debugLog, debugWarn, debugError } from '@/utils/debug';

interface UsePollingStateManagerProps {
  activeFlowId: string | null;
  isLoading: boolean;
  formData: CollectionFormData | null;
}

interface UsePollingStateManagerReturn {
  isPollingActive: boolean;
  requestStatusUpdate: () => Promise<unknown>;
  flowState: ReturnType<typeof useCollectionStatePolling>['flowState'];
}

/**
 * Hook for managing HTTP polling state during workflow initialization
 */
export const usePollingStateManager = ({
  activeFlowId,
  isLoading,
  formData,
}: UsePollingStateManagerProps): UsePollingStateManagerReturn => {
  // Use HTTP polling for real-time updates during workflow initialization
  const { isActive: isPollingActive, requestStatusUpdate, flowState } =
    useCollectionStatePolling({
      flowId: activeFlowId,
      enabled: !!activeFlowId && isLoading && !formData,
      onQuestionnaireReady: (state) => {
        debugLog('🎉 HTTP Polling: Questionnaire ready notification');
      },
      onStatusUpdate: (state) => {
        debugLog('📊 HTTP Polling: Workflow status update:', state);
      },
      onError: (error) => {
        debugError('❌ HTTP Polling: Collection workflow error:', error);
        // Security: Sanitize error message to avoid exposing sensitive information
        const userFriendlyMessage = typeof error === 'string'
          ? error
          : error?.message || 'An unexpected error occurred during workflow processing';
        toast({
          title: 'Workflow Error',
          description: userFriendlyMessage.includes('network') || userFriendlyMessage.includes('timeout')
            ? 'Network error occurred. Please check your connection and try again.'
            : 'Collection workflow encountered an error. Please try again or contact support if the issue persists.',
          variant: 'destructive',
        });
      },
    });

  return {
    isPollingActive,
    requestStatusUpdate,
    flowState,
  };
};
