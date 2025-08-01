/**
 * Engagement Context Hooks
 * Custom hooks for accessing the Engagement context
 */

import React, { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { EngagementContext } from './context';
import type { EngagementContextType } from './types';

export const useEngagement = (): EngagementContextType => {
  const context = useContext(EngagementContext);
  if (context === undefined) {
    throw new Error('useEngagement must be used within an EngagementProvider');
  }
  return context;
};

export const withEngagement = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  requireEngagement: boolean = true
) => {
  return function WithEngagementComponent(props: P): React.ReactElement | null {
    const { currentEngagement, isLoading } = useEngagement();
    const navigate = useNavigate();

    useEffect(() => {
      if (!isLoading && requireEngagement && !currentEngagement) {
        navigate('/engagements');
      }
    }, [currentEngagement, isLoading, navigate]);

    if (isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            <p className="text-gray-600">Loading engagement...</p>
          </div>
        </div>
      );
    }

    if (requireEngagement && !currentEngagement) {
      return null;
    }

    return <WrappedComponent {...props} />;
  };
};
