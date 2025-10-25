/**
 * React Query hooks for bulk answer operations
 * Handles multi-asset answer preview and submission with conflict resolution
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { collectionFlowApi } from "@/services/api/collection-flow";
import type {
  BulkAnswerPreviewRequest,
  BulkAnswerPreviewResponse,
  BulkAnswerSubmitRequest,
  BulkAnswerSubmitResponse,
} from "@/services/api/collection-flow";

/**
 * Hook for previewing bulk answer operation
 * Shows conflicts and potential issues before submission
 */
export const useBulkAnswerPreview = (): ReturnType<typeof useMutation<BulkAnswerPreviewResponse, Error, BulkAnswerPreviewRequest>> => {
  return useMutation<BulkAnswerPreviewResponse, Error, BulkAnswerPreviewRequest>({
    mutationFn: (request) => collectionFlowApi.previewBulkAnswers(request),
    onError: (error) => {
      console.error("❌ Bulk answer preview failed:", error);
    },
  });
};

/**
 * Hook for submitting bulk answers
 * Processes answers in chunks with atomic transactions
 */
export const useBulkAnswerSubmit = (): ReturnType<typeof useMutation<BulkAnswerSubmitResponse, Error, BulkAnswerSubmitRequest>> => {
  return useMutation<BulkAnswerSubmitResponse, Error, BulkAnswerSubmitRequest>({
    mutationFn: (request) => collectionFlowApi.submitBulkAnswers(request),
    onSuccess: (data) => {
      console.log(
        `✅ Bulk answers submitted: ${data.assets_updated} assets, ${data.questions_answered} questions`
      );
      if (data.failed_chunks && data.failed_chunks.length > 0) {
        console.warn(
          `⚠️  ${data.failed_chunks.length} chunks failed:`,
          data.failed_chunks
        );
      }
    },
    onError: (error) => {
      console.error("❌ Bulk answer submission failed:", error);
    },
  });
};
