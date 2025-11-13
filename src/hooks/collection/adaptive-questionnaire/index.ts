/**
 * Adaptive Questionnaire Hooks
 * React Query hooks for Collection Flow adaptive questionnaire features
 *
 * Features:
 * - Bulk Answer: Multi-asset answer propagation with conflict resolution
 * - Dynamic Questions: Asset-type-specific filtering with agent pruning
 * - Bulk Import: CSV/JSON import with intelligent field mapping
 */

export {
  useBulkAnswerPreview,
  useBulkAnswerSubmit,
} from "./useBulkAnswer";

export {
  useFilteredQuestions,
  useDependencyChange,
  type UseFilteredQuestionsOptions,
} from "./useDynamicQuestions";

export {
  useBulkImportAnalyze,
  useBulkImportExecute,
  useImportTaskStatus,
  type AnalyzeImportFileRequest,
  type UseImportTaskStatusOptions,
} from "./useBulkImport";
