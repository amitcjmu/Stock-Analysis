import { useState, useCallback } from 'react'
import { useEffect } from 'react'
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

interface UserType {
  user_id: string;
  is_demo_admin: boolean;
  client_account_id: string;
  engagement_id: string;
  is_demo_tenant: boolean;
  access_level: 'demo' | 'production';
}

interface UserTypeResponse {
  status: string;
  user_type: UserType;
}

export const useUserType = (): JSX.Element => {
  const [userType, setUserType] = useState<UserType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { getAuthHeaders, isAuthenticated } = useAuth();

  const fetchUserType = useCallback(async (): Promise<void> => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await apiCall('/auth/user-type', {
        headers: getAuthHeaders()
      });

      if (response.status === 'success') {
        setUserType(response.user_type);
      } else {
        // Fallback to demo mode for safety
        setUserType({
          user_id: 'unknown',
          is_demo_admin: true,
          client_account_id: 'demo',
          engagement_id: 'demo',
          is_demo_tenant: true,
          access_level: 'demo'
        });
      }
    } catch (err) {
      console.error('Failed to fetch user type:', err);
      setError('Failed to determine user access level');

      // Fallback to demo mode for safety
      setUserType({
        user_id: 'unknown',
        is_demo_admin: true,
        client_account_id: 'demo',
        engagement_id: 'demo',
        is_demo_tenant: true,
        access_level: 'demo'
      });
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, isAuthenticated]);

  useEffect(() => {
    fetchUserType();
  }, [fetchUserType]);

  return {
    userType,
    loading,
    error,
    refetch: fetchUserType,
    isDemoUser: userType?.is_demo_admin || userType?.is_demo_tenant || false,
    shouldUseMockData: userType?.is_demo_tenant || false,
    accessLevel: userType?.access_level || 'demo'
  };
};
