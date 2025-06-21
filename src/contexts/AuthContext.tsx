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

// --- Demo Mode Constants ---
const DEMO_USER_ID = '44444444-4444-4444-4444-444444444444';
const DEMO_CLIENT_ID = '11111111-1111-1111-1111-111111111111';
const DEMO_ENGAGEMENT_ID = '22222222-2222-2222-2222-222222222222';
const DEMO_SESSION_ID = '33333333-3333-3333-3333-333333333333';

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

const DEMO_USER: User = {
  id: DEMO_USER_ID,
  email: 'demo@democorp.com',
  role: 'admin', // Give demo user admin privileges
  full_name: 'Demo User',
  username: 'demo',
  status: 'active',
  organization: 'Democorp',
  role_description: 'Demo User',
  client_account_id: DEMO_CLIENT_ID,
  client_accounts: [{ 
    id: DEMO_CLIENT_ID, 
    name: 'Democorp', 
    role: 'admin' 
  }],
};

const DEMO_CLIENT: Client = {
  id: DEMO_CLIENT_ID,
  name: 'Democorp',
  status: 'active',
};

const DEMO_ENGAGEMENT: Engagement = {
  id: DEMO_ENGAGEMENT_ID,
  name: 'Cloud Migration 2024',
  status: 'active',
};

const DEMO_SESSION: Session = {
  id: DEMO_SESSION_ID,
  name: 'Demo Session',
  status: 'active',
};
// -------------------------

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
  loginWithDemoUser: () => Promise<void>;
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

  const isDemoMode = user?.id === DEMO_USER_ID;
  const isAuthenticated = !!user;
  const isAdmin = user?.role === 'admin';

  // Debug logging for admin access with more details
  useEffect(() => {
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
      token: tokenStorage.getToken() ? 'present' : 'missing',
      localStorage_user: tokenStorage.getUser() ? 'present' : 'missing'
    });
  }, [user, isAuthenticated, isAdmin, isDemoMode]);

  useEffect(() => {
    updateApiContext({ user, client, engagement, session });
  }, [user, client, engagement, session]);

  const getAuthHeaders = useCallback((): Record<string, string> => {
    const token = tokenStorage.getToken();
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (user) {
      headers['X-User-ID'] = user.id;
      headers['X-User-Role'] = user.role;
    }

    if (client) {
      headers['X-Client-Account-ID'] = client.id;
    }

    if (engagement) {
      headers['X-Engagement-ID'] = engagement.id;
    }
    
    if (session) {
      headers['X-Session-ID'] = session.id;
    }

    return headers;
  }, [user, client, engagement, session]);

  const logout = useCallback(() => {
    localStorage.removeItem('demoMode');
    tokenStorage.setToken('');
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
          setIsLoading(false);
          return;
        }

        // Verify token and get user info
        const userInfo = await apiCall('/auth/me', {
          method: 'GET',
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (userInfo && userInfo.id) {
          setUser(userInfo);
          
          // Get stored context from localStorage (persistent across sessions)
          const storedClient = localStorage.getItem('auth_client');
          const storedEngagement = localStorage.getItem('auth_engagement');
          const storedSession = localStorage.getItem('auth_session');
          
          // Only restore context if all parts are present and valid
          if (storedClient && storedEngagement && storedSession) {
            try {
              const clientData = JSON.parse(storedClient);
              const engagementData = JSON.parse(storedEngagement);
              const sessionData = JSON.parse(storedSession);
              
              // Validate that the stored data has required fields
              if (clientData.id && engagementData.id && sessionData.id) {
                console.log('🔄 Restoring context from localStorage:', {
                  client: clientData.name,
                  engagement: engagementData.name,
                  session: sessionData.id
                });
                
                setClient(clientData);
                setEngagement(engagementData);
                setSession(sessionData);
                setIsLoading(false);
                return; // Exit early - don't fetch defaults
              }
            } catch (parseError) {
              console.warn('Failed to parse stored context, will fetch defaults:', parseError);
              // Clear invalid stored data
              localStorage.removeItem('auth_client');
              localStorage.removeItem('auth_engagement');
              localStorage.removeItem('auth_session');
            }
          }
          
          // Only fetch default context if no valid stored context exists
          console.log('🔄 No valid stored context found, fetching defaults...');
          await fetchDefaultContext();
        } else {
          tokenStorage.removeToken();
          setUser(null);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        tokenStorage.removeToken();
        setUser(null);
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
      
      // Use first available client as default only if no client is set
      const defaultClient = clientsResponse.clients[0];
      if (!client && defaultClient) {
        await switchClient(defaultClient.id, defaultClient);
      }
      
    } catch (error) {
      console.error('Error fetching default context:', error);
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
        const context = await apiCall('/me', {}, false); // Don't include context headers for /me endpoint
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
  const loginWithDemoUser = async () => {
    setIsLoading(true);
    setIsLoginInProgress(true);
    try {
      localStorage.setItem('demoMode', 'true');
      tokenStorage.setToken('db-token-' + DEMO_USER_ID + '-demo123');
      tokenStorage.setUser(DEMO_USER);
      
      setUser(DEMO_USER);
      
      // Small delay to ensure localStorage is updated
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Fetch context from backend to ensure consistency
      try {
        const backendContext = await apiCall('/me', {}, false); // Don't include context headers for /me endpoint
        console.log('🔐 Demo login - Backend context:', backendContext);
        
        if (backendContext?.client) {
          setClient(backendContext.client);
          setEngagement(backendContext.engagement || null);
          setSession(backendContext.session || null);
          
          // Save the actual backend context
          contextStorage.setContext({
            client: backendContext.client,
            engagement: backendContext.engagement,
            session: backendContext.session,
            timestamp: Date.now(),
            source: 'demo_login_backend'
          });
          
          console.log('🔐 Demo login complete - Context set:', {
            client: backendContext.client,
            engagement: backendContext.engagement,
            session: backendContext.session
          });
        } else {
          console.warn('🔐 Backend context missing for demo, using hardcoded');
          setClient(DEMO_CLIENT);
          setEngagement(DEMO_ENGAGEMENT);
          setSession(DEMO_SESSION);
        }
      } catch (error) {
        console.error('🔐 Failed to fetch demo context from backend, using hardcoded:', error);
        setClient(DEMO_CLIENT);
        setEngagement(DEMO_ENGAGEMENT);
        setSession(DEMO_SESSION);
      }
      
      setError(null);
      
      // Use setTimeout to ensure state updates are complete before navigation
      setTimeout(() => {
        console.log('🔐 Demo login - Navigating to admin dashboard');
        navigate('/admin/dashboard');
      }, 300);
    } catch (error) {
      console.error('Demo login failed:', error);
      setError('Demo login failed');
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
        const response = await apiCall(`/api/v1/clients/${clientId}`, {
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
      
      // Get engagements for this client using context establishment endpoint
      const engagementsResponse = await apiCall(`/api/v1/context/engagements?client_id=${clientId}`, {
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
        const response = await apiCall(`/api/v1/clients/${client.id}/engagements/${engagementId}`, {
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
      
      // Create or get session for this engagement
      const sessionResponse = await apiCall('/api/v1/sessions', {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          client_account_id: client?.id,
          engagement_id: engagementId,
          session_name: `${fullEngagementData.name} Session`,
          session_type: 'discovery'
        })
      });
      
      if (sessionResponse?.session) {
        setSession(sessionResponse.session);
        // Persist to localStorage for cross-session persistence
        localStorage.setItem('auth_session', JSON.stringify(sessionResponse.session));
      }
      
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
      loginWithDemoUser,
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