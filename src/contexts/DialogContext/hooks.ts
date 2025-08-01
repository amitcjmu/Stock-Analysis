/**
 * Dialog Context Hooks
 * Custom hooks for accessing the Dialog context
 */

import { useContext } from 'react';
import { DialogContext } from './context';
import type { DialogContextValue } from './types';

export const useDialog = (): DialogContextValue => {
  const context = useContext(DialogContext);
  if (!context) {
    throw new Error('useDialog must be used within a DialogProvider');
  }
  return context;
};