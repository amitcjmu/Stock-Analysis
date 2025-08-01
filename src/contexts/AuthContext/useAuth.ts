/**
 * useAuth Hook
 * Hook for accessing the AuthContext
 */

import { useContext } from 'react';
import { AuthContext } from './context';
import type { AuthContextType } from './types';

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};