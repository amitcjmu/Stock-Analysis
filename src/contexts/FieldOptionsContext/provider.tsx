/**
 * Field Options Context Provider
 * React context provider for field options state management
 */

import React, { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { FieldOptionsContext } from './context';
import { ASSET_TARGET_FIELDS } from './constants';
import type { TargetField } from './types';
import { useAuth } from '../AuthContext';

interface FieldOptionsProviderProps {
  children: ReactNode;
}

export const FieldOptionsProvider: React.FC<FieldOptionsProviderProps> = ({ children }) => {
  const { client, engagement } = useAuth();
  const [availableFields, setAvailableFields] = useState<TargetField[]>(ASSET_TARGET_FIELDS);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchFields = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('http://localhost:8000/api/v1/data-import/available-target-fields', {
        headers: {
          'X-Client-Account-ID': client?.id || '11111111-1111-1111-1111-111111111111',
          'X-Engagement-ID': engagement?.id || '22222222-2222-2222-2222-222222222222',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch fields: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.fields && Array.isArray(data.fields)) {
        console.log('✅ FieldOptionsProvider - Loaded', data.fields.length, 'fields from database schema');
        console.log('   Categories:', Object.keys(data.categories || {}).length);
        console.log('   Source:', data.source);
        setAvailableFields(data.fields);
        setLastUpdated(new Date());
      } else {
        throw new Error('Invalid response format from backend');
      }
    } catch (err) {
      console.error('❌ Failed to fetch fields from backend, using fallback:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      // Fallback to hardcoded fields
      setAvailableFields(ASSET_TARGET_FIELDS);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFields();
  }, [client?.id, engagement?.id]);

  const refetchFields = async () =>  {
    console.log('🔄 FieldOptionsProvider - Refetching fields from backend...');
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
