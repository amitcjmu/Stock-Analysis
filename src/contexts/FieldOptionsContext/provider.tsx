/**
 * Field Options Context Provider
 * React context provider for field options state management
 */

import React, { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { FieldOptionsContext } from './context';
import type { TargetField } from './types';
import { useAuth } from '../AuthContext';
import { apiCall } from '@/config/api';

interface FieldOptionsProviderProps {
  children: ReactNode;
}

export const FieldOptionsProvider: React.FC<FieldOptionsProviderProps> = ({ children }) => {
  const { client, engagement } = useAuth();
  const [availableFields, setAvailableFields] = useState<TargetField[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchFields = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Use apiCall utility which handles environment-specific URLs (localhost/Vercel/Railway)
      const data = await apiCall('/data-import/available-target-fields', {
        method: 'GET',
      });

      if (data.fields && Array.isArray(data.fields)) {
        setAvailableFields(data.fields);
        setLastUpdated(new Date());
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      console.error('Failed to fetch available fields:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setAvailableFields([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch if we have both client and engagement context
    if (client?.id && engagement?.id) {
      fetchFields();
    } else {
      console.warn('FieldOptionsProvider: Skipping fetch - missing client or engagement context', {
        hasClient: !!client?.id,
        hasEngagement: !!engagement?.id
      });
    }
  }, [client?.id, engagement?.id]);

  const refetchFields = async () =>  {
    await fetchFields();
  };

  return (
    <FieldOptionsContext.Provider
      value={{
        availableFields,
        isLoading,
        error,
        refetchFields,
        lastUpdated
      }}
    >
      {children}
    </FieldOptionsContext.Provider>
  );
};
