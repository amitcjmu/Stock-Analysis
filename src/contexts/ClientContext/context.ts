/**
 * Client Context
 * React context definition for client management
 */

import { createContext } from 'react';
import type { ClientContextType } from './types';

export const ClientContext = createContext<ClientContextType | undefined>(undefined);
