import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';

export const useDependencyNavigation = (flowId?: string, dependencyData?: unknown) => {
  const navigate = useNavigate();
  const { flowState: flow, executeFlowPhase: updatePhase } = useUnifiedDiscoveryFlow(flowId);

  const handleContinueToNextPhase = useCallback(async () => {
    try {
      if (flow && flow.flow_id) {
        // Update to tech debt analysis phase
        await updatePhase('tech_debt_analysis');
        navigate('/discovery/tech-debt');
      }
    } catch (error) {
      console.error('Failed to proceed to tech debt analysis:', error);
    }
  }, [flow, updatePhase, navigate, dependencyData]);

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
