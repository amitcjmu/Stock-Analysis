import { useNavigate } from 'react-router-dom';
import { authApi } from '@/lib/api/auth';
import type { updateApiContext } from '@/config/api'
import { apiCall } from '@/config/api'
import { updateUserDefaults } from '@/lib/api/context';
import type { User, Client, Engagement, Flow, UserRegistrationResponse } from '../types';

// CC: Registration and API response interfaces
interface UserRegistrationData {
  email: string;
  password: string;
  full_name: string;
  role?: string;
  [key: string]: unknown;
}

interface ClientSwitchData extends Client {
  [key: string]: unknown;
}

interface EngagementSwitchData extends Engagement {
  [key: string]: unknown;
}

// CC: Function guard for preventing concurrent execution
interface GuardedFunction {
  (...args: unknown[]): Promise<unknown>;
  isRunning?: boolean;
}
import { tokenStorage, contextStorage, persistClientData, persistEngagementData, syncContextToIndividualKeys, clearAllStoredData } from '../storage'

export const useAuthService = (
  user: User | null,
  client: Client | null,
  engagement: Engagement | null,
  flow: Flow | null,
  setUser: (user: User | null) => void,
  setClient: (client: Client | null) => void,
  setEngagement: (engagement: Engagement | null) => void,
  setFlow: (flow: Flow | null) => void,
  setIsLoading: (loading: boolean) => void,
  setError: (error: string | null) => void,
  setIsLoginInProgress: (loading: boolean) => void,
  getAuthHeaders: () => Record<string, string>
): AuthActions => {
  const navigate = useNavigate();

  const logout = (): unknown => {
    // Clear auth and context data, but PRESERVE schema version
    // The schema version persists across sessions to detect data format changes
    tokenStorage.removeToken();
    tokenStorage.removeRefreshToken();
    tokenStorage.removeUser();
    contextStorage.clearContext();

    // Clear individual context keys
    try {
      localStorage.removeItem('auth_client');
      localStorage.removeItem('auth_engagement');
      localStorage.removeItem('auth_session');
      localStorage.removeItem('auth_client_id');
      localStorage.removeItem('auth_flow');
      localStorage.removeItem('user_data');
    } catch (error) {
      console.warn('Failed to clear context data:', error);
    }

    // Reset in-memory state
    setUser(null);
    setClient(null);
    setEngagement(null);
    setFlow(null);

    // Clear the initialization state so user can log back in
    try {
      sessionStorage.removeItem('auth_init_completed');
    } catch {
      // Ignore storage errors
    }

    navigate('/login');
  };

  const login = async (email: string, password: string): Promise<User> => {
    try {
      setIsLoading(true);
      setIsLoginInProgress(true);
      setError(null);

      // Starting parallel authentication flow...
      const startTime = performance.now();

      // CRITICAL PATH: Only login authentication is blocking
      const response = await authApi.login(email, password);

      if (response.status !== 'success' || !response.user || !response.token) {
        throw new Error(response.message || 'Login failed');
      }

      // Immediately set essential authentication data
      tokenStorage.setToken(response.token.access_token);
      // Store refresh token if provided
      if (response.token.refresh_token) {
        tokenStorage.setRefreshToken(response.token.refresh_token);
      }
      tokenStorage.setUser(response.user);
      setUser(response.user);

      // Login Step 1 - Authentication completed

      // PARALLEL ENHANCEMENT: Start all context-related operations simultaneously
      const parallelStartTime = performance.now();
      const [
        contextResult,
        cachedClientResult,
        cachedEngagementResult
      ] = await Promise.allSettled([
        // Essential: Get user context from backend
        apiCall('/api/v1/context/me', {}, false).catch(err => ({ error: err, source: 'context_api' })),
        // Enhancement: Check for cached client data
        Promise.resolve(localStorage.getItem('auth_client')).then(cached =>
          cached ? JSON.parse(cached) : null
        ).catch(() => null),
        // Enhancement: Check for cached engagement data
        Promise.resolve(localStorage.getItem('auth_engagement')).then(cached =>
          cached ? JSON.parse(cached) : null
        ).catch(() => null)
      ]);

      console.log('🚀 Parallel context operations completed:', {
        elapsed: `${Math.round(performance.now() - parallelStartTime)}ms`,
        contextStatus: contextResult.status,
        hasCachedClient: cachedClientResult.status === 'fulfilled' && cachedClientResult.value,
        hasCachedEngagement: cachedEngagementResult.status === 'fulfilled' && cachedEngagementResult.value
      });

      let actualUserRole = response.user.role;
      let finalContext = null;

      // BEST EFFORT: Use best available context (fresh > cached > defaults)
      if (contextResult.status === 'fulfilled' && !contextResult.value?.error) {
        // Fresh context from API - highest priority
        finalContext = contextResult.value;
        console.log('✅ Using fresh context from API');
      } else if (cachedClientResult.status === 'fulfilled' && cachedClientResult.value) {
        // Cached context - fallback option
        finalContext = {
          client: cachedClientResult.value,
          engagement: cachedEngagementResult.status === 'fulfilled' ? cachedEngagementResult.value : null,
          user: response.user
        };
        console.log('🔄 Using cached context as fallback');
      }

      // Apply context if available
      if (finalContext) {
        setClient(finalContext.client || null);
        setEngagement(finalContext.engagement || null);
        setFlow(finalContext.current_flow || null);

        contextStorage.setContext({
          client: finalContext.client,
          engagement: finalContext.engagement,
          flow: finalContext.current_flow,
          timestamp: Date.now(),
          source: finalContext.client ? 'login_optimized' : 'login_cached'
        });

        // Sync context to individual localStorage keys
        syncContextToIndividualKeys();

        // Update user role if provided by fresh context
        if (finalContext.user?.role && finalContext.user.role !== response.user.role) {
          actualUserRole = finalContext.user.role;
          const updatedUser = { ...response.user, role: finalContext.user.role };
          tokenStorage.setUser(updatedUser);
          setUser(updatedUser);
          console.log('🔐 User role updated from context:', actualUserRole);
        }

        console.log('🔐 Context applied:', {
          hasClient: !!finalContext.client,
          hasEngagement: !!finalContext.engagement,
          hasFlow: !!finalContext.current_flow,
          source: finalContext.client ? 'api' : 'cache'
        });
      }

      // BACKGROUND ENHANCEMENT: Update user defaults non-blocking
      if (finalContext?.client?.id) {
        updateUserDefaults({
          client_id: finalContext.client.id,
          engagement_id: finalContext.engagement?.id
        }).catch(error => {
          console.warn('⚠️ Background user defaults update failed (non-blocking):', error);
        });
      }

      // IMMEDIATE NAVIGATION: Don't wait for background operations
      const redirectPath = actualUserRole === 'admin'
        ? '/admin/dashboard'
        : (tokenStorage.getRedirectPath() || '/');
      tokenStorage.clearRedirectPath();

      const totalTime = Math.round(performance.now() - startTime);
      console.log('🔐 Login completed - Performance metrics:', {
        totalTime: `${totalTime}ms`,
        improvement: totalTime < 1000 ? `~${Math.round((2000 - totalTime) / 2000 * 100)}% faster` : 'within target',
        redirectPath,
        finalRole: actualUserRole
      });

      // Navigate immediately - context will continue loading in background
      setTimeout(() => {
        navigate(redirectPath);
      }, 50); // Minimal delay for state updates

      return response.user;
    } catch (error) {
      setError((error as Error).message);
      throw error;
    } finally {
      setIsLoading(false);
      setIsLoginInProgress(false);
    }
  };

  const register = async (userData: UserRegistrationData): Promise<UserRegistrationResponse> => {
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

  const switchClient = async (clientId: string, clientData?: ClientSwitchData): Promise<void> => {
    try {
      console.log('🔍 switchClient - Starting with:', { clientId, hasClientData: !!clientData });

      let fullClientData = clientData;

      if (!fullClientData) {
        console.log('🔍 switchClient - Fetching client data from API');
        const response = await apiCall(`/api/v1/context-establishment/clients`, {
          method: 'GET',
          headers: getAuthHeaders()
        }, false); // Don't include context - we're establishing it
        console.log('🔍 switchClient - Got clients response:', response);
        fullClientData = response.clients?.find((c: Client) => c.id === clientId);
      }

      if (!fullClientData) {
        throw new Error('Client data not found');
      }

      console.log('🔍 switchClient - Setting client:', fullClientData);
      setClient(fullClientData);
      persistClientData(fullClientData);

      // API context will be updated automatically by useApiContextSync hook
      // No need to call updateApiContext manually here

      console.log('🔍 switchClient - Fetching engagements for client:', clientId);
      const engagementsResponse = await apiCall(`/api/v1/context-establishment/engagements?client_id=${clientId}`, {
        method: 'GET',
        headers: getAuthHeaders()
      }, false); // Don't include context - we're establishing it

      console.log('🔍 switchClient - Got engagements response:', engagementsResponse);

      if (engagementsResponse?.engagements && engagementsResponse.engagements.length > 0) {
        const defaultEngagement = engagementsResponse.engagements[0];
        console.log('🔍 switchClient - Switching to default engagement:', defaultEngagement.id);
        await switchEngagement(defaultEngagement.id, defaultEngagement);
        console.log('🔍 switchClient - switchEngagement completed');
      } else {
        console.log('🔍 switchClient - No engagements found, clearing engagement/flow');
        setEngagement(null);
        setFlow(null);
        localStorage.removeItem('auth_engagement');
        localStorage.removeItem('auth_flow');

        try {
          console.log('🔍 switchClient - Updating user defaults');
          const result = await updateUserDefaults({ client_id: clientId });
          // The API returns a success response with message
          if (result && result.message) {
            console.log('✅ Updated user default client:', clientId);
          } else {
            console.warn('⚠️ Failed to update user default client (non-blocking):', result);
          }
        } catch (defaultError) {
          console.warn('⚠️ Failed to update user default client (non-blocking):', defaultError);
        }
      }

      console.log('🔍 switchClient - Completed successfully');

      // CRITICAL: Sync context to individual localStorage keys for new API client
      syncContextToIndividualKeys();

    } catch (error) {
      console.error('Error switching client:', error);
      throw error;
    }
  };

  const switchEngagement = async (engagementId: string, engagementData?: EngagementSwitchData): Promise<void> => {
    try {
      console.log('🔍 switchEngagement - Starting with:', { engagementId, hasEngagementData: !!engagementData });

      let fullEngagementData = engagementData;

      if (!fullEngagementData && client) {
        try {
          console.log('🔍 switchEngagement - Fetching engagement data from API');
          const response = await apiCall(`/api/v1/context-establishment/engagements?client_id=${client.id}`, {
            method: 'GET',
            headers: getAuthHeaders()
          }, false); // Don't include context - we're establishing it
          console.log('🔍 switchEngagement - Got engagements response:', response);
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

      console.log('🔍 switchEngagement - Setting engagement:', fullEngagementData);
      setEngagement(fullEngagementData);
      persistEngagementData(fullEngagementData);

      console.log('🔍 switchEngagement - Creating flow data');
      const flowData = {
        id: fullEngagementData.id,
        name: `${fullEngagementData.name} Flow`,
        flow_type: 'discovery',
        engagement_id: engagementId,
        status: 'active',
        auto_created: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      console.log('🔍 switchEngagement - Setting flow:', flowData);
      setFlow(flowData);

      // API context will be updated automatically by useApiContextSync hook
      // No need to call updateApiContext manually here

      try {
        console.log('🔍 switchEngagement - Updating user defaults');
        const effectiveClientId = fullEngagementData?.client_id;
        if (effectiveClientId && fullEngagementData?.client_id === effectiveClientId) {
          const result = await updateUserDefaults({
            client_id: effectiveClientId,
            engagement_id: engagementId
          });
          // The API returns a success response with message
          if (result && result.message) {
            console.log('✅ Updated user defaults - client:', effectiveClientId, 'engagement:', engagementId);
          } else {
            console.warn('⚠️ Failed to update user defaults (non-blocking):', result);
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

      console.log('🔍 switchEngagement - Completed successfully');

      // CRITICAL: Sync context to individual localStorage keys for new API client
      syncContextToIndividualKeys();

    } catch (error) {
      console.error('Error switching engagement:', error);
      throw error;
    }
  };

  const switchFlow = async (flowId: string, flowData?: Flow) =>  {
    try {
      console.log('🔄 Switching to flow:', flowId, flowData);

      let fullFlowData = flowData;

      if (!fullFlowData) {
        // For now, just create a basic flow object
        // In a real implementation, you might fetch from `/flows/${flowId}`
        fullFlowData = {
          id: flowId,
          name: `Flow ${flowId.slice(-8)}`,
          status: 'active',
          engagement_id: engagement?.id
        };
      }

      setFlow(fullFlowData);

      // API context will be updated automatically by useApiContextSync hook
      // No need to call updateApiContext manually here

      console.log('✅ Switched to flow:', fullFlowData.id);
    } catch (error) {
      console.error('Error switching flow:', error);
      throw error;
    }
  };

  // Debouncing for fetchDefaultContext to prevent rapid successive calls
  let fetchDefaultContextTimer: NodeJS.Timeout | null = null;
  let lastFetchDefaultContextTime = 0;
  const FETCH_DEFAULT_CONTEXT_DEBOUNCE = 1000; // 1 second debounce

  const fetchDefaultContext = async (): Promise<void> => {
    try {
      const startTime = performance.now();
      console.log('🚀 fetchDefaultContext - Starting parallel context fetch...');

      // Verify we have authentication before making API calls
      const token = tokenStorage.getToken();
      if (!token || !user) {
        console.warn('⚠️ fetchDefaultContext - No token or user available, skipping context fetch');
        return;
      }

      // Debouncing logic
      const now = Date.now();
      if (now - lastFetchDefaultContextTime < FETCH_DEFAULT_CONTEXT_DEBOUNCE) {
        console.log('🔄 fetchDefaultContext debounced, skipping rapid call');
        return;
      }
      lastFetchDefaultContextTime = now;

      // Clear any pending debounced calls
      if (fetchDefaultContextTimer) {
        clearTimeout(fetchDefaultContextTimer);
        fetchDefaultContextTimer = null;
      }

      // Early return if we already have complete context
      if (client && engagement) {
        console.log('✅ Complete context already available, skipping fetch');
        return;
      }

      // Add a guard to prevent concurrent executions
      if ((fetchDefaultContext as GuardedFunction).isRunning) {
        console.log('🔄 fetchDefaultContext already running, skipping');
        return;
      }

      (fetchDefaultContext as GuardedFunction).isRunning = true;

      // PARALLEL EXECUTION: Fetch clients and check cache simultaneously
      const [
        clientsResult,
        cachedClientResult,
        cachedEngagementResult
      ] = await Promise.allSettled([
        // Fresh data: Get available clients
        apiCall('/api/v1/context-establishment/clients', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${tokenStorage.getToken()}`,
            'Content-Type': 'application/json'
          }
        }, false),
        // Cached data: Check for stored client preference
        Promise.resolve(localStorage.getItem('auth_client_id')),
        // Cached data: Check for stored engagement data
        Promise.resolve(localStorage.getItem('auth_engagement')).then(cached =>
          cached ? JSON.parse(cached) : null
        ).catch(() => null)
      ]);

      console.log('🚀 Parallel context fetch completed:', {
        elapsed: `${Math.round(performance.now() - startTime)}ms`,
        clientsStatus: clientsResult.status,
        hasCachedClientId: cachedClientResult.status === 'fulfilled' && cachedClientResult.value,
        hasCachedEngagement: cachedEngagementResult.status === 'fulfilled' && cachedEngagementResult.value
      });

      // Handle clients response
      if (clientsResult.status !== 'fulfilled' || !clientsResult.value?.clients?.length) {
        console.warn('No clients available or failed to fetch clients');
        return;
      }

      const clientsResponse = clientsResult.value;
      console.log(`🚀 Found ${clientsResponse.clients.length} available clients`);

      // INTELLIGENT CLIENT SELECTION: Use cached preference or default
      let targetClient = null;
      const storedClientId = cachedClientResult.status === 'fulfilled' ? cachedClientResult.value : null;

      if (storedClientId) {
        targetClient = clientsResponse.clients.find(c => c.id === storedClientId);
        if (targetClient) {
          console.log(`✅ Using cached client preference: ${targetClient.name}`);
        } else {
          console.log(`🔄 Cached client ${storedClientId} not found in available clients`);
          localStorage.removeItem('auth_client_id');
        }
      }

      if (!targetClient && !client) {
        targetClient = clientsResponse.clients[0];
        console.log(`🚀 Using first available client as default: ${targetClient.name}`);
      }

      // CLIENT CONTEXT UPDATE: Only switch if needed
      if (targetClient && (!client || client.id !== targetClient.id)) {
        console.log('🚀 Switching to target client:', targetClient.id);

        // PARALLEL ENGAGEMENT FETCH: Start engagement fetch while setting client
        const engagementPromise = apiCall(`/api/v1/context-establishment/engagements?client_id=${targetClient.id}`, {
          method: 'GET',
          headers: getAuthHeaders()
        }, false).catch(error => ({ error, source: 'engagements' }));

        // Update client immediately
        setClient(targetClient);
        persistClientData(targetClient);

        // Await engagement data
        const engagementsResponse = await engagementPromise;

        if (!engagementsResponse.error && engagementsResponse?.engagements?.length > 0) {
          const defaultEngagement = engagementsResponse.engagements[0];
          console.log('🚀 Setting default engagement:', defaultEngagement.id);

          await switchEngagement(defaultEngagement.id, defaultEngagement);
        } else {
          console.log('🚀 No engagements available, clearing engagement/flow');
          setEngagement(null);
          setFlow(null);
          localStorage.removeItem('auth_engagement');
          localStorage.removeItem('auth_flow');

          // BACKGROUND USER DEFAULTS UPDATE: Non-blocking
          updateUserDefaults({ client_id: targetClient.id }).catch(error => {
            console.warn('⚠️ Background user defaults update failed:', error);
          });
        }
      } else if (targetClient && !engagement) {
        // CLIENT EXISTS, MISSING ENGAGEMENT: Use cached or fetch fresh
        const cachedEngagement = cachedEngagementResult.status === 'fulfilled' ? cachedEngagementResult.value : null;

        if (cachedEngagement && cachedEngagement.client_id === targetClient.id) {
          console.log('✅ Using cached engagement:', cachedEngagement.name);
          setEngagement(cachedEngagement);
          // Create flow data from engagement
          const flowData = {
            id: cachedEngagement.id,
            name: `${cachedEngagement.name} Flow`,
            flow_type: 'discovery',
            engagement_id: cachedEngagement.id,
            status: 'active',
            auto_created: true
          };
          setFlow(flowData);
        } else {
          console.log('🚀 Fetching fresh engagements for existing client');
          try {
            const engagementsResponse = await apiCall(`/api/v1/context-establishment/engagements?client_id=${targetClient.id}`, {
              method: 'GET',
              headers: getAuthHeaders()
            }, false);

            if (engagementsResponse?.engagements?.length > 0) {
              await switchEngagement(engagementsResponse.engagements[0].id, engagementsResponse.engagements[0]);
            }
          } catch (error) {
            console.warn('⚠️ Failed to fetch engagements for existing client:', error);
          }
        }
      }

      // FINAL SYNC: Ensure context is properly synchronized
      syncContextToIndividualKeys();

      const totalTime = Math.round(performance.now() - startTime);
      console.log('✅ fetchDefaultContext completed:', {
        totalTime: `${totalTime}ms`,
        hasClient: !!client,
        hasEngagement: !!engagement,
        improvement: totalTime < 1000 ? 'optimized' : 'standard'
      });

    } catch (error: unknown) {
      console.error('Error fetching default context:', error);
      if (error.message === 'Unauthorized' || error.status === 401) {
        console.log('🔄 Authentication expired during context fetch');
        tokenStorage.removeToken();
        setUser(null);
        navigate('/login');
      } else {
        console.warn('⚠️ Context fetch failed but continuing with existing authentication:', error.message);
        // Don't fail the entire auth flow for context fetch errors
        // The user is still authenticated, just missing context
      }
    } finally {
      (fetchDefaultContext as GuardedFunction).isRunning = false;
    }
  };

  // Debounced version of fetchDefaultContext for use in hooks that need delayed execution
  const debouncedFetchDefaultContext = (): unknown => {
    if (fetchDefaultContextTimer) {
      clearTimeout(fetchDefaultContextTimer);
    }

    fetchDefaultContextTimer = setTimeout(() => {
      fetchDefaultContext();
    }, FETCH_DEFAULT_CONTEXT_DEBOUNCE);
  };

  return {
    login,
    register,
    logout,
    switchClient,
    switchEngagement,
    switchFlow,
    fetchDefaultContext,
    debouncedFetchDefaultContext
  };
};
