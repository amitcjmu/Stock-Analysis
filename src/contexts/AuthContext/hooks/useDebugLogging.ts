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
    // Only log authentication state changes, not every render
    if (process.env.NODE_ENV === 'development') {
      console.log('🔐 Auth State:', {
        authenticated: isAuthenticated,
        user: user?.email || 'none',
        role: user?.role || 'none'
      });
    }
  }, [isAuthenticated, user?.id]); // Only log when authentication status or user actually changes
};