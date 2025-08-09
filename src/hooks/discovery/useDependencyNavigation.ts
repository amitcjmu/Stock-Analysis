import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';
import { collectionFlowApi } from '@/services/api/collection-flow';

interface DependencyNavigationHandlers {
  handleContinueToNextPhase: () => Promise<void>;
  handleNavigateToInventory: () => void;
  handleNavigateToDataCleansing: () => void;
  handleNavigateToAttributeMapping: () => void;
}

export const useDependencyNavigation = (
  flowId?: string,
  dependencyData?: unknown
): DependencyNavigationHandlers => {
  const navigate = useNavigate();
  const { flowState: flow, executeFlowPhase: updatePhase } = useUnifiedDiscoveryFlow(flowId);

  const handleContinueToNextPhase = useCallback(async () => {
    try {
      // Ensure a collection flow exists for this engagement
      const ensured = await collectionFlowApi.ensureFlow();
      const id = ensured?.id;
      if (id) {
        navigate(`/collection/progress?flowId=${id}`);
        return;
      }
    } catch (error) {
      console.error('ensureFlow failed, falling back:', error);
    }

    try {
      if (flow && flow.flow_id) {
        // After dependencies, route to Collection Progress to complete data enrichment
        navigate(`/collection/progress?flowId=${flow.flow_id}`);
      } else {
        navigate('/collection/progress');
      }
    } catch (error) {
      console.error('Failed to proceed to collection progress:', error);
    }
  }, [flow, updatePhase, navigate]);

  const handleNavigateToInventory = useCallback(() => {
    navigate('/discovery/inventory');
  }, [navigate]);

  const handleNavigateToDataCleansing = useCallback(() => {
    navigate('/discovery/data-cleansing');
  }, [navigate]);

  const handleNavigateToAttributeMapping = useCallback(() => {
    navigate('/discovery/attribute-mapping');
  }, [navigate]);

  return {
    handleContinueToNextPhase,
    handleNavigateToInventory,
    handleNavigateToDataCleansing,
    handleNavigateToAttributeMapping
  };
};
