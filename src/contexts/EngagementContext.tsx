import React from 'react'
import { createContext, useContext, useState } from 'react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom';
import { apiCall } from '@/config/api';
import { useAuth } from './AuthContext';
import { useClient } from './ClientContext';
import { DEMO_USER_ID, DEMO_ENGAGEMENT_DATA } from '@/constants/demo';

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
  metadata: Record<string, string | number | boolean | null>;
}

interface EngagementContextType {
  currentEngagement: Engagement | null;
  isLoading: boolean;
  error: Error | null;
  selectEngagement: (id: string) => Promise<void>;
  clearEngagement: () => void;
  getEngagementId: () => string | null;
  setDemoEngagement: (engagement: Engagement) => void;
}

const EngagementContext = createContext<EngagementContextType | undefined>(undefined);

const ENGAGEMENT_KEY = 'current_engagement';

export const EngagementProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentEngagement, setCurrentEngagement] = useState<Engagement | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { user, getContextHeaders } = useAuth();
  const { currentClient } = useClient();
  const navigate = useNavigate();

  useEffect(() => {
    // If demo user, set demo engagement and skip fetch
    const demoEngagement = DEMO_ENGAGEMENT_DATA;
    if (user && user.id === DEMO_USER_ID) {
      setCurrentEngagement(demoEngagement);
      setIsLoading(false);
      setError(null);
      return;
    }

    const initializeEngagement = async () => {
      try {
        const engagementId = sessionStorage.getItem(ENGAGEMENT_KEY);
        if (!engagementId || !currentClient) {
          setIsLoading(false);
          return;
        }

        const response = await apiCall(`/context/engagements/${engagementId}`, {
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
  }, [user, getContextHeaders, currentClient]);

  const selectEngagement = async (id: string): Promise<void> => {
    try {
      if (!currentClient) {
        throw new Error('No client selected');
      }

      setIsLoading(true);
      setError(null);

      const response = await apiCall(`/context/engagements/${id}`, {
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

  const setDemoEngagement = (engagement: Engagement) => {
    setCurrentEngagement(engagement);
    setIsLoading(false);
    setError(null);
  };

  const value = {
    currentEngagement,
    isLoading,
    error,
    selectEngagement,
    clearEngagement,
    getEngagementId,
    setDemoEngagement
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