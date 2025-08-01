/**
 * Dialog Context
 * React context definition for dialog management
 */

import { createContext } from 'react';
import type { DialogContextValue } from './types';

export const DialogContext = createContext<DialogContextValue | undefined>(undefined);
