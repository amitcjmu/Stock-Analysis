import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDiscoveryFlowV2 } from './useDiscoveryFlowV2';

export const useDependencyNavigation = (flowId?: string, dependencyData?: any) => {
  const navigate = useNavigate();
  const { flow, updatePhase } = useDiscoveryFlowV2(flowId);

  const handleContinueToNextPhase = useCallback(async () => {
    try {
      if (flow && flow.flow_id) {
        // Update to tech debt analysis phase using V2 API
        await updatePhase('tech_debt_analysis', {
          completed_phases: [...(flow.phases ? Object.keys(flow.phases).filter(p => flow.phases[p]) : []), 'dependency_analysis'],
          current_phase: 'tech_debt_analysis',
          progress_data: dependencyData
        });
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