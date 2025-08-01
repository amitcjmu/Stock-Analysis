/**
 * ChatFeedback Context
 * React context definition for chat feedback functionality
 */

import { createContext } from 'react';
import type { ChatFeedbackContextType } from './types';

export const ChatFeedbackContext = createContext<ChatFeedbackContextType | undefined>(undefined);
