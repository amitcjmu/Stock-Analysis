import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDiscoveryFlowV2 } from './useDiscoveryFlowV2';

interface InventoryProgress {
  total_assets: number;
  classified_assets: number;
  servers: number;
  applications: number;
  devices: number;
  databases: number;
  unknown: number;
  classification_accuracy: number;
  crew_completion_status: Record<string, boolean>;
}

interface InventoryNavigationOptions {
  flow_session_id?: string;
  inventory_progress: InventoryProgress;
  client_account_id: string;
  engagement_id: string;
}

export const useInventoryNavigation = (flowId?: string) => {
  const navigate = useNavigate();
  const { flow, updatePhase } = useDiscoveryFlowV2(flowId);

  const handleContinueToAppServerDependencies = useCallback(async (options?: {
    flow_session_id?: string;
    inventory_progress?: any;
    client_account_id?: number;
    engagement_id?: number;
  }) => {
    try {
      if (flow && flow.flow_id) {
        // Update to dependency analysis phase using V2 API
        await updatePhase('dependency_analysis', {
          completed_phases: [...(flow.phases ? Object.keys(flow.phases).filter(p => flow.phases[p]) : []), 'inventory'],
          current_phase: 'dependency_analysis',
          progress_data: options?.inventory_progress
        });
        navigate('/discovery/dependencies');
      }
    } catch (error) {
      console.error('Failed to proceed to dependency analysis:', error);
    }
  }, [flow, updatePhase, navigate]);

  const handleNavigateToDataCleansing = useCallback(() => {
    navigate('/discovery/data-cleansing');
  }, [navigate]);

  const handleNavigateToAttributeMapping = useCallback(() => {
    navigate('/discovery/attribute-mapping');
  }, [navigate]);

  const validateInventoryCompletion = useCallback(() => {
    // TODO: Implement inventory completion validation logic
    return true;
  }, []);

  const getInventoryCompletionMessage = useCallback(() => {
    // TODO: Implement completion message logic
    return 'Inventory analysis complete. Ready to proceed to dependency analysis.';
  }, []);

  return {
    handleContinueToAppServerDependencies,
    handleNavigateToDataCleansing,
    handleNavigateToAttributeMapping,
    validateInventoryCompletion,
    getInventoryCompletionMessage,
  };
}; 