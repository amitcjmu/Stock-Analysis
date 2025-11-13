/**
 * React Query hooks for bulk import operations
 * Handles CSV/JSON file analysis, field mapping, and import execution
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { collectionFlowApi } from "@/services/api/collection-flow";
import type {
  ImportAnalysisResponse,
  ImportExecutionRequest,
  ImportTaskResponse,
  ImportTaskDetailResponse,
} from "@/services/api/collection-flow";

export interface AnalyzeImportFileRequest {
  file: File;
  import_type: "application" | "server" | "database";
}

/**
 * Hook for analyzing import file
 * Returns field mapping suggestions and validation warnings
 */
export const useBulkImportAnalyze = (): ReturnType<typeof useMutation<ImportAnalysisResponse, Error, AnalyzeImportFileRequest>> => {
  return useMutation<ImportAnalysisResponse, Error, AnalyzeImportFileRequest>({
    mutationFn: ({ file, import_type }) =>
      collectionFlowApi.analyzeImportFile(file, import_type),
    onSuccess: (data) => {
      console.log(
        `📊 Analyzed import file: ${data.file_name} (${data.total_rows} rows, ${data.detected_columns.length} columns)`
      );
      if (data.validation_warnings.length > 0) {
        console.warn(
          `⚠️  ${data.validation_warnings.length} validation warnings:`,
          data.validation_warnings
        );
      }
    },
    onError: (error) => {
      console.error("❌ Import file analysis failed:", error);
    },
  });
};

/**
 * Hook for executing import with confirmed mappings
 * Creates a background task for async processing
 */
export const useBulkImportExecute = (): ReturnType<typeof useMutation<ImportTaskResponse, Error, ImportExecutionRequest>> => {
  return useMutation<ImportTaskResponse, Error, ImportExecutionRequest>({
    mutationFn: (request) => collectionFlowApi.executeImport(request),
    onSuccess: (data) => {
      console.log(
        `✅ Import task created: ${data.id} (status: ${data.status})`
      );
    },
    onError: (error) => {
      console.error("❌ Import execution failed:", error);
    },
  });
};

export interface UseImportTaskStatusOptions {
  task_id?: string;
  enabled?: boolean;
  /**
   * Polling interval in milliseconds when task is running
   * Default: 2000 (2 seconds)
   */
  pollingInterval?: number;
}

/**
 * Hook for polling import task status
 * Automatically polls while task is pending or running
 */
export const useImportTaskStatus = ({
  task_id,
  enabled = true,
  pollingInterval = 2000,
}: UseImportTaskStatusOptions): ReturnType<typeof useQuery<ImportTaskDetailResponse, Error>> => {
  const queryResult = useQuery<ImportTaskDetailResponse, Error>({
    queryKey: ["import-task-status", task_id],
    queryFn: () => {
      if (!task_id) {
        throw new Error("Task ID is required");
      }
      return collectionFlowApi.getImportTaskStatus(task_id);
    },
    enabled: enabled && !!task_id,
    // Poll while task is pending or running
    refetchInterval: (data) => {
      if (!data) return false;
      if (data.status === "pending" || data.status === "running") {
        return pollingInterval;
      }
      return false; // Stop polling when completed or failed
    },
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: false,
    staleTime: 1000, // 1 second - keep status fresh
    gcTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error) => {
      // Don't retry on 404 (task not found)
      if (error && typeof error === "object" && "status" in error) {
        const typedError = error as { status?: number };
        if (typedError.status === 404) {
          return false;
        }
      }
      // Retry up to 3 times for other errors
      return failureCount < 3;
    },
  });

  return queryResult;
};
