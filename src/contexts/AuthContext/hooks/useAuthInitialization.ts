import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUserContext } from '@/lib/api/context';
import { User, Client, Engagement, Flow } from '../types';
import { tokenStorage } from '../storage';

interface UseAuthInitializationProps {
  setUser: (user: User | null) => void;
  setClient: (client: Client | null) => void;
  setEngagement: (engagement: Engagement | null) => void;
  setFlow: (flow: Flow | null) => void;
  setIsLoading: (loading: boolean) => void;
  switchClient: (clientId: string, clientData?: Client) => Promise<void>;
  fetchDefaultContext: () => Promise<void>;
}

export const useAuthInitialization = ({
  setUser,
  setClient,
  setEngagement,
  setFlow,
  setIsLoading,
  switchClient,
  fetchDefaultContext
}: UseAuthInitializationProps) => {
  const navigate = useNavigate();

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setIsLoading(true);
        
        const token = tokenStorage.getToken();
        if (!token) {
          console.log('🔄 No authentication token found, redirecting to login');
          setUser(null);
          setClient(null);
          setEngagement(null);
          setFlow(null);
          setIsLoading(false);
          navigate('/login');
          return;
        }

        // Try to get user context from the modern API
        try {
          const userContext = await getUserContext();
          
          if (userContext?.user) {
            setUser(userContext.user);
            
            if (userContext.client) {
              setClient(userContext.client);
            }
            
            if (userContext.engagement) {
              setEngagement(userContext.engagement);
            }
            
            if (userContext.flow) {
              setFlow(userContext.flow);
            }
            
            console.log('✅ User context loaded from API');
          } else {
            // If no context from API, try to use stored user and fetch defaults
            const storedUser = tokenStorage.getUser();
            if (storedUser) {
              setUser(storedUser);
              await fetchDefaultContext();
            } else {
              throw new Error('No user data available');
            }
          }
        } catch (error: any) {
          if (error.status === 401) {
            console.log('🔄 Token is invalid, clearing authentication and redirecting to login');
            tokenStorage.removeToken();
            setUser(null);
            setClient(null);
            setEngagement(null);
            setFlow(null);
            navigate('/login');
            return;
          } else {
            console.error('🔄 Error getting user context:', error);
            // Try to use stored user as fallback
            const storedUser = tokenStorage.getUser();
            if (storedUser) {
              setUser(storedUser);
              await fetchDefaultContext();
            } else {
              throw error;
            }
          }
        }
      } catch (error: any) {
        console.error('Auth initialization error:', error);
        tokenStorage.removeToken();
        setUser(null);
        setClient(null);
        setEngagement(null);
        setFlow(null);
        navigate('/login');
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);
};