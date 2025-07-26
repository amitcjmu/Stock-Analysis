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
            console.log('🔄 Token expired, clearing from storage');
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
        localStorage.setItem('auth_token', token);
      } else {
        localStorage.removeItem('auth_token');
      }
    } catch (error) {
      console.error("Failed to set token in localStorage", error);
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
  removeToken: () => {
    try {
      localStorage.removeItem('auth_token');
    } catch (error) {
      console.error("Failed to remove token from localStorage", error);
    }
  },
  removeUser: () => {
    try {
      localStorage.removeItem('auth_user');
    } catch (error) {
      console.error("Failed to remove user from localStorage", error);
    }
  },
};

const CONTEXT_STORAGE_KEY = 'user_context_selection';

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
  setContext: (context: ContextData) => {
    localStorage.setItem(CONTEXT_STORAGE_KEY, JSON.stringify(context));
  },
  clearContext: () => {
    localStorage.removeItem(CONTEXT_STORAGE_KEY);
  }
};

export const persistClientData = (client: Client): any => {
  localStorage.setItem('auth_client', JSON.stringify(client));
  localStorage.setItem('auth_client_id', client.id);
};

export const persistEngagementData = (engagement: Engagement): any => {
  localStorage.setItem('auth_engagement', JSON.stringify(engagement));
};

export const persistSessionData = (session: ExternalSessionData): any => {
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

export const clearInvalidContextData = (): any => {
  console.log('🧹 Clearing invalid context data from localStorage');
  localStorage.removeItem('auth_client');
  localStorage.removeItem('auth_engagement');
  localStorage.removeItem('auth_client_id');
  localStorage.removeItem('user_context_selection');
};

export const clearAllStoredData = (): any => {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  localStorage.removeItem('auth_client');
  localStorage.removeItem('auth_engagement');
  localStorage.removeItem('auth_session');
  localStorage.removeItem('auth_client_id');
  localStorage.removeItem('user_data');
  localStorage.removeItem('user_context_selection');
};
