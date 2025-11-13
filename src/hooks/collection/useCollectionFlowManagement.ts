import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom';
import { collectionFlowApi } from '@/services/api/collection-flow';
import { useToast } from '@/hooks/use-toast';
import type { tokenStorage } from '@/contexts/AuthContext/storage';

// CC: Collection flow configuration interfaces
interface CollectionConfig {
  automation_level?: string;
  collection_strategy?: string;
  validation_rules?: string[];
  [key: string]: unknown;
}

interface FlowDetails {
  id: string;
  name?: string;
  status: string;
  created_at: string;
  [key: string]: unknown;
}

interface CleanupCriteria {
  expiration_hours: number;
  include_failed?: boolean;
  include_cancelled?: boolean;
  [key: string]: unknown;
}

interface ResumeContext {
  phase?: string;
  progress?: number;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface CollectionFlow {
  id: string;
  flow_id?: string;
  flow_name?: string;
  status: string;
  current_phase: string;
  progress: number;
  automation_tier: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  collection_config?: CollectionConfig;
  gaps_identified?: number;
  can_resume?: boolean;
  assessment_flow_id?: string; // CRITICAL UX FIX: Track if flow came from assessment flow
}

export interface CleanupOptions {
  expirationHours: number;
  dryRun: boolean;
  includeFailedFlows?: boolean;
  includeCancelledFlows?: boolean;
}

export interface CleanupResult {
  flows_cleaned: number;
  space_recovered: string;
  dry_run: boolean;
  flows_details: FlowDetails[];
  cleanup_criteria: CleanupCriteria;
}

export interface FlowContinueResult {
  status: string;
  message: string;
  flow_id: string;
  current_phase?: string;
  flow_status?: string;
  action_status?: string;
  action_description?: string;
  has_applications?: boolean;
  mfo_execution_triggered?: boolean;
  master_flow_id?: string;
  resume_result?: Record<string, unknown>;
  mfo_result?: Record<string, unknown>;
  next_steps?: Array<{
    action: string;
    endpoint: string;
    description: string;
  }>;
}

// Hook for detecting incomplete collection flows
export const useIncompleteCollectionFlows = (enabled: boolean = true) => {
  // console.log('🔍 useIncompleteCollectionFlows hook called with enabled:', enabled);

  const queryResult = useQuery({
    queryKey: ['collection-flows', 'incomplete'],
    queryFn: async () => {
      console.log('🚀 Fetching incomplete collection flows...');
      try {
        const result = await collectionFlowApi.getIncompleteFlows();
        console.log('✅ Incomplete flows fetched:', result);
        return result;
      } catch (error: unknown) {
        console.error('❌ Failed to fetch incomplete flows:', error);

        // If it's an auth error, don't throw it back to React Query
        // This prevents retries and lets the auth context handle the redirect
        if (error?.status === 401 || error?.isAuthError) {
          console.warn('🔐 Authentication error in collection flows query - stopping retries');
          // Return empty array to prevent UI errors
          return [];
        }

        throw error;
      }
    },
    enabled,
    refetchInterval: (data, query) => {
      // STOP INFINITE LOOPS: Disable aggressive polling
      // Don't refetch if there was any error
      if (query?.state?.error) {
        console.log('🛑 Error detected, stopping all polling:', query.state.error);
        return false;
      }

      // Don't refetch if there was an auth error
      if (query?.state?.error?.status === 401 || query?.state?.error?.isAuthError) {
        return false;
      }

      // Stop polling if all flows are in terminal states
      if (data && Array.isArray(data)) {
        const hasActiveFlows = data.some(flow => {
          const status = flow.status?.toLowerCase();
          return status !== 'completed' && status !== 'failed' && status !== 'cancelled';
        });

        if (!hasActiveFlows) {
          console.log('✅ All flows are in terminal states, stopping polling');
          return false;
        }
      }

      // Reduce polling frequency to prevent spam
      return 60000; // Refetch every 60 seconds instead of 30
    },
    staleTime: 10000, // Consider data stale after 10 seconds
    retry: (failureCount, error: unknown) => {
      // STOP INFINITE LOOPS: No retries for critical errors
      // Don't retry on authentication errors
      if (error?.status === 401 || error?.isAuthError) {
        return false;
      }
      // Don't retry on 409 conflicts - these need user intervention
      if (error?.status === 409) {
        return false;
      }
      // Don't retry on 500 server errors - these need backend fixes
      if (error?.status === 500) {
        return false;
      }
      // Only retry on network errors (no status code) and 1 attempt max
      return !error?.status && failureCount < 1;
    }
  });

  // Commented out to reduce console spam
  // console.log('🔍 Query result:', {
  //   isLoading: queryResult.isLoading,
  //   isFetching: queryResult.isFetching,
  //   isError: queryResult.isError,
  //   data: queryResult.data,
  //   error: queryResult.error
  // });

  return queryResult;
};

// Hook for detecting actively incomplete collection flows (INITIALIZED, RUNNING only)
// Per ADR-012, PAUSED flows are waiting for user input and should not block new operations
export const useActivelyIncompleteCollectionFlows = (enabled: boolean = true) => {
  const queryResult = useQuery({
    queryKey: ['collection-flows', 'actively-incomplete'],
    queryFn: async () => {
      console.log('🚀 Fetching actively incomplete collection flows...');
      try {
        const result = await collectionFlowApi.getActivelyIncompleteFlows();
        console.log('✅ Actively incomplete flows fetched:', result);
        return result;
      } catch (error: unknown) {
        console.error('❌ Failed to fetch actively incomplete flows:', error);

        // If it's an auth error, don't throw it back to React Query
        // This prevents retries and lets the auth context handle the redirect
        if (error?.status === 401 || error?.isAuthError) {
          console.warn('🔐 Authentication error in actively incomplete flows query - stopping retries');
          // Return empty array to prevent UI errors
          return [];
        }

        throw error;
      }
    },
    enabled,
    refetchInterval: (data, query) => {
      // STOP INFINITE LOOPS: Disable aggressive polling
      // Don't refetch if there was any error
      if (query?.state?.error) {
        console.log('🛑 Error detected, stopping all polling:', query.state.error);
        return false;
      }

      // Stop polling if all flows are in terminal states
      if (data && Array.isArray(data)) {
        const hasActiveFlows = data.some(flow => {
          const status = flow.status?.toLowerCase();
          return status !== 'completed' && status !== 'failed' && status !== 'cancelled';
        });

        if (!hasActiveFlows) {
          console.log('✅ All actively incomplete flows are in terminal states, stopping polling');
          return false;
        }
      }

      // Reduce polling frequency to prevent spam
      return 60000; // Refetch every 60 seconds
    },
    staleTime: 10000, // Consider data stale after 10 seconds
    retry: (failureCount, error: unknown) => {
      // STOP INFINITE LOOPS: No retries for critical errors
      // Don't retry on authentication errors
      if (error?.status === 401 || error?.isAuthError) {
        return false;
      }
      // Don't retry on 409 conflicts - these need user intervention
      if (error?.status === 409) {
        return false;
      }
      // Don't retry on 500 server errors - these need backend fixes
      if (error?.status === 500) {
        return false;
      }
      // Only retry on network errors (no status code) and 1 attempt max
      return !error?.status && failureCount < 1;
    }
  });

  return queryResult;
};

export const useCollectionFlowManagement = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [isOperationPending, setIsOperationPending] = useState(false);

  // Continue/resume flow mutation
  const continueFlowMutation = useMutation({
    mutationFn: ({ flowId, resumeContext }: { flowId: string; resumeContext?: ResumeContext }) =>
      collectionFlowApi.continueFlow(flowId, resumeContext),
    onMutate: () => setIsOperationPending(true),
    onSuccess: (data: FlowContinueResult) => {
      toast({
        title: "Flow Resumed",
        description: `Collection flow ${data.flow_id} has been resumed successfully`,
        variant: "default"
      });
      // Invalidate and refetch flow queries
      queryClient.invalidateQueries({ queryKey: ['collection-flows'] });
    },
    onError: (error: unknown) => {
      toast({
        title: "Resume Failed",
        description: error.response?.data?.detail || "Failed to resume collection flow",
        variant: "destructive"
      });
    },
    onSettled: () => setIsOperationPending(false)
  });

  // Delete single flow mutation
  const deleteFlowMutation = useMutation({
    mutationFn: ({ flowId, force = false }: { flowId: string; force?: boolean }) =>
      collectionFlowApi.deleteFlow(flowId, force),
    onMutate: () => setIsOperationPending(true),
    onSuccess: (data) => {
      toast({
        title: "Flow Deleted",
        description: `Collection flow ${data.flow_id} has been deleted successfully`,
        variant: "default"
      });
      queryClient.invalidateQueries({ queryKey: ['collection-flows'] });
    },
    onError: (error: unknown) => {
      toast({
        title: "Delete Failed",
        description: error.response?.data?.detail || "Failed to delete collection flow",
        variant: "destructive"
      });
    },
    onSettled: () => setIsOperationPending(false)
  });

  // Batch delete flows mutation
  const batchDeleteMutation = useMutation({
    mutationFn: ({ flowIds, force = false }: { flowIds: string[]; force?: boolean }) =>
      collectionFlowApi.batchDeleteFlows(flowIds, force),
    onMutate: () => setIsOperationPending(true),
    onSuccess: (data) => {
      toast({
        title: "Batch Delete Completed",
        description: `Successfully deleted ${data.deleted_count} flows${data.failed_count > 0 ? `, ${data.failed_count} failed` : ''}`,
        variant: data.failed_count > 0 ? "destructive" : "default"
      });
      queryClient.invalidateQueries({ queryKey: ['collection-flows'] });
    },
    onError: (error: unknown) => {
      toast({
        title: "Batch Delete Failed",
        description: error.response?.data?.detail || "Failed to delete collection flows",
        variant: "destructive"
      });
    },
    onSettled: () => setIsOperationPending(false)
  });

  // Cleanup flows mutation
  const cleanupFlowsMutation = useMutation({
    mutationFn: (options: CleanupOptions) =>
      collectionFlowApi.cleanupFlows(
        options.expirationHours,
        options.dryRun,
        options.includeFailedFlows,
        options.includeCancelledFlows
      ),
    onMutate: () => setIsOperationPending(true),
    onSuccess: (data: CleanupResult) => {
      const title = data.dry_run ? "Cleanup Preview" : "Cleanup Completed";
      const description = data.dry_run
        ? `Would clean ${data.flows_cleaned} flows, recovering ${data.space_recovered}`
        : `Cleaned ${data.flows_cleaned} flows, recovered ${data.space_recovered}`;

      toast({
        title,
        description,
        variant: "default"
      });

      if (!data.dry_run) {
        queryClient.invalidateQueries({ queryKey: ['collection-flows'] });
      }
    },
    onError: (error: unknown) => {
      toast({
        title: "Cleanup Failed",
        description: error.response?.data?.detail || "Failed to cleanup collection flows",
        variant: "destructive"
      });
    },
    onSettled: () => setIsOperationPending(false)
  });

  // Helper functions
  const continueFlow = async (flowId: string, resumeContext?: ResumeContext) =>  {
    return continueFlowMutation.mutateAsync({ flowId, resumeContext });
  };

  const deleteFlow = async (flowId: string, force: boolean = false) =>  {
    return deleteFlowMutation.mutateAsync({ flowId, force });
  };

  const batchDeleteFlows = async (flowIds: string[], force: boolean = false) =>  {
    return batchDeleteMutation.mutateAsync({ flowIds, force });
  };

  const cleanupFlows = async (options: CleanupOptions) =>  {
    return cleanupFlowsMutation.mutateAsync(options);
  };

  return {
    // Mutations
    continueFlow,
    deleteFlow,
    batchDeleteFlows,
    cleanupFlows,

    // Loading states
    isContinuing: continueFlowMutation.isPending,
    isDeleting: deleteFlowMutation.isPending,
    isBatchDeleting: batchDeleteMutation.isPending,
    isCleaning: cleanupFlowsMutation.isPending,
    isOperationPending,

    // Mutation objects for advanced usage
    continueFlowMutation,
    deleteFlowMutation,
    batchDeleteMutation,
    cleanupFlowsMutation
  };
};

export const useCollectionFlowStatus = (flowId?: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['collection-flows', 'status', flowId],
    queryFn: () => collectionFlowApi.getFlowStatus(),
    enabled: enabled && !!flowId,
    refetchInterval: (data, query) => {
      // Stop polling if there was an error
      if (query?.state?.error) {
        console.log('🛑 Error detected in flow status query, stopping polling:', query.state.error);
        return false;
      }

      // Stop polling if flow is in terminal state
      if (data) {
        const status = data.status?.toLowerCase();
        const progress = data.progress || 0;

        if (status === 'completed' || status === 'failed' || status === 'cancelled' || progress >= 100) {
          console.log(`✅ Flow ${flowId} reached terminal state (${status}, progress: ${progress}%), stopping polling`);
          return false;
        }

        // If flow is in error state, stop aggressive polling
        if (status === 'error') {
          console.log(`⚠️ Flow ${flowId} in error state, reducing polling frequency`);
          return 30000; // Poll every 30 seconds for error states
        }
      }

      return 5000; // Continue polling every 5 seconds for active monitoring
    },
    staleTime: 2000,
    retry: (failureCount, error) => {
      // Don't retry on authentication errors
      if (error?.status === 401) {
        return false;
      }
      // Don't retry on 500 server errors
      if (error?.status === 500) {
        return false;
      }
      // Only retry network errors once
      return !error?.status && failureCount < 1;
    }
  });
};

export const useCollectionFlowDetails = (flowId: string, enabled: boolean = true): unknown => {
  return useQuery({
    queryKey: ['collection-flows', 'details', flowId],
    queryFn: () => collectionFlowApi.getFlowDetails(flowId),
    enabled: enabled && !!flowId,
    staleTime: 30000,
    retry: (failureCount, error) => {
      // Don't retry on 404 (flow not found) or auth errors
      if (error?.status === 404 || error?.status === 401) {
        return false;
      }
      // Only retry network errors once
      return !error?.status && failureCount < 1;
    }
  });
};

export const useCollectionFlowGaps = (flowId: string, enabled: boolean = true): unknown => {
  return useQuery({
    queryKey: ['collection-flows', 'gaps', flowId],
    queryFn: () => collectionFlowApi.getFlowGaps(flowId),
    enabled: enabled && !!flowId,
    staleTime: 60000
  });
};

export const useCollectionFlowQuestionnaires = (flowId: string, enabled: boolean = true): unknown => {
  return useQuery({
    queryKey: ['collection-flows', 'questionnaires', flowId],
    queryFn: () => collectionFlowApi.getFlowQuestionnaires(flowId),
    enabled: enabled && !!flowId,
    staleTime: 30000, // Reduce stale time for more responsive updates
    retry: (failureCount, error) => {
      // Don't retry on 404 (not found) or 422 (no applications selected)
      if (error?.status === 404 || error?.status === 422) {
        return false;
      }
      // Don't retry on auth errors
      if (error?.status === 401) {
        return false;
      }
      // Only retry network errors once
      return !error?.status && failureCount < 1;
    }
  });
};
