/**
 * Field Options Context
 * React context for field options state management
 */

import { createContext } from 'react';
import type { FieldOptionsContextType } from './types';

export const FieldOptionsContext = createContext<FieldOptionsContextType | undefined>(undefined);