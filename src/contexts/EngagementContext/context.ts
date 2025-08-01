/**
 * Engagement Context
 * React context for engagement state management
 */

import { createContext } from 'react';
import type { EngagementContextType } from './types';

export const EngagementContext = createContext<EngagementContextType | undefined>(undefined);