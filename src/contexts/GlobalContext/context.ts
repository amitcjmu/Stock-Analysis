/**
 * GlobalContext creation
 * Separated to avoid React Fast Refresh warnings
 */

import { createContext } from 'react';
import type { GlobalContextType } from './types';

// Create the context
export const GlobalContext = createContext<GlobalContextType | undefined>(undefined);