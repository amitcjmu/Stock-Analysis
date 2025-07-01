import { useState, useEffect, useMemo } from 'react';
import { toast } from 'sonner';
import type { BulkAnalysisJob, BulkAnalysisResult, BulkAnalysisSummary, BulkAnalysisState, JobCreationFormData } from '../types';
import { sortJobs, calculateQueueStats, filterJobs } from '../utils/analysisUtils';

interface UseBulkAnalysisProps {
  jobs: BulkAnalysisJob[];
  results: BulkAnalysisResult[];
  summary: BulkAnalysisSummary;
  maxConcurrentJobs?: number;
  onCreateJob?: (jobConfig: Partial<BulkAnalysisJob>) => void;
  onStartJob?: (jobId: string) => void;
  onPauseJob?: (jobId: string) => void;
  onCancelJob?: (jobId: string) => void;
  onRetryJob?: (jobId: string) => void;
  onDeleteJob?: (jobId: string) => void;
  onExportResults?: (jobId: string, format: 'csv' | 'json' | 'excel') => void;
}

export const useBulkAnalysis = ({
  jobs,
  results,
  summary,
  maxConcurrentJobs = 3,
  onCreateJob,
  onStartJob,
  onPauseJob,
  onCancelJob,
  onRetryJob,
  onDeleteJob,
  onExportResults
}: UseBulkAnalysisProps) => {
  
  const [state, setState] = useState<BulkAnalysisState>({
    jobs,
    results,
    summary,
    selectedJobs: [],
    activeTab: 'queue',
    sortBy: 'created_at',
    sortOrder: 'desc',
    filterStatus: 'all',
    filterPriority: 'all',
    searchQuery: '',
    showCreateDialog: false,
    showResultsDialog: false,
    selectedJobForResults: null,
    isLoading: false,
    error: null
  });

  const [newJobConfig, setNewJobConfig] = useState<JobCreationFormData>({
    name: '',
    description: '',
    selectedApplications: [],
    priority: 'medium',
    parameters: {
      parallel_limit: 5,
      retry_failed: true,
      auto_approve_high_confidence: false,
      confidence_threshold: 0.8
    }
  });

  // Update state when props change
  useEffect(() => {
    setState(prev => ({
      ...prev,
      jobs,
      results,
      summary
    }));
  }, [jobs, results, summary]);

  // Real-time updates simulation
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate progress updates for running jobs
      // In real implementation, this would come from WebSocket or polling
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Filter and sort jobs
  const filteredAndSortedJobs = useMemo(() => {
    const filtered = filterJobs(jobs, {
      status: state.filterStatus,
      priority: state.filterPriority,
      search: state.searchQuery
    });
    return sortJobs(filtered);
  }, [jobs, state.filterStatus, state.filterPriority, state.searchQuery]);

  // Calculate queue statistics
  const queueStats = useMemo(() => {
    return calculateQueueStats(jobs, maxConcurrentJobs);
  }, [jobs, maxConcurrentJobs]);

  // Actions
  const actions = {
    setSelectedJobs: (selectedJobs: string[]) => {
      setState(prev => ({ ...prev, selectedJobs }));
    },

    setActiveTab: (activeTab: string) => {
      setState(prev => ({ ...prev, activeTab }));
    },

    setFilterStatus: (filterStatus: string) => {
      setState(prev => ({ ...prev, filterStatus }));
    },

    setFilterPriority: (filterPriority: string) => {
      setState(prev => ({ ...prev, filterPriority }));
    },

    setSearchQuery: (searchQuery: string) => {
      setState(prev => ({ ...prev, searchQuery }));
    },

    setShowCreateDialog: (showCreateDialog: boolean) => {
      setState(prev => ({ ...prev, showCreateDialog }));
    },

    setShowResultsDialog: (showResultsDialog: boolean) => {
      setState(prev => ({ ...prev, showResultsDialog }));
    },

    setSelectedJobForResults: (selectedJobForResults: string | null) => {
      setState(prev => ({ ...prev, selectedJobForResults }));
    },

    handleSelectJob: (jobId: string) => {
      setState(prev => ({
        ...prev,
        selectedJobs: prev.selectedJobs.includes(jobId)
          ? prev.selectedJobs.filter(id => id !== jobId)
          : [...prev.selectedJobs, jobId]
      }));
    },

    handleSelectAll: () => {
      setState(prev => ({
        ...prev,
        selectedJobs: prev.selectedJobs.length === jobs.length ? [] : jobs.map(j => j.id)
      }));
    },

    handleCreateJob: () => {
      if (!newJobConfig.name.trim()) {
        toast.error('Please enter a job name');
        return;
      }

      if (onCreateJob) {
        onCreateJob({
          name: newJobConfig.name,
          description: newJobConfig.description,
          priority: newJobConfig.priority,
          applications: newJobConfig.selectedApplications,
          parameters: newJobConfig.parameters
        });
        
        setState(prev => ({ ...prev, showCreateDialog: false }));
        setNewJobConfig({
          name: '',
          description: '',
          selectedApplications: [],
          priority: 'medium',
          parameters: {
            parallel_limit: 5,
            retry_failed: true,
            auto_approve_high_confidence: false,
            confidence_threshold: 0.8
          }
        });
        
        toast.success('Job created successfully');
      }
    },

    handleStartJob: (jobId: string) => {
      if (!queueStats.canStartMore) {
        toast.error(`Cannot start more than ${maxConcurrentJobs} concurrent jobs`);
        return;
      }
      
      if (onStartJob) {
        onStartJob(jobId);
        toast.success('Job started');
      }
    },

    handlePauseJob: (jobId: string) => {
      if (onPauseJob) {
        onPauseJob(jobId);
        toast.success('Job paused');
      }
    },

    handleCancelJob: (jobId: string) => {
      if (onCancelJob) {
        onCancelJob(jobId);
        toast.success('Job cancelled');
      }
    },

    handleRetryJob: (jobId: string) => {
      if (onRetryJob) {
        onRetryJob(jobId);
        toast.success('Job retry initiated');
      }
    },

    handleDeleteJob: (jobId: string) => {
      if (onDeleteJob) {
        onDeleteJob(jobId);
        toast.success('Job deleted');
      }
    },

    handleBulkAction: (action: string, jobIds: string[]) => {
      if (jobIds.length === 0) {
        toast.error('No jobs selected');
        return;
      }

      switch (action) {
        case 'start':
          if (queueStats.runningJobs + jobIds.length > maxConcurrentJobs) {
            toast.error(`Cannot start more than ${maxConcurrentJobs} concurrent jobs`);
            return;
          }
          jobIds.forEach(id => actions.handleStartJob(id));
          break;
        case 'pause':
          jobIds.forEach(id => actions.handlePauseJob(id));
          break;
        case 'cancel':
          jobIds.forEach(id => actions.handleCancelJob(id));
          break;
        case 'delete':
          jobIds.forEach(id => actions.handleDeleteJob(id));
          break;
        default:
          toast.error('Unknown action');
      }
    },

    handleExportResults: (jobId: string, format: 'csv' | 'json' | 'excel') => {
      if (onExportResults) {
        onExportResults(jobId, format);
        toast.success(`Results exported as ${format.toUpperCase()}`);
      }
    },

    handleViewResults: (jobId: string) => {
      setState(prev => ({
        ...prev,
        selectedJobForResults: jobId,
        showResultsDialog: true
      }));
    }
  };

  return {
    // State
    state,
    newJobConfig,
    setNewJobConfig,
    
    // Computed values
    filteredAndSortedJobs,
    queueStats,
    
    // Actions
    ...actions
  };
};