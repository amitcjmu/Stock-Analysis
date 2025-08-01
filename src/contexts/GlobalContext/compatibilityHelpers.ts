/**
 * Helper functions and constants for GlobalContext compatibility
 * Separated to avoid React Fast Refresh warnings
 */

import type { Client, Engagement, User } from './types';

// Type definitions
export interface AuthCompatReturn {
  user: User | null;
  isLoading: boolean;
  isInitialized: boolean;
  error: Error | null;
  isDemoMode: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (credentials: { username: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  initializeAuth: () => Promise<void>;
  refreshUser: () => Promise<void>;
  getAuthHeaders: () => Record<string, string>;
  clearError: () => void;
  checkAuthStatus: () => Promise<void>;
}

export interface ClientCompatReturn {
  client: Client | null;
  isLoading: boolean;
  error: Error | null;
  setClient: (client: Client | null) => void;
  clearClient: () => void;
  getClientId: () => string | null;
  setDemoClient: (clientData: unknown) => void;
}

export interface EngagementCompatReturn {
  engagement: Engagement | null;
  engagements: Engagement[];
  isLoading: boolean;
  error: Error | null;
  switchEngagement: (id: string) => Promise<void>;
  clearEngagement: () => void;
  getEngagementId: () => string | null;
  setDemoEngagement: (engagementData: unknown) => void;
}

export interface GlobalAuthState {
  state?: unknown;
  metrics?: unknown;
  enabled?: boolean;
}

// Helper function to check if context is available
export const hasContext = (
  isAuthenticated: boolean,
  client: Client | null,
  engagement: Engagement | null,
  requireAuth: boolean,
  requireClient: boolean,
  requireEngagement: boolean
): boolean => {
  if (requireAuth && !isAuthenticated) return false;
  if (requireClient && !client) return false;
  if (requireEngagement && !engagement) return false;
  return true;
};

// Context debugging helpers
export const getDebugState = (state: unknown): unknown => {
  return state || {};
};

export const getPerformanceMetrics = (auth: GlobalAuthState): { metrics: unknown; enabled: boolean } => {
  return {
    metrics: auth.metrics || {},
    enabled: auth.enabled || false
  };
};
