import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';

export const useAttributeMappingNavigation = (flowState?: any, mappingProgress?: any) => {
  const navigate = useNavigate();
  const { user, client, engagement } = useAuth();
  const { executeFlowPhase, canProceedToPhase } = useUnifiedDiscoveryFlow();

  const handleContinueToDataCleansing = useCallback(async () => {
    if (canProceedToPhase('data_cleansing')) {
      await executeFlowPhase('data_cleansing');
      navigate('/discovery/data-cleansing');
    }
  }, [executeFlowPhase, canProceedToPhase, navigate]);

  return {
    handleContinueToDataCleansing
  };
}; 