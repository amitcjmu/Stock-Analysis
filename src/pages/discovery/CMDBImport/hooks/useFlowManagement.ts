import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  useIncompleteFlowDetectionV2, 
  useFlowResumptionV2,
  useBulkFlowOperationsV2 
} from '@/hooks/discovery/useFlowOperations';
import { useFlowDeletion } from '@/hooks/useFlowDeletion';
import { getDiscoveryPhaseRoute } from '@/config/flowRoutes';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/use-toast';

export const useFlowManagement = () => {
  const navigate = useNavigate();
  const { client, engagement, user } = useAuth();
  const { toast } = useToast();
  
  // Flow Management State
  const { data: incompleteFlowsData, isLoading: checkingFlows } = useIncompleteFlowDetectionV2();
  const flowResumption = useFlowResumptionV2();
  const [deletionState, deletionActions] = useFlowDeletion(
    // onDeletionComplete callback
    () => {
      // Refresh flows after deletion
      // Note: refetch is not available here, but the query will be invalidated by the hook
    },
    // onDeletionError callback
    (error) => {
      console.error('Flow deletion error:', error);
      toast({
        title: "Deletion Failed",
        description: error.message || "Failed to delete flow",
        variant: "destructive",
      });
    }
  );
  const bulkFlowOperations = useBulkFlowOperationsV2();
  
  const [showFlowManager, setShowFlowManager] = useState(false);
  interface ConflictFlow {
    flow_id: string;
    phase: string;
    status: string;
    created_at: string;
    updated_at: string;
    [key: string]: unknown;
  }

  const [conflictFlows, setConflictFlows] = useState<ConflictFlow[]>([]);
  
  const incompleteFlows = incompleteFlowsData?.flows || [];
  const hasIncompleteFlows = incompleteFlows.length > 0;

  // Flow Management Handlers
  const handleContinueFlow = useCallback((flowId: string) => {
    flowResumption.mutate(flowId);
  }, [flowResumption]);

  const handleDeleteFlow = useCallback(async (flowId: string) => {
    if (!client?.id) {
      toast({
        title: "Error",
        description: "Client context is required for flow deletion",
        variant: "destructive",
      });
      return;
    }
    
    await deletionActions.requestDeletion(
      [flowId],
      client.id,
      engagement?.id,
      'manual',
      user?.id
    );
  }, [deletionActions, client, engagement, user, toast]);

  const handleBatchDeleteFlows = useCallback(async (flowIds: string[]) => {
    if (!client?.id) {
      toast({
        title: "Error",
        description: "Client context is required for flow deletion",
        variant: "destructive",
      });
      return;
    }
    
    await deletionActions.requestDeletion(
      flowIds,
      client.id,
      engagement?.id,
      'bulk_cleanup',
      user?.id
    );
  }, [deletionActions, client, engagement, user, toast]);

  const handleViewFlowDetails = useCallback((flowId: string, phase: string) => {
    // If phase is undefined or empty, default to field_mapping since the flow is waiting for approval
    const actualPhase = phase || 'field_mapping';
    
    // Navigate to phase-specific page using centralized routing configuration
    const route = getDiscoveryPhaseRoute(actualPhase, flowId);
    navigate(route);
  }, [navigate]);

  return {
    // State
    showFlowManager,
    setShowFlowManager,
    conflictFlows,
    setConflictFlows,
    incompleteFlows,
    hasIncompleteFlows,
    checkingFlows,
    
    // Actions
    handleContinueFlow,
    handleDeleteFlow,
    handleBatchDeleteFlows,
    handleViewFlowDetails,
    
    // Flow operations
    flowResumption,
    bulkFlowOperations
  };
};