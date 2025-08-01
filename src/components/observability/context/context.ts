/**
 * Observability Context Export
 * Exports the context for use by hooks
 */

import { createContext } from 'react';
import type { ObservabilityContextValue } from './ObservabilityContext';

export const ObservabilityContext = createContext<ObservabilityContextValue | undefined>(undefined);