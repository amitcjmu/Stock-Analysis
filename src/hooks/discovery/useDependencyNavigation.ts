import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';

export const useDependencyNavigation = (flowId?: string, dependencyData?: unknown): unknown => {
  const navigate = useNavigate();
  const { flowState: flow, executeFlowPhase: updatePhase } = useUnifiedDiscoveryFlow(flowId);

  const handleContinueToNextPhase = useCallback(async () => {
    try {
      if (flow && flow.flow_id) {
        // After dependencies, route to Collection Progress to complete data enrichment
        navigate(`/collection/progress?flowId=${flow.flow_id}`);
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
