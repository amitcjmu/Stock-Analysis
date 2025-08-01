/**
 * GlobalContext hooks
 * Separated to avoid React Fast Refresh warnings
 */

import { useContext } from 'react';
import { GlobalContext } from './context';
import type { GlobalContextType } from './types';

/**
 * Hook to use the Global Context
 */
export const useGlobalContext = (): GlobalContextType => {
  const context = useContext(GlobalContext);
  if (context === undefined) {
    throw new Error('useGlobalContext must be used within a GlobalContextProvider');
  }
  return context;
};

/**
 * Hook to use auth state and actions
 */
export const useGlobalAuth = (): {
  user: GlobalContextType['state']['auth']['user'];
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;
  isDemoMode: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: GlobalContextType['login'];
  logout: GlobalContextType['logout'];
  initializeAuth: GlobalContextType['initializeAuth'];
} => {
  const { state, login, logout, initializeAuth, isAuthenticated, isAdmin } = useGlobalContext();

  return {
    user: state.auth.user,
    isLoading: state.auth.isLoading,
    isInitialized: state.auth.isInitialized,
    error: state.auth.error,
    isDemoMode: state.auth.isDemoMode,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    initializeAuth,
  };
};

/**
 * Hook to use context state and actions
 */
export const useGlobalUserContext = (): {
  client: GlobalContextType['state']['context']['client'];
  engagement: GlobalContextType['state']['context']['engagement'];
  flow: GlobalContextType['state']['context']['flow'];
  isLoading: boolean;
  error: string | null;
  switchClient: GlobalContextType['switchClient'];
  switchEngagement: GlobalContextType['switchEngagement'];
  switchFlow: GlobalContextType['switchFlow'];
  hasContext: boolean;
  getAuthHeaders: GlobalContextType['getAuthHeaders'];
} => {
  const {
    state,
    switchClient,
    switchEngagement,
    switchFlow,
    hasContext,
    getAuthHeaders
  } = useGlobalContext();

  return {
    client: state.context.client,
    engagement: state.context.engagement,
    flow: state.context.flow,
    isLoading: state.context.isLoading,
    error: state.context.error,
    switchClient,
    switchEngagement,
    switchFlow,
    hasContext,
    getAuthHeaders,
  };
};

/**
 * Hook to use UI state and actions
 */
export const useGlobalUIState = (): {
  sidebarOpen: boolean;
  notifications: GlobalContextType['state']['ui']['notifications'];
  isLoading: boolean;
  theme: GlobalContextType['state']['ui']['theme'];
  toggleSidebar: () => void;
  setTheme: (theme: GlobalContextType['state']['ui']['theme']) => void;
  addNotification: GlobalContextType['addNotification'];
  removeNotification: GlobalContextType['removeNotification'];
} => {
  const { state, dispatch, addNotification, removeNotification } = useGlobalContext();

  return {
    sidebarOpen: state.ui.sidebarOpen,
    notifications: state.ui.notifications,
    isLoading: state.ui.isLoading,
    theme: state.ui.theme,
    toggleSidebar: () => dispatch({ type: 'UI_TOGGLE_SIDEBAR' }),
    setTheme: (theme) => dispatch({ type: 'UI_SET_THEME', payload: theme }),
    addNotification,
    removeNotification,
  };
};

/**
 * Hook to use cache state
 */
export const useGlobalCacheState = (): {
  isEnabled: boolean;
  isConnected: boolean;
  lastSyncTime: number | null;
  pendingInvalidations: string[];
  invalidateCache: GlobalContextType['invalidateCache'];
} => {
  const { state, invalidateCache } = useGlobalContext();

  return {
    isEnabled: state.cache.isEnabled,
    isConnected: state.cache.isConnected,
    lastSyncTime: state.cache.lastSyncTime,
    pendingInvalidations: state.cache.pendingInvalidations,
    invalidateCache,
  };
};
