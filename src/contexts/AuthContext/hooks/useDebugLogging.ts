import { useEffect } from 'react';
import { User, Client, Engagement, Session } from '../types';
import { tokenStorage } from '../storage';

export const useDebugLogging = (
  user: User | null,
  isAuthenticated: boolean,
  isAdmin: boolean,
  isDemoMode: boolean,
  getAuthHeaders: () => Record<string, string>
) => {
  useEffect(() => {
    const token = tokenStorage.getToken();
    const storedUser = tokenStorage.getUser();
    console.log('🔍 Auth State Debug:', {
      user: user ? { 
        id: user.id, 
        role: user.role, 
        full_name: user.full_name,
        email: user.email 
      } : null,
      isAuthenticated,
      isAdmin,
      isDemoMode,
      token: token ? `present (${token.substring(0, 20)}...)` : 'missing',
      tokenLength: token ? token.length : 0,
      localStorage_user: storedUser ? `present (${storedUser.email})` : 'missing',
      localStorage_keys: Object.keys(localStorage).filter(key => key.startsWith('auth_')),
      getAuthHeaders_result: getAuthHeaders()
    });
  }, [user, isAuthenticated, isAdmin, isDemoMode, getAuthHeaders]);
};