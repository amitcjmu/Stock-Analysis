import type { BulkAnalysisJob, BulkAnalysisResult } from '../types';

// Status colors for badges
export const statusColors = {
  pending: 'bg-gray-100 text-gray-800',
  running: 'bg-blue-100 text-blue-800',
  paused: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-orange-100 text-orange-800'
};

export const priorityColors = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800'
};

export const strategyColors = {
  rehost: 'bg-blue-100 text-blue-800',
  replatform: 'bg-green-100 text-green-800',
  refactor: 'bg-yellow-100 text-yellow-800',
  rearchitect: 'bg-purple-100 text-purple-800',
  rewrite: 'bg-indigo-100 text-indigo-800',
  replace: 'bg-orange-100 text-orange-800',
  retire: 'bg-red-100 text-red-800'
};

// Utility functions for job management
export const sortJobs = (jobs: BulkAnalysisJob[]): BulkAnalysisJob[] => {
  return [...jobs].sort((a, b) => {
    // Running jobs first, then by priority, then by creation date
    if (a.status === 'running' && b.status !== 'running') return -1;
    if (b.status === 'running' && a.status !== 'running') return 1;

    const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
    const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
    if (priorityDiff !== 0) return priorityDiff;

    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
};

export const calculateQueueStats = (jobs: BulkAnalysisJob[], maxConcurrentJobs: number): { runningJobs: number; pendingJobs: number; availableSlots: number; totalApplicationsInQueue: number; estimatedTimeRemaining: number } => {
  const runningJobs = jobs.filter(j => j.status === 'running').length;
  const pendingJobs = jobs.filter(j => j.status === 'pending').length;
  const totalApplicationsInQueue = jobs
    .filter(j => j.status === 'pending' || j.status === 'running')
    .reduce((sum, j) => sum + j.total_applications, 0);

  const estimatedTimeRemaining = jobs
    .filter(j => j.status === 'pending')
    .reduce((sum, j) => sum + j.estimated_duration, 0);

  return {
    runningJobs,
    pendingJobs,
    totalApplicationsInQueue,
    estimatedTimeRemaining,
    canStartMore: runningJobs < maxConcurrentJobs
  };
};

export const formatDuration = (minutes: number): string => {
  if (minutes < 60) {
    return `${Math.round(minutes)}m`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = Math.round(minutes % 60);
  if (hours < 24) {
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
  }
  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;
  return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`;
};

export const getStatusIcon = (status: string): string => {
  switch (status) {
    case 'pending':
      return '⏳';
    case 'running':
      return '▶️';
    case 'paused':
      return '⏸️';
    case 'completed':
      return '✅';
    case 'failed':
      return '❌';
    case 'cancelled':
      return '🚫';
    default:
      return '❓';
  }
};

export const getPriorityIcon = (priority: string): string => {
  switch (priority) {
    case 'urgent':
      return '🔴';
    case 'high':
      return '🟠';
    case 'medium':
      return '🟡';
    case 'low':
      return '🔵';
    default:
      return '⚪';
  }
};

export const calculateProgress = (job: BulkAnalysisJob): number => {
  if (job.total_applications === 0) return 0;
  return Math.round((job.completed_applications / job.total_applications) * 100);
};

export const getJobDuration = (job: BulkAnalysisJob): number | null => {
  if (!job.started_at) return null;
  const endTime = job.completed_at || new Date();
  return Math.round((endTime.getTime() - job.started_at.getTime()) / (1000 * 60)); // in minutes
};

export const filterJobs = (
  jobs: BulkAnalysisJob[],
  filters: {
    status?: string;
    priority?: string;
    search?: string;
  }
) => {
  return jobs.filter(job => {
    if (filters.status && filters.status !== 'all' && job.status !== filters.status) {
      return false;
    }
    if (filters.priority && filters.priority !== 'all' && job.priority !== filters.priority) {
      return false;
    }
    if (filters.search && !job.name.toLowerCase().includes(filters.search.toLowerCase()) &&
        !job.description?.toLowerCase().includes(filters.search.toLowerCase())) {
      return false;
    }
    return true;
  });
};

export const exportJobResults = (jobId: string, results: BulkAnalysisResult[], format: 'csv' | 'json' | 'excel'): void => {
  const jobResults = results.filter(r => r.job_id === jobId);

  switch (format) {
    case 'csv': {
      const headers = ['Application ID', 'Application Name', 'Status', 'Recommended Strategy', 'Confidence Score', 'Processing Time', 'Error Message'];
      const csvData = [
        headers.join(','),
        ...jobResults.map(result => [
          result.application_id,
          `"${result.application_name}"`,
          result.status,
          result.recommended_strategy,
          result.confidence_score,
          result.processing_time,
          result.error_message ? `"${result.error_message.replace(/"/g, '""')}"` : ''
        ].join(','))
      ].join('\n');

      const blob = new Blob([csvData], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bulk-analysis-${jobId}-results.csv`;
      a.click();
      URL.revokeObjectURL(url);
      break;
    }

    case 'json': {
      const jsonData = JSON.stringify(jobResults, null, 2);
      const blob = new Blob([jsonData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bulk-analysis-${jobId}-results.json`;
      a.click();
      URL.revokeObjectURL(url);
      break;
    }

    default:
      console.warn(`Export format ${format} not yet implemented`);
  }
};
