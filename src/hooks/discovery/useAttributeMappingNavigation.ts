import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export const useAttributeMappingNavigation = (flowState: any, mappingProgress: any) => {
  const navigate = useNavigate();
  const { user, client, engagement } = useAuth();

  const handleContinueToDataCleansing = () => {
    navigate('/discovery/data-cleansing', {
      replace: true,
      state: {
        flow_session_id: flowState?.session_id || `session-${Date.now()}`,
        from_phase: 'field_mapping',
        mapping_progress: mappingProgress,
        client_account_id: client?.id,
        engagement_id: engagement?.id,
        user_id: user?.id
      }
    });
  };

  return {
    handleContinueToDataCleansing,
  };
}; 