import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiCall, updateApiContext } from '@/config/api';
import { User, Client, Engagement, Session } from '../types';
import { tokenStorage, contextStorage, getStoredClientData, getStoredEngagementData, getStoredSessionData } from '../storage';
import { migrateAuthData } from '@/utils/authDataMigration';

interface UseAuthInitializationProps {
  setUser: (user: User | null) => void;
  setClient: (client: Client | null) => void;
  setEngagement: (engagement: Engagement | null) => void;
  setSession: (session: Session | null) => void;
  setIsLoading: (loading: boolean) => void;
  switchClient: (clientId: string, clientData?: Client) => Promise<void>;
  fetchDefaultContext: () => Promise<void>;
}

export const useAuthInitialization = ({
  setUser,
  setClient,
  setEngagement,
  setSession,
  setIsLoading,
  switchClient,
  fetchDefaultContext
}: UseAuthInitializationProps) => {
  const navigate = useNavigate();

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setIsLoading(true);
        
        // Run auth data migration first
        migrateAuthData();
        
        const token = tokenStorage.getToken();
        if (!token) {
          console.log('🔄 No authentication token found, redirecting to login');
          setUser(null);
          setClient(null);
          setEngagement(null);
          setSession(null);
          setIsLoading(false);
          navigate('/login');
          return;
        }

        let userInfo = null;
        let needsContextEstablishment = false;
        
        try {
          userInfo = await apiCall('/context/me', {}, false);
        } catch (error: any) {
          if (error.message === 'Not Found' || error.status === 404) {
            console.log('🔄 User exists but needs context establishment');
            needsContextEstablishment = true;
          } else if (error.message === 'Unauthorized' || error.status === 401) {
            console.log('🔄 Token is invalid, clearing authentication and redirecting to login');
            tokenStorage.removeToken();
            setUser(null);
            setClient(null);
            setEngagement(null);
            setSession(null);
            setIsLoading(false);
            navigate('/login');
            return;
          } else {
            console.error('🔄 Unexpected error from /context/me endpoint:', error);
            needsContextEstablishment = true;
          }
        }

        if (userInfo && userInfo.user && userInfo.user.id) {
          setUser(userInfo.user);
          
          if (userInfo.client && userInfo.engagement && userInfo.session) {
            console.log('🔄 Using context from /context/me endpoint:', {
              client: userInfo.client.name,
              engagement: userInfo.engagement.name,
              session: userInfo.session.id
            });
            
            setClient(userInfo.client);
            setEngagement(userInfo.engagement);
            setSession(userInfo.session);
            
            updateApiContext({ 
              user: userInfo.user, 
              client: userInfo.client, 
              engagement: userInfo.engagement, 
              session: userInfo.session 
            });
            
            localStorage.setItem('auth_client', JSON.stringify(userInfo.client));
            localStorage.setItem('auth_engagement', JSON.stringify(userInfo.engagement));
            localStorage.setItem('auth_session', JSON.stringify(userInfo.session));
            
            setIsLoading(false);
            return;
          }
          
          const storedClient = getStoredClientData();
          const storedEngagement = getStoredEngagementData();
          const storedSession = getStoredSessionData();
          
          if (storedClient && storedClient.id && storedClient.name) {
            console.log('🔄 Restoring client from localStorage:', {
              client: storedClient.name,
              id: storedClient.id
            });
            
            setClient(storedClient);
            
            if (storedEngagement && storedSession && storedEngagement.id && storedSession.id) {
              console.log('🔄 Restoring full context from localStorage:', {
                engagement: storedEngagement.name,
                session: storedSession.id
              });
              
              setEngagement(storedEngagement);
              setSession(storedSession);
              
              updateApiContext({ 
                user: userInfo.user, 
                client: storedClient, 
                engagement: storedEngagement, 
                session: storedSession 
              });
              
              setIsLoading(false);
              return;
            }
            
            console.log('🔄 Client restored, fetching engagement for client:', storedClient.name);
            await switchClient(storedClient.id, storedClient);
            setIsLoading(false);
            return;
          }
          
          console.log('🔄 No context available, fetching defaults...');
          await fetchDefaultContext();
        } else if (needsContextEstablishment) {
          console.log('🔄 User authenticated but needs context establishment');
          const storedUser = tokenStorage.getUser();
          if (storedUser) {
            setUser(storedUser);
            console.log('🔄 Using stored user info:', storedUser);
          }
          
          setClient(null);
          setEngagement(null);
          setSession(null);
        } else {
          console.log('🔄 Authentication failed, redirecting to login');
          tokenStorage.removeToken();
          setUser(null);
          setClient(null);
          setEngagement(null);
          setSession(null);
          navigate('/login');
        }
      } catch (error: any) {
        console.error('Auth initialization error:', error);
        if (error.message === 'Unauthorized' || error.status === 401) {
          console.log('🔄 Authentication error, redirecting to login');
          tokenStorage.removeToken();
          setUser(null);
          setClient(null);
          setEngagement(null);
          setSession(null);
          navigate('/login');
        } else {
          console.log('🔄 Network or other error during auth initialization:', error);
          setUser(null);
        }
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);
};