import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useDiscoveryFlowV2 } from './useDiscoveryFlowV2';

export const useAttributeMappingNavigation = (flowState?: any, mappingProgress?: any) => {
  const navigate = useNavigate();
  const { user, client, engagement } = useAuth();
  const { flow, updatePhase } = useDiscoveryFlowV2(flowState?.flow_id);

  const handleContinueToDataCleansing = useCallback(async () => {
    try {
      if (flow && flow.flow_id) {
        // Update to data cleansing phase using V2 API
        await updatePhase('data_cleansing', { 
          completed_phases: [...(flow.phases ? Object.keys(flow.phases).filter(p => flow.phases[p]) : []), 'attribute_mapping'],
          current_phase: 'data_cleansing',
          progress_data: mappingProgress 
        });
        navigate('/discovery/data-cleansing');
      }
    } catch (error) {
      console.error('Failed to proceed to data cleansing:', error);
    }
  }, [flow, updatePhase, navigate, mappingProgress]);

  return {
    handleContinueToDataCleansing
  };
}; 