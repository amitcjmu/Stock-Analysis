/**
 * useFlowParams Hook
 * Extracts URL parameters and authentication context
 */

import { useSearchParams, useParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface UseFlowParamsReturn {
  applicationId: string | null;
  flowId: string | null;
  client: ReturnType<typeof useAuth>['client'];
  engagement: ReturnType<typeof useAuth>['engagement'];
  user: ReturnType<typeof useAuth>['user'];
}

/**
 * Hook for extracting URL parameters and auth context
 */
export const useFlowParams = (): UseFlowParamsReturn => {
  const [searchParams] = useSearchParams();
  const routeParams = useParams<{ flowId?: string; applicationId?: string }>();
  const { client, engagement, user } = useAuth();

  // Get application ID and flow ID from URL params (route params take precedence over query params)
  const applicationId = routeParams.applicationId || searchParams.get('applicationId');
  const flowId = routeParams.flowId || searchParams.get('flowId');

  return {
    applicationId,
    flowId,
    client,
    engagement,
    user,
  };
};
