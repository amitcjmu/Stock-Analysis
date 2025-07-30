interface LogData {
  [key: string]: unknown;
}

/**
 * Secure logging utility that prevents sensitive data exposure
 * CC - Security hardened logging for production environments
 */
class SecureLogger {
  private static sensitiveFields = [
    'raw_data', 'field_mappings', 'flow_id', 'client_account_id',
    'engagement_id', 'user_id', 'api_key', 'token', 'password',
    'flowRawData', 'flowFieldMappings', 'flowImportMetadata',
    'flowRawDataLength', 'fieldMappingsKeys', 'cleansingProgress',
    'effectiveFlowId', 'autoDetectedFlowId', 'urlFlowId',
    'allFlows', 'flowKeys', 'dataCleansingKeys'
  ];

  /**
   * Recursively redact sensitive data from objects
   */
  private static redactSensitiveData(data: LogData): LogData {
    if (!data || typeof data !== 'object') {
      return data;
    }

    const redacted = Array.isArray(data) ? [...data] : { ...data };

    Object.keys(redacted).forEach(key => {
      // Check if key contains sensitive information
      const isSensitive = this.sensitiveFields.some(field =>
        key.toLowerCase().includes(field.toLowerCase()) ||
        field.toLowerCase().includes(key.toLowerCase())
      );

      if (isSensitive) {
        redacted[key] = '[REDACTED]';
      } else if (typeof redacted[key] === 'object' && redacted[key] !== null) {
        redacted[key] = this.redactSensitiveData(redacted[key] as LogData);
      }
    });

    return redacted;
  }

  /**
   * Secure logging method that redacts sensitive data
   */
  static log(level: 'info' | 'warn' | 'error', message: string, data?: LogData): void {
    // In production, only log errors and warnings
    if (process.env.NODE_ENV === 'production') {
      if (level === 'error' || level === 'warn') {
        const sanitizedMessage = message.replace(/[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}/gi, '[FLOW-ID]');
        console[level](sanitizedMessage, data ? this.redactSensitiveData(data) : '');
      }
      return;
    }

    // In development, redact sensitive data but allow more verbose logging
    const redactedData = data ? this.redactSensitiveData(data) : undefined;
    const sanitizedMessage = message.replace(/[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}/gi, '[FLOW-ID]');

    console[level](sanitizedMessage, redactedData);
  }

  /**
   * Log debug information (development only)
   */
  static debug(message: string, data?: LogData): void {
    if (process.env.NODE_ENV !== 'production') {
      this.log('info', `🔍 [DEBUG] ${message}`, data);
    }
  }

  /**
   * Log information with data redaction
   */
  static info(message: string, data?: LogData): void {
    this.log('info', message, data);
  }

  /**
   * Log warnings with data redaction
   */
  static warn(message: string, data?: LogData): void {
    this.log('warn', message, data);
  }

  /**
   * Log errors with data redaction
   */
  static error(message: string, data?: LogData): void {
    this.log('error', message, data);
  }
}

export default SecureLogger;
