/**
 * Enhanced Flow Management Hook
 * Integrates with the hybrid CrewAI + PostgreSQL persistence architecture.
 * Provides comprehensive flow validation, recovery, and cleanup capabilities.
 */

import { useState } from 'react'
import { useCallback } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/config/api';

// ========================================
// TYPES
// ========================================

interface FlowStateValidationResponse {
  status: string;
  flow_id: string;
  overall_valid: boolean;
  crewai_validation: Record<string, unknown>;
  postgresql_validation: Record<string, unknown>;
  phase_executors?: Record<string, unknown>;
  validation_timestamp: string;
  recommendations?: string[];
}

interface FlowRecoveryResponse {
  status: string;
  flow_id: string;
  recovery_successful: boolean;
  recovered_state?: Record<string, unknown>;
  recovery_strategy_used: string;
  recovery_timestamp: string;
  next_steps?: string[];
}

interface FlowCleanupResponse {
  status: string;
  flows_cleaned: number;
  flow_ids_cleaned: string[];
  dry_run: boolean;
  cleanup_timestamp: string;
  space_recovered?: string;
}

interface FlowPersistenceStatusResponse {
  flow_id: string;
  crewai_persistence: Record<string, unknown>;
  postgresql_persistence: Record<string, unknown>;
  bridge_status: Record<string, unknown>;
  sync_enabled: boolean;
  last_sync_timestamp?: string;
}

interface BulkValidationResponse {
  status: string;
  total_flows: number;
  valid_flows: number;
  invalid_flows: number;
  results: Array<{
    flow_id: string;
    status: string;
    valid?: boolean;
    summary?: Record<string, unknown>;
    error?: string;
  }>;
  validation_timestamp: string;
}

// ========================================
// API FUNCTIONS
// ========================================

const validateFlowState = async (flowId: string, comprehensive: boolean = true): Promise<FlowStateValidationResponse> => {
  const response = await apiClient.post(`/discovery/enhanced/flows/${flowId}/validate`, {
    flow_id: flowId,
    comprehensive
  });
  return response.data;
};

const recoverFlowState = async (
  flowId: string,
  recoveryStrategy: string = 'postgresql',
  forceRecovery: boolean = false
): Promise<FlowRecoveryResponse> => {
  const response = await apiClient.post(`/discovery/enhanced/flows/${flowId}/recover`, {
    flow_id: flowId,
    recovery_strategy: recoveryStrategy,
    force_recovery: forceRecovery
  });
  return response.data;
};

const cleanupExpiredFlows = async (
  expirationHours: number = 72,
  dryRun: boolean = false,
  specificFlowIds?: string[]
): Promise<FlowCleanupResponse> => {
  const response = await apiClient.post('/discovery/enhanced/flows/cleanup', {
    expiration_hours: expirationHours,
    dry_run: dryRun,
    specific_flow_ids: specificFlowIds
  });
  return response.data;
};

const getFlowPersistenceStatus = async (flowId: string): Promise<FlowPersistenceStatusResponse> => {
  const response = await apiClient.get(`/discovery/enhanced/flows/${flowId}/persistence-status`);
  return response.data;
};

const bulkValidateFlows = async (flowIds: string[]): Promise<BulkValidationResponse> => {
  const response = await apiClient.post('/discovery/enhanced/flows/bulk-validate', flowIds);
  return response.data;
};

const checkPersistenceHealth = async (): Promise<Record<string, unknown>> => {
  const response = await apiClient.get('/discovery/enhanced/health/persistence');
  return response.data;
};

// ========================================
// MAIN HOOK
// ========================================

export const useEnhancedFlowManagement = (): any => {
  const [isValidating, setIsValidating] = useState(false);
  const [isRecovering, setIsRecovering] = useState(false);
  const [isCleaning, setIsCleaning] = useState(false);

  // Flow State Validation
  const validateFlow = useMutation({
    mutationFn: ({ flowId, comprehensive = true }: { flowId: string; comprehensive?: boolean }) =>
      validateFlowState(flowId, comprehensive),
    onMutate: () => setIsValidating(true),
    onSettled: () => setIsValidating(false),
  });

  // Flow State Recovery
  const recoverFlow = useMutation({
    mutationFn: ({
      flowId,
      recoveryStrategy = 'postgresql',
      forceRecovery = false
    }: {
      flowId: string;
      recoveryStrategy?: string;
      forceRecovery?: boolean;
    }) => recoverFlowState(flowId, recoveryStrategy, forceRecovery),
    onMutate: () => setIsRecovering(true),
    onSettled: () => setIsRecovering(false),
  });

  // Flow Cleanup
  const cleanupFlows = useMutation({
    mutationFn: ({
      expirationHours = 72,
      dryRun = false,
      specificSessionIds
    }: {
      expirationHours?: number;
      dryRun?: boolean;
      specificFlowIds?: string[];
    }) => cleanupExpiredFlows(expirationHours, dryRun, specificSessionIds),
    onMutate: () => setIsCleaning(true),
    onSettled: () => setIsCleaning(false),
  });

  // Bulk Validation
  const bulkValidate = useMutation({
    mutationFn: (flowIds: string[]) => bulkValidateFlows(flowIds),
  });

  // Persistence Status Query
  const usePersistenceStatus = (flowId: string, enabled: boolean = true): any => {
    return useQuery({
      queryKey: ['flow-persistence-status', flowId],
      queryFn: () => getFlowPersistenceStatus(flowId),
      enabled: enabled && !!flowId,
      refetchInterval: false, // DISABLED: No automatic polling
    });
  };

  // Persistence Health Query
  const usePersistenceHealth = (): any => {
    return useQuery({
      queryKey: ['persistence-health'],
      queryFn: checkPersistenceHealth,
      refetchInterval: false, // DISABLED: No automatic polling
    });
  };

  // Convenience Methods
  const validateFlowWithRecommendations = useCallback(async (flowId: string) => {
    try {
      const result = await validateFlow.mutateAsync({ flowId, comprehensive: true });

      return {
        ...result,
        hasIssues: !result.overall_valid,
        criticalIssues: result.postgresql_validation?.errors?.length > 0,
        warningCount: result.postgresql_validation?.warnings?.length || 0,
        actionableRecommendations: result.recommendations?.filter(rec =>
          rec.includes('Address') || rec.includes('Review') || rec.includes('Consider')
        ) || []
      };
    } catch (error) {
      console.error('Flow validation failed:', error);
      throw error;
    }
  }, [validateFlow]);

  const performFlowRecovery = useCallback(async (flowId: string, strategy: 'postgresql' | 'hybrid' = 'postgresql') => {
    try {
      const result = await recoverFlow.mutateAsync({
        flowId,
        recoveryStrategy: strategy,
        forceRecovery: false
      });

      return {
        ...result,
        canResume: result.recovery_successful && result.recovered_state,
        requiresValidation: result.recovery_successful,
        nextAction: result.recovery_successful ? 'validate_and_resume' : 'manual_investigation'
      };
    } catch (error) {
      console.error('Flow recovery failed:', error);
      throw error;
    }
  }, [recoverFlow]);

  const performFlowCleanup = useCallback(async (
    options: {
      expirationHours?: number;
      dryRun?: boolean;
      specificSessions?: string[];
    } = {}
  ) => {
    try {
      const result = await cleanupFlows.mutateAsync({
        expirationHours: options.expirationHours || 72,
        dryRun: options.dryRun || false,
        specificFlowIds: options.specificSessions
      });

      return {
        ...result,
        cleanupEffective: result.flows_cleaned > 0,
        spaceRecovered: result.space_recovered,
        requiresValidation: !options.dryRun && result.flows_cleaned > 0
      };
    } catch (error) {
      console.error('Flow cleanup failed:', error);
      throw error;
    }
  }, [cleanupFlows]);

  const performBulkValidation = useCallback(async (flowIds: string[]) => {
    try {
      const result = await bulkValidate.mutateAsync(flowIds);

      const healthyFlows = result.results.filter(r => r.valid);
      const problematicFlows = result.results.filter(r => !r.valid || r.error);

      return {
        ...result,
        healthyFlows,
        problematicFlows,
        healthPercentage: (result.valid_flows / result.total_flows) * 100,
        needsAttention: problematicFlows.length > 0,
        summary: {
          total: result.total_flows,
          healthy: result.valid_flows,
          problematic: result.invalid_flows,
          healthScore: Math.round((result.valid_flows / result.total_flows) * 100)
        }
      };
    } catch (error) {
      console.error('Bulk validation failed:', error);
      throw error;
    }
  }, [bulkValidate]);

  return {
    // Mutation hooks
    validateFlow,
    recoverFlow,
    cleanupFlows,
    bulkValidate,

    // Query hooks (functions that return useQuery)
    usePersistenceStatus,
    usePersistenceHealth,

    // Loading states
    isValidating,
    isRecovering,
    isCleaning,
    isBulkValidating: bulkValidate.isPending,

    // Enhanced convenience methods
    validateFlowWithRecommendations,
    performFlowRecovery,
    performFlowCleanup,
    performBulkValidation,

    // Status checks
    isAnyOperationPending: isValidating || isRecovering || isCleaning || bulkValidate.isPending,
  };
};

// ========================================
// UTILITY HOOKS
// ========================================

/**
 * Hook for monitoring multiple flows' health
 */
export const useFlowHealthMonitor = (flowIds: string[], enabled: boolean = true): any => {
  const { performBulkValidation } = useEnhancedFlowManagement();

  return useQuery({
    queryKey: ['flow-health-monitor', flowIds],
    queryFn: () => performBulkValidation(flowIds),
    enabled: enabled && flowIds.length > 0,
    refetchInterval: false, // DISABLED: No automatic polling
    retry: 2,
  });
};

/**
 * Hook for cleanup recommendations only (NO automatic cleanup)
 * @deprecated Use useFlowCleanupRecommendations from useFlowDeletion instead
 */
export const useAutomaticCleanup = (enabled: boolean = false): any => {
  console.warn('⚠️ useAutomaticCleanup is deprecated. Automatic cleanup is disabled for user safety. Use useFlowCleanupRecommendations instead.');

  // Always return disabled state - no automatic cleanup allowed
  return {
    data: null,
    isLoading: false,
    isError: false,
    error: null,
    refetch: () => Promise.resolve(),
  };
};
