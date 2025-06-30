/**
 * Logging Interceptor for API v3
 * Handles request/response logging for debugging and monitoring
 */

export interface LoggingConfig {
  enabled?: boolean;
  logRequests?: boolean;
  logResponses?: boolean;
  logErrors?: boolean;
  logTiming?: boolean;
  maxBodyLength?: number;
  sensitiveHeaders?: string[];
  sensitiveFields?: string[];
  onLog?: (logEntry: LogEntry) => void;
}

export interface LogEntry {
  type: 'request' | 'response' | 'error';
  timestamp: string;
  requestId?: string;
  method?: string;
  url?: string;
  status?: number;
  duration?: number;
  headers?: Record<string, string>;
  body?: any;
  error?: any;
}

const DEFAULT_LOGGING_CONFIG: Required<LoggingConfig> = {
  enabled: process.env.NODE_ENV === 'development',
  logRequests: true,
  logResponses: true,
  logErrors: true,
  logTiming: true,
  maxBodyLength: 1000,
  sensitiveHeaders: [
    'authorization',
    'cookie',
    'x-api-key',
    'x-auth-token'
  ],
  sensitiveFields: [
    'password',
    'token',
    'secret',
    'key',
    'auth',
    'credential'
  ],
  onLog: (entry) => {
    const prefix = entry.type === 'error' ? '❌' : 
                   entry.type === 'request' ? '📤' : '📥';
    
    if (entry.type === 'error') {
      console.error(`${prefix} API ${entry.type.toUpperCase()}:`, entry);
    } else {
      console.log(`${prefix} API ${entry.type.toUpperCase()}:`, entry);
    }
  }
};

/**
 * Request timing storage
 */
const requestTimings = new Map<string, number>();

/**
 * Create logging interceptor with custom configuration
 */
export function createLoggingInterceptor(config: LoggingConfig = {}) {
  const loggingConfig = { ...DEFAULT_LOGGING_CONFIG, ...config };

  return {
    request: createRequestLogger(loggingConfig),
    response: createResponseLogger(loggingConfig),
    error: createErrorLogger(loggingConfig)
  };
}

/**
 * Create request logger
 */
function createRequestLogger(config: Required<LoggingConfig>) {
  return (request: Request): Request => {
    if (!config.enabled || !config.logRequests) {
      return request;
    }

    const requestId = getRequestId(request);
    const timestamp = new Date().toISOString();

    // Store timing for this request
    if (config.logTiming && requestId) {
      requestTimings.set(requestId, Date.now());
    }

    const logEntry: LogEntry = {
      type: 'request',
      timestamp,
      requestId,
      method: request.method,
      url: sanitizeUrl(request.url),
      headers: sanitizeHeaders(getHeadersAsObject(request.headers), config.sensitiveHeaders)
    };

    // Log request body for non-GET requests
    if (request.method !== 'GET' && request.body) {
      logEntry.body = sanitizeBody(request.body, config);
    }

    config.onLog(logEntry);
    return request;
  };
}

/**
 * Create response logger
 */
function createResponseLogger(config: Required<LoggingConfig>) {
  return async (response: Response, request?: Request): Promise<Response> => {
    if (!config.enabled || !config.logResponses) {
      return response;
    }

    const requestId = request ? getRequestId(request) : undefined;
    const timestamp = new Date().toISOString();
    let duration: number | undefined;

    // Calculate duration if timing is enabled
    if (config.logTiming && requestId && requestTimings.has(requestId)) {
      duration = Date.now() - requestTimings.get(requestId)!;
      requestTimings.delete(requestId);
    }

    const logEntry: LogEntry = {
      type: 'response',
      timestamp,
      requestId,
      method: request?.method,
      url: request ? sanitizeUrl(request.url) : undefined,
      status: response.status,
      duration,
      headers: sanitizeHeaders(getHeadersAsObject(response.headers), config.sensitiveHeaders)
    };

    // Clone response to read body without consuming it
    const clonedResponse = response.clone();
    try {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const body = await clonedResponse.json();
        logEntry.body = sanitizeBody(body, config);
      } else if (contentType && contentType.includes('text/')) {
        const text = await clonedResponse.text();
        logEntry.body = truncateString(text, config.maxBodyLength);
      }
    } catch (error) {
      // Ignore body parsing errors
    }

    config.onLog(logEntry);
    return response;
  };
}

/**
 * Create error logger
 */
function createErrorLogger(config: Required<LoggingConfig>) {
  return (error: any, request?: Request): void => {
    if (!config.enabled || !config.logErrors) {
      return;
    }

    const requestId = request ? getRequestId(request) : undefined;
    const timestamp = new Date().toISOString();
    let duration: number | undefined;

    // Calculate duration if timing is enabled
    if (config.logTiming && requestId && requestTimings.has(requestId)) {
      duration = Date.now() - requestTimings.get(requestId)!;
      requestTimings.delete(requestId);
    }

    const logEntry: LogEntry = {
      type: 'error',
      timestamp,
      requestId,
      method: request?.method,
      url: request ? sanitizeUrl(request.url) : undefined,
      duration,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
        status: error.status,
        statusText: error.statusText
      }
    };

    config.onLog(logEntry);
  };
}

/**
 * Get request ID from headers
 */
function getRequestId(request: Request): string | undefined {
  return request.headers.get('X-Request-ID') || undefined;
}

/**
 * Convert Headers object to plain object
 */
function getHeadersAsObject(headers: Headers): Record<string, string> {
  const obj: Record<string, string> = {};
  headers.forEach((value, key) => {
    obj[key] = value;
  });
  return obj;
}

/**
 * Sanitize headers by removing sensitive information
 */
function sanitizeHeaders(
  headers: Record<string, string>,
  sensitiveHeaders: string[]
): Record<string, string> {
  const sanitized: Record<string, string> = {};
  
  Object.entries(headers).forEach(([key, value]) => {
    const lowerKey = key.toLowerCase();
    if (sensitiveHeaders.includes(lowerKey)) {
      sanitized[key] = '[REDACTED]';
    } else {
      sanitized[key] = value;
    }
  });
  
  return sanitized;
}

/**
 * Sanitize request/response body
 */
function sanitizeBody(body: any, config: Required<LoggingConfig>): any {
  if (!body) {
    return body;
  }

  try {
    // Handle FormData
    if (body instanceof FormData) {
      const entries: Record<string, any> = {};
      body.forEach((value, key) => {
        if (value instanceof File) {
          entries[key] = `[File: ${value.name}, ${value.size} bytes]`;
        } else {
          entries[key] = isSensitiveField(key, config.sensitiveFields) ? '[REDACTED]' : value;
        }
      });
      return entries;
    }

    // Handle string body
    if (typeof body === 'string') {
      return truncateString(body, config.maxBodyLength);
    }

    // Handle object body
    if (typeof body === 'object') {
      return sanitizeObjectFields(body, config.sensitiveFields, config.maxBodyLength);
    }

    return body;
  } catch (error) {
    return '[Error parsing body]';
  }
}

/**
 * Sanitize object fields recursively
 */
function sanitizeObjectFields(
  obj: any,
  sensitiveFields: string[],
  maxLength: number
): any {
  if (!obj || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.slice(0, 10).map(item => sanitizeObjectFields(item, sensitiveFields, maxLength));
  }

  const sanitized: any = {};
  Object.entries(obj).forEach(([key, value]) => {
    if (isSensitiveField(key, sensitiveFields)) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'string') {
      sanitized[key] = truncateString(value, maxLength);
    } else if (typeof value === 'object') {
      sanitized[key] = sanitizeObjectFields(value, sensitiveFields, maxLength);
    } else {
      sanitized[key] = value;
    }
  });

  return sanitized;
}

/**
 * Check if field name is sensitive
 */
function isSensitiveField(fieldName: string, sensitiveFields: string[]): boolean {
  const lowerFieldName = fieldName.toLowerCase();
  return sensitiveFields.some(sensitive => lowerFieldName.includes(sensitive));
}

/**
 * Truncate string to max length
 */
function truncateString(str: string, maxLength: number): string {
  if (str.length <= maxLength) {
    return str;
  }
  return str.substring(0, maxLength) + '... [truncated]';
}

/**
 * Sanitize URL by removing sensitive query parameters
 */
function sanitizeUrl(url: string): string {
  try {
    const urlObj = new URL(url);
    const sensitiveParams = ['token', 'key', 'secret', 'password', 'auth'];
    
    sensitiveParams.forEach(param => {
      if (urlObj.searchParams.has(param)) {
        urlObj.searchParams.set(param, '[REDACTED]');
      }
    });
    
    return urlObj.toString();
  } catch {
    return url;
  }
}

/**
 * Default logging interceptor instance
 */
export const loggingInterceptor = createLoggingInterceptor();

/**
 * Production-safe logging interceptor (minimal logging)
 */
export const productionLoggingInterceptor = createLoggingInterceptor({
  enabled: true,
  logRequests: false,
  logResponses: false,
  logErrors: true,
  logTiming: true,
  maxBodyLength: 200
});

/**
 * Debug logging interceptor (verbose logging)
 */
export const debugLoggingInterceptor = createLoggingInterceptor({
  enabled: true,
  logRequests: true,
  logResponses: true,
  logErrors: true,
  logTiming: true,
  maxBodyLength: 5000,
  onLog: (entry) => {
    console.group(`🔍 API ${entry.type.toUpperCase()} - ${entry.requestId}`);
    console.log('Timestamp:', entry.timestamp);
    if (entry.method && entry.url) {
      console.log('Request:', `${entry.method} ${entry.url}`);
    }
    if (entry.status) {
      console.log('Status:', entry.status);
    }
    if (entry.duration) {
      console.log('Duration:', `${entry.duration}ms`);
    }
    if (entry.headers) {
      console.log('Headers:', entry.headers);
    }
    if (entry.body) {
      console.log('Body:', entry.body);
    }
    if (entry.error) {
      console.error('Error:', entry.error);
    }
    console.groupEnd();
  }
});