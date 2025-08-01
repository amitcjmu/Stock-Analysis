/**
 * Compatibility hooks for GlobalContext
 * Separated to avoid React Fast Refresh warnings
 */

import React from 'react';
import { useGlobalAuth, useGlobalUserContext } from './hooks';
import type { AuthContextType } from '../AuthContext/types';
import type { Client, Engagement, Flow } from './types';
import {
  type AuthCompatReturn,
  type ClientCompatReturn,
  type EngagementCompatReturn,
  type GlobalAuthState,
  getDebugState,
  getPerformanceMetrics
} from './compatibilityHelpers';

/**
 * Compatibility hook that maintains the same interface as the original useAuth hook
 * This allows for gradual migration without breaking existing components
 */
export const useAuthCompat = (): AuthContextType => {
  const {
    user,
    isLoading,
    isInitialized,
    error,
    isDemoMode,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    initializeAuth,
  } = useGlobalAuth();

  const {
    client,
    engagement,
    flow,
    switchClient,
    switchEngagement,
    switchFlow,
    getAuthHeaders,
  } = useGlobalUserContext();

  // Create a compatible interface
  return React.useMemo(() => ({
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
    register: async (userData: { email: string; password: string; name?: string }) => {
      // Placeholder for register functionality
      throw new Error('Register functionality not yet migrated to GlobalContext');
    },
    logout,
    switchClient: async (clientId: string, clientData?: Client) => {
      await switchClient(clientId, clientData);
    },
    switchEngagement: async (engagementId: string, engagementData?: Engagement) => {
      await switchEngagement(engagementId, engagementData);
    },
    switchFlow: async (flowId: string, flowData?: Flow) => {
      await switchFlow(flowId, flowData);
    },
    setCurrentFlow: (flow: Flow | null) => {
      if (flow) {
        switchFlow(flow.id, flow);
      }
    },
    currentEngagementId: engagement?.id || null,
    currentFlowId: flow?.id || null,
    getAuthHeaders,
  }), [
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
    logout,
    switchClient,
    switchEngagement,
    switchFlow,
    getAuthHeaders,
  ]);
};

/**
 * Compatibility hook for ClientContext
 */
export const useClientCompat = (): ClientCompatReturn => {
  const { client, switchClient } = useGlobalUserContext();

  return React.useMemo(() => ({
    client: client,
    isLoading: false, // GlobalContext handles loading differently
    error: null,
    setClient: async (client: Client | null) => {
      if (client) {
        await switchClient(client.id, client);
      }
    },
    clearClient: () => {
      // This would need to be implemented in GlobalContext
    },
    getClientId: () => client?.id || null,
    setDemoClient: (clientData: unknown) => {
      // This would need to be implemented in GlobalContext
    },
  }), [client, switchClient]);
};

/**
 * Compatibility hook for EngagementContext
 */
export const useEngagementCompat = (): EngagementCompatReturn => {
  const { engagement, switchEngagement } = useGlobalUserContext();

  return React.useMemo(() => ({
    engagement: engagement,
    engagements: [], // This would need to be fetched from an API
    isLoading: false,
    error: null,
    switchEngagement: async (id: string) => {
      await switchEngagement(id);
    },
    clearEngagement: () => {
      // This would need to be implemented in GlobalContext
    },
    getEngagementId: () => engagement?.id || null,
    setDemoEngagement: (engagementData: unknown) => {
      // This would need to be implemented in GlobalContext
    },
  }), [engagement, switchEngagement]);
};

/**
 * Higher-order component to provide compatibility during migration
 */
export const withContextMigration = <P extends object>(
  Component: React.ComponentType<P>,
  options: {
    requireAuth?: boolean;
    requireClient?: boolean;
    requireEngagement?: boolean;
  } = {}
): React.ComponentType<P> => {
  const { requireAuth = true, requireClient = false, requireEngagement = false } = options;

  return React.memo((props: P): React.ReactElement | null => {
    const { isAuthenticated, isLoading: authLoading } = useGlobalAuth();
    const { client, engagement, isLoading: contextLoading } = useGlobalUserContext();

    // Loading state
    if (authLoading || contextLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            <p className="text-gray-600">Loading...</p>
          </div>
        </div>
      );
    }

    // Auth requirement
    if (requireAuth && !isAuthenticated) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
            <p className="text-gray-600">Please log in to access this page.</p>
          </div>
        </div>
      );
    }

    // Client requirement
    if (requireClient && !client) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">Client Selection Required</h2>
            <p className="text-gray-600">Please select a client to continue.</p>
          </div>
        </div>
      );
    }

    // Engagement requirement
    if (requireEngagement && !engagement) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">Engagement Selection Required</h2>
            <p className="text-gray-600">Please select an engagement to continue.</p>
          </div>
        </div>
      );
    }

    return <Component {...props} />;
  });
};

/**
 * Hook for context debugging
 */
export const useContextDebug = (): { state: unknown; metrics: unknown; enabled: boolean } => {
  const auth = useGlobalAuth() as GlobalAuthState;
  const state = getDebugState(auth.state);
  const { metrics, enabled } = getPerformanceMetrics(auth);
  
  return { state, metrics, enabled };
};