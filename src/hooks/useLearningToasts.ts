/**
 * Learning Toasts Hook
 *
 * Custom hook for displaying toast notifications related to field mapping learning actions.
 * Provides consistent feedback for approval, rejection, and learning operations.
 */

import { useCallback } from 'react';
import type {
  FieldMappingLearningResponse,
  BulkFieldMappingLearningResponse
} from '../services/api/discoveryFlowService';

interface ToastConfig {
  title: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

// This would typically integrate with your app's toast system (react-hot-toast, sonner, etc.)
const showToast = (config: ToastConfig) => {
  // For now, we'll use console logging and try to use a global toast function if available
  console.log(`[${config.type.toUpperCase()}] ${config.title}: ${config.message}`);

  // Try to use global toast function if available (many apps add this to window)
  if (typeof window !== 'undefined') {
    if (window.showSuccessToast && config.type === 'success') {
      window.showSuccessToast(config.message);
    } else if (window.showErrorToast && config.type === 'error') {
      window.showErrorToast(config.message);
    } else if (window.showWarningToast && config.type === 'warning') {
      window.showWarningToast(config.message);
    } else if (window.showInfoToast && config.type === 'info') {
      window.showInfoToast(config.message);
    }
  }
};

// Extend window interface for toast functions
declare global {
  interface Window {
    showSuccessToast?: (message: string) => void;
    showErrorToast?: (message: string) => void;
    showWarningToast?: (message: string) => void;
    showInfoToast?: (message: string) => void;
  }
}

export const useLearningToasts = () => {
  const showApprovalSuccess = useCallback((response: FieldMappingLearningResponse, fieldName: string) => {
    const patternsText = response.patterns_created
      ? `${response.patterns_created} new pattern(s) learned`
      : 'Pattern updated';

    showToast({
      title: 'Mapping Approved',
      message: `"${fieldName}" mapping approved successfully. ${patternsText}.`,
      type: 'success',
      duration: 4000
    });
  }, []);

  const showApprovalError = useCallback((error: unknown, fieldName: string) => {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';

    showToast({
      title: 'Approval Failed',
      message: `Failed to approve "${fieldName}" mapping: ${errorMessage}`,
      type: 'error',
      duration: 5000
    });
  }, []);

  const showRejectionSuccess = useCallback((response: FieldMappingLearningResponse, fieldName: string) => {
    const patternsText = response.patterns_created
      ? `${response.patterns_created} rejection pattern(s) learned`
      : 'Rejection pattern updated';

    showToast({
      title: 'Mapping Rejected',
      message: `"${fieldName}" mapping rejected. ${patternsText}.`,
      type: 'success',
      duration: 4000
    });
  }, []);

  const showRejectionError = useCallback((error: unknown, fieldName: string) => {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';

    showToast({
      title: 'Rejection Failed',
      message: `Failed to reject "${fieldName}" mapping: ${errorMessage}`,
      type: 'error',
      duration: 5000
    });
  }, []);

  const showBulkLearningSuccess = useCallback((response: BulkFieldMappingLearningResponse) => {
    const { successful_actions, total_actions, global_patterns_created, global_patterns_updated } = response;

    if (successful_actions === total_actions) {
      showToast({
        title: 'Bulk Learning Complete',
        message: `All ${total_actions} mappings processed. ${global_patterns_created} patterns created, ${global_patterns_updated} updated.`,
        type: 'success',
        duration: 5000
      });
    } else {
      showToast({
        title: 'Bulk Learning Partial Success',
        message: `${successful_actions}/${total_actions} mappings processed successfully. ${global_patterns_created} patterns created.`,
        type: 'warning',
        duration: 6000
      });
    }
  }, []);

  const showBulkLearningError = useCallback((error: unknown, actionCount: number) => {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';

    showToast({
      title: 'Bulk Learning Failed',
      message: `Failed to process ${actionCount} mapping(s): ${errorMessage}`,
      type: 'error',
      duration: 5000
    });
  }, []);

  const showLearningCacheRefresh = useCallback(() => {
    showToast({
      title: 'Learning Cache Refreshed',
      message: 'Field mapping patterns have been refreshed from the learning system.',
      type: 'info',
      duration: 3000
    });
  }, []);

  const showLearningInfo = useCallback((message: string) => {
    showToast({
      title: 'Learning System',
      message,
      type: 'info',
      duration: 4000
    });
  }, []);

  const showConfidenceAdjustment = useCallback((oldScore: number, newScore: number, fieldName: string) => {
    const direction = newScore > oldScore ? 'increased' : 'decreased';
    const change = Math.abs((newScore - oldScore) * 100).toFixed(0);

    showToast({
      title: 'Confidence Adjusted',
      message: `"${fieldName}" confidence ${direction} by ${change}% (now ${(newScore * 100).toFixed(0)}%)`,
      type: 'info',
      duration: 3000
    });
  }, []);

  const showLearningProgress = useCallback((learnedCount: number, totalCount: number) => {
    if (learnedCount === 0) return;

    const percentage = Math.round((learnedCount / totalCount) * 100);

    showToast({
      title: 'Learning Progress',
      message: `${learnedCount} of ${totalCount} mappings have been learned (${percentage}%)`,
      type: 'info',
      duration: 3000
    });
  }, []);

  return {
    showApprovalSuccess,
    showApprovalError,
    showRejectionSuccess,
    showRejectionError,
    showBulkLearningSuccess,
    showBulkLearningError,
    showLearningCacheRefresh,
    showLearningInfo,
    showConfidenceAdjustment,
    showLearningProgress
  };
};
