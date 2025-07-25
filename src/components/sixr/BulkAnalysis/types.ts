// TypeScript interfaces for Bulk Analysis
export interface BulkAnalysisJob {
  id: string;
  name: string;
  description?: string;
  applications: number[];
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_at: Date;
  started_at?: Date;
  completed_at?: Date;
  progress: number;
  total_applications: number;
  completed_applications: number;
  failed_applications: number;
  estimated_duration: number; // in minutes
  actual_duration?: number; // in minutes
  created_by: string;
  parameters?: {
    parallel_limit: number;
    retry_failed: boolean;
    auto_approve_high_confidence: boolean;
    confidence_threshold: number;
  };
}

export interface BulkAnalysisResult {
  job_id: string;
  application_id: number;
  application_name: string;
  status: 'completed' | 'failed' | 'skipped';
  recommended_strategy: string;
  confidence_score: number;
  processing_time: number; // in seconds
  error_message?: string;
  iteration_count: number;
}

export interface BulkAnalysisSummary {
  total_jobs: number;
  active_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_applications_processed: number;
  average_confidence: number;
  strategy_distribution: Record<string, number>;
  processing_time_stats: {
    min: number;
    max: number;
    average: number;
    total: number;
  };
}

export interface BulkAnalysisProps {
  jobs: BulkAnalysisJob[];
  results: BulkAnalysisResult[];
  summary: BulkAnalysisSummary;
  onCreateJob?: (jobConfig: Partial<BulkAnalysisJob>) => void;
  onStartJob?: (jobId: string) => void;
  onPauseJob?: (jobId: string) => void;
  onCancelJob?: (jobId: string) => void;
  onRetryJob?: (jobId: string) => void;
  onDeleteJob?: (jobId: string) => void;
  onViewResults?: (jobId: string) => void;
  onExportResults?: (jobId: string, format: 'csv' | 'json' | 'excel') => void;
}

export interface JobCreationFormData {
  name: string;
  description: string;
  selectedApplications: number[];
  priority: 'low' | 'medium' | 'high' | 'urgent';
  parameters: {
    parallel_limit: number;
    retry_failed: boolean;
    auto_approve_high_confidence: boolean;
    confidence_threshold: number;
  };
}

export interface BulkAnalysisState {
  jobs: BulkAnalysisJob[];
  results: BulkAnalysisResult[];
  summary: BulkAnalysisSummary;
  selectedJobs: string[];
  activeTab: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  filterStatus: string;
  filterPriority: string;
  searchQuery: string;
  showCreateDialog: boolean;
  showResultsDialog: boolean;
  selectedJobForResults: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface BulkAnalysisActions {
  setSelectedJobs: (jobs: string[]) => void;
  setActiveTab: (tab: string) => void;
  setSortBy: (field: string) => void;
  setSortOrder: (order: 'asc' | 'desc') => void;
  setFilterStatus: (status: string) => void;
  setFilterPriority: (priority: string) => void;
  setSearchQuery: (query: string) => void;
  setShowCreateDialog: (show: boolean) => void;
  setShowResultsDialog: (show: boolean) => void;
  setSelectedJobForResults: (jobId: string | null) => void;
  handleCreateJob: (jobConfig: Partial<BulkAnalysisJob>) => void;
  handleStartJob: (jobId: string) => void;
  handlePauseJob: (jobId: string) => void;
  handleCancelJob: (jobId: string) => void;
  handleRetryJob: (jobId: string) => void;
  handleDeleteJob: (jobId: string) => void;
  handleBulkAction: (action: string, jobIds: string[]) => void;
  handleExportResults: (jobId: string, format: 'csv' | 'json' | 'excel') => void;
}
