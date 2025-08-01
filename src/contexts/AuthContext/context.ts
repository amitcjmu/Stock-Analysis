/**
 * AuthContext
 * React context definition for authentication
 */

import { createContext } from 'react';
import type { AuthContextType } from './types';

export const AuthContext = createContext<AuthContextType | undefined>(undefined);