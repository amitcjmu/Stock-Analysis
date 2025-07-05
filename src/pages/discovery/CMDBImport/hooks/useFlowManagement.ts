import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  useIncompleteFlowDetectionV2, 
  useFlowResumptionV2, 
  useFlowDeletionV2, 
  useBulkFlowOperationsV2 
} from '@/hooks/discovery/useFlowOperations';
import { getDiscoveryPhaseRoute } from '@/config/flowRoutes';

export const useFlowManagement = () => {
  const navigate = useNavigate();
  
  // Flow Management State
  const { data: incompleteFlowsData, isLoading: checkingFlows } = useIncompleteFlowDetectionV2();
  const flowResumption = useFlowResumptionV2();
  const flowDeletion = useFlowDeletionV2();
  const bulkFlowOperations = useBulkFlowOperationsV2();
  
  const [showFlowManager, setShowFlowManager] = useState(false);
  const [conflictFlows, setConflictFlows] = useState<any[]>([]);
  
  const incompleteFlows = incompleteFlowsData?.flows || [];
  const hasIncompleteFlows = incompleteFlows.length > 0;

  // Flow Management Handlers
  const handleContinueFlow = useCallback((flowId: string) => {
    flowResumption.mutate(flowId);
  }, [flowResumption]);

  const handleDeleteFlow = useCallback((flowId: string) => {
    flowDeletion.mutate(flowId);
  }, [flowDeletion]);

  const handleBatchDeleteFlows = useCallback((flowIds: string[]) => {
    bulkFlowOperations.mutate({ flow_ids: flowIds });
  }, [bulkFlowOperations]);

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
    flowDeletion,
    bulkFlowOperations
  };
};