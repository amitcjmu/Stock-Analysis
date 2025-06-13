/**
 * Simple logger utility for consistent logging across the application.
 */

export const logger = {
  debug: (message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.debug('[AI Force Debug]', message, data);
    }
  },

  info: (message: string, data?: any) => {
    console.info('[AI Force Info]', message, data);
  },

  warn: (message: string, data?: any) => {
    console.warn('[AI Force Warning]', message, data);
  },

  error: (message: string, error?: Error | any) => {
    console.error('[AI Force Error]', message, error);
  }
}; 