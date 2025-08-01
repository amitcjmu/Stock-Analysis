import { useEffect } from 'react';
import type { User, Client, Engagement, Session } from '../types';
import type { tokenStorage } from '../storage';

export const useDebugLogging = (
  user: User | null,
  isAuthenticated: boolean,
  isAdmin: boolean,
  isDemoMode: boolean,
  getAuthHeaders: () => Record<string, string>
): void => {
  useEffect(() => {
    // Only log authentication state changes, not every render
    if (process.env.NODE_ENV === 'development') {
      console.log('🔐 Auth State:', {
        authenticated: isAuthenticated,
        user: user?.email || 'none',
        role: user?.role || 'none',
        isAdmin,
        expectedIsAdmin: user?.role === 'admin'
      });
    }
  }, [isAuthenticated, user?.id, user?.role, user?.email, isAdmin]); // Only log when authentication status or user actually changes
};
