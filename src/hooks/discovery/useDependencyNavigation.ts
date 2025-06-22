import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';

export const useDependencyNavigation = (flowState?: any, dependencyData?: any) => {
  const navigate = useNavigate();
  const { executeFlowPhase, canProceedToPhase } = useUnifiedDiscoveryFlow();

  const handleContinueToNextPhase = useCallback(async () => {
    if (canProceedToPhase('tech_debt_analysis')) {
      await executeFlowPhase('tech_debt_analysis');
      navigate('/discovery/tech-debt');
    }
  }, [executeFlowPhase, canProceedToPhase, navigate]);

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