import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'user';
  status: 'approved' | 'pending' | 'rejected' | 'suspended';
  client_accounts?: string[];
  engagements?: string[];
  default_engagement_id?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  currentEngagementId: string | null;
  currentSessionId: string | null;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  register: (userData: RegisterData) => Promise<void>;
  getAuthHeaders: () => Record<string, string>;
  setCurrentEngagementId: (engagementId: string | null) => void;
  setCurrentSessionId: (sessionId: string | null) => void;
}

interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  username: string;
  organization: string;
  role_description: string;
  justification?: string;
  requested_access: {
    client_accounts: string[];
    engagements: string[];
    access_level: string;
  };
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentEngagementId, setCurrentEngagementId] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is already logged in (check localStorage for token)
    const token = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        
        // Handle migration from old user ID format to UUID format
        if (parsedUser.id === 'admin-1' && parsedUser.email === 'admin@aiforce.com') {
          parsedUser.id = '2a0de3df-7484-4fab-98b9-2ca126e2ab21'; // Update to real admin UUID
          localStorage.setItem('user_data', JSON.stringify(parsedUser));
          localStorage.setItem('auth_source', 'demo');
        } else if (parsedUser.id === 'user-1' && parsedUser.email === 'user@demo.com') {
          parsedUser.id = 'demo-user-12345678-1234-5678-9012-123456789012'; // Update to UUID format
          localStorage.setItem('user_data', JSON.stringify(parsedUser));
          localStorage.setItem('auth_source', 'demo');
        }
        
        setUser(parsedUser);
        setIsAuthenticated(true);

        // Set initial engagement and session from localStorage or user defaults
        const storedEngagementId = localStorage.getItem('selectedEngagementId');
        if (storedEngagementId) {
          setCurrentEngagementId(storedEngagementId);
        } else if (parsedUser.default_engagement_id) {
          setCurrentEngagementId(parsedUser.default_engagement_id);
        }
        
        const storedSessionId = localStorage.getItem('selectedSessionId');
        if (storedSessionId) {
          setCurrentSessionId(storedSessionId);
        }

      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('auth_source');
      }
    }
    setIsLoading(false); // Always set loading to false after checking
  }, []);

  const login = async (email: string, password: string): Promise<User> => {
    try {
      // First try to authenticate against the database
      try {
        const apiUrl = import.meta.env.VITE_BACKEND_URL || '';
        const response = await fetch(`${apiUrl}/api/v1/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email, password })
        });

        if (response.ok) {
          const result = await response.json();
          
          if (result.status === 'success' && result.user) {
            // Store auth token and user data
            localStorage.setItem('auth_token', result.token);
            localStorage.setItem('user_data', JSON.stringify(result.user));
            localStorage.setItem('auth_source', 'database'); // Track the auth source
            
            setUser(result.user);
            setIsAuthenticated(true);
            return result.user; // Successful database authentication
          }
        }
      } catch (dbError) {
        console.log('Database authentication failed, trying demo credentials');
      }

      // Fall back to demo authentication if database auth fails
      if (email === 'admin@democorp.com' && password === 'admin123') {
        // Use the real admin UUID from the database for demo auth
        const adminUser: User = {
          id: 'c8dd279c-ec', // This should be the real admin ID from the database
          username: 'admin',
          email: 'admin@democorp.com',
          full_name: 'Admin User',
          role: 'admin',
          status: 'approved'
        };
        
        // Store auth token and user data
        const token = 'demo-admin-token-' + Date.now();
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_data', JSON.stringify(adminUser));
        localStorage.setItem('auth_source', 'demo'); // Track the auth source
        
        setUser(adminUser);
        setIsAuthenticated(true);
        return adminUser;
      } else if (email === 'demo@democorp.com' && password === 'user123') {
        // Generate a proper UUID for demo user instead of "user-1"
        const demoUser: User = {
          id: 'a769ca2c-1b', // This should be the real demo user ID
          username: 'demo_user',
          email: 'demo@democorp.com',
          full_name: 'Demo User',
          role: 'user',
          status: 'approved',
          client_accounts: ['client-1'],
          engagements: ['engagement-1']
        };
        
        const token = 'demo-user-token-' + Date.now();
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_data', JSON.stringify(demoUser));
        localStorage.setItem('auth_source', 'demo'); // Track the auth source
        
        setUser(demoUser);
        setIsAuthenticated(true);
        return demoUser;
      } else {
        throw new Error('Invalid email or password');
      }
    } catch (error) {
      throw new Error('Login failed: ' + (error as Error).message);
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    localStorage.removeItem('auth_source');
    localStorage.removeItem('selectedEngagementId');
    localStorage.removeItem('selectedSessionId');
    setUser(null);
    setIsAuthenticated(false);
    setCurrentEngagementId(null);
    setCurrentSessionId(null);
  };

  const register = async (userData: RegisterData): Promise<void> => {
    try {
      // Transform frontend data structure to match backend expectations
      const registrationPayload = {
        email: userData.email,
        full_name: userData.full_name,
        organization: userData.organization || "User Organization",
        role_description: userData.role_description || "Platform User",
        registration_reason: userData.justification || "User registration for platform access",
        requested_access_level: userData.requested_access.access_level,
        phone_number: null,
        manager_email: null,
        linkedin_profile: null,
        notification_preferences: {
          email_notifications: true,
          system_alerts: true,
          learning_updates: false,
          weekly_reports: true
        }
      };

      const apiUrl = import.meta.env.VITE_BACKEND_URL || '';
      // Make API call to register user
      const response = await fetch(`${apiUrl}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registrationPayload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      // Registration successful - user needs approval
      const result = await response.json();
      
      if (result.status === 'success') {
        // Registration successful, pending approval
        return;
      } else {
        throw new Error(result.message || 'Registration failed');
      }
    } catch (error) {
      throw new Error('Registration failed: ' + (error as Error).message);
    }
  };

  const getAuthHeaders = (): Record<string, string> => {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (user) {
      headers['X-User-ID'] = user.id;
      headers['X-User-Role'] = user.role;
    }

    if (currentEngagementId) {
      headers['X-Engagement-ID'] = currentEngagementId;
    }
    
    if (currentSessionId) {
      headers['X-Session-ID'] = currentSessionId;
    }

    return headers;
  };

  const handleSetCurrentEngagementId = (engagementId: string | null) => {
    setCurrentEngagementId(engagementId);
    if (engagementId) {
      localStorage.setItem('selectedEngagementId', engagementId);
    } else {
      localStorage.removeItem('selectedEngagementId');
    }
    // When engagement changes, clear the session
    setCurrentSessionId(null);
    localStorage.removeItem('selectedSessionId');
  };

  const handleSetCurrentSessionId = (sessionId: string | null) => {
    setCurrentSessionId(sessionId);
    if (sessionId) {
      localStorage.setItem('selectedSessionId', sessionId);
    } else {
      localStorage.removeItem('selectedSessionId');
    }
  };

  const isAdmin = user?.role === 'admin';

  const value = {
    user,
    isAuthenticated,
    isAdmin,
    isLoading,
    currentEngagementId,
    currentSessionId,
    login,
    logout,
    register,
    getAuthHeaders,
    setCurrentEngagementId: handleSetCurrentEngagementId,
    setCurrentSessionId: handleSetCurrentSessionId,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 