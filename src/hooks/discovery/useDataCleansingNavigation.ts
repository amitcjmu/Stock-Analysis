import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export const useDataCleansingNavigation = (flowState: unknown, cleansingProgress: unknown): unknown => {
  const navigate = useNavigate();
  const { user, client, engagement } = useAuth();

  const handleBackToAttributeMapping = (): void => {
    navigate('/discovery/attribute-mapping');
  };

  const handleContinueToInventory = (): void => {
    const flowId = flowState?.flow_id || `flow-${Date.now()}`;
    // CC FIX (Bug #835): Include flow_id in URL path to prevent validation errors
    // when navigating from Data Cleansing to Inventory for completed flows
    navigate(`/discovery/inventory/${flowId}`, {
      replace: true,
      state: {
        flow_id: flowId,
        from_phase: 'data_cleansing',
        cleansing_progress: cleansingProgress,
        client_account_id: client?.id,
        engagement_id: engagement?.id,
        user_id: user?.id
      }
    });
  };

  return {
    handleBackToAttributeMapping,
    handleContinueToInventory,
  };
};
