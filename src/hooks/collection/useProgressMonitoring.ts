/**
 * Custom hook for monitoring collection progress
 *
 * Extracted from Progress.tsx to provide reusable progress monitoring logic
 * for collection workflows and flow management.
 */

import { useState, useEffect, useCallback } from 'react'
import { useToast } from '@/components/ui/use-toast';
import type { ProgressMilestone } from '@/components/collection/types';
import { collectionFlowApi } from '@/services/api/collection-flow';

export interface CollectionFlow {
  id: string;
  name: string;
  type: 'adaptive' | 'bulk' | 'integration';
  status: 'running' | 'paused' | 'completed' | 'failed';
  progress: number;
  startedAt: string;
  completedAt?: string;
  estimatedCompletion?: string;
  applicationCount: number;
  completedApplications: number;
}

export interface CollectionMetrics {
  totalFlows: number;
  activeFlows: number;
  completedFlows: number;
  failedFlows: number;
  totalApplications: number;
  completedApplications: number;
  averageCompletionTime: number;
  dataQualityScore: number;
}

export interface UseProgressMonitoringOptions {
  flowId?: string | null;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export interface ProgressMonitoringState {
  flows: CollectionFlow[];
  metrics: CollectionMetrics | null;
  selectedFlow: string | null;
  isLoading: boolean;
  error: Error | null;
}

export interface ReadinessSummary {
  flow_id: string;
  apps_ready_for_assessment: number;
  phase_scores: { collection: number; discovery: number };
  quality: { collection_quality_score: number; confidence_score: number };
}

export interface ProgressMonitoringActions {
  selectFlow: (flowId: string) => void;
  handleFlowAction: (flowId: string, action: 'pause' | 'resume' | 'stop') => Promise<void>;
  refreshData: () => void;
  exportReport: () => void;
  toggleAutoRefresh: () => void;
}

/**
 * Gets milestone configuration for different flow types
 */
export const getFlowMilestones = (flow: CollectionFlow): ProgressMilestone[] => {
  const baseProgress = flow.progress;

  switch (flow.type) {
    case 'adaptive':
      return [
        {
          id: 'initialization',
          title: 'Flow Initialization',
          description: 'Collection flow setup and configuration',
          achieved: baseProgress >= 10,
          achievedAt: baseProgress >= 10 ? flow.startedAt : undefined,
          weight: 0.1,
          required: true
        },
        {
          id: 'form-generation',
          title: 'Form Generation',
          description: 'Adaptive forms generated for applications',
          achieved: baseProgress >= 25,
          weight: 0.15,
          required: true
        },
        {
          id: 'data-collection',
          title: 'Data Collection',
          description: 'Collecting application data via forms',
          achieved: baseProgress >= 75,
          weight: 0.5,
          required: true
        },
        {
          id: 'validation',
          title: 'Data Validation',
          description: 'Validating collected data quality',
          achieved: baseProgress >= 90,
          weight: 0.15,
          required: true
        },
        {
          id: 'completion',
          title: 'Flow Completion',
          description: 'Collection process completed',
          achieved: baseProgress >= 100,
          achievedAt: flow.completedAt,
          weight: 0.1,
          required: true
        }
      ];

    case 'bulk':
      return [
        {
          id: 'upload',
          title: 'File Upload',
          description: 'Bulk data file uploaded',
          achieved: baseProgress >= 20,
          weight: 0.2,
          required: true
        },
        {
          id: 'parsing',
          title: 'Data Parsing',
          description: 'File data parsed and structured',
          achieved: baseProgress >= 40,
          weight: 0.2,
          required: true
        },
        {
          id: 'processing',
          title: 'Data Processing',
          description: 'Processing and normalizing data',
          achieved: baseProgress >= 80,
          weight: 0.4,
          required: true
        },
        {
          id: 'completion',
          title: 'Processing Complete',
          description: 'Bulk processing completed',
          achieved: baseProgress >= 100,
          achievedAt: flow.completedAt,
          weight: 0.2,
          required: true
        }
      ];

    case 'integration':
      return [
        {
          id: 'source-analysis',
          title: 'Source Analysis',
          description: 'Analyzing data from multiple sources',
          achieved: baseProgress >= 25,
          weight: 0.25,
          required: true
        },
        {
          id: 'conflict-detection',
          title: 'Conflict Detection',
          description: 'Identifying data conflicts',
          achieved: baseProgress >= 50,
          weight: 0.25,
          required: true
        },
        {
          id: 'resolution',
          title: 'Conflict Resolution',
          description: 'Resolving data conflicts',
          achieved: baseProgress >= 85,
          weight: 0.35,
          required: true
        },
        {
          id: 'integration',
          title: 'Data Integration',
          description: 'Final data integration and validation',
          achieved: baseProgress >= 100,
          achievedAt: flow.completedAt,
          weight: 0.15,
          required: true
        }
      ];

    default:
      return [];
  }
};

/**
 * Generates mock flow data - in real implementation this would come from API
 */
export const generateMockFlows = (includeSpecificFlow?: string): CollectionFlow[] => {
  const baseFlows: CollectionFlow[] = [
    {
      id: 'flow-001',
      name: 'Enterprise Applications - Adaptive Collection',
      type: 'adaptive',
      status: 'running',
      progress: 68,
      startedAt: '2025-07-19T09:00:00Z',
      applicationCount: 45,
      completedApplications: 31,
      estimatedCompletion: '2025-07-19T16:30:00Z'
    },
    {
      id: 'flow-002',
      name: 'Legacy Systems - Bulk Upload',
      type: 'bulk',
      status: 'completed',
      progress: 100,
      startedAt: '2025-07-19T08:00:00Z',
      completedAt: '2025-07-19T10:45:00Z',
      applicationCount: 150,
      completedApplications: 150
    },
    {
      id: 'flow-003',
      name: 'Data Integration - Conflict Resolution',
      type: 'integration',
      status: 'paused',
      progress: 42,
      startedAt: '2025-07-19T11:00:00Z',
      applicationCount: 8,
      completedApplications: 3
    },
    {
      id: 'flow-004',
      name: 'Cloud Services - Adaptive Collection',
      type: 'adaptive',
      status: 'failed',
      progress: 25,
      startedAt: '2025-07-19T12:00:00Z',
      applicationCount: 20,
      completedApplications: 5
    }
  ];

  // If a specific flow ID is provided, ensure it exists in the mock data
  if (includeSpecificFlow && !baseFlows.find(f => f.id === includeSpecificFlow)) {
    baseFlows.unshift({
      id: includeSpecificFlow,
      name: 'Current Collection Flow',
      type: 'adaptive',
      status: 'running',
      progress: 35,
      startedAt: new Date().toISOString(),
      applicationCount: 10,
      completedApplications: 3,
      estimatedCompletion: new Date(Date.now() + 3600000).toISOString() // 1 hour from now
    });
  }

  return baseFlows;
};

/**
 * Generates mock metrics data
 */
export const generateMockMetrics = (flows: CollectionFlow[]): CollectionMetrics => {
  const totalApplications = flows.reduce((sum, flow) => sum + flow.applicationCount, 0);
  const completedApplications = flows.reduce((sum, flow) => sum + flow.completedApplications, 0);

  return {
    totalFlows: flows.length,
    activeFlows: flows.filter(f => f.status === 'running').length,
    completedFlows: flows.filter(f => f.status === 'completed').length,
    failedFlows: flows.filter(f => f.status === 'failed').length,
    totalApplications,
    completedApplications,
    averageCompletionTime: 180000, // 3 minutes in ms
    dataQualityScore: 92.5
  };
};

export const useProgressMonitoring = (
  options: UseProgressMonitoringOptions = {}
): ProgressMonitoringState & ProgressMonitoringActions & { autoRefresh: boolean } => {
  const { flowId, autoRefresh: initialAutoRefresh = true, refreshInterval = 30000 } = options; // 30 seconds instead of 3
  const { toast } = useToast();

  const [state, setState] = useState<ProgressMonitoringState>({
    flows: [],
    metrics: null,
    selectedFlow: null,
    isLoading: true,
    error: null
  });

  const [autoRefresh, setAutoRefresh] = useState(initialAutoRefresh);
  const [readiness, setReadiness] = useState<ReadinessSummary | null>(null);

  /**
   * Load initial data
   */
  const loadData = useCallback(async (): Promise<void> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      // If a specific flow ID is provided, fetch that flow's details
      if (flowId) {
        const flowDetails = await collectionFlowApi.getFlowDetails(flowId);

        // Transform API response to match our CollectionFlow interface
        const flow: CollectionFlow = {
          id: flowDetails.id,
          name: `Collection Flow - ${flowDetails.automation_tier}`,
          type: flowDetails.automation_tier === 'tier_1' ? 'adaptive' :
                flowDetails.automation_tier === 'tier_2' ? 'bulk' : 'integration',
          status: flowDetails.status === 'initialized' || flowDetails.status === 'running' ? 'running' :
                  flowDetails.status === 'completed' ? 'completed' :
                  flowDetails.status === 'paused' ? 'paused' : 'failed',
          progress: flowDetails.progress_percentage || 0,  // Use correct field
          startedAt: flowDetails.created_at,
          completedAt: flowDetails.completed_at,
          applicationCount: flowDetails.collection_metrics?.platforms_detected || 0,
          completedApplications: flowDetails.collection_metrics?.data_collected || 0
        };

        // Create metrics from single flow
        const metrics: CollectionMetrics = {
          totalFlows: 1,
          activeFlows: flow.status === 'running' ? 1 : 0,
          completedFlows: flow.status === 'completed' ? 1 : 0,
          failedFlows: flow.status === 'failed' ? 1 : 0,
          totalApplications: flow.applicationCount,
          completedApplications: flow.completedApplications,
          averageCompletionTime: 0,
          dataQualityScore: flowDetails.collection_metrics?.data_collected || 0
        };

        setState(prev => ({
          ...prev,
          flows: [flow],
          metrics,
          selectedFlow: flow.id,
          isLoading: false
        }));

        // Fetch readiness summary for selected flow
        try {
          const r = await collectionFlowApi.getFlowReadiness(flow.id);
          setReadiness({
            flow_id: r.flow_id,
            apps_ready_for_assessment: r.apps_ready_for_assessment,
            phase_scores: r.phase_scores,
            quality: r.quality
          });
        } catch {
          setReadiness(null);
        }
      } else {
        // Load all incomplete flows if no specific flow ID
        const incompleteFlows = await collectionFlowApi.getIncompleteFlows();

        // Transform flows (REAL data only; remove any mock generation)
        const flows: CollectionFlow[] = incompleteFlows.map(flowDetails => ({
          id: flowDetails.id,
          name: `Collection Flow - ${flowDetails.automation_tier}`,
          type: flowDetails.automation_tier === 'tier_1' ? 'adaptive' :
                flowDetails.automation_tier === 'tier_2' ? 'bulk' : 'integration',
          status: flowDetails.status === 'initialized' || flowDetails.status === 'running' ? 'running' :
                  flowDetails.status === 'completed' ? 'completed' :
                  flowDetails.status === 'paused' ? 'paused' : 'failed',
          progress: flowDetails.progress_percentage || 0,  // Use correct field
          startedAt: flowDetails.created_at,
          completedAt: flowDetails.completed_at,
          applicationCount: flowDetails.collection_metrics?.platforms_detected || 10,
          completedApplications: flowDetails.collection_metrics?.data_collected || 0
        }));

        // Calculate metrics from actual flows
        const metrics: CollectionMetrics = {
          totalFlows: flows.length,
          activeFlows: flows.filter(f => f.status === 'running').length,
          completedFlows: flows.filter(f => f.status === 'completed').length,
          failedFlows: flows.filter(f => f.status === 'failed').length,
          totalApplications: flows.reduce((sum, f) => sum + f.applicationCount, 0),
          completedApplications: flows.reduce((sum, f) => sum + f.completedApplications, 0),
          averageCompletionTime: 0,
          dataQualityScore: 0
        };

        setState(prev => ({
          ...prev,
          flows,
          metrics,
          selectedFlow: flows[0]?.id || null,
          isLoading: false
        }));

        // Fetch readiness for first flow if available
        try {
          if (flows[0]?.id) {
            const r = await collectionFlowApi.getFlowReadiness(flows[0].id);
            setReadiness({
              flow_id: r.flow_id,
              apps_ready_for_assessment: r.apps_ready_for_assessment,
              phase_scores: r.phase_scores,
              quality: r.quality
            });
          } else {
            setReadiness(null);
          }
        } catch {
          setReadiness(null);
        }
      }
    } catch (error: unknown) {
      console.error('Failed to load collection flow data:', error);

      // Create a more descriptive error message based on the error type
      let errorMessage: string;
      let processedError: Error;

      if (error && typeof error === 'object' && 'status' in error) {
        const statusCode = (error as any).status;
        if (statusCode === 404) {
          errorMessage = flowId
            ? `Collection flow '${flowId}' not found or has been deleted`
            : 'No collection flows found or access denied';
          processedError = new Error(errorMessage);
        } else if (statusCode === 403) {
          errorMessage = 'Access denied to collection flow data';
          processedError = new Error(errorMessage);
        } else if (statusCode >= 500) {
          errorMessage = 'Server error occurred while loading collection data';
          processedError = new Error(errorMessage);
        } else {
          errorMessage = `API error (${statusCode}): Unable to load collection data`;
          processedError = new Error(errorMessage);
        }
      } else if (error && typeof error === 'object' && 'message' in error) {
        const apiError = error as any;
        if (apiError.message?.includes('Context extraction failed')) {
          errorMessage = 'Context extraction failed - unable to process collection data';
          processedError = new Error(errorMessage);
        } else if (apiError.message?.includes('Network Error') || apiError.message?.includes('fetch')) {
          errorMessage = 'Network connection error - please check your internet connection';
          processedError = new Error(errorMessage);
        } else {
          errorMessage = apiError.message || 'Unknown error occurred while loading data';
          processedError = new Error(errorMessage);
        }
      } else if (typeof error === 'string') {
        if (error.includes('Context extraction failed')) {
          errorMessage = 'Context extraction failed - unable to process collection data';
          processedError = new Error(errorMessage);
        } else {
          errorMessage = error;
          processedError = new Error(errorMessage);
        }
      } else {
        errorMessage = 'Unable to load collection flow data';
        processedError = new Error(errorMessage);
      }

      setState(prev => ({ ...prev, error: processedError, isLoading: false }));

      // STOP INFINITE LOOPS: Handle 404/403 errors differently - don't retry for non-existent/unauthorized flows
      if (error && typeof error === 'object' && 'status' in error) {
        const statusCode = (error as any).status;
        if (statusCode === 404 || statusCode === 403) {
          const reason = statusCode === 404 ? 'Flow not found' : 'Access denied';
          console.warn(`⚠️ ${reason} - stopping auto-refresh to prevent infinite ${statusCode} retries`);
          setAutoRefresh(false); // Stop auto-refresh for 404/403 errors

          toast({
            title: statusCode === 404 ? 'Collection Flow Not Found' : 'Access Denied',
            description: errorMessage,
            variant: 'destructive'
          });
        } else {
          // Show descriptive error toast for other errors
          toast({
            title: 'Failed to load data',
            description: errorMessage,
            variant: 'destructive'
          });
        }
      }
    }
  }, [flowId, toast]);

  /**
   * Refresh data (for manual refresh)
   */
  const refreshData = (): void => {
    // Reset error state when manually refreshing
    setState(prev => ({ ...prev, error: null }));
    // Re-enable auto-refresh when user manually refreshes
    setAutoRefresh(true);
    loadData();
  };

  /**
   * Select a specific flow for detailed monitoring
   */
  const selectFlow = (flowId: string): void => {
    setState(prev => ({ ...prev, selectedFlow: flowId }));
  };

  /**
   * Handle flow actions (pause, resume, stop)
   */
  const handleFlowAction = async (flowId: string, action: 'pause' | 'resume' | 'stop'): Promise<void> => {
    try {
      if (action === 'resume') {
        // Use continue endpoint for resume
        await collectionFlowApi.continueFlow(flowId);
      } else if (action === 'stop') {
        // Use update endpoint to cancel the flow
        await collectionFlowApi.updateFlow(flowId, { action: 'cancel' });
      } else if (action === 'pause') {
        // Use update endpoint to pause
        await collectionFlowApi.updateFlow(flowId, { action: 'pause' });
      }

      // Reload data to get updated status
      await loadData();

      toast({
        title: `Flow ${action}${action.endsWith('e') ? 'd' : 'ped'}`,
        description: `Collection flow has been ${action}${action.endsWith('e') ? 'd' : 'ped'} successfully.`
      });
    } catch (error) {
      console.error(`Failed to ${action} flow:`, error);
      toast({
        title: 'Action Failed',
        description: `Failed to ${action} the collection flow.`,
        variant: 'destructive'
      });
    }
  };

  /**
   * Export progress report
   */
  const exportReport = (): void => {
    const reportData = {
      generatedAt: new Date().toISOString(),
      metrics: state.metrics,
      flows: state.flows.map(flow => ({
        ...flow,
        milestones: getFlowMilestones(flow)
      }))
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `collection-progress-report-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);

    toast({
      title: 'Report Exported',
      description: 'Progress report has been downloaded successfully.'
    });
  };

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = (): void => {
    setAutoRefresh(prev => !prev);
  };

  // Auto-refresh effect
  useEffect(() => {
    // STOP INFINITE LOOPS: Don't auto-refresh if there's an error or if disabled
    if (!autoRefresh || state.error) {
      console.log('🛑 Auto-refresh disabled due to error or manual setting');
      return;
    }

    const interval = setInterval(async () => {
      // Reload actual data from API with error handling
      try {
        await loadData();
      } catch (error) {
        console.error('❌ Auto-refresh failed, stopping future refreshes:', error);
        setAutoRefresh(false); // Stop auto-refresh on any error
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, flowId, state.error, loadData]);

  // Initial data load
  useEffect(() => {
    loadData();
  }, [flowId, loadData]);

  return {
    // State
    ...state,
    autoRefresh,
    readiness,

    // Actions
    selectFlow,
    handleFlowAction,
    refreshData,
    exportReport,
    toggleAutoRefresh
  };
};
