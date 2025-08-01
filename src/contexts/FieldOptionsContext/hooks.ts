/**
 * Field Options Context Hooks
 * Custom hooks for accessing the Field Options context
 */

import { useContext } from 'react';
import { FieldOptionsContext } from './context';
import type { FieldOptionsContextType } from './types';

export const useFieldOptions = (): FieldOptionsContextType => {
  const context = useContext(FieldOptionsContext);
  if (context === undefined) {
    throw new Error('useFieldOptions must be used within a FieldOptionsProvider');
  }
  return context;
};
