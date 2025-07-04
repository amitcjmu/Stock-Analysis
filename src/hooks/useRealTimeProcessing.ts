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
  status: 'initializing' | 'processing' | 'validating' | 'completed' | 'failed' | 'error' | 'paused' | 'waiting_for_user_approval' | 'running' | 'in_progress';
  progress_percentage: number;
  progress?: number; // Alternative progress field name
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
    polling_interval = 5000, // Reduced to 5 seconds for faster updates
    max_updates_history = 50,
    enabled = true
  } = options;

  const queryClient = useQueryClient();
  const [updates, setUpdates] = useState<ProcessingUpdate[]>([]);
  const [isProcessingActive, setIsProcessingActive] = useState(false);
  const [consecutiveErrors, setConsecutiveErrors] = useState(0);
  const [lastSuccessfulPoll, setLastSuccessfulPoll] = useState<number>(Date.now());
  const MAX_CONSECUTIVE_ERRORS = 3;
  const CIRCUIT_BREAKER_TIMEOUT = 60000; // 1 minute timeout

  // Circuit breaker logic
  const isCircuitBreakerOpen = consecutiveErrors >= MAX_CONSECUTIVE_ERRORS;
  const shouldRespectCircuitBreaker = isCircuitBreakerOpen && 
    (Date.now() - lastSuccessfulPoll) < CIRCUIT_BREAKER_TIMEOUT;

  const {
    data: processingStatus,
    isLoading: isLoadingStatus,
    error: statusError,
    refetch
  } = useQuery({
    queryKey: ['processing-status', flow_id, phase],
    queryFn: async () => {
      try {
        // Use the ACTUAL working endpoint first
        const url = `/api/v1/discovery/flow/status/${flow_id}`;
        console.log(`[useRealTimeProcessing] Fetching status from: ${url}`);
        const response = await apiCall(url);
        
        console.log(`[useRealTimeProcessing] Response for flow ${flow_id}:`, response);
        
        // Reset error count on successful response
        setConsecutiveErrors(0);
        setLastSuccessfulPoll(Date.now());
        
        // Transform the unified discovery response to match the expected format
        const transformedResponse = {
          flow_id: response.flow_id || flow_id,
          phase: response.current_phase || response.phase || 'data_import',
          status: response.status || 'initializing',
          progress_percentage: response.progress_percentage || response.progress || 0,
          progress: response.progress_percentage || response.progress || 0,
          records_processed: response.results?.total_records || response.records_processed || 0,
          records_total: response.results?.total_records || response.records_total || 0,
          records_failed: response.records_failed || 0,
          validation_status: response.validation_status || {
            format_valid: true,
            security_scan_passed: true,
            data_quality_score: 1.0,
            issues_found: []
          },
          agent_status: response.agent_status || {},
          recent_updates: response.recent_updates || [],
          estimated_completion: response.estimated_completion || null,
          last_update: response.updated_at || response.last_update || new Date().toISOString()
        };
        
        console.log(`[useRealTimeProcessing] Transformed response:`, transformedResponse);
        return transformedResponse;
      } catch (err: any) {
        // If the primary endpoint fails, try the processing-status endpoint
        if (err.status === 404 || err.response?.status === 404) {
          console.log(`[useRealTimeProcessing] Primary endpoint failed, trying processing-status endpoint`);
          
          try {
            const processingUrl = `/api/v1/discovery/flow/${flow_id}/processing-status${phase ? `?phase=${phase}` : ''}`;
            const response = await apiCall(processingUrl);
            console.log(`[useRealTimeProcessing] Processing status response:`, response);
            
            setConsecutiveErrors(0);
            setLastSuccessfulPoll(Date.now());
            return response;
          } catch (secondErr) {
            console.log(`[useRealTimeProcessing] Both endpoints failed for flow: ${flow_id}`);
            setConsecutiveErrors(prev => prev + 1);
            
            // Return a default "initializing" status instead of null to show proper UI
            return {
              flow_id: flow_id,
              phase: phase || 'data_import',
              status: 'initializing',
              progress_percentage: 0,
              progress: 0,
              records_processed: 0,
              records_total: 0,
              records_failed: 0,
              validation_status: {
                format_valid: true,
                security_scan_passed: true,
                data_quality_score: 1.0,
                issues_found: []
              },
              agent_status: {},
              recent_updates: [],
              estimated_completion: null,
              last_update: new Date().toISOString()
            };
          }
        }
        
        // Handle other errors with circuit breaker logic
        setConsecutiveErrors(prev => {
          const newCount = prev + 1;
          console.warn(`Processing status error ${newCount}/${MAX_CONSECUTIVE_ERRORS} for flow ${flow_id}:`, err.message);
          return newCount;
        });
        
        // Don't throw if circuit breaker should open
        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS - 1) {
          console.warn(`Circuit breaker opening for processing status on flow ${flow_id}`);
          return null;
        }
        
        throw err;
      }
    },
    enabled: enabled && !!flow_id && !shouldRespectCircuitBreaker,
    staleTime: 3000, // Reduced to 3 seconds for fresher data
    refetchInterval: (data) => {
      // Stop polling if flow is completed, failed, paused, or waiting for user approval
      if (!enabled || !flow_id || shouldRespectCircuitBreaker) {
        return false;
      }
      
      // Check if we should stop polling based on processing status
      if (data && typeof data === 'object') {
        const status = (data as any)?.status;
        const phase = (data as any)?.phase;
        const progress = (data as any)?.progress;
        const progressPercentage = (data as any)?.progress_percentage;
        const currentPhase = (data as any)?.current_phase;
        
        // Check various status fields for completion
        const finalResult = (data as any)?.final_result;
        const isCompleted = status === 'completed' || 
            status === 'failed' || 
            status === 'error' ||
            status === 'paused' ||
            status === 'waiting_for_user_approval' ||
            finalResult === 'discovery_failed' ||
            currentPhase === 'failed' ||
            (phase === 'attribute_mapping' && (progress >= 90 || progressPercentage >= 90)) ||
            (currentPhase === 'completed') ||
            progressPercentage === 100 ||
            (phase === 'data_import' && progressPercentage >= 100) ||
            (currentPhase === 'data_import' && (status === 'active' || status === 'initialized') && progressPercentage === 0); // Flow created but waiting for next phase
            
        if (isCompleted) {
          console.log(`[useRealTimeProcessing] Stopping polling for flow ${flow_id} - Status: ${status}, Phase: ${phase || currentPhase}, Progress: ${progress || progressPercentage}%`);
          return false;
        }
      }
      
      return polling_interval;
    },
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    retry: (failureCount, error: any) => {
      if (error?.status === 404 || 
          error?.response?.status === 404 || 
          consecutiveErrors >= MAX_CONSECUTIVE_ERRORS ||
          shouldRespectCircuitBreaker) {
        return false;
      }
      return failureCount < 2; // Allow a couple retries
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000), // Exponential backoff
  });

  // Update processing active status
  useEffect(() => {
    if (processingStatus) {
      const isActive = processingStatus.status === 'running' || 
                      processingStatus.status === 'processing' || 
                      processingStatus.status === 'validating' ||
                      processingStatus.status === 'in_progress';
      setIsProcessingActive(isActive);
    }
  }, [processingStatus]);

  // Accumulate processing updates
  useEffect(() => {
    if (processingStatus?.recent_updates) {
      setUpdates(prev => {
        const newUpdates = processingStatus.recent_updates.filter(
          (update: ProcessingUpdate) => !prev.some(existing => existing.id === update.id)
        );
        const combined = [...prev, ...newUpdates];
        return combined.slice(-max_updates_history);
      });
    }
  }, [processingStatus?.recent_updates, max_updates_history]);

  const clearUpdates = () => setUpdates([]);
  const resetErrorState = () => {
    setConsecutiveErrors(0);
    setLastSuccessfulPoll(Date.now());
  };

  return {
    processingStatus,
    updates,
    accumulatedUpdates: updates,
    isProcessingActive,
    isLoading: isLoadingStatus,
    error: statusError,
    consecutiveErrors,
    isPollingDisabled: consecutiveErrors >= MAX_CONSECUTIVE_ERRORS,
    lastSuccessfulPoll,
    refetch,
    clearUpdates,
    resetErrorState,
    // Utility functions
    getUpdatesByPhase: (targetPhase: string) => 
      updates.filter(update => update.phase === targetPhase),
    getUpdatesByAgent: (agent_name: string) => 
      updates.filter(update => update.agent_name === agent_name),
    getLatestUpdate: () => updates[updates.length - 1],
    hasRecentErrors: () => 
      updates.some(update => 
        update.update_type === 'error' && 
        Date.now() - new Date(update.timestamp).getTime() < 300000 // 5 minutes
      ),
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
  const [consecutiveErrors, setConsecutiveErrors] = useState(0);
  const [lastSuccessfulPoll, setLastSuccessfulPoll] = useState<number>(Date.now());
  const MAX_CONSECUTIVE_ERRORS = 3;
  const CIRCUIT_BREAKER_TIMEOUT = 60000; // 1 minute timeout

  // Stop polling if flow is completed or too many errors
  const isCompleted = processingStatus && (
    processingStatus.status === 'completed' || 
    processingStatus.status === 'failed' || 
    processingStatus.status === 'error'
  );
  
  const isCircuitBreakerOpen = consecutiveErrors >= MAX_CONSECUTIVE_ERRORS;
  const shouldRespectCircuitBreaker = isCircuitBreakerOpen && 
    (Date.now() - lastSuccessfulPoll) < CIRCUIT_BREAKER_TIMEOUT;
  
  const shouldPoll = !!flow_id && 
    !isCompleted && 
    !shouldRespectCircuitBreaker &&
    consecutiveErrors < MAX_CONSECUTIVE_ERRORS;

  const {
    data: insightsData,
    isLoading,
    error
  } = useQuery({
    queryKey: ['real-time-agent-insights', flow_id, page_context],
    queryFn: async () => {
      try {
        const url = `/api/v1/discovery/flow/${flow_id}/agent-insights${page_context ? `?page_context=${page_context}` : ''}`;
        const response = await apiCall(url);
        
        // Reset error count on successful response
        setConsecutiveErrors(0);
        setLastSuccessfulPoll(Date.now());
        
        return response;
      } catch (err: any) {
        // Handle 404 errors gracefully - these endpoints may not exist yet
        if (err.status === 404 || err.response?.status === 404) {
          console.log(`Agent insights endpoint not available for flow: ${flow_id}`);
          setConsecutiveErrors(prev => prev + 1);
          return { insights: [] };
        }
        
        // Handle other errors with circuit breaker logic
        setConsecutiveErrors(prev => {
          const newCount = prev + 1;
          console.warn(`Agent insights error ${newCount}/${MAX_CONSECUTIVE_ERRORS} for flow ${flow_id}:`, err.message);
          return newCount;
        });
        
        // Don't throw if circuit breaker should open
        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS - 1) {
          console.warn(`Circuit breaker opening for agent insights on flow ${flow_id}`);
          return { 
            insights: [],
            error: 'Polling temporarily disabled due to repeated errors'
          };
        }
        
        throw err;
      }
    },
    enabled: shouldPoll,
    staleTime: 10000, // Increased from 5000 to reduce requests
    refetchInterval: shouldPoll ? 15000 : false, // Increased from 5000 to reduce load
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    retry: (failureCount, error: any) => {
      if (error?.status === 404 || 
          error?.response?.status === 404 || 
          consecutiveErrors >= MAX_CONSECUTIVE_ERRORS ||
          shouldRespectCircuitBreaker) {
        return false;
      }
      return failureCount < 1; // Reduced retry attempts
    },
    retryDelay: (attemptIndex) => Math.min(2000 * 2 ** attemptIndex, 15000), // Exponential backoff
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
    consecutiveErrors,
    isPollingDisabled: consecutiveErrors >= MAX_CONSECUTIVE_ERRORS,
    clearInsights: () => setStreamingInsights([]),
    resetErrorState: () => setConsecutiveErrors(0),
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
  const [consecutiveErrors, setConsecutiveErrors] = useState(0);
  const [lastSuccessfulPoll, setLastSuccessfulPoll] = useState<number>(Date.now());
  const MAX_CONSECUTIVE_ERRORS = 3;
  const CIRCUIT_BREAKER_TIMEOUT = 60000; // 1 minute timeout
  
  // Stop polling if flow is completed, paused, or too many errors
  const isCompleted = processingStatus && (
    processingStatus.status === 'completed' || 
    processingStatus.status === 'failed' || 
    processingStatus.status === 'error' ||
    processingStatus.status === 'paused' ||
    processingStatus.status === 'waiting_for_user_approval' ||
    (processingStatus.phase === 'attribute_mapping' && processingStatus.progress >= 90)
  );
  
  const isCircuitBreakerOpen = consecutiveErrors >= MAX_CONSECUTIVE_ERRORS;
  const shouldRespectCircuitBreaker = isCircuitBreakerOpen && 
    (Date.now() - lastSuccessfulPoll) < CIRCUIT_BREAKER_TIMEOUT;
  
  const shouldPoll = !!flow_id && 
    !isCompleted && 
    !shouldRespectCircuitBreaker &&
    consecutiveErrors < MAX_CONSECUTIVE_ERRORS;

  const {
    data: validationData,
    isLoading,
    error
  } = useQuery({
    queryKey: ['real-time-validation', flow_id],
    queryFn: async () => {
      try {
        const response = await apiCall(`/api/v1/discovery/flow/${flow_id}/validation-status`);
        
        // Reset error count on successful response
        setConsecutiveErrors(0);
        setLastSuccessfulPoll(Date.now());
        
        return response;
      } catch (err: any) {
        // Handle 404 errors gracefully - these endpoints may not exist yet
        if (err.status === 404 || err.response?.status === 404) {
          console.log(`Validation status endpoint not available for flow: ${flow_id}`);
          setConsecutiveErrors(prev => prev + 1);
          return { 
            security_scan: { issues: [] }, 
            format_validation: { errors: [] }, 
            data_quality: { score: 1.0 },
            validation_progress: 0,
            agents_completed: 0,
            total_agents: 4
          };
        }
        
        // Handle other errors with circuit breaker logic
        setConsecutiveErrors(prev => {
          const newCount = prev + 1;
          console.warn(`Validation status error ${newCount}/${MAX_CONSECUTIVE_ERRORS} for flow ${flow_id}:`, err.message);
          return newCount;
        });
        
        // Don't throw if circuit breaker should open
        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS - 1) {
          console.warn(`Circuit breaker opening for validation status on flow ${flow_id}`);
          return { 
            security_scan: { issues: ['Polling temporarily disabled'] }, 
            format_validation: { errors: [] }, 
            data_quality: { score: 0.0 },
            validation_progress: 0,
            agents_completed: 0,
            total_agents: 4,
            error: 'Polling temporarily disabled due to repeated errors'
          };
        }
        
        throw err;
      }
    },
    enabled: shouldPoll,
    staleTime: 10000, // Increased from 3000 to reduce requests
    refetchInterval: shouldPoll ? 20000 : false, // Increased from 3000 to reduce load
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    retry: (failureCount, error: any) => {
      if (error?.status === 404 || 
          error?.response?.status === 404 || 
          consecutiveErrors >= MAX_CONSECUTIVE_ERRORS ||
          shouldRespectCircuitBreaker) {
        return false;
      }
      return failureCount < 1; // Reduced retry attempts
    },
    retryDelay: (attemptIndex) => Math.min(2000 * 2 ** attemptIndex, 20000), // Exponential backoff
  });

  const hasSecurityIssues = validationData?.security_scan?.issues?.length > 0;
  const hasFormatErrors = validationData?.format_validation?.errors?.length > 0;
  const hasDataQualityIssues = validationData?.data_quality?.score < 0.7;

  return {
    validationData,
    isLoading,
    error,
    consecutiveErrors,
    isPollingDisabled: consecutiveErrors >= MAX_CONSECUTIVE_ERRORS,
    hasSecurityIssues,
    hasFormatErrors,
    hasDataQualityIssues,
    overallValidationPassed: !hasSecurityIssues && !hasFormatErrors && !hasDataQualityIssues,
    getSecurityIssues: () => validationData?.security_scan?.issues || [],
    getFormatErrors: () => validationData?.format_validation?.errors || [],
    getQualityScore: () => validationData?.data_quality?.score || 0,
    resetErrorState: () => setConsecutiveErrors(0),
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