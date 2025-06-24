import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, User } from '@/lib/api/auth';
import { apiCall, updateApiContext } from '@/config/api';

interface TokenStorage {
  getToken: () => string | null;
  setToken: (token: string) => void;
  getUser: () => User | null;
  setUser: (user: User) => void;
  getRedirectPath: () => string | null;
  setRedirectPath: (path: string) => void;
  clearRedirectPath: () => void;
  removeToken: () => void;
}

export interface Client {
  id: string;
  name: string;
  status: string;
}

export interface Engagement {
  id: string;
  name: string;
  status: string;
}

export interface Session {
  id: string;
  name: string;
  status: string;
}

const tokenStorage: TokenStorage = {
  getToken: () => localStorage.getItem('auth_token'),
  setToken: (token) => localStorage.setItem('auth_token', token),
  getUser: () => {
    const userData = localStorage.getItem('user_data');
    try {
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error("Failed to parse user data from localStorage", error);
      return null;
    }
  },
  setUser: (user) => localStorage.setItem('user_data', JSON.stringify(user)),
  getRedirectPath: () => localStorage.getItem('redirect_path'),
  setRedirectPath: (path) => localStorage.setItem('redirect_path', path),
  clearRedirectPath: () => localStorage.removeItem('redirect_path'),
  removeToken: () => localStorage.removeItem('auth_token'),
};



// --- Context Persistence ---
const CONTEXT_STORAGE_KEY = 'user_context_selection';

const contextStorage = {
  getContext: () => {
    const contextData = localStorage.getItem(CONTEXT_STORAGE_KEY);
    try {
      return contextData ? JSON.parse(contextData) : null;
    } catch (error) {
      console.error("Failed to parse context data from localStorage", error);
      return null;
    }
  },
  setContext: (context: any) => {
    localStorage.setItem(CONTEXT_STORAGE_KEY, JSON.stringify(context));
  },
  clearContext: () => {
    localStorage.removeItem(CONTEXT_STORAGE_KEY);
  }
};



interface AuthContextType {
  user: User | null;
  client: Client | null;
  engagement: Engagement | null;
  session: Session | null;
  isLoading: boolean;
  error: string | null;
  isDemoMode: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (userData: any) => Promise<any>;
  logout: () => void;
  switchClient: (clientId: string, clientData?: Client) => Promise<void>;
  switchEngagement: (engagementId: string, engagementData?: Engagement) => Promise<void>;
  switchSession: (sessionId: string) => Promise<void>;

  setCurrentSession: (session: Session | null) => void;
  currentEngagementId: string | null;
  currentSessionId: string | null;
  getAuthHeaders: () => Record<string, string>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(() => tokenStorage.getUser());
  const [client, setClient] = useState<Client | null>(null);
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Start with loading true
  const [error, setError] = useState<string | null>(null);
  const [isLoginInProgress, setIsLoginInProgress] = useState(false);

  const isDemoMode = false; // Demo mode authentication bypass removed for security
  const isAuthenticated = !!user;
  const isAdmin = user?.role === 'admin' || user?.role === 'platform_admin';

  // Debug logging for admin access with more details
  useEffect(() => {
    const token = tokenStorage.getToken();
    const storedUser = tokenStorage.getUser();
    console.log('🔍 Auth State Debug:', {
      user: user ? { 
        id: user.id, 
        role: user.role, 
        full_name: user.full_name,
        email: user.email 
      } : null,
      isAuthenticated,
      isAdmin,
      isDemoMode,
      token: token ? `present (${token.substring(0, 20)}...)` : 'missing',
      tokenLength: token ? token.length : 0,
      localStorage_user: storedUser ? `present (${storedUser.email})` : 'missing',
      localStorage_keys: Object.keys(localStorage).filter(key => key.startsWith('auth_')),
      getAuthHeaders_result: getAuthHeaders()
    });
  }, [user, isAuthenticated, isAdmin, isDemoMode]);

  useEffect(() => {
    updateApiContext({ user, client, engagement, session });
  }, [user, client, engagement, session]);

  const getAuthHeaders = useCallback((): Record<string, string> => {
    const token = tokenStorage.getToken();
    const storedUser = tokenStorage.getUser(); // Get user from storage as fallback
    const headers: Record<string, string> = {};
    
    // Use current user or fallback to stored user
    const effectiveUser = user || storedUser;
    
    // Debug logging for authentication headers
    console.log('🔍 getAuthHeaders Debug:', {
      token: token ? `present (${token.substring(0, 20)}...)` : 'missing',
      user: user ? { 
        id: user.id, 
        role: user.role, 
        full_name: user.full_name,
        email: user.email 
      } : null,
      storedUser: storedUser ? {
        id: storedUser.id,
        role: storedUser.role,
        full_name: storedUser.full_name,
        email: storedUser.email
      } : null,
      effectiveUser: effectiveUser ? {
        id: effectiveUser.id,
        role: effectiveUser.role,
        full_name: effectiveUser.full_name,
        email: effectiveUser.email
      } : null,
      client: client ? { id: client.id, name: client.name } : null,
      engagement: engagement ? { id: engagement.id, name: engagement.name } : null,
      session: session ? { id: session.id, name: session.name } : null
    });
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Try to get user ID from effective user (current or stored)
    if (effectiveUser && effectiveUser.id) {
      headers['X-User-ID'] = effectiveUser.id;
      headers['X-User-Role'] = effectiveUser.role || 'user';
      console.log('✅ Added X-User-ID header:', effectiveUser.id);
    } else if (token) {
      // Last resort: extract user ID from token if it's in the expected format
      const tokenMatch = token.match(/db-token-([a-f0-9-]{36})/);
      if (tokenMatch) {
        const extractedUserId = tokenMatch[1];
        headers['X-User-ID'] = extractedUserId;
        headers['X-User-Role'] = 'user';
        console.log('✅ Extracted X-User-ID from token:', extractedUserId);
      } else {
        console.warn('⚠️ No user or user.id available and could not extract from token:', { effectiveUser, token: token ? token.substring(0, 30) + '...' : null });
      }
    } else {
      console.warn('⚠️ No user or user.id available for X-User-ID header:', { effectiveUser });
    }

    if (client && client.id) {
      headers['X-Client-Account-ID'] = client.id;
      console.log('✅ Added X-Client-Account-ID header:', client.id);
    } else {
      console.warn('⚠️ No client or client.id available for X-Client-Account-ID header:', { client });
    }

    if (engagement && engagement.id) {
      headers['X-Engagement-ID'] = engagement.id;
      console.log('✅ Added X-Engagement-ID header:', engagement.id);
    } else {
      console.warn('⚠️ No engagement or engagement.id available for X-Engagement-ID header:', { engagement });
    }
    
    if (session && session.id) {
      headers['X-Session-ID'] = session.id;
      console.log('✅ Added X-Session-ID header:', session.id);
    } else {
      console.warn('⚠️ No session or session.id available for X-Session-ID header:', { session });
    }

    console.log('🔍 Final headers being sent:', headers);
    return headers;
  }, [user, client, engagement, session]);

  const logout = useCallback(() => {
    tokenStorage.removeToken();
    tokenStorage.setUser(null);
    contextStorage.clearContext(); // Clear persisted context on logout
    setUser(null);
    setClient(null);
    setEngagement(null);
    setSession(null);
    navigate('/login');
  }, [navigate]);

  // Initialize auth state from storage on mount
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
          setSession(null);
          setIsLoading(false);
          navigate('/login');
          return;
        }

        // Verify token and get user info
        let userInfo = null;
        let needsContextEstablishment = false;
        
        try {
          userInfo = await apiCall('/context/me', {}, false); // Don't include context headers for /context/me endpoint
        } catch (error: any) {
          // Check if this is a context establishment issue (404) vs authentication issue (401)
          if (error.message === 'Not Found' || error.status === 404) {
            console.log('🔄 User exists but needs context establishment');
            needsContextEstablishment = true;
            // Don't clear token - user is authenticated but needs context
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
            // For other errors, don't clear token but continue with context establishment
            needsContextEstablishment = true;
          }
        }

        if (userInfo && userInfo.user && userInfo.user.id) {
          setUser(userInfo.user);
          
          // Check if /context/me endpoint returned context information
          if (userInfo.client && userInfo.engagement && userInfo.session) {
            console.log('🔄 Using context from /context/me endpoint:', {
              client: userInfo.client.name,
              engagement: userInfo.engagement.name,
              session: userInfo.session.id
            });
            
            setClient(userInfo.client);
            setEngagement(userInfo.engagement);
            setSession(userInfo.session);
            
            // Immediately update API context before any other API calls
            updateApiContext({ 
              user: userInfo.user, 
              client: userInfo.client, 
              engagement: userInfo.engagement, 
              session: userInfo.session 
            });
            
            // Save context to localStorage for persistence
            localStorage.setItem('auth_client', JSON.stringify(userInfo.client));
            localStorage.setItem('auth_engagement', JSON.stringify(userInfo.engagement));
            localStorage.setItem('auth_session', JSON.stringify(userInfo.session));
            
            setIsLoading(false);
            return; // Exit early - context is complete
          }
          
          // Fallback: Get stored context from localStorage (persistent across sessions)
          const storedClient = localStorage.getItem('auth_client');
          const storedEngagement = localStorage.getItem('auth_engagement');
          const storedSession = localStorage.getItem('auth_session');
          
          // Try to restore client context even if engagement/session are missing
          if (storedClient) {
            try {
              const clientData = JSON.parse(storedClient);
              
              // Validate that the stored client data has required fields
              if (clientData.id && clientData.name) {
                console.log('🔄 Restoring client from localStorage:', {
                  client: clientData.name,
                  id: clientData.id
                });
                
                setClient(clientData);
                
                // Try to restore engagement and session if available
                if (storedEngagement && storedSession) {
                  try {
                    const engagementData = JSON.parse(storedEngagement);
                    const sessionData = JSON.parse(storedSession);
                    
                    if (engagementData.id && sessionData.id) {
                      console.log('🔄 Restoring full context from localStorage:', {
                        engagement: engagementData.name,
                        session: sessionData.id
                      });
                      
                      setEngagement(engagementData);
                      setSession(sessionData);
                      
                      // Immediately update API context before any other API calls
                      updateApiContext({ 
                        user: userInfo.user, 
                        client: clientData, 
                        engagement: engagementData, 
                        session: sessionData 
                      });
                      
                      setIsLoading(false);
                      return; // Exit early - context fully restored
                    }
                  } catch (parseError) {
                    console.warn('Failed to parse stored engagement/session, keeping client:', parseError);
                    // Clear invalid stored engagement/session data but keep client
                    localStorage.removeItem('auth_engagement');
                    localStorage.removeItem('auth_session');
                  }
                }
                
                // Client restored but need to fetch engagement/session
                console.log('🔄 Client restored, fetching engagement for client:', clientData.name);
                await switchClient(clientData.id, clientData);
                setIsLoading(false);
                return; // Exit early - client context restored
              }
            } catch (parseError) {
              console.warn('Failed to parse stored client, will fetch defaults:', parseError);
              // Clear invalid stored data
              localStorage.removeItem('auth_client');
              localStorage.removeItem('auth_engagement');
              localStorage.removeItem('auth_session');
            }
          }
          
          // Last resort: fetch default context if no context is available
          console.log('🔄 No context available, fetching defaults...');
          await fetchDefaultContext();
        } else if (needsContextEstablishment) {
          // User is authenticated but needs context establishment
          console.log('🔄 User authenticated but needs context establishment');
          // Try to get user info from token storage as fallback
          const storedUser = tokenStorage.getUser();
          if (storedUser) {
            setUser(storedUser);
            console.log('🔄 Using stored user info:', storedUser);
          }
          
          // Set user to null initially to trigger context establishment flow
          setClient(null);
          setEngagement(null);
          setSession(null);
          
          // The ContextBreadcrumbs component will handle the context establishment
        } else {
          // Authentication failed - clear everything and redirect to login
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
        // Only clear token if this is a clear authentication failure
        // Don't clear token for network errors or other issues
        if (error.message === 'Unauthorized' || error.status === 401) {
          console.log('🔄 Authentication error, redirecting to login');
          tokenStorage.removeToken();
          setUser(null);
          setClient(null);
          setEngagement(null);
          setSession(null);
          navigate('/login');
        } else {
          // For other errors, keep the token but clear user state
          // This allows for retry on network issues
          console.log('🔄 Network or other error during auth initialization:', error);
          setUser(null);
        }
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const fetchDefaultContext = async () => {
    try {
      // Don't fetch defaults if we already have a complete context
      if (client && engagement && session) {
        console.log('🔄 Context already complete, skipping default fetch');
        return;
      }
      
      console.log('🔄 Fetching default context...');
      
      // Get available clients first - use context establishment endpoint
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
      
      // Check if we have a stored client preference that's still valid
      const storedClientId = localStorage.getItem('auth_client_id');
      let targetClient = null;
      
      if (storedClientId) {
        targetClient = clientsResponse.clients.find(c => c.id === storedClientId);
        if (targetClient) {
          console.log(`🔄 Using stored client preference: ${targetClient.name}`);
        } else {
          console.log(`🔄 Stored client ${storedClientId} not found in available clients`);
          // Clear invalid stored client ID
          localStorage.removeItem('auth_client_id');
        }
      }
      
      // Use first available client as default only if no valid stored client and no current client
      if (!targetClient && !client) {
        targetClient = clientsResponse.clients[0];
        console.log(`🔄 Using first available client as default: ${targetClient.name}`);
      }
      
      if (targetClient && (!client || client.id !== targetClient.id)) {
        await switchClient(targetClient.id, targetClient);
      }
      
    } catch (error: any) {
      console.error('Error fetching default context:', error);
      // Don't clear authentication on context fetch errors
      // The user is still authenticated, they just need to manually select context
      if (error.message === 'Unauthorized' || error.status === 401) {
        console.log('🔄 Authentication expired during context fetch');
        tokenStorage.removeToken();
        setUser(null);
        navigate('/login');
      }
    }
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

      // Set token and user data
      tokenStorage.setToken(response.token.access_token);
      tokenStorage.setUser(response.user);
      setUser(response.user);

      console.log('🔐 Login Step 1 - Initial user set:', {
        user: response.user,
        role: response.user.role,
        token: response.token.access_token.substring(0, 20) + '...'
      });

      // Small delay to ensure localStorage is updated
      await new Promise(resolve => setTimeout(resolve, 100));

      // Always fetch fresh context from backend to ensure consistency
      let actualUserRole = response.user.role; // fallback to login response role
      try {
        const context = await apiCall('/context/me', {}, false); // Don't include context headers for /context/me endpoint
        console.log('🔐 Login Step 2 - Context from /me:', context);
        
        if (context) {
          // Set context from backend response
          setClient(context.client || null);
          setEngagement(context.engagement || null);
          setSession(context.session || null);
          
          // Save the actual backend context
          contextStorage.setContext({
            client: context.client,
            engagement: context.engagement,
            session: context.session,
            timestamp: Date.now(),
            source: 'login_backend'
          });
          
          // Use the role from /me endpoint as it's more accurate
          if (context.user && context.user.role) {
            actualUserRole = context.user.role;
            // Update the user object with the correct role
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
        // Clear context on error
        setClient(null);
        setEngagement(null);
        setSession(null);
        contextStorage.clearContext();
      }

      // Determine redirect path based on actual user role
      const redirectPath = actualUserRole === 'admin' 
        ? '/admin/dashboard' 
        : (tokenStorage.getRedirectPath() || '/');
      tokenStorage.clearRedirectPath();
      
      console.log('🔐 Login Step 4 - Redirect decision:', {
        actualUserRole,
        redirectPath,
        isAdminRole: actualUserRole === 'admin'
      });
      
      // Use setTimeout to ensure navigation happens after state updates
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


  const setCurrentSession = useCallback((session: Session | null) => {
    setSession(session);
  }, []);

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
      
      // If no client data provided, fetch it
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
      // Persist to localStorage for cross-session persistence
      localStorage.setItem('auth_client', JSON.stringify(fullClientData));
      localStorage.setItem('auth_client_id', fullClientData.id); // Store ID separately for preference
      
      // Immediately update API context
      updateApiContext({ 
        user, 
        client: fullClientData, 
        engagement, 
        session 
      });
      
      // Get engagements for this client using context establishment endpoint
      const engagementsResponse = await apiCall(`/context/clients/${clientId}/engagements`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
      
      if (engagementsResponse?.engagements && engagementsResponse.engagements.length > 0) {
        // Use first engagement as default
        const defaultEngagement = engagementsResponse.engagements[0];
        await switchEngagement(defaultEngagement.id, defaultEngagement);
      } else {
        // Clear engagement and session if no engagements available
        setEngagement(null);
        setSession(null);
        localStorage.removeItem('auth_engagement');
        localStorage.removeItem('auth_session');
      }
      
    } catch (error) {
      console.error('Error switching client:', error);
      throw error;
    }
  };

  const switchEngagement = async (engagementId: string, engagementData?: any) => {
    try {
      console.log('🔄 Switching to engagement:', engagementId);
      
      let fullEngagementData = engagementData;
      
      // If no engagement data provided, fetch it
      if (!fullEngagementData && client) {
        const response = await apiCall(`/context/clients/${client.id}/engagements/${engagementId}`, {
          method: 'GET',
          headers: getAuthHeaders()
        });
        fullEngagementData = response.engagement;
      }
      
      if (!fullEngagementData) {
        throw new Error('Engagement data not found');
      }
      
      setEngagement(fullEngagementData);
      // Persist to localStorage for cross-session persistence
      localStorage.setItem('auth_engagement', JSON.stringify(fullEngagementData));
      
      // Immediately update API context
      updateApiContext({ 
        user, 
        client, 
        engagement: fullEngagementData, 
        session 
      });
      
      // For demo user, create a simple session object based on engagement
      // V2 Discovery Flow API handles session management internally
      const sessionData = {
        id: fullEngagementData.id, // Use engagement ID as session ID for demo
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
      // Persist to localStorage for cross-session persistence
      localStorage.setItem('auth_session', JSON.stringify(sessionData));
      
      // Immediately update API context
      updateApiContext({ 
        user, 
        client, 
        engagement: fullEngagementData, 
        session: sessionData 
      });
      
    } catch (error) {
      console.error('Error switching engagement:', error);
      throw error;
    }
  };

  const switchSession = async (sessionId: string) => {
    if (isDemoMode) return; // Switching not allowed in demo mode
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


  return (
    <AuthContext.Provider value={{
      user,
      client,
      engagement,
      session,
      isLoading,
      error,
      isDemoMode,
      isAuthenticated,
      isAdmin,
      login,
      register,
      logout,
      switchClient,
      switchEngagement,
      switchSession,

      setCurrentSession,
      currentEngagementId: engagement?.id || null,
      currentSessionId: session?.id || null,
      getAuthHeaders,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};