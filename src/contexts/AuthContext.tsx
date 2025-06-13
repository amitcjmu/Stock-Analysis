import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, User } from '@/lib/api/auth';
import { apiCall } from '@/lib/api';

interface TokenStorage {
  getToken: () => string | null;
  setToken: (token: string) => void;
  getUser: () => User | null;
  setUser: (user: User) => void;
  getRedirectPath: () => string | null;
  setRedirectPath: (path: string) => void;
  clearRedirectPath: () => void;
}

interface Client {
  id: string;
  name: string;
  status: string;
}

interface Engagement {
  id: string;
  name: string;
  status: string;
}

interface Session {
  id: string;
  name: string;
  status: string;
}

const tokenStorage: TokenStorage = {
  getToken: () => localStorage.getItem('auth_token'),
  setToken: (token) => localStorage.setItem('auth_token', token),
  getUser: () => {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
  },
  setUser: (user) => localStorage.setItem('user_data', JSON.stringify(user)),
  getRedirectPath: () => localStorage.getItem('redirect_path'),
  setRedirectPath: (path) => localStorage.setItem('redirect_path', path),
  clearRedirectPath: () => localStorage.removeItem('redirect_path'),
};

interface AuthContextType {
  user: User | null;
  client: Client | null;
  engagement: Engagement | null;
  session: Session | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<User>;
  register: (userData: any) => Promise<any>;
  logout: () => void;
  switchClient: (clientId: string) => Promise<void>;
  switchEngagement: (engagementId: string) => Promise<void>;
  switchSession: (sessionId: string) => Promise<void>;
  loginWithDemoUser: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
export { AuthContext };

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(tokenStorage.getUser());
  const [client, setClient] = useState<Client | null>(null);
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Function to get user context including client and engagement
  const getUserContext = async () => {
    try {
      const context = await apiCall('me');
      if (context) {
        // Update client if available
        if (context.client) {
          setClient(context.client);
        }

        // Update engagement if available
        if (context.engagement) {
          setEngagement(context.engagement);
        }

        // Update session if available
        if (context.session) {
          setSession(context.session);
        }

        // Update user with context
        if (context.user) {
          const updatedUser = {
            ...user,
            ...context.user
          };
          tokenStorage.setUser(updatedUser);
          setUser(updatedUser);
        }
      }
    } catch (error) {
      // Only logout if NOT the demo user
      if (!user || user.id !== '44444444-4444-4444-4444-444444444444') {
        logout();
      }
      // else: do nothing, keep demo user context
    }
  };

  useEffect(() => {
    const token = tokenStorage.getToken();
    if (token && !user) {
      authApi.validateToken(token)
        .then((validatedUser) => {
          if (validatedUser) {
            tokenStorage.setUser(validatedUser);
            setUser(validatedUser);
            // Get complete user context
            getUserContext();
          } else {
            tokenStorage.setToken('');
            tokenStorage.setUser(null);
            setUser(null);
          }
        })
        .catch(() => {
          tokenStorage.setToken('');
          tokenStorage.setUser(null);
          setUser(null);
        });
    }
  }, []);

  // Effect to handle user context when user changes
  useEffect(() => {
    if (user) {
      getUserContext();
    }
  }, [user]);

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await authApi.login(email, password);

      if (response.status !== 'success' || !response.user || !response.token) {
        throw new Error(response.message || 'Login failed');
      }

      tokenStorage.setToken(response.token.access_token);
      tokenStorage.setUser(response.user);
      setUser(response.user);

      // Get complete user context
      await getUserContext();

      // Redirect based on user role and context
      const redirectPath = response.user.role === 'admin' 
        ? '/admin/dashboard' 
        : (tokenStorage.getRedirectPath() || '/');
      tokenStorage.clearRedirectPath();
      navigate(redirectPath);

      return response.user;
    } catch (error) {
      setError((error as Error).message);
      throw error;
    } finally {
      setIsLoading(false);
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

  const switchClient = async (clientId: string) => {
    try {
      const response = await apiCall(`/clients/${clientId}`);
      if (response) {
        setClient(response);
        // Clear engagement and session when switching client
        setEngagement(null);
        setSession(null);
      }
    } catch (error) {
      console.error('Error switching client:', error);
      throw error;
    }
  };

  const switchEngagement = async (engagementId: string) => {
    try {
      const response = await apiCall(`/engagements/${engagementId}`);
      if (response) {
        setEngagement(response);
        // Clear session when switching engagement
        setSession(null);
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

  const logout = () => {
    localStorage.removeItem('demoMode');
    tokenStorage.setToken('');
    tokenStorage.setUser(null);
    setUser(null);
    setClient(null);
    setEngagement(null);
    setSession(null);
    navigate('/login');
  };

  const loginWithDemoUser = () => {
    localStorage.setItem('demoMode', 'true');
    const demoUser = {
      id: '44444444-4444-4444-4444-444444444444',
      email: 'demo@democorp.com',
      role: 'demo',
      full_name: 'Demo User',
      username: 'demo',
      status: 'active',
      organization: 'Democorp',
      role_description: 'Demo User',
      client_account_id: '11111111-1111-1111-1111-111111111111',
      client_accounts: [{ id: '11111111-1111-1111-1111-111111111111', name: 'Democorp', role: 'demo' }],
    };
    const demoClient = {
      id: '11111111-1111-1111-1111-111111111111',
      name: 'Democorp',
      status: 'active' as const,
      type: 'enterprise' as const,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      metadata: {
        industry: 'Technology',
        size: 'Enterprise',
        location: 'Global'
      }
    };
    const demoEngagement = {
      id: '22222222-2222-2222-2222-222222222222',
      name: 'Cloud Migration 2024',
      client_id: '11111111-1111-1111-1111-111111111111',
      status: 'active' as const,
      type: 'migration' as const,
      start_date: '2024-01-01T00:00:00Z',
      end_date: '2024-12-31T23:59:59Z',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      metadata: {
        project_manager: 'Demo PM',
        budget: 1000000
      }
    };
    const demoSession = {
      id: '33333333-3333-3333-3333-333333333333',
      name: 'Demo Session',
      session_name: 'demo_session',
      session_type: 'analysis' as any,
      engagement_id: '22222222-2222-2222-2222-222222222222',
      client_account_id: '11111111-1111-1111-1111-111111111111',
      is_default: true,
      status: 'active' as const,
      auto_created: false,
      created_by: '44444444-4444-4444-4444-444444444444',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    };
    setUser(demoUser);
    setClient(demoClient);
    setEngagement(demoEngagement);
    setSession(demoSession);
    setError(null);
    setIsLoading(false);
    navigate('/');
  };

  return (
    <AuthContext.Provider value={{
      user,
      client,
      engagement,
      session,
      isLoading,
      error,
      login,
      register,
      logout,
      switchClient,
      switchEngagement,
      switchSession,
      loginWithDemoUser
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