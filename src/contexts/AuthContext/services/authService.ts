import { useNavigate } from 'react-router-dom';
import { authApi } from '@/lib/api/auth';
import { apiCall, updateApiContext } from '@/config/api';
import { updateUserDefaults } from '@/lib/api/context';
import { User, Client, Engagement, Session } from '../types';
import { tokenStorage, contextStorage, persistClientData, persistEngagementData, persistSessionData } from '../storage';

export const useAuthService = (
  user: User | null,
  client: Client | null,
  engagement: Engagement | null,
  session: Session | null,
  setUser: (user: User | null) => void,
  setClient: (client: Client | null) => void,
  setEngagement: (engagement: Engagement | null) => void,
  setSession: (session: Session | null) => void,
  setIsLoading: (loading: boolean) => void,
  setError: (error: string | null) => void,
  setIsLoginInProgress: (loading: boolean) => void,
  getAuthHeaders: () => Record<string, string>
) => {
  const navigate = useNavigate();

  const logout = () => {
    tokenStorage.removeToken();
    tokenStorage.setUser(null);
    contextStorage.clearContext();
    setUser(null);
    setClient(null);
    setEngagement(null);
    setSession(null);
    navigate('/login');
  };

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setIsLoginInProgress(true);
      setError(null);

      const response = await authApi.login(email, password);

      if (response.status !== 'success' || !response.user || !response.token) {
        throw new Error(response.message || 'Login failed');
      }

      tokenStorage.setToken(response.token.access_token);
      tokenStorage.setUser(response.user);
      setUser(response.user);

      console.log('🔐 Login Step 1 - Initial user set:', {
        user: response.user,
        role: response.user.role,
        token: response.token.access_token.substring(0, 20) + '...'
      });

      await new Promise(resolve => setTimeout(resolve, 100));

      let actualUserRole = response.user.role;
      try {
        const context = await apiCall('/context/me', {}, false);
        console.log('🔐 Login Step 2 - Context from /me:', context);
        
        if (context) {
          setClient(context.client || null);
          setEngagement(context.engagement || null);
          setSession(context.session || null);
          
          contextStorage.setContext({
            client: context.client,
            engagement: context.engagement,
            session: context.session,
            timestamp: Date.now(),
            source: 'login_backend'
          });
          
          if (context.user && context.user.role) {
            actualUserRole = context.user.role;
            const updatedUser = { ...response.user, role: context.user.role };
            tokenStorage.setUser(updatedUser);
            setUser(updatedUser);
            
            console.log('🔐 Login Step 3 - User updated with context role:', {
              updatedUser,
              actualUserRole,
              isAdminCheck: updatedUser.role === 'admin'
            });
          }
          
          console.log('🔐 Login Step 3 - Context set from backend:', {
            client: context.client,
            engagement: context.engagement,
            session: context.session
          });
        }
      } catch (contextError) {
        console.warn('Failed to load user context, using defaults:', contextError);
        setClient(null);
        setEngagement(null);
        setSession(null);
        contextStorage.clearContext();
      }

      const redirectPath = actualUserRole === 'admin' 
        ? '/admin/dashboard' 
        : (tokenStorage.getRedirectPath() || '/');
      tokenStorage.clearRedirectPath();
      
      console.log('🔐 Login Step 4 - Redirect decision:', {
        actualUserRole,
        redirectPath,
        isAdminRole: actualUserRole === 'admin'
      });
      
      setTimeout(() => {
        console.log('🔐 Login Step 5 - Navigating to:', redirectPath);
        navigate(redirectPath);
      }, 200);

      return response.user;
    } catch (error) {
      setError((error as Error).message);
      throw error;
    } finally {
      setIsLoading(false);
      setIsLoginInProgress(false);
    }
  };

  const register = async (userData: any) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await authApi.register(userData);

      if (response.status !== 'success') {
        throw new Error(response.message || 'Registration failed');
      }

      return response;
    } catch (error) {
      setError((error as Error).message);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const switchClient = async (clientId: string, clientData?: any) => {
    try {
      console.log('🔄 Switching to client:', clientId);
      
      let fullClientData = clientData;
      
      if (!fullClientData) {
        const response = await apiCall(`/context/clients/${clientId}`, {
          method: 'GET',
          headers: getAuthHeaders()
        });
        fullClientData = response.client;
      }
      
      if (!fullClientData) {
        throw new Error('Client data not found');
      }
      
      setClient(fullClientData);
      persistClientData(fullClientData);
      
      updateApiContext({ 
        user, 
        client: fullClientData, 
        engagement, 
        session 
      });
      
      const engagementsResponse = await apiCall(`/context/clients/${clientId}/engagements`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      
      if (engagementsResponse?.engagements && engagementsResponse.engagements.length > 0) {
        const defaultEngagement = engagementsResponse.engagements[0];
        await switchEngagement(defaultEngagement.id, defaultEngagement);
      } else {
        setEngagement(null);
        setSession(null);
        localStorage.removeItem('auth_engagement');
        localStorage.removeItem('auth_session');
        
        try {
          const result = await updateUserDefaults({ client_id: clientId });
          if (result.success) {
            console.log('✅ Updated user default client:', clientId);
          } else {
            console.warn('⚠️ Failed to update user default client (non-blocking):', result.message);
          }
        } catch (defaultError) {
          console.warn('⚠️ Failed to update user default client (non-blocking):', defaultError);
        }
      }
      
    } catch (error) {
      console.error('Error switching client:', error);
      throw error;
    }
  };

  const switchEngagement = async (engagementId: string, engagementData?: any) => {
    try {
      console.log('🔄 Switching to engagement:', engagementId, 'with data:', engagementData);
      
      let fullEngagementData = engagementData;
      
      if (!fullEngagementData && client) {
        try {
          const response = await apiCall(`/context/clients/${client.id}/engagements`, {
            method: 'GET',
            headers: getAuthHeaders()
          });
          if (response.engagements) {
            fullEngagementData = response.engagements.find(e => e.id === engagementId);
          }
        } catch (fetchError) {
          console.warn('Failed to fetch engagement data:', fetchError);
        }
      }
      
      if (!fullEngagementData) {
        throw new Error('Engagement data not found');
      }
      
      setEngagement(fullEngagementData);
      persistEngagementData(fullEngagementData);
      
      updateApiContext({ 
        user, 
        client, 
        engagement: fullEngagementData, 
        session 
      });
      
      const sessionData = {
        id: fullEngagementData.id,
        name: `${fullEngagementData.name} Session`,
        session_display_name: `${fullEngagementData.name} Session`,
        session_name: `${fullEngagementData.name.toLowerCase().replace(/\s+/g, '_')}_session`,
        engagement_id: engagementId,
        is_default: true,
        status: 'active',
        session_type: 'data_import',
        auto_created: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      setSession(sessionData);
      persistSessionData(sessionData);
      
      updateApiContext({ 
        user, 
        client, 
        engagement: fullEngagementData, 
        session: sessionData 
      });
      
      try {
        const effectiveClientId = fullEngagementData?.client_id;
        if (effectiveClientId && fullEngagementData?.client_id === effectiveClientId) {
          const result = await updateUserDefaults({
            client_id: effectiveClientId,
            engagement_id: engagementId
          });
          if (result.success) {
            console.log('✅ Updated user defaults - client:', effectiveClientId, 'engagement:', engagementId);
          } else {
            console.warn('⚠️ Failed to update user defaults (non-blocking):', result.message);
          }
        } else {
          console.warn('⚠️ Skipping user defaults update - engagement data missing client_id:', {
            engagementData: fullEngagementData,
            engagementId
          });
        }
      } catch (defaultError) {
        console.warn('⚠️ Failed to update user defaults (non-blocking):', defaultError);
      }
      
    } catch (error) {
      console.error('Error switching engagement:', error);
      throw error;
    }
  };

  const switchSession = async (sessionId: string) => {
    try {
      const response = await apiCall(`/sessions/${sessionId}`);
      if (response) {
        setSession(response);
      }
    } catch (error) {
      console.error('Error switching session:', error);
      throw error;
    }
  };

  const fetchDefaultContext = async () => {
    try {
      if (client && engagement && session) {
        console.log('🔄 Context already complete, skipping default fetch');
        return;
      }
      
      console.log('🔄 Fetching default context...');
      
      const clientsResponse = await apiCall('/api/v1/context/clients', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${tokenStorage.getToken()}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!clientsResponse?.clients || clientsResponse.clients.length === 0) {
        console.warn('No clients available');
        return;
      }
      
      console.log(`🔄 Found ${clientsResponse.clients.length} available clients:`, 
        clientsResponse.clients.map(c => c.name));
      
      const storedClientId = localStorage.getItem('auth_client_id');
      let targetClient = null;
      
      if (storedClientId) {
        targetClient = clientsResponse.clients.find(c => c.id === storedClientId);
        if (targetClient) {
          console.log(`🔄 Using stored client preference: ${targetClient.name}`);
        } else {
          console.log(`🔄 Stored client ${storedClientId} not found in available clients`);
          localStorage.removeItem('auth_client_id');
        }
      }
      
      if (!targetClient && !client) {
        targetClient = clientsResponse.clients[0];
        console.log(`🔄 Using first available client as default: ${targetClient.name}`);
      }
      
      if (targetClient && (!client || client.id !== targetClient.id)) {
        await switchClient(targetClient.id, targetClient);
      }
      
    } catch (error: any) {
      console.error('Error fetching default context:', error);
      if (error.message === 'Unauthorized' || error.status === 401) {
        console.log('🔄 Authentication expired during context fetch');
        tokenStorage.removeToken();
        setUser(null);
        navigate('/login');
      }
    }
  };

  return {
    login,
    register,
    logout,
    switchClient,
    switchEngagement,
    switchSession,
    fetchDefaultContext
  };
};