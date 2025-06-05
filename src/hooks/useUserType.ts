import { useState, useEffect } from 'react';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

interface UserType {
  user_id: string;
  is_demo_admin: boolean;
  is_mock_user: boolean;
  should_see_mock_data_only: boolean;
  access_level: 'demo' | 'production';
}

interface UserTypeResponse {
  status: string;
  user_type: UserType;
}

export const useUserType = () => {
  const [userType, setUserType] = useState<UserType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { getAuthHeaders, isAuthenticated } = useAuth();

  const fetchUserType = async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await apiCall('/api/v1/auth/user-type', {
        headers: getAuthHeaders()
      });

      if (response.status === 'success') {
        setUserType(response.user_type);
      } else {
        // Fallback to demo mode for safety
        setUserType({
          user_id: 'unknown',
          is_demo_admin: true,
          is_mock_user: false,
          should_see_mock_data_only: true,
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
        is_mock_user: false,
        should_see_mock_data_only: true,
        access_level: 'demo'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserType();
  }, [isAuthenticated]);

  return {
    userType,
    loading,
    error,
    refetch: fetchUserType,
    isDemoUser: userType?.is_demo_admin || userType?.is_mock_user || false,
    shouldUseMockData: userType?.should_see_mock_data_only || false,
    accessLevel: userType?.access_level || 'demo'
  };
};