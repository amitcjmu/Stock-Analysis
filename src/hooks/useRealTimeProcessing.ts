import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect, useRef, useCallback } from 'react';
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
  const [accumulatedUpdates, setAccumulatedUpdates] = useState<ProcessingUpdate[]>([]);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const consecutiveErrors = useRef<number>(0);
  const lastSuccessfulFetch = useRef<number>(0);
  const maxConsecutiveErrors = 3;

  // Query for processing status with enhanced error handling
  const {
    data: processingStatus,
    isLoading,
    error,
    refetch
  } = useQuery<ProcessingStatus>({
    queryKey: ['real-time-processing', flow_id, phase],
    queryFn: async (): Promise<ProcessingStatus> => {
      if (!flow_id) throw new Error('Flow ID is required');
      
      try {
        const response = await apiCall(`/api/v1/discovery/flow/${flow_id}/processing-status`, {
          params: phase ? { phase } : undefined
        });
        
        // Reset error count on successful fetch
        consecutiveErrors.current = 0;
        lastSuccessfulFetch.current = Date.now();
        
        return response;
      } catch (err: any) {
        consecutiveErrors.current += 1;
        console.error(`❌ Processing status fetch error (attempt ${consecutiveErrors.current}):`, err);
        
        // Stop polling after max consecutive errors
        if (consecutiveErrors.current >= maxConsecutiveErrors) {
          console.warn(`🚫 Stopping polling for flow ${flow_id} after ${maxConsecutiveErrors} consecutive failures`);
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
        }
        
        // Handle 404 errors gracefully - flow may not exist
        if (err.status === 404 || err.response?.status === 404) {
          console.warn(`🚫 Flow ${flow_id} not found, stopping polling`);
          throw new Error(`Flow ${flow_id} not found`);
        }
        
        throw err;
      }
    },
    enabled: enabled && !!flow_id && consecutiveErrors.current < maxConsecutiveErrors,
    staleTime: 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    refetchOnReconnect: false,
    retry: (failureCount, error) => {
      // Don't retry if we've hit max consecutive errors
      if (consecutiveErrors.current >= maxConsecutiveErrors) {
        console.warn(`🚫 Max consecutive errors reached, stopping retries for flow ${flow_id}`);
        return false;
      }
      
      // Don't retry 404 errors (flow doesn't exist)
      if (error && ('status' in error && error.status === 404)) {
        console.warn(`🚫 Flow ${flow_id} not found, stopping retries`);
        return false;
      }
      
      // Don't retry if error message indicates flow not found
      if (error && error.message && error.message.includes('not found')) {
        console.warn(`🚫 Flow ${flow_id} not found (from message), stopping retries`);
        return false;
      }
      
      return failureCount < 2;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });

  // Check if processing is active
  const isProcessingActive = processingStatus && (
    processingStatus.status === 'processing' || 
    processingStatus.status === 'initializing' ||
    processingStatus.status === 'validating'
  );

  // Accumulate updates from processing status
  useEffect(() => {
    if (processingStatus?.recent_updates) {
      setAccumulatedUpdates(prev => {
        const newUpdates = processingStatus.recent_updates.filter(update => 
          !prev.some(existing => existing.id === update.id)
        );
        const combined = [...prev, ...newUpdates];
        return combined.slice(-max_updates_history);
      });
    }
  }, [processingStatus, max_updates_history]);

  // Enhanced polling control with error handling
  useEffect(() => {
    if (!enabled || !flow_id || consecutiveErrors.current >= maxConsecutiveErrors) {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      return;
    }

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

    // Implement exponential backoff after errors
    let intervalDelay = polling_interval;
    if (consecutiveErrors.current > 0) {
      intervalDelay = Math.min(polling_interval * Math.pow(2, consecutiveErrors.current), 30000); // Max 30 seconds
      console.log(`⚠️ Using exponential backoff: ${intervalDelay}ms delay after ${consecutiveErrors.current} errors`);
    }

    if (isProcessingActive) {
      // Fast polling during active processing
      pollingRef.current = setInterval(() => {
        if (consecutiveErrors.current < maxConsecutiveErrors) {
          refetch();
        }
      }, intervalDelay);
    } else {
      // Slower polling when idle
      pollingRef.current = setInterval(() => {
        if (consecutiveErrors.current < maxConsecutiveErrors) {
          refetch();
        }
      }, intervalDelay * 3);
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [enabled, flow_id, isProcessingActive, polling_interval, refetch, processingStatus, consecutiveErrors.current]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  // Recovery function to reset error state
  const resetErrorState = useCallback(() => {
    consecutiveErrors.current = 0;
    lastSuccessfulFetch.current = Date.now();
    console.log(`🔄 Reset error state for flow ${flow_id}`);
  }, [flow_id]);

  return {
    processingStatus,
    accumulatedUpdates,
    isProcessingActive,
    isLoading,
    error,
    refetch,
    consecutiveErrors: consecutiveErrors.current,
    isPollingDisabled: consecutiveErrors.current >= maxConsecutiveErrors,
    resetErrorState,
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
      try {
        const response = await apiCall(`/api/v1/discovery/flow/${flow_id}/agent-insights`, {
          params: page_context ? { page_context } : undefined
        });
        return response;
      } catch (err: any) {
        // Handle 404 errors gracefully - these endpoints may not exist yet
        if (err.status === 404 || err.response?.status === 404) {
          console.log('Agent insights endpoint not available yet');
          return { insights: [] };
        }
        throw err;
      }
    },
    enabled: !!flow_id && !isCompleted,
    staleTime: 5000, // 5 seconds
    refetchInterval: isCompleted ? false : 5000, // Stop polling when completed
    refetchOnWindowFocus: false,
    retry: (failureCount, error: any) => {
      // Don't retry on 404 errors
      if (error?.status === 404 || error?.response?.status === 404) {
        return false;
      }
      return failureCount < 3;
    },
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
      try {
        const response = await apiCall(`/api/v1/discovery/flow/${flow_id}/validation-status`);
        return response;
      } catch (err: any) {
        // Handle 404 errors gracefully - these endpoints may not exist yet
        if (err.status === 404 || err.response?.status === 404) {
          console.log('Validation status endpoint not available yet');
          return { security_scan: { issues: [] }, format_validation: { errors: [] }, data_quality: { score: 1.0 } };
        }
        throw err;
      }
    },
    enabled: !!flow_id && !isCompleted,
    staleTime: 3000, // 3 seconds
    refetchInterval: isCompleted ? false : 3000, // Stop polling when completed
    refetchOnWindowFocus: false,
    retry: (failureCount, error: any) => {
      // Don't retry on 404 errors
      if (error?.status === 404 || error?.response?.status === 404) {
        return false;
      }
      return failureCount < 3;
    },
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