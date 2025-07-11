/**
 * Unified Flow Deletion Hook
 * Replaces all scattered deletion logic with centralized user-approval system
 * Consolidates: useFlowDeletionV2, useBulkFlowOperationsV2, and manual deletion handlers
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { flowDeletionService, FlowDeletionResult } from '@/services/flowDeletionService';

interface FlowDeletionOptions {
  deletion_source?: 'manual' | 'bulk_cleanup' | 'navigation' | 'automatic_cleanup';
  onSuccess?: (result: FlowDeletionResult) => void;
  onError?: (error: any) => void;
  skip_confirmation?: boolean; // For testing only - never use in production
}

export const useFlowDeletion = (options: FlowDeletionOptions = {}) => {
  const { client, engagement, user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const {
    deletion_source = 'manual',
    onSuccess,
    onError,
    skip_confirmation = false
  } = options;

  const deletionMutation = useMutation({
    mutationFn: async (flowIds: string[]) => {
      if (!client?.id) {
        throw new Error('Client context is required for flow deletion');
      }

      console.log('🗑️ Flow deletion requested:', {
        flowIds,
        deletion_source,
        client: client.id,
        engagement: engagement?.id,
        user: user?.id
      });

      // Use centralized deletion service
      const result = await flowDeletionService.requestFlowDeletion(
        flowIds,
        client.id,
        engagement?.id,
        deletion_source,
        user?.id
      );

      console.log('📋 Flow deletion result:', result);
      return result;
    },
    
    onSuccess: (result) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-flows'] });
      queryClient.invalidateQueries({ queryKey: ['active-flows'] });
      queryClient.invalidateQueries({ queryKey: ['master-flows'] });

      // Show appropriate toast messages
      if (result.success) {
        if (result.deleted_count > 0) {
          toast({
            title: "✅ Flow Deletion Successful",
            description: `Successfully deleted ${result.deleted_count} flow${result.deleted_count > 1 ? 's' : ''}${result.failed_count > 0 ? `, ${result.failed_count} failed` : ''}.`,
            variant: "default",
          });
        }
        
        if (result.failed_count > 0) {
          toast({
            title: "⚠️ Some Deletions Failed",
            description: `Failed to delete ${result.failed_count} flow${result.failed_count > 1 ? 's' : ''}. Please try again or contact support.`,
            variant: "destructive",
          });
        }
      } else {
        if (result.audit_trail.reason === 'user_declined') {
          toast({
            title: "❌ Deletion Cancelled",
            description: "Flow deletion was cancelled by user.",
            variant: "default",
          });
        } else {
          toast({
            title: "❌ Deletion Failed",
            description: "Flow deletion failed. Please try again or contact support.",
            variant: "destructive",
          });
        }
      }

      // Call custom success handler
      if (onSuccess) {
        onSuccess(result);
      }
    },

    onError: (error) => {
      console.error('❌ Flow deletion mutation error:', error);
      
      toast({
        title: "❌ Deletion Error",
        description: error instanceof Error ? error.message : "An unexpected error occurred during deletion.",
        variant: "destructive",
      });

      // Call custom error handler
      if (onError) {
        onError(error);
      }
    }
  });

  return {
    // Main deletion function
    deleteFlows: deletionMutation.mutate,
    deleteFlowsAsync: deletionMutation.mutateAsync,
    
    // Single flow deletion convenience method
    deleteFlow: (flowId: string) => deletionMutation.mutate([flowId]),
    deleteFlowAsync: (flowId: string) => deletionMutation.mutateAsync([flowId]),
    
    // Bulk deletion convenience method
    bulkDeleteFlows: (flowIds: string[]) => deletionMutation.mutate(flowIds),
    bulkDeleteFlowsAsync: (flowIds: string[]) => deletionMutation.mutateAsync(flowIds),
    
    // Status and loading states
    isDeleting: deletionMutation.isPending,
    isError: deletionMutation.isError,
    error: deletionMutation.error,
    isSuccess: deletionMutation.isSuccess,
    
    // Reset mutation state
    reset: deletionMutation.reset,
  };
};

/**
 * Hook for cleanup recommendations (system suggests but never auto-deletes)
 */
export const useFlowCleanupRecommendations = () => {
  const { client, engagement } = useAuth();
  
  const recommendationsMutation = useMutation({
    mutationFn: async (flowType?: string) => {
      if (!client?.id) {
        throw new Error('Client context is required for cleanup recommendations');
      }

      console.log('🧹 Fetching cleanup recommendations for:', {
        client: client.id,
        engagement: engagement?.id,
        flowType
      });

      const candidates = await flowDeletionService.identifyDeletionCandidates(
        client.id,
        engagement?.id,
        flowType
      );

      console.log('📋 Cleanup recommendations:', candidates);
      return candidates;
    }
  });

  return {
    getRecommendations: recommendationsMutation.mutate,
    getRecommendationsAsync: recommendationsMutation.mutateAsync,
    
    recommendations: recommendationsMutation.data,
    isLoading: recommendationsMutation.isPending,
    isError: recommendationsMutation.isError,
    error: recommendationsMutation.error,
    
    reset: recommendationsMutation.reset,
  };
};

/**
 * Hook for cleanup flows specifically (what UploadBlocker should use)
 */
export const useFlowCleanup = () => {
  const deletionHook = useFlowDeletion({ 
    deletion_source: 'automatic_cleanup' 
  });
  
  const recommendationsHook = useFlowCleanupRecommendations();

  return {
    // Get cleanup recommendations
    getCleanupRecommendations: recommendationsHook.getRecommendationsAsync,
    recommendations: recommendationsHook.recommendations,
    isLoadingRecommendations: recommendationsHook.isLoading,
    
    // Execute cleanup with user approval
    executeCleanup: deletionHook.deleteFlowsAsync,
    isExecutingCleanup: deletionHook.isDeleting,
    
    // Combined method for full cleanup workflow
    performCleanup: async (flowType?: string) => {
      const recommendations = await recommendationsHook.getRecommendationsAsync(flowType);
      
      if (recommendations.length === 0) {
        return { success: true, message: 'No flows need cleanup' };
      }
      
      const flowIds = recommendations.map(r => r.flowId);
      return await deletionHook.deleteFlowsAsync(flowIds);
    }
  };
};