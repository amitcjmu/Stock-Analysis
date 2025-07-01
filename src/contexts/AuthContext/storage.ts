import { TokenStorage, User, ContextData } from './types';

export const tokenStorage: TokenStorage = {
  getToken: () => localStorage.getItem('auth_token'),
  setToken: (token) => localStorage.setItem('auth_token', token),
  getUser: () => {
    const userData = localStorage.getItem('user_data');
    try {
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error("Failed to parse user data from localStorage", error);
      return null;
    }
  },
  setUser: (user) => localStorage.setItem('user_data', JSON.stringify(user)),
  getRedirectPath: () => localStorage.getItem('redirect_path'),
  setRedirectPath: (path) => localStorage.setItem('redirect_path', path),
  clearRedirectPath: () => localStorage.removeItem('redirect_path'),
  removeToken: () => localStorage.removeItem('auth_token'),
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

export const persistClientData = (client: any) => {
  localStorage.setItem('auth_client', JSON.stringify(client));
  localStorage.setItem('auth_client_id', client.id);
};

export const persistEngagementData = (engagement: any) => {
  localStorage.setItem('auth_engagement', JSON.stringify(engagement));
};

export const persistSessionData = (session: any) => {
  localStorage.setItem('auth_session', JSON.stringify(session));
};

export const getStoredClientData = () => {
  const storedClient = localStorage.getItem('auth_client');
  if (storedClient) {
    try {
      return JSON.parse(storedClient);
    } catch (error) {
      console.warn('Failed to parse stored client data:', error);
      return null;
    }
  }
  return null;
};

export const getStoredEngagementData = () => {
  const storedEngagement = localStorage.getItem('auth_engagement');
  if (storedEngagement) {
    try {
      return JSON.parse(storedEngagement);
    } catch (error) {
      console.warn('Failed to parse stored engagement data:', error);
      return null;
    }
  }
  return null;
};

export const getStoredSessionData = () => {
  const storedSession = localStorage.getItem('auth_session');
  if (storedSession) {
    try {
      return JSON.parse(storedSession);
    } catch (error) {
      console.warn('Failed to parse stored session data:', error);
      return null;
    }
  }
  return null;
};

export const clearAllStoredData = () => {
  localStorage.removeItem('auth_client');
  localStorage.removeItem('auth_engagement');
  localStorage.removeItem('auth_session');
  localStorage.removeItem('auth_client_id');
};