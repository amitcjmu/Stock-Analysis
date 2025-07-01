import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  useIncompleteFlowDetectionV2, 
  useFlowResumptionV2, 
  useFlowDeletionV2, 
  useBulkFlowOperationsV2 
} from '@/hooks/discovery/useIncompleteFlowDetectionV2';

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
  const handleContinueFlow = useCallback((sessionId: string) => {
    flowResumption.mutate(sessionId);
  }, [flowResumption]);

  const handleDeleteFlow = useCallback((sessionId: string) => {
    flowDeletion.mutate(sessionId);
  }, [flowDeletion]);

  const handleBatchDeleteFlows = useCallback((sessionIds: string[]) => {
    bulkFlowOperations.mutate({ session_ids: sessionIds });
  }, [bulkFlowOperations]);

  const handleViewFlowDetails = useCallback((sessionId: string, phase: string) => {
    // Navigate to phase-specific page using correct phase names
    const phaseRoutes = {
      'data_import': `/discovery/import`,
      'attribute_mapping': `/discovery/attribute-mapping/${sessionId}`,
      'data_cleansing': `/discovery/data-cleansing/${sessionId}`,
      'inventory': `/discovery/inventory/${sessionId}`,
      'dependencies': `/discovery/dependencies/${sessionId}`,
      'tech_debt': `/discovery/tech-debt/${sessionId}`
    };
    const route = phaseRoutes[phase as keyof typeof phaseRoutes] || `/discovery/enhanced-dashboard`;
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