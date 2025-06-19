import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export const useDataCleansingNavigation = (flowState: any, cleansingProgress: any) => {
  const navigate = useNavigate();
  const { user, client, engagement } = useAuth();

  const handleBackToAttributeMapping = () => {
    navigate('/discovery/attribute-mapping');
  };

  const handleContinueToInventory = () => {
    navigate('/discovery/inventory', {
      replace: true,
      state: {
        flow_session_id: flowState?.session_id || `session-${Date.now()}`,
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