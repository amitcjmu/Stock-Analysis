/**
 * Simple logger utility for consistent logging across the application.
 */

/**
 * Logger utility types
 */
type LogData = Record<string, unknown> | string | number | boolean | null | undefined;
type LogError = Error | string | Record<string, unknown>;

/**
 * Logger interface for type safety
 */
interface Logger {
  debug: (message: string, data?: LogData) => void;
  info: (message: string, data?: LogData) => void;
  warn: (message: string, data?: LogData) => void;
  error: (message: string, error?: LogError) => void;
}

/**
 * Format log data for output
 */
const formatLogData = (data: LogData): LogData => {
  if (data === null || data === undefined) {
    return data;
  }

  if (typeof data === 'object' && data !== null) {
    try {
      return JSON.parse(JSON.stringify(data));
    } catch {
      return '[Circular or non-serializable object]';
    }
  }

  return data;
};

/**
 * Format error for output
 */
const formatError = (error: LogError): LogError => {
  if (error instanceof Error) {
    return {
      name: error.name,
      message: error.message,
      stack: error.stack,
      ...(error.cause && { cause: error.cause })
    };
  }

  if (typeof error === 'string') {
    return error;
  }

  return formatLogData(error) as LogError;
};

export const logger: Logger = {
  debug: (message: string, data?: LogData) => {
    if (process.env.NODE_ENV === 'development') {
      console.debug('[AI Modernize Debug]', message, data ? formatLogData(data) : undefined);
    }
  },

  info: (message: string, data?: LogData) => {
    console.info('[AI Modernize Info]', message, data ? formatLogData(data) : undefined);
  },

  warn: (message: string, data?: LogData) => {
    console.warn('[AI Modernize Warning]', message, data ? formatLogData(data) : undefined);
  },

  error: (message: string, error?: LogError) => {
    console.error('[AI Modernize Error]', message, error ? formatError(error) : undefined);
  }
};
