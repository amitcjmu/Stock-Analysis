import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { discoveryFlowService } from '../../services/api/discoveryFlowService';
import { masterFlowService } from '../../services/api/masterFlowService';
import SecureLogger from '../../utils/secureLogger';

// Types for discovery flow state
export interface DiscoveryFlowState {
  flow_id?: string;
  flowId?: string;
  status: 'idle' | 'initializing' | 'running' | 'in_progress' | 'paused' | 'completed' | 'failed' | 'error';
  progress_percentage?: number;
  progressPercentage?: number;
  current_phase?: string;
  currentPhase?: string;
  crew_results?: Record<string, unknown>;
  crewResults?: Record<string, unknown>;
  phase_completion?: Record<string, boolean>;
  phaseCompletion?: Record<string, boolean>;
  error_message?: string;
  errorMessage?: string;
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
  updatedAt?: string;
}

// Crew result interface
export interface CrewResult {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'error';
  execution_time?: number;
  executionTime?: number;
  progress_percentage?: number;
  progressPercentage?: number;
  error_message?: string;
  errorMessage?: string;
  results?: unknown;
}

// Hook return type
export interface UseDiscoveryFlowReturn {
  flow: DiscoveryFlowState | null;
  isLoading: boolean;
  error: Error | null;
  initializeFlow: () => Promise<void>;
  startDiscovery: () => Promise<void>;
  pauseFlow?: () => Promise<void>;
  resumeFlow?: () => Promise<void>;
  refreshFlow: () => Promise<void>;
  executePhase: (phase: string) => Promise<void>;
  getCrewResult: (crewName: string) => CrewResult | null;
}

/**
 * Hook for managing discovery flow operations
 * Provides comprehensive flow management with proper error handling and state management
 */
export const useDiscoveryFlow = (flowId?: string): UseDiscoveryFlowReturn => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [error, setError] = useState<Error | null>(null);

  // Query key for caching
  const flowQueryKey = ['discoveryFlow', flowId];

  // Fetch flow data with proper error handling
  const {
    data: rawFlowData,
    isLoading,
    error: queryError,
    refetch
  } = useQuery({
    queryKey: flowQueryKey,
    queryFn: async () => {
      if (!flowId || !user?.client_account_id || !user?.engagement_id) {
        return null;
      }

      try {
        // Try discovery flow service first
        const response = await discoveryFlowService.getOperationalStatus(
          flowId,
          user.client_account_id,
          user.engagement_id
        );
        return response;
      } catch (discoveryError) {
        SecureLogger.warn('Discovery flow service failed, trying master flow service', {
          flowId,
          error: discoveryError
        });

        try {
          // Fallback to master flow service
          const response = await masterFlowService.getFlowDetails(flowId);
          return response;
        } catch (masterError) {
          SecureLogger.error('Both services failed to fetch flow data', {
            flowId,
            discoveryError,
            masterError
          });
          throw masterError;
        }
      }
    },
    enabled: !!flowId && !!user?.client_account_id,
    staleTime: 30000, // 30 seconds
    refetchInterval: (data) => {
      // Auto-refresh if flow is running
      const status = data?.status;
      return (status === 'running' || status === 'in_progress') ? 5000 : false;
    },
    retry: 2,
    retryDelay: 1000
  });

  // Use raw flow data directly (already in snake_case)
  const flow = rawFlowData || null;

  // Initialize flow mutation
  const initializeFlowMutation = useMutation({
    mutationFn: async () => {
      if (!user?.client_account_id) {
        throw new Error('User context not available');
      }

      try {
        const response = await masterFlowService.initializeFlow({
          client_account_id: user.client_account_id,
          engagement_id: user.engagement_id,
          flow_type: 'discovery'
        });
        return response;
      } catch (error) {
        SecureLogger.error('Failed to initialize discovery flow', {
          error,
          clientAccountId: user.client_account_id,
          engagementId: user.engagement_id
        });
        throw error;
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(flowQueryKey, data);
      setError(null);
    },
    onError: (error: Error) => {
      setError(error);
      SecureLogger.error('Initialize flow mutation failed', { error });
    }
  });

  // Start discovery mutation
  const startDiscoveryMutation = useMutation({
    mutationFn: async () => {
      if (!flowId || !user?.client_account_id || !user?.engagement_id) {
        throw new Error('Flow ID and user context are required');
      }

      try {
        // Use discovery flow service to execute the first phase
        const response = await discoveryFlowService.executePhase(
          flowId,
          'field_mapping',
          {},
          user.client_account_id,
          user.engagement_id
        );
        return response;
      } catch (error) {
        SecureLogger.error('Failed to start discovery flow', {
          flowId,
          error
        });
        throw error;
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(flowQueryKey, data);
      setError(null);
    },
    onError: (error: Error) => {
      setError(error);
      SecureLogger.error('Start discovery mutation failed', { error });
    }
  });

  // Execute phase mutation
  const executePhaseMutation = useMutation({
    mutationFn: async (phase: string) => {
      if (!flowId || !user?.client_account_id || !user?.engagement_id) {
        throw new Error('Flow ID and user context are required');
      }

      try {
        const response = await discoveryFlowService.executePhase(
          flowId,
          phase,
          {},
          user.client_account_id,
          user.engagement_id
        );
        return response;
      } catch (error) {
        SecureLogger.error('Failed to execute phase', {
          flowId,
          phase,
          error
        });
        throw error;
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(flowQueryKey, data);
      setError(null);
    },
    onError: (error: Error) => {
      setError(error);
      SecureLogger.error('Execute phase mutation failed', { error });
    }
  });

  // Pause flow mutation
  const pauseFlowMutation = useMutation({
    mutationFn: async () => {
      if (!flowId) {
        throw new Error('Flow ID is required');
      }

      try {
        const response = await masterFlowService.pauseFlow(flowId);
        return response;
      } catch (error) {
        SecureLogger.error('Failed to pause flow', {
          flowId,
          error
        });
        throw error;
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(flowQueryKey, data);
      setError(null);
    },
    onError: (error: Error) => {
      setError(error);
      SecureLogger.error('Pause flow mutation failed', { error });
    }
  });

  // Resume flow mutation
  const resumeFlowMutation = useMutation({
    mutationFn: async () => {
      if (!flowId) {
        throw new Error('Flow ID is required');
      }

      try {
        const response = await masterFlowService.resumeFlow(flowId);
        return response;
      } catch (error) {
        SecureLogger.error('Failed to resume flow', {
          flowId,
          error
        });
        throw error;
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(flowQueryKey, data);
      setError(null);
    },
    onError: (error: Error) => {
      setError(error);
      SecureLogger.error('Resume flow mutation failed', { error });
    }
  });

  // Callback functions with proper error handling
  const initializeFlow = useCallback(async () => {
    try {
      await initializeFlowMutation.mutateAsync();
    } catch (error) {
      SecureLogger.error('Initialize flow failed', { error });
      throw error;
    }
  }, [initializeFlowMutation]);

  const startDiscovery = useCallback(async () => {
    try {
      await startDiscoveryMutation.mutateAsync();
    } catch (error) {
      SecureLogger.error('Start discovery failed', { error });
      throw error;
    }
  }, [startDiscoveryMutation]);

  const pauseFlow = useCallback(async () => {
    try {
      await pauseFlowMutation.mutateAsync();
    } catch (error) {
      SecureLogger.error('Pause flow failed', { error });
      throw error;
    }
  }, [pauseFlowMutation]);

  const resumeFlow = useCallback(async () => {
    try {
      await resumeFlowMutation.mutateAsync();
    } catch (error) {
      SecureLogger.error('Resume flow failed', { error });
      throw error;
    }
  }, [resumeFlowMutation]);

  const executePhase = useCallback(async (phase: string) => {
    try {
      await executePhaseMutation.mutateAsync(phase);
    } catch (error) {
      SecureLogger.error('Execute phase failed', { phase, error });
      throw error;
    }
  }, [executePhaseMutation]);

  const refreshFlow = useCallback(async () => {
    try {
      await refetch();
      setError(null);
    } catch (error) {
      SecureLogger.error('Refresh flow failed', { error });
      setError(error as Error);
    }
  }, [refetch]);

  // Get crew result with null safety
  const getCrewResult = useCallback((crewName: string): CrewResult | null => {
    if (!flow) return null;

    const crewResults = flow.crewResults || flow.crew_results;
    if (!crewResults || !crewResults[crewName]) return null;

    return crewResults[crewName];
  }, [flow]);

  // Update error state when query error changes
  useEffect(() => {
    if (queryError) {
      setError(queryError);
    } else {
      setError(null);
    }
  }, [queryError]);

  // Log flow status changes for debugging
  useEffect(() => {
    if (flow) {
      SecureLogger.debug('Discovery flow status updated', {
        flowId,
        status: flow.status,
        progress: flow.progressPercentage || flow.progress_percentage,
        currentPhase: flow.currentPhase || flow.current_phase
      });
    }
  }, [flow, flowId]);

  return {
    flow,
    isLoading,
    error,
    initializeFlow,
    startDiscovery,
    pauseFlow,
    resumeFlow,
    refreshFlow,
    executePhase,
    getCrewResult
  };
};

export default useDiscoveryFlow;
