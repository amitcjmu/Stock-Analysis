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
};

// --- Demo Mode Constants ---
const DEMO_USER_ID = '44444444-4444-4444-4444-444444444444';
const DEMO_CLIENT_ID = '11111111-1111-1111-1111-111111111111';
const DEMO_ENGAGEMENT_ID = '22222222-2222-2222-2222-222222222222';
const DEMO_SESSION_ID = '33333333-3333-3333-3333-333333333333';

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
  switchClient: (clientId: string) => Promise<void>;
  switchEngagement: (engagementId: string) => Promise<void>;
  switchSession: (sessionId: string) => Promise<void>;
  loginWithDemoUser: () => void;
  setCurrentSession: (session: Session | null) => void;
  currentEngagementId: string | null;
  currentSessionId: string | null;
  getAuthHeaders: () => Record<string, string>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
export { AuthContext };

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(() => tokenStorage.getUser());
  const [client, setClient] = useState<Client | null>(null);
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Start with loading true
  const [error, setError] = useState<string | null>(null);

  const isDemoMode = user?.id === DEMO_USER_ID;
  const isAuthenticated = !!user;
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    updateApiContext({ client, engagement, session });
  }, [client, engagement, session]);

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
    setUser(null);
    setClient(null);
    setEngagement(null);
    setSession(null);
    navigate('/login');
  }, [navigate]);

  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);
      try {
        const token = tokenStorage.getToken();
        const storedUser = tokenStorage.getUser();

        if (storedUser?.id === DEMO_USER_ID) {
          setUser(DEMO_USER);
          setClient(DEMO_CLIENT);
          setEngagement(DEMO_ENGAGEMENT);
          setSession(DEMO_SESSION);
        } else if (token) {
          const validatedUser = await authApi.validateToken(token);
          if (validatedUser) {
            tokenStorage.setUser(validatedUser);
            setUser(validatedUser);
            const context = await apiCall('/me');
            if (context) {
              setClient(context.client || null);
              setEngagement(context.engagement || null);
              setSession(context.session || null);
            }
          } else {
            // Token is invalid, log out
            logout();
          }
        }
      } catch (err) {
        console.error("Authentication initialization failed:", err);
        // Also log out on error
        logout();
      } finally {
        // This is the crucial change: ensure loading is false only after all checks are done
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [logout]);


  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await authApi.login(email, password);

      if (response.status !== 'success' || !response.user || !response.token) {
        throw new Error(response.message || 'Login failed');
      }

      // Set token and user data
      tokenStorage.setToken(response.token.access_token);
      tokenStorage.setUser(response.user);
      setUser(response.user);

      // Small delay to ensure localStorage is updated
      await new Promise(resolve => setTimeout(resolve, 100));

      // Get user context with the new token to get the actual user role
      let actualUserRole = response.user.role; // fallback to login response role
      try {
        const context = await apiCall('/me');
        if (context) {
          setClient(context.client || null);
          setEngagement(context.engagement || null);
          setSession(context.session || null);
          // Use the role from /me endpoint as it's more accurate
          if (context.user && context.user.role) {
            actualUserRole = context.user.role;
            // Update the user object with the correct role
            const updatedUser = { ...response.user, role: context.user.role };
            tokenStorage.setUser(updatedUser);
            setUser(updatedUser);
          }
        }
      } catch (contextError) {
        console.warn('Failed to load user context, using defaults:', contextError);
        // Continue with login even if context fails
      }

      // Determine redirect path based on actual user role
      const redirectPath = actualUserRole === 'admin' 
        ? '/admin/dashboard' 
        : (tokenStorage.getRedirectPath() || '/');
      tokenStorage.clearRedirectPath();
      
      // Use setTimeout to ensure navigation happens after state updates
      setTimeout(() => {
        navigate(redirectPath);
      }, 200);

      return response.user;
    } catch (error) {
      setError((error as Error).message);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };
  const loginWithDemoUser = () => {
    setIsLoading(true);
    localStorage.setItem('demoMode', 'true');
    tokenStorage.setToken('demo-token-' + DEMO_USER_ID);
    tokenStorage.setUser(DEMO_USER);
    
    setUser(DEMO_USER);
    setClient(DEMO_CLIENT);
    setEngagement(DEMO_ENGAGEMENT);
    setSession(DEMO_SESSION);
    setError(null);
    setIsLoading(false);
    
    navigate('/admin/dashboard');
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

  const switchClient = async (clientId: string) => {
    if (isDemoMode) return; // Switching not allowed in demo mode
    try {
      const response = await apiCall(`/clients/${clientId}`);
      if (response) {
        setClient(response);
        setEngagement(null);
        setSession(null);
      }
    } catch (error) {
      console.error('Error switching client:', error);
      throw error;
    }
  };

  const switchEngagement = async (engagementId: string) => {
    if (isDemoMode) return; // Switching not allowed in demo mode
    try {
      const response = await apiCall(`/engagements/${engagementId}`);
      if (response) {
        setEngagement(response);
        setSession(null);
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