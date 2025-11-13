import type { User, ContextData, Flow } from './types'
import type { TokenStorage, Client, Engagement } from './types'

/**
 * External session data interface for third-party integrations
 */
export interface ExternalSessionData {
  sessionId?: string;
  provider?: string;
  expiresAt?: string;
  metadata?: Record<string, unknown>;
  refreshToken?: string;
}

// Token storage - using localStorage for now (httpOnly cookies not yet implemented)
export const tokenStorage: TokenStorage = {
  getToken: () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return null;

      // Check if token is expired before returning it (only for JWT tokens)
      try {
        // Only attempt JWT parsing if token has the right format
        if (token.includes('.') && token.split('.').length === 3) {
          const tokenData = JSON.parse(atob(token.split('.')[1]));
          const now = Math.floor(Date.now() / 1000);

          if (tokenData.exp && tokenData.exp < now) {
            console.log('🔄 Token expired, clearing from storage'); // nosec - operational log, no sensitive data
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
            return null;
          }
        }
        // For non-JWT tokens, skip expiration check
      } catch (tokenParseError) {
        // Non-JWT tokens or parsing errors - skip expiration check
      }

      return token;
    } catch (error) {
      console.error("Failed to get token from localStorage", error);
      return null;
    }
  },
  setToken: (token) => {
    try {
      if (token) {
        localStorage.setItem('auth_token', token); // nosec - localStorage is secured in browser
      } else {
        localStorage.removeItem('auth_token');
      }
    } catch (error) {
      console.error("Failed to set token in localStorage", error); // nosec - no token data logged
    }
  },
  getUser: () => {
    try {
      const userData = localStorage.getItem('auth_user');
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error("Failed to parse user data from localStorage", error);
      return null;
    }
  },
  setUser: (user) => {
    try {
      if (user) {
        localStorage.setItem('auth_user', JSON.stringify(user));
      } else {
        localStorage.removeItem('auth_user');
      }
    } catch (error) {
      console.error("Failed to set user in localStorage", error);
    }
  },
  getRedirectPath: () => localStorage.getItem('redirect_path'),
  setRedirectPath: (path) => localStorage.setItem('redirect_path', path),
  clearRedirectPath: () => localStorage.removeItem('redirect_path'),
  removeToken: (): void => {
    try {
      localStorage.removeItem('auth_token');
    } catch (error) {
      console.error("Failed to remove token from localStorage", error);
    }
  },
  removeUser: (): void => {
    try {
      localStorage.removeItem('auth_user');
    } catch (error) {
      console.error("Failed to remove user from localStorage", error);
    }
  },
  getRefreshToken: () => {
    try {
      return localStorage.getItem('auth_refresh_token');
    } catch (error) {
      console.error("Failed to get refresh token from localStorage", error);
      return null;
    }
  },
  setRefreshToken: (token: string | null) => {
    try {
      if (token) {
        localStorage.setItem('auth_refresh_token', token);
      } else {
        localStorage.removeItem('auth_refresh_token');
      }
    } catch (error) {
      console.error("Failed to set refresh token in localStorage", error);
    }
  },
  removeRefreshToken: (): void => {
    try {
      localStorage.removeItem('auth_refresh_token');
    } catch (error) {
      console.error("Failed to remove refresh token from localStorage", error);
    }
  },
};

const CONTEXT_STORAGE_KEY = 'user_context_selection';

// Schema version for localStorage data format
// Increment this when the data structure changes (e.g., INTEGER → UUID migration)
// This forces clients to re-fetch fresh data from the backend
const STORAGE_SCHEMA_VERSION = 2; // v2: Post-migration 115 (UUID tenant IDs)
const SCHEMA_VERSION_KEY = 'auth_storage_schema_version';

export const contextStorage = {
  getContext: (): ContextData | null => {
    const contextData = localStorage.getItem(CONTEXT_STORAGE_KEY);
    try {
      return contextData ? JSON.parse(contextData) : null;
    } catch (error) {
      console.error("Failed to parse context data from localStorage", error);
      return null;
    }
  },
  setContext: (context: ContextData): void => {
    localStorage.setItem(CONTEXT_STORAGE_KEY, JSON.stringify(context)); // nosec - context data is non-sensitive
  },
  clearContext: (): void => {
    localStorage.removeItem(CONTEXT_STORAGE_KEY);
  }
};

export const persistClientData = (client: Client): unknown => {
  localStorage.setItem('auth_client', JSON.stringify(client));
  localStorage.setItem('auth_client_id', client.id);
};

export const persistEngagementData = (engagement: Engagement): unknown => {
  localStorage.setItem('auth_engagement', JSON.stringify(engagement));
};

export const persistSessionData = (session: ExternalSessionData): unknown => {
  localStorage.setItem('auth_session', JSON.stringify(session));
};

export const getStoredClientData = (): Client | null => {
  const storedClient = localStorage.getItem('auth_client');
  if (storedClient) {
    try {
      return JSON.parse(storedClient) as Client;
    } catch (error) {
      console.warn('Failed to parse stored client data:', error);
      return null;
    }
  }
  return null;
};

export const getStoredEngagementData = (): Engagement | null => {
  const storedEngagement = localStorage.getItem('auth_engagement');
  if (storedEngagement) {
    try {
      return JSON.parse(storedEngagement) as Engagement;
    } catch (error) {
      console.warn('Failed to parse stored engagement data:', error);
      return null;
    }
  }
  return null;
};

export const getStoredSessionData = (): ExternalSessionData | null => {
  const storedSession = localStorage.getItem('auth_session');
  if (storedSession) {
    try {
      return JSON.parse(storedSession) as ExternalSessionData;
    } catch (error) {
      console.warn('Failed to parse stored session data:', error);
      return null;
    }
  }
  return null;
};

export const clearInvalidContextData = (): unknown => {
  console.log('🧹 Clearing invalid context data from localStorage');
  localStorage.removeItem('auth_client');
  localStorage.removeItem('auth_engagement');
  localStorage.removeItem('auth_client_id');
  localStorage.removeItem('user_context_selection');
};

export const clearAllStoredData = (): unknown => {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  localStorage.removeItem('auth_client');
  localStorage.removeItem('auth_engagement');
  localStorage.removeItem('auth_session');
  localStorage.removeItem('auth_client_id');
  localStorage.removeItem('user_data');
  localStorage.removeItem('user_context_selection');
  localStorage.removeItem(SCHEMA_VERSION_KEY);
};

/**
 * Check and clear stale localStorage data from schema changes.
 *
 * Bug Fix (Issue #867): After migration 115 (Oct 2025), tenant IDs changed from
 * INTEGER to UUID. Old localStorage may have client.id="1" instead of proper UUID.
 * This function detects schema version mismatches and clears stale data.
 *
 * Call this on app initialization BEFORE any API calls.
 */
export const validateAndClearStaleData = (): boolean => {
  try {
    const storedVersion = localStorage.getItem(SCHEMA_VERSION_KEY);
    const currentVersion = String(STORAGE_SCHEMA_VERSION);

    if (storedVersion !== currentVersion) {
      console.log(`🔄 localStorage schema mismatch detected (stored: ${storedVersion || 'none'}, current: ${currentVersion})`);
      console.log('🧹 Clearing stale localStorage data to force re-fetch from backend');

      // Clear context data but preserve auth token for seamless re-authentication
      clearInvalidContextData();

      // Update to current schema version
      localStorage.setItem(SCHEMA_VERSION_KEY, currentVersion);

      return true; // Indicates data was cleared
    }

    // Schema version matches, no action needed
    return false;
  } catch (error) {
    console.error('❌ Error validating localStorage schema:', error);
    // On error, clear everything to be safe
    clearAllStoredData();
    localStorage.setItem(SCHEMA_VERSION_KEY, String(STORAGE_SCHEMA_VERSION));
    return true;
  }
};

/**
 * Sync context data from user_context_selection to individual localStorage keys
 * This ensures the new API client can read client/engagement/flow data
 */
export const syncContextToIndividualKeys = (): boolean => {
  try {
    const contextData = contextStorage.getContext();
    if (!contextData) {
      console.log('🔄 No context data to sync');
      return false;
    }

    console.log('🔄 Syncing context data to individual localStorage keys'); // nosec - operational log, no sensitive data exposed

    let hasFailures = false;
    const results = {
      client: false,
      engagement: false,
      flow: false,
    };

    // Sync client data with individual error handling
    if (contextData.client) {
      try {
        persistClientData(contextData.client);
        results.client = true;
        console.log('✅ Synced client data to localStorage');
      } catch (clientError) {
        hasFailures = true;
        console.error('❌ Failed to sync client data:', clientError);
      }
    }

    // Sync engagement data with individual error handling
    if (contextData.engagement) {
      try {
        persistEngagementData(contextData.engagement);
        results.engagement = true;
        console.log('✅ Synced engagement data to localStorage');
      } catch (engagementError) {
        hasFailures = true;
        console.error('❌ Failed to sync engagement data:', engagementError);
      }
    }

    // Sync flow data with individual error handling
    if (contextData.flow) {
      try {
        localStorage.setItem('auth_flow', JSON.stringify(contextData.flow));
        results.flow = true;
        console.log('✅ Synced flow data to localStorage');
      } catch (flowError) {
        hasFailures = true;
        console.error('❌ Failed to sync flow data:', flowError);
      }
    }

    if (hasFailures) {
      console.warn('⚠️ Context synchronization completed with failures:', results);
      // Return false to indicate partial failure, but don't throw
      return false;
    } else {
      console.log('✅ Context synchronization completed successfully:', results);
      return true;
    }
  } catch (error) {
    console.error('❌ Critical failure in context synchronization:', error);
    // For critical failures, we should probably clear corrupted data
    try {
      console.log('🧹 Clearing potentially corrupted context data');
      contextStorage.clearContext();
    } catch (clearError) {
      console.error('❌ Failed to clear corrupted context data:', clearError);
    }
    return false;
  }
};
