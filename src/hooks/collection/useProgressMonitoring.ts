/**
 * Custom hook for monitoring collection progress
 * 
 * Extracted from Progress.tsx to provide reusable progress monitoring logic
 * for collection workflows and flow management.
 */

import { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/use-toast';
import type { ProgressMilestone } from '@/components/collection/types';

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
  const { flowId, autoRefresh: initialAutoRefresh = true, refreshInterval = 3000 } = options;
  const { toast } = useToast();
  
  const [state, setState] = useState<ProgressMonitoringState>({
    flows: [],
    metrics: null,
    selectedFlow: null,
    isLoading: true,
    error: null
  });
  
  const [autoRefresh, setAutoRefresh] = useState(initialAutoRefresh);

  /**
   * Load initial data
   */
  const loadData = (): void => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const mockFlows = generateMockFlows(flowId || undefined);
      const mockMetrics = generateMockMetrics(mockFlows);
      
      setState(prev => ({
        ...prev,
        flows: mockFlows,
        metrics: mockMetrics,
        selectedFlow: flowId || mockFlows[0]?.id || null,
        isLoading: false
      }));
    } catch (error: any) {
      setState(prev => ({ ...prev, error, isLoading: false }));
    }
  };

  /**
   * Refresh data (for manual refresh)
   */
  const refreshData = (): void => {
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
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setState(prev => ({
        ...prev,
        flows: prev.flows.map(flow => {
          if (flow.id === flowId) {
            switch (action) {
              case 'pause':
                return { ...flow, status: 'paused' as const };
              case 'resume':
                return { ...flow, status: 'running' as const };
              case 'stop':
                return { ...flow, status: 'failed' as const };
              default:
                return flow;
            }
          }
          return flow;
        })
      }));

      toast({
        title: `Flow ${action}${action.endsWith('e') ? 'd' : 'ped'}`,
        description: `Collection flow has been ${action}${action.endsWith('e') ? 'd' : 'ped'} successfully.`
      });
    } catch (error) {
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
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simulate progress updates for running flows
      setState(prev => ({
        ...prev,
        flows: prev.flows.map(flow => {
          if (flow.status === 'running' && flow.progress < 100) {
            const newProgress = Math.min(flow.progress + Math.random() * 5, 100);
            const newCompleted = Math.floor((newProgress / 100) * flow.applicationCount);
            
            return {
              ...flow,
              progress: newProgress,
              completedApplications: newCompleted,
              ...(newProgress >= 100 && {
                status: 'completed' as const,
                completedAt: new Date().toISOString()
              })
            };
          }
          return flow;
        })
      }));
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // Initial data load
  useEffect(() => {
    loadData();
  }, [flowId]);

  return {
    // State
    ...state,
    autoRefresh,
    
    // Actions
    selectFlow,
    handleFlowAction,
    refreshData,
    exportReport,
    toggleAutoRefresh
  };
};