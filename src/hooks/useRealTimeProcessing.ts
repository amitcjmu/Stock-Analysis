import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect, useRef } from 'react';
import { apiCall } from '@/config/api';

// Types for real-time processing updates
export interface ProcessingUpdate {
  id: string;
  timestamp: string;
  phase: string;
  agent_name: string;
  update_type: 'progress' | 'validation' | 'insight' | 'error' | 'warning' | 'success';
  message: string;
  details?: {
    records_processed?: number;
    records_total?: number;
    records_failed?: number;
    validation_errors?: string[];
    security_issues?: string[];
    confidence_score?: number;
    supporting_data?: Record<string, any>;
  };
}

export interface ProcessingStatus {
  flow_id: string;
  phase: string;
  status: 'initializing' | 'processing' | 'validating' | 'completed' | 'failed' | 'error';
  progress_percentage: number;
  records_processed: number;
  records_total: number;
  records_failed: number;
  validation_status: {
    format_valid: boolean;
    security_scan_passed: boolean;
    data_quality_score: number;
    issues_found: string[];
  };
  agent_status: {
    [agent_name: string]: {
      status: 'idle' | 'processing' | 'completed' | 'error';
      confidence: number;
      insights_generated: number;
      clarifications_pending: number;
    };
  };
  recent_updates: ProcessingUpdate[];
  estimated_completion: string | null;
  last_update: string;
}

export interface RealTimeProcessingOptions {
  flow_id: string;
  phase?: string;
  polling_interval?: number;
  max_updates_history?: number;
  enabled?: boolean;
}

/**
 * Hook for real-time processing updates during discovery flows
 * Provides live feedback on validation, record processing, and agent insights
 */
export const useRealTimeProcessing = (options: RealTimeProcessingOptions) => {
  const {
    flow_id,
    phase,
    polling_interval = 2000, // 2 seconds for real-time feel
    max_updates_history = 50,
    enabled = true
  } = options;

  const queryClient = useQueryClient();
  const [isProcessingActive, setIsProcessingActive] = useState(false);
  const [accumulatedUpdates, setAccumulatedUpdates] = useState<ProcessingUpdate[]>([]);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Main processing status query
  const {
    data: processingStatus,
    isLoading,
    error,
    refetch
  } = useQuery<ProcessingStatus>({
    queryKey: ['real-time-processing', flow_id, phase],
    queryFn: async (): Promise<ProcessingStatus> => {
      const response = await apiCall(`/api/v1/discovery/flow/${flow_id}/processing-status`, {
        params: phase ? { phase } : undefined
      });
      return response;
    },
    enabled: enabled && !!flow_id,
    staleTime: 1000, // 1 second
    refetchOnWindowFocus: false,
  });

  // Check if processing is active and adjust polling
  useEffect(() => {
    if (processingStatus) {
      const isActive = processingStatus.status === 'processing' || 
                      processingStatus.status === 'validating' ||
                      processingStatus.status === 'initializing';
      setIsProcessingActive(isActive);
      
      // Add new updates to accumulated list
      if (processingStatus.recent_updates && processingStatus.recent_updates.length > 0) {
        setAccumulatedUpdates(prev => {
          const newUpdates = [...prev, ...processingStatus.recent_updates];
          // Keep only the most recent updates
          return newUpdates.slice(-max_updates_history);
        });
      }
    }
  }, [processingStatus, max_updates_history]);

  // Dynamic polling based on processing status
  useEffect(() => {
    if (!enabled || !flow_id) return;

    // Clear existing polling
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    // Check if processing is completely finished
    const isFinished = processingStatus && (
      processingStatus.status === 'completed' || 
      processingStatus.status === 'failed' || 
      processingStatus.status === 'error'
    );

    if (isFinished) {
      // Stop polling when processing is finished
      console.log(`🛑 Stopping polling for flow ${flow_id} - Status: ${processingStatus?.status}`);
      return;
    }

    if (isProcessingActive) {
      // Fast polling during active processing
      pollingRef.current = setInterval(() => {
        refetch();
      }, polling_interval);
    } else {
      // Slower polling when idle
      pollingRef.current = setInterval(() => {
        refetch();
      }, polling_interval * 3);
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [enabled, flow_id, isProcessingActive, polling_interval, refetch, processingStatus]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  return {
    processingStatus,
    accumulatedUpdates,
    isProcessingActive,
    isLoading,
    error,
    refetch,
    // Utility functions
    getLatestUpdate: () => accumulatedUpdates[accumulatedUpdates.length - 1],
    getUpdatesByType: (type: ProcessingUpdate['update_type']) => 
      accumulatedUpdates.filter(update => update.update_type === type),
    clearUpdates: () => setAccumulatedUpdates([]),
  };
};

/**
 * Hook for triggering manual processing steps
 */
export const useProcessingActions = () => {
  const queryClient = useQueryClient();

  const triggerValidation = useMutation({
    mutationFn: async (data: { flow_id: string; validation_type: 'security' | 'format' | 'quality' | 'all' }) => {
      return await apiCall(`/api/v1/discovery/flow/${data.flow_id}/validate`, {
        method: 'POST',
        body: JSON.stringify({ validation_type: data.validation_type }),
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['real-time-processing', variables.flow_id] });
    },
  });

  const retryProcessing = useMutation({
    mutationFn: async (data: { flow_id: string; phase?: string; retry_failed_only?: boolean }) => {
      return await apiCall(`/api/v1/discovery/flow/${data.flow_id}/retry`, {
        method: 'POST',
        body: JSON.stringify({ 
          phase: data.phase,
          retry_failed_only: data.retry_failed_only ?? true 
        }),
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['real-time-processing', variables.flow_id] });
    },
  });

  const pauseProcessing = useMutation({
    mutationFn: async (data: { flow_id: string; reason?: string }) => {
      return await apiCall(`/api/v1/discovery/flow/${data.flow_id}/pause`, {
        method: 'POST',
        body: JSON.stringify({ reason: data.reason ?? 'User requested' }),
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['real-time-processing', variables.flow_id] });
    },
  });

  const resumeProcessing = useMutation({
    mutationFn: async (data: { flow_id: string }) => {
      return await apiCall(`/api/v1/discovery/flow/${data.flow_id}/resume`, {
        method: 'POST',
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['real-time-processing', variables.flow_id] });
    },
  });

  return {
    triggerValidation,
    retryProcessing,
    pauseProcessing,
    resumeProcessing,
  };
};

/**
 * Hook for enhanced agent insights with real-time streaming
 */
export const useRealTimeAgentInsights = (flow_id: string, page_context?: string, processingStatus?: ProcessingStatus) => {
  const [streamingInsights, setStreamingInsights] = useState<any[]>([]);

  // Stop polling if flow is completed
  const isCompleted = processingStatus && (
    processingStatus.status === 'completed' || 
    processingStatus.status === 'failed' || 
    processingStatus.status === 'error'
  );

  const {
    data: insightsData,
    isLoading,
    error
  } = useQuery({
    queryKey: ['real-time-agent-insights', flow_id, page_context],
    queryFn: async () => {
      const response = await apiCall(`/api/v1/discovery/flow/${flow_id}/agent-insights`, {
        params: page_context ? { page_context } : undefined
      });
      return response;
    },
    enabled: !!flow_id && !isCompleted,
    staleTime: 5000, // 5 seconds
    refetchInterval: isCompleted ? false : 5000, // Stop polling when completed
    refetchOnWindowFocus: false,
  });

  // Update streaming insights when new data arrives
  useEffect(() => {
    if (insightsData?.insights) {
      setStreamingInsights(prev => {
        const newInsights = insightsData.insights.filter((insight: any) => 
          !prev.some(existing => existing.id === insight.id)
        );
        return [...prev, ...newInsights];
      });
    }
  }, [insightsData]);

  return {
    insights: streamingInsights,
    latestInsights: insightsData?.insights || [],
    isLoading,
    error,
    clearInsights: () => setStreamingInsights([]),
    getInsightsByAgent: (agent_name: string) => 
      streamingInsights.filter(insight => insight.agent_name === agent_name),
    getInsightsByType: (insight_type: string) => 
      streamingInsights.filter(insight => insight.insight_type === insight_type),
  };
};

/**
 * Hook for real-time validation feedback
 */
export const useRealTimeValidation = (flow_id: string, processingStatus?: ProcessingStatus) => {
  // Stop polling if flow is completed
  const isCompleted = processingStatus && (
    processingStatus.status === 'completed' || 
    processingStatus.status === 'failed' || 
    processingStatus.status === 'error'
  );

  const {
    data: validationData,
    isLoading,
    error
  } = useQuery({
    queryKey: ['real-time-validation', flow_id],
    queryFn: async () => {
      const response = await apiCall(`/api/v1/discovery/flow/${flow_id}/validation-status`);
      return response;
    },
    enabled: !!flow_id && !isCompleted,
    staleTime: 3000, // 3 seconds
    refetchInterval: isCompleted ? false : 3000, // Stop polling when completed
    refetchOnWindowFocus: false,
  });

  const hasSecurityIssues = validationData?.security_scan?.issues?.length > 0;
  const hasFormatErrors = validationData?.format_validation?.errors?.length > 0;
  const hasDataQualityIssues = validationData?.data_quality?.score < 0.7;

  return {
    validationData,
    isLoading,
    error,
    hasSecurityIssues,
    hasFormatErrors,
    hasDataQualityIssues,
    overallValidationPassed: !hasSecurityIssues && !hasFormatErrors && !hasDataQualityIssues,
    getSecurityIssues: () => validationData?.security_scan?.issues || [],
    getFormatErrors: () => validationData?.format_validation?.errors || [],
    getQualityScore: () => validationData?.data_quality?.score || 0,
  };
};

/**
 * Combined hook for comprehensive real-time monitoring
 */
export const useComprehensiveRealTimeMonitoring = (flow_id: string, page_context?: string) => {
  const processing = useRealTimeProcessing({ flow_id, enabled: !!flow_id });
  const insights = useRealTimeAgentInsights(flow_id, page_context, processing.processingStatus);
  const validation = useRealTimeValidation(flow_id, processing.processingStatus);
  const actions = useProcessingActions();

  return {
    processing,
    insights,
    validation,
    actions,
    // Convenience properties
    isAnyProcessingActive: processing.isProcessingActive,
    hasAnyIssues: validation.hasSecurityIssues || validation.hasFormatErrors || validation.hasDataQualityIssues,
    overallStatus: processing.processingStatus?.status || 'unknown',
    // Utility functions
    refreshAll: () => {
      processing.refetch();
      insights.clearInsights();
      // Validation will auto-refresh via its own polling
    },
  };
}; 