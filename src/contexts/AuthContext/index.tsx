import React from 'react'
import { createContext, useContext, useState } from 'react'
import { useCallback } from 'react'
import type { AuthContextType } from './types'
import type { User, Client, Engagement, Flow } from './types'
import { tokenStorage } from './storage';
import { useAuthHeaders } from './hooks/useAuthHeaders';
import { useAuthInitialization } from './hooks/useAuthInitialization';
import { useAuthService } from './services/authService';
import { useDebugLogging } from './hooks/useDebugLogging';
import { useApiContextSync } from './hooks/useApiContextSync';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => tokenStorage.getUser());
  const [client, setClient] = useState<Client | null>(() => {
    try {
      const stored = localStorage.getItem('auth_client');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [engagement, setEngagement] = useState<Engagement | null>(() => {
    try {
      const stored = localStorage.getItem('auth_engagement');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [flow, setFlow] = useState<Flow | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoginInProgress, setIsLoginInProgress] = useState(false);

  const isDemoMode = false;
  const isAuthenticated = !!user;
  const isAdmin = user?.role === 'admin' || user?.role === 'platform_admin';

  const getAuthHeaders = useAuthHeaders(user, client, engagement, flow?.id || null);

  const {
    login,
    register,
    logout,
    switchClient,
    switchEngagement,
    switchFlow,
    fetchDefaultContext,
    debouncedFetchDefaultContext
  } = useAuthService(
    user,
    client,
    engagement,
    flow,
    setUser,
    setClient,
    setEngagement,
    setFlow,
    setIsLoading,
    setError,
    setIsLoginInProgress,
    getAuthHeaders
  );

  useAuthInitialization({
    setUser,
    setClient,
    setEngagement,
    setFlow,
    setIsLoading,
    switchClient,
    fetchDefaultContext
  });

  useDebugLogging(user, isAuthenticated, isAdmin, isDemoMode, getAuthHeaders);
  useApiContextSync(user, client, engagement, flow);

  const setCurrentFlow = useCallback((flow: Flow | null) => {
    setFlow(flow);
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      client,
      engagement,
      flow,
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
      switchFlow,
      setCurrentFlow,
      currentEngagementId: engagement?.id || null,
      currentFlowId: flow?.id || null,
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

// Re-export types for convenience
export type { AuthContextType, User, Client, Engagement, Session, Flow } from './types';