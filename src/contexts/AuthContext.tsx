import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { apiCall } from '@/lib/api';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  permissions: string[];
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  error: Error | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  getContextHeaders: () => Record<string, string>;
  checkPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const router = useRouter();

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = sessionStorage.getItem(TOKEN_KEY);
        if (!token) {
          setIsLoading(false);
          return;
        }

        const storedUser = sessionStorage.getItem(USER_KEY);
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        }

        // Verify token and refresh user data
        const response = await apiCall('/api/v1/auth/verify', {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        if (response.user) {
          setUser(response.user);
          sessionStorage.setItem(USER_KEY, JSON.stringify(response.user));
        } else {
          // Token invalid
          sessionStorage.removeItem(TOKEN_KEY);
          sessionStorage.removeItem(USER_KEY);
          setUser(null);
        }
      } catch (err) {
        console.error('Auth initialization error:', err);
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(USER_KEY);
        setUser(null);
        setError(err instanceof Error ? err : new Error('Authentication failed'));
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiCall('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });

      const { token, user } = response;

      sessionStorage.setItem(TOKEN_KEY, token);
      sessionStorage.setItem(USER_KEY, JSON.stringify(user));
      setUser(user);

      // Redirect to dashboard or last attempted page
      const redirectPath = sessionStorage.getItem('auth_redirect') || '/dashboard';
      sessionStorage.removeItem('auth_redirect');
      router.push(redirectPath);
    } catch (err) {
      console.error('Login error:', err);
      setError(err instanceof Error ? err : new Error('Login failed'));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      const token = sessionStorage.getItem(TOKEN_KEY);
      if (token) {
        await apiCall('/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(USER_KEY);
      setUser(null);
      router.push('/login');
    }
  };

  const getContextHeaders = () => {
    const token = sessionStorage.getItem(TOKEN_KEY);
    return {
      Authorization: token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json'
    };
  };

  const checkPermission = (permission: string): boolean => {
    if (!user) return false;
    return user.permissions.includes(permission);
  };

  const value = {
    user,
    isLoading,
    error,
    login,
    logout,
    getContextHeaders,
    checkPermission
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const withAuth = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  requiredPermissions: string[] = []
) => {
  return function WithAuthComponent(props: P) {
    const { user, isLoading, checkPermission } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!isLoading && !user) {
        sessionStorage.setItem('auth_redirect', router.asPath);
        router.push('/login');
        return;
      }

      if (!isLoading && user && requiredPermissions.length > 0) {
        const hasAllPermissions = requiredPermissions.every(permission =>
          checkPermission(permission)
        );

        if (!hasAllPermissions) {
          router.push('/unauthorized');
        }
      }
    }, [user, isLoading, router]);

    if (isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            <p className="text-gray-600">Loading...</p>
          </div>
        </div>
      );
    }

    if (!user) {
      return null;
    }

    if (requiredPermissions.length > 0) {
      const hasAllPermissions = requiredPermissions.every(permission =>
        checkPermission(permission)
      );

      if (!hasAllPermissions) {
        return null;
      }
    }

    return <WrappedComponent {...props} />;
  };
}; 