import React, { createContext, useContext, useState, useCallback } from 'react';
import { AuthContextType, User, Client, Engagement, Session, Flow } from './types';
import { tokenStorage } from './storage';
import { useAuthHeaders } from './hooks/useAuthHeaders';
import { useAuthInitialization } from './hooks/useAuthInitialization';
import { useAuthService } from './services/authService';
import { useDebugLogging } from './hooks/useDebugLogging';
import { useApiContextSync } from './hooks/useApiContextSync';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => tokenStorage.getUser());
  const [client, setClient] = useState<Client | null>(null);
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [session, setSession] = useState<Session | null>(null);
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
    switchSession,
    fetchDefaultContext
  } = useAuthService(
    user,
    client,
    engagement,
    session,
    setUser,
    setClient,
    setEngagement,
    setSession,
    setIsLoading,
    setError,
    setIsLoginInProgress,
    getAuthHeaders
  );

  useAuthInitialization({
    setUser,
    setClient,
    setEngagement,
    setSession,
    setIsLoading,
    switchClient,
    fetchDefaultContext
  });

  useDebugLogging(user, isAuthenticated, isAdmin, isDemoMode, getAuthHeaders);
  useApiContextSync(user, client, engagement, session);

  const setCurrentSession = useCallback((session: Session | null) => {
    setSession(session);
  }, []);

  const setCurrentFlow = useCallback((flow: Flow | null) => {
    setFlow(flow);
  }, []);

  const switchFlow = async (flowId: string, flowData?: Flow) => {
    // Placeholder for flow switching implementation
    console.log('Switching to flow:', flowId, flowData);
    if (flowData) {
      setFlow(flowData);
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      client,
      engagement,
      session,
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
      switchSession,
      switchFlow,
      setCurrentSession,
      setCurrentFlow,
      currentEngagementId: engagement?.id || null,
      currentSessionId: session?.id || null,
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