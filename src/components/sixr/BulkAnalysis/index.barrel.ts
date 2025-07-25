// Main exports for BulkAnalysis module
export { default } from './index';

// Hook exports
export { useBulkAnalysis } from './hooks/useBulkAnalysis';

// Component exports
export { JobQueue } from './components/JobQueue';
export { JobCreationDialog } from './components/JobCreationDialog';
export { JobResults } from './components/JobResults';
export { AnalyticsSummary } from './components/AnalyticsSummary';

// Utility exports
export {
  statusColors,
  priorityColors,
  strategyColors,
  sortJobs,
  calculateQueueStats,
  formatDuration,
  getStatusIcon,
  getPriorityIcon,
  calculateProgress,
  getJobDuration,
  filterJobs,
  exportJobResults
} from './utils/analysisUtils';

// Type exports
export type {
  BulkAnalysisJob,
  BulkAnalysisResult,
  BulkAnalysisSummary,
  BulkAnalysisProps,
  JobCreationFormData,
  BulkAnalysisState,
  BulkAnalysisActions
} from './types';

// Legacy export for backward compatibility
export { default as BulkAnalysis } from './index';
