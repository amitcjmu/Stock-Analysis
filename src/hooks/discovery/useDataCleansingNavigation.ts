import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export const useDataCleansingNavigation = (flowState: any, cleansingProgress: unknown) => {
  const navigate = useNavigate();
  const { user, client, engagement } = useAuth();

  const handleBackToAttributeMapping = () => {
    navigate('/discovery/attribute-mapping');
  };

  const handleContinueToInventory = () => {
    navigate('/discovery/inventory', {
      replace: true,
      state: {
        flow_id: flowState?.flow_id || `flow-${Date.now()}`,
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