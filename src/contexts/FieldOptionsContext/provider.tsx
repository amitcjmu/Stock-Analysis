/**
 * Field Options Context Provider
 * React context provider for field options state management
 */

import React, { useState } from 'react';
import type { ReactNode } from 'react';
import { FieldOptionsContext } from './context';
import { ASSET_TARGET_FIELDS } from './constants';
import type { TargetField } from './types';

interface FieldOptionsProviderProps {
  children: ReactNode;
}

export const FieldOptionsProvider: React.FC<FieldOptionsProviderProps> = ({ children }) => {
  // Use hardcoded fields directly - no API calls needed
  const [availableFields] = useState<TargetField[]>(ASSET_TARGET_FIELDS);
  const [isLoading] = useState(false); // Always false since no API calls
  const [error] = useState<string | null>(null); // Always null since no API calls
  const [lastUpdated] = useState<Date | null>(new Date()); // Always current time

  console.log('✅ FieldOptionsProvider - Using hardcoded asset fields list with', ASSET_TARGET_FIELDS.length, 'fields');

  const refetchFields = async () =>  {
    console.log('🔄 FieldOptionsProvider - Refetch requested but using hardcoded fields');
    // No-op since we're using hardcoded fields
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