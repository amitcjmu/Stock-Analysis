import React from 'react';
import { useGlobalAuth, useGlobalUserContext } from './index';
import type { AuthContextType } from '../AuthContext/types';

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
    register: async (userData: any) => {
      // Placeholder for register functionality
      throw new Error('Register functionality not yet migrated to GlobalContext');
    },
    logout,
    switchClient: async (clientId: string, clientData?: any) => {
      await switchClient(clientId, clientData);
    },
    switchEngagement: async (engagementId: string, engagementData?: any) => {
      await switchEngagement(engagementId, engagementData);
    },
    switchFlow: async (flowId: string, flowData?: any) => {
      await switchFlow(flowId, flowData);
    },
    setCurrentFlow: (flow: any) => {
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
export const useClientCompat = () => {
  const { client, switchClient, hasContext } = useGlobalUserContext();
  const { user } = useGlobalAuth();

  return React.useMemo(() => ({
    currentClient: client,
    availableClients: [], // This would need to be fetched from an API
    isLoading: false, // GlobalContext handles loading differently
    error: null,
    selectClient: async (id: string) => {
      await switchClient(id);
    },
    switchClient: async (id: string) => {
      await switchClient(id);
    },
    clearClient: () => {
      // This would need to be implemented in GlobalContext
    },
    getClientId: () => client?.id || null,
    setDemoClient: (clientData: any) => {
      // This would need to be implemented in GlobalContext
    },
  }), [client, switchClient, hasContext]);
};

/**
 * Compatibility hook for EngagementContext
 */
export const useEngagementCompat = () => {
  const { engagement, switchEngagement } = useGlobalUserContext();

  return React.useMemo(() => ({
    currentEngagement: engagement,
    isLoading: false,
    error: null,
    selectEngagement: async (id: string) => {
      await switchEngagement(id);
    },
    clearEngagement: () => {
      // This would need to be implemented in GlobalContext
    },
    getEngagementId: () => engagement?.id || null,
    setDemoEngagement: (engagementData: any) => {
      // This would need to be implemented in GlobalContext
    },
  }), [engagement, switchEngagement]);
};

/**
 * Feature flag controlled context provider wrapper
 * This allows gradual rollout of the new GlobalContext
 */
interface ContextMigrationProviderProps {
  children: React.ReactNode;
  useGlobalContext?: boolean;
}

export const ContextMigrationProvider: React.FC<ContextMigrationProviderProps> = ({
  children,
  useGlobalContext = process.env.NODE_ENV === 'development',
}) => {
  if (useGlobalContext) {
    // Use the new GlobalContext system
    return <>{children}</>;
  } else {
    // Fall back to the original context providers
    // This would import and use the original providers
    return <>{children}</>;
  }
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
) => {
  const { requireAuth = true, requireClient = false, requireEngagement = false } = options;

  return React.memo((props: P) => {
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
 * Context debugging tools
 */
export const ContextDebugger: React.FC = () => {
  const { state } = useGlobalAuth() as any; // Access to full global state
  const [isVisible, setIsVisible] = React.useState(false);

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <>
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="fixed bottom-4 right-4 bg-blue-600 text-white p-2 rounded-full shadow-lg z-50"
        title="Toggle Context Debugger"
      >
        🐛
      </button>

      {isVisible && (
        <div className="fixed bottom-16 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-md max-h-96 overflow-auto z-50">
          <h3 className="font-semibold mb-2">Context Debug Info</h3>
          <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto">
            {JSON.stringify({
              auth: state?.auth,
              context: state?.context,
              ui: state?.ui,
              cache: state?.cache,
              performance: state?.performance,
              featureFlags: state?.featureFlags,
            }, null, 2)}
          </pre>
        </div>
      )}
    </>
  );
};

/**
 * Performance debugging component
 */
export const PerformanceDebugger: React.FC = () => {
  const { metrics, enabled } = useGlobalAuth() as any; // Access to performance metrics
  const [isVisible, setIsVisible] = React.useState(false);

  if (process.env.NODE_ENV !== 'development' || !enabled) {
    return null;
  }

  return (
    <>
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="fixed bottom-4 right-16 bg-green-600 text-white p-2 rounded-full shadow-lg z-50"
        title="Toggle Performance Debugger"
      >
        ⚡
      </button>

      {isVisible && (
        <div className="fixed bottom-16 right-16 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-md z-50">
          <h3 className="font-semibold mb-2">Performance Metrics</h3>
          <div className="text-sm space-y-1">
            <div>Render Count: {metrics?.renderCount || 0}</div>
            <div>Avg Render Time: {(metrics?.averageRenderTime || 0).toFixed(2)}ms</div>
            <div>Cache Hit Rate: {((metrics?.cacheHitRate || 0) * 100).toFixed(1)}%</div>
            <div>API Calls: {metrics?.apiCallCount || 0}</div>
          </div>
        </div>
      )}
    </>
  );
};

/**
 * Migration status indicator
 */
export const MigrationStatusIndicator: React.FC = () => {
  const [migrationStatus] = React.useState({
    globalContext: true,
    performanceMonitoring: true,
    featureFlags: true,
    cacheIntegration: true,
  });

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  const completedCount = Object.values(migrationStatus).filter(Boolean).length;
  const totalCount = Object.keys(migrationStatus).length;
  const percentage = (completedCount / totalCount) * 100;

  return (
    <div className="fixed top-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-3 text-sm z-50">
      <div className="font-semibold mb-1">Migration Status</div>
      <div className="flex items-center space-x-2">
        <div className="w-20 bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span>{completedCount}/{totalCount}</span>
      </div>
    </div>
  );
};
