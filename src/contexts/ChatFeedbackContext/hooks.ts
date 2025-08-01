/**
 * ChatFeedback Context Hooks
 * Custom hooks for accessing the ChatFeedback context
 */

import { useContext } from 'react';
import { ChatFeedbackContext } from './context';
import type { ChatFeedbackContextType } from './types';

export const useChatFeedback = (): ChatFeedbackContextType => {
  const context = useContext(ChatFeedbackContext);
  if (!context) {
    throw new Error('useChatFeedback must be used within a ChatFeedbackProvider');
  }
  return context;
};
