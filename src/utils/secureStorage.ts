import SecureLogger from './secureLogger';

/**
 * Secure storage utility for handling sensitive data in localStorage
 * CC - Security hardened storage operations with input validation
 */
class SecureStorage {
  /**
   * Validate if a string is a valid UUID v4 format
   */
  private static validateFlowId(flowId: string): boolean {
    if (!flowId || typeof flowId !== 'string') {
      return false;
    }

    // UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

    return uuidRegex.test(flowId) && flowId.length === 36;
  }

  /**
   * Sanitize input to prevent XSS and injection attacks
   */
  private static sanitizeInput(input: string): string {
    if (!input || typeof input !== 'string') {
      return '';
    }

    // Remove HTML tags and potentially dangerous characters
    return input
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/[<>'"&\x00-\x1F\x7F-\x9F]/g, '') // Remove dangerous characters
      .replace(/javascript:/gi, '') // Remove javascript: protocol
      .replace(/data:/gi, '') // Remove data: protocol
      .trim();
  }

  /**
   * Securely set flow ID in localStorage with validation
   */
  static setFlowId(flowId: string): boolean {
    try {
      if (!flowId) {
        SecureLogger.warn('SecureStorage: Empty flow ID provided');
        return false;
      }

      const sanitized = this.sanitizeInput(flowId);

      if (!this.validateFlowId(sanitized)) {
        SecureLogger.warn('SecureStorage: Invalid flow ID format, not storing');
        return false;
      }

      localStorage.setItem('currentFlowId', sanitized);
      return true;
    } catch (error) {
      SecureLogger.error('SecureStorage: Failed to store flow ID securely', { error: error instanceof Error ? error.message : String(error) });
      return false;
    }
  }

  /**
   * Securely retrieve flow ID from localStorage with validation
   */
  static getFlowId(): string | null {
    try {
      const flowId = localStorage.getItem('currentFlowId');

      if (!flowId) {
        return null;
      }

      // Validate stored flow ID
      if (!this.validateFlowId(flowId)) {
        SecureLogger.warn('SecureStorage: Invalid flow ID found in storage, removing');
        this.clearFlowId();
        return null;
      }

      return flowId;
    } catch (error) {
      SecureLogger.error('SecureStorage: Failed to retrieve flow ID', { error: error instanceof Error ? error.message : String(error) });
      return null;
    }
  }

  /**
   * Clear flow ID from localStorage
   */
  static clearFlowId(): void {
    try {
      localStorage.removeItem('currentFlowId');
    } catch (error) {
      SecureLogger.error('SecureStorage: Failed to clear flow ID', { error: error instanceof Error ? error.message : String(error) });
    }
  }

  /**
   * Validate and sanitize URL-extracted flow ID
   */
  static validateUrlFlowId(flowId: string | null): string | null {
    if (!flowId) {
      return null;
    }

    const sanitized = this.sanitizeInput(flowId);

    if (!this.validateFlowId(sanitized)) {
      SecureLogger.warn('SecureStorage: Invalid flow ID extracted from URL');
      return null;
    }

    return sanitized;
  }

  /**
   * Check if localStorage is available and secure
   */
  static isStorageAvailable(): boolean {
    try {
      const test = '__storage_test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch (error) {
      SecureLogger.warn('SecureStorage: localStorage not available');
      return false;
    }
  }
}

// Export the validateFlowId function for use in other security utilities
export function validateFlowId(flowId: string): boolean {
  if (!flowId || typeof flowId !== 'string') {
    return false;
  }

  // UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

  return uuidRegex.test(flowId) && flowId.length === 36;
}

export default SecureStorage;
