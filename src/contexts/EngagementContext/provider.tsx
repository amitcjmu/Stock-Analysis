/**
 * Engagement Context Provider
 * React context provider for engagement state management
 */

import React, { useState, useEffect } from 'react';
import { apiCall } from '@/config/api';
import { useAuth } from '../AuthContext';
import { useClient } from '../ClientContext';
import { DEMO_USER_ID, DEMO_ENGAGEMENT_DATA } from '@/constants/demo';
import { EngagementContext } from './context';
import type { Engagement } from './types';
import { ENGAGEMENT_KEY } from './types';

export const EngagementProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentEngagement, setCurrentEngagement] = useState<Engagement | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { user, getContextHeaders } = useAuth();
  const { currentClient } = useClient();

  useEffect(() => {
    // If demo user, set demo engagement and skip fetch
    const demoEngagement = DEMO_ENGAGEMENT_DATA;
    if (user && user.id === DEMO_USER_ID) {
      setCurrentEngagement(demoEngagement);
      setIsLoading(false);
      setError(null);
      return;
    }

    const initializeEngagement = async (): Promise<void> => {
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

  const clearEngagement = (): void => {
    sessionStorage.removeItem(ENGAGEMENT_KEY);
    setCurrentEngagement(null);
  };

  const getEngagementId = (): string | null => {
    return sessionStorage.getItem(ENGAGEMENT_KEY);
  };

  const setDemoEngagement = (engagement: Engagement): void => {
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
