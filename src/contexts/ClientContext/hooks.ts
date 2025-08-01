/**
 * Client Context Hooks
 * Custom hooks for accessing the Client context
 */

import React from 'react';
import { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClientContext } from './context';
import type { ClientContextType } from './types';
import { useAuth } from '../AuthContext';

export const useClient = (): ClientContextType => {
  const context = useContext(ClientContext);
  if (context === undefined) {
    throw new Error('useClient must be used within a ClientProvider');
  }
  return context;
};

export const withClient = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  requireClient: boolean = true
) => {
  return function WithClientComponent(props: P): React.ReactElement | null {
    const { currentClient, isLoading } = useClient();
    const { user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
      if (!isLoading && requireClient && !currentClient) {
        // Skip client requirement for admin routes
        if (user?.role === 'admin' && window.location.pathname.startsWith('/admin')) {
          return;
        }

        // For non-admin users or admin users on non-admin routes
        if (!currentClient) {
          navigate('/session/select');
        }
      }
    }, [currentClient, isLoading, navigate, user?.role]);

    if (isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            <p className="text-gray-600">Loading client...</p>
          </div>
        </div>
      );
    }

    // Skip client requirement for admin routes
    if (requireClient && !currentClient && !(user?.role === 'admin' && window.location.pathname.startsWith('/admin'))) {
      return null;
    }

    return <WrappedComponent {...props} />;
  };
};