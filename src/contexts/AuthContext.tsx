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
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (userData: RegisterData) => Promise<void>;
  getAuthHeaders: () => Record<string, string>;
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

  useEffect(() => {
    // Check if user is already logged in (check localStorage for token)
    const token = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
      }
    }
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    try {
      // First try to authenticate against the database
      try {
        const response = await fetch('/api/v1/auth/login', {
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
            
            setUser(result.user);
            setIsAuthenticated(true);
            return; // Successful database authentication
          }
        }
      } catch (dbError) {
        console.log('Database authentication failed, trying demo credentials');
      }

      // Fall back to demo authentication if database auth fails
      if (email === 'admin@aiforce.com' && password === 'admin123') {
        const adminUser: User = {
          id: 'admin-1',
          username: 'admin',
          email: 'admin@aiforce.com',
          full_name: 'Admin User',
          role: 'admin',
          status: 'approved'
        };
        
        // Store auth token and user data
        const token = 'demo-admin-token-' + Date.now();
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_data', JSON.stringify(adminUser));
        
        setUser(adminUser);
        setIsAuthenticated(true);
      } else if (email === 'user@demo.com' && password === 'user123') {
        const demoUser: User = {
          id: 'user-1',
          username: 'demo_user',
          email: 'user@demo.com',
          full_name: 'Demo User',
          role: 'user',
          status: 'approved',
          client_accounts: ['client-1'],
          engagements: ['engagement-1']
        };
        
        const token = 'demo-user-token-' + Date.now();
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_data', JSON.stringify(demoUser));
        
        setUser(demoUser);
        setIsAuthenticated(true);
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
    setUser(null);
    setIsAuthenticated(false);
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

      // Make API call to register user
      const response = await fetch('/api/v1/auth/register', {
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
    
    return headers;
  };

  const isAdmin = user?.role === 'admin';

  const value = {
    user,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    register,
    getAuthHeaders
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 