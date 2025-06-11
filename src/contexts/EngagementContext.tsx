import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from './AuthContext';
import { useClient } from './ClientContext';
import { apiCall } from '@/lib/api';

interface Engagement {
  id: string;
  name: string;
  client_id: string;
  status: 'planning' | 'active' | 'completed' | 'on_hold';
  type: 'migration' | 'assessment' | 'modernization';
  start_date: string;
  end_date: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

interface EngagementContextType {
  currentEngagement: Engagement | null;
  isLoading: boolean;
  error: Error | null;
  selectEngagement: (id: string) => Promise<void>;
  clearEngagement: () => void;
  getEngagementId: () => string | null;
}

const EngagementContext = createContext<EngagementContextType | undefined>(undefined);

const ENGAGEMENT_KEY = 'current_engagement';

export const EngagementProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentEngagement, setCurrentEngagement] = useState<Engagement | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { getContextHeaders } = useAuth();
  const { currentClient } = useClient();
  const router = useRouter();

  useEffect(() => {
    const initializeEngagement = async () => {
      try {
        const engagementId = sessionStorage.getItem(ENGAGEMENT_KEY);
        if (!engagementId || !currentClient) {
          setIsLoading(false);
          return;
        }

        const response = await apiCall(`/api/v1/engagements/${engagementId}`, {
          method: 'GET',
          headers: getContextHeaders()
        });

        if (response.engagement && response.engagement.client_id === currentClient.id) {
          setCurrentEngagement(response.engagement);
        } else {
          sessionStorage.removeItem(ENGAGEMENT_KEY);
          setCurrentEngagement(null);
        }
      } catch (err) {
        console.error('Engagement initialization error:', err);
        sessionStorage.removeItem(ENGAGEMENT_KEY);
        setCurrentEngagement(null);
        setError(err instanceof Error ? err : new Error('Engagement initialization failed'));
      } finally {
        setIsLoading(false);
      }
    };

    initializeEngagement();
  }, [getContextHeaders, currentClient]);

  const selectEngagement = async (id: string): Promise<void> => {
    try {
      if (!currentClient) {
        throw new Error('No client selected');
      }

      setIsLoading(true);
      setError(null);

      const response = await apiCall(`/api/v1/engagements/${id}`, {
        method: 'GET',
        headers: getContextHeaders()
      });

      if (response.engagement && response.engagement.client_id === currentClient.id) {
        sessionStorage.setItem(ENGAGEMENT_KEY, id);
        setCurrentEngagement(response.engagement);
      } else {
        throw new Error('Engagement not found or not accessible');
      }
    } catch (err) {
      console.error('Select engagement error:', err);
      setError(err instanceof Error ? err : new Error('Failed to select engagement'));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const clearEngagement = () => {
    sessionStorage.removeItem(ENGAGEMENT_KEY);
    setCurrentEngagement(null);
  };

  const getEngagementId = (): string | null => {
    return sessionStorage.getItem(ENGAGEMENT_KEY);
  };

  const value = {
    currentEngagement,
    isLoading,
    error,
    selectEngagement,
    clearEngagement,
    getEngagementId
  };

  return <EngagementContext.Provider value={value}>{children}</EngagementContext.Provider>;
};

export const useEngagement = () => {
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
  return function WithEngagementComponent(props: P) {
    const { currentEngagement, isLoading } = useEngagement();
    const router = useRouter();

    useEffect(() => {
      if (!isLoading && requireEngagement && !currentEngagement) {
        router.push('/engagements');
      }
    }, [currentEngagement, isLoading, router]);

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