/**
 * Enhanced Flow Management Hook
 * Integrates with the hybrid CrewAI + PostgreSQL persistence architecture.
 * Provides comprehensive flow validation, recovery, and cleanup capabilities.
 */

import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/config/api';

// ========================================
// TYPES
// ========================================

interface FlowStateValidationResponse {
  status: string;
  session_id: string;
  overall_valid: boolean;
  crewai_validation: Record<string, any>;
  postgresql_validation: Record<string, any>;
  phase_executors?: Record<string, any>;
  validation_timestamp: string;
  recommendations?: string[];
}

interface FlowRecoveryResponse {
  status: string;
  session_id: string;
  recovery_successful: boolean;
  recovered_state?: Record<string, any>;
  recovery_strategy_used: string;
  recovery_timestamp: string;
  next_steps?: string[];
}

interface FlowCleanupResponse {
  status: string;
  flows_cleaned: number;
  session_ids_cleaned: string[];
  dry_run: boolean;
  cleanup_timestamp: string;
  space_recovered?: string;
}

interface FlowPersistenceStatusResponse {
  session_id: string;
  crewai_persistence: Record<string, any>;
  postgresql_persistence: Record<string, any>;
  bridge_status: Record<string, any>;
  sync_enabled: boolean;
  last_sync_timestamp?: string;
}

interface BulkValidationResponse {
  status: string;
  total_flows: number;
  valid_flows: number;
  invalid_flows: number;
  results: Array<{
    session_id: string;
    status: string;
    valid?: boolean;
    summary?: Record<string, any>;
    error?: string;
  }>;
  validation_timestamp: string;
}

// ========================================
// API FUNCTIONS
// ========================================

const validateFlowState = async (sessionId: string, comprehensive: boolean = true): Promise<FlowStateValidationResponse> => {
  const response = await apiClient.post(`/discovery/enhanced/flows/${sessionId}/validate`, {
    session_id: sessionId,
    comprehensive
  });
  return response.data;
};

const recoverFlowState = async (
  sessionId: string, 
  recoveryStrategy: string = 'postgresql',
  forceRecovery: boolean = false
): Promise<FlowRecoveryResponse> => {
  const response = await apiClient.post(`/discovery/enhanced/flows/${sessionId}/recover`, {
    session_id: sessionId,
    recovery_strategy: recoveryStrategy,
    force_recovery: forceRecovery
  });
  return response.data;
};

const cleanupExpiredFlows = async (
  expirationHours: number = 72,
  dryRun: boolean = false,
  specificSessionIds?: string[]
): Promise<FlowCleanupResponse> => {
  const response = await apiClient.post('/discovery/enhanced/flows/cleanup', {
    expiration_hours: expirationHours,
    dry_run: dryRun,
    specific_session_ids: specificSessionIds
  });
  return response.data;
};

const getFlowPersistenceStatus = async (sessionId: string): Promise<FlowPersistenceStatusResponse> => {
  const response = await apiClient.get(`/discovery/enhanced/flows/${sessionId}/persistence-status`);
  return response.data;
};

const bulkValidateFlows = async (sessionIds: string[]): Promise<BulkValidationResponse> => {
  const response = await apiClient.post('/discovery/enhanced/flows/bulk-validate', sessionIds);
  return response.data;
};

const checkPersistenceHealth = async (): Promise<Record<string, any>> => {
  const response = await apiClient.get('/discovery/enhanced/health/persistence');
  return response.data;
};

// ========================================
// MAIN HOOK
// ========================================

export const useEnhancedFlowManagement = () => {
  const [isValidating, setIsValidating] = useState(false);
  const [isRecovering, setIsRecovering] = useState(false);
  const [isCleaning, setIsCleaning] = useState(false);

  // Flow State Validation
  const validateFlow = useMutation({
    mutationFn: ({ sessionId, comprehensive = true }: { sessionId: string; comprehensive?: boolean }) =>
      validateFlowState(sessionId, comprehensive),
    onMutate: () => setIsValidating(true),
    onSettled: () => setIsValidating(false),
  });

  // Flow State Recovery
  const recoverFlow = useMutation({
    mutationFn: ({ 
      sessionId, 
      recoveryStrategy = 'postgresql', 
      forceRecovery = false 
    }: { 
      sessionId: string; 
      recoveryStrategy?: string; 
      forceRecovery?: boolean; 
    }) => recoverFlowState(sessionId, recoveryStrategy, forceRecovery),
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
      specificSessionIds?: string[]; 
    }) => cleanupExpiredFlows(expirationHours, dryRun, specificSessionIds),
    onMutate: () => setIsCleaning(true),
    onSettled: () => setIsCleaning(false),
  });

  // Bulk Validation
  const bulkValidate = useMutation({
    mutationFn: (sessionIds: string[]) => bulkValidateFlows(sessionIds),
  });

  // Persistence Status Query
  const usePersistenceStatus = (sessionId: string, enabled: boolean = true) => {
    return useQuery({
      queryKey: ['flow-persistence-status', sessionId],
      queryFn: () => getFlowPersistenceStatus(sessionId),
      enabled: enabled && !!sessionId,
      refetchInterval: 30000, // Refresh every 30 seconds
    });
  };

  // Persistence Health Query
  const usePersistenceHealth = () => {
    return useQuery({
      queryKey: ['persistence-health'],
      queryFn: checkPersistenceHealth,
      refetchInterval: 60000, // Refresh every minute
    });
  };

  // Convenience Methods
  const validateFlowWithRecommendations = useCallback(async (sessionId: string) => {
    try {
      const result = await validateFlow.mutateAsync({ sessionId, comprehensive: true });
      
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

  const performFlowRecovery = useCallback(async (sessionId: string, strategy: 'postgresql' | 'hybrid' = 'postgresql') => {
    try {
      const result = await recoverFlow.mutateAsync({ 
        sessionId, 
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
        specificSessionIds: options.specificSessions
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

  const performBulkValidation = useCallback(async (sessionIds: string[]) => {
    try {
      const result = await bulkValidate.mutateAsync(sessionIds);
      
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
export const useFlowHealthMonitor = (sessionIds: string[], enabled: boolean = true) => {
  const { performBulkValidation } = useEnhancedFlowManagement();
  
  return useQuery({
    queryKey: ['flow-health-monitor', sessionIds],
    queryFn: () => performBulkValidation(sessionIds),
    enabled: enabled && sessionIds.length > 0,
    refetchInterval: 120000, // Check every 2 minutes
    retry: 2,
  });
};

/**
 * Hook for automatic cleanup scheduling
 */
export const useAutomaticCleanup = (enabled: boolean = false) => {
  const { performFlowCleanup } = useEnhancedFlowManagement();
  
  return useQuery({
    queryKey: ['automatic-cleanup'],
    queryFn: () => performFlowCleanup({ expirationHours: 72, dryRun: false }),
    enabled,
    refetchInterval: 24 * 60 * 60 * 1000, // Run daily
    retry: 1,
  });
}; 