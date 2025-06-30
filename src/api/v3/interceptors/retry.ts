/**
 * Retry Interceptor for API v3
 * Handles automatic retries for failed requests with exponential backoff
 */

import { shouldRetryRequest, calculateRetryDelay as utilCalculateRetryDelay } from '../utils/requestConfig';
import { NetworkError, TimeoutError } from '../types/responses';

export interface RetryConfig {
  maxAttempts?: number;
  baseDelay?: number;
  maxDelay?: number;
  retryCondition?: (error: any, attempt: number) => boolean;
  onRetry?: (error: any, attempt: number, delay: number) => void;
  onMaxRetriesReached?: (error: any, attempts: number) => void;
  enableJitter?: boolean;
}

const DEFAULT_RETRY_CONFIG: Required<RetryConfig> = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 30000,
  retryCondition: (error: any, attempt: number) => shouldRetryRequest(error, attempt, 3),
  onRetry: (error, attempt, delay) => {
    console.warn(`Retrying request (attempt ${attempt}) after ${delay}ms:`, error.message);
  },
  onMaxRetriesReached: (error, attempts) => {
    console.error(`Max retries (${attempts}) reached for request:`, error);
  },
  enableJitter: true
};

/**
 * Create retry interceptor with custom configuration
 */
export function createRetryInterceptor(config: RetryConfig = {}) {
  const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...config };

  return async function retryInterceptor(
    fetchFn: () => Promise<Response>,
    originalRequest?: Request
  ): Promise<Response> {
    let lastError: any;
    let attempt = 0;

    while (attempt < retryConfig.maxAttempts) {
      attempt++;

      try {
        const response = await fetchFn();
        
        // If response is successful or shouldn't be retried, return it
        if (response.ok || !retryConfig.retryCondition(
          { status: response.status },
          attempt,
          retryConfig.maxAttempts
        )) {
          return response;
        }

        // Treat non-ok response as an error for retry logic
        lastError = {
          status: response.status,
          statusText: response.statusText,
          message: `HTTP ${response.status}: ${response.statusText}`
        };

      } catch (error) {
        lastError = error;

        // Convert AbortError to TimeoutError for better error handling
        if (error instanceof Error && error.name === 'AbortError') {
          lastError = new TimeoutError(30000, 'Request timed out');
        }

        // Convert fetch network errors to NetworkError
        if (error instanceof TypeError && error.message.includes('fetch')) {
          lastError = new NetworkError('Network request failed', error);
        }
      }

      // Check if we should retry
      if (!retryConfig.retryCondition(lastError, attempt, retryConfig.maxAttempts)) {
        break;
      }

      // If this was the last attempt, don't wait
      if (attempt >= retryConfig.maxAttempts) {
        break;
      }

      // Calculate delay for next attempt
      const delay = calculateRetryDelay(attempt, retryConfig.baseDelay, retryConfig);
      
      // Call retry callback
      retryConfig.onRetry(lastError, attempt, delay);

      // Wait before retrying
      await sleep(delay);
    }

    // Max retries reached
    retryConfig.onMaxRetriesReached(lastError, attempt);
    throw lastError;
  };
}

/**
 * Enhanced retry delay calculation with jitter and max delay
 */
function calculateRetryDelay(
  attempt: number, 
  baseDelay: number, 
  config: Required<RetryConfig>
): number {
  // Exponential backoff: baseDelay * 2^(attempt-1)
  let delay = baseDelay * Math.pow(2, attempt - 1);

  // Add jitter to prevent thundering herd
  if (config.enableJitter) {
    const jitter = Math.random() * baseDelay * 0.5; // Up to 50% of base delay
    delay += jitter;
  }

  // Cap at max delay
  return Math.min(delay, config.maxDelay);
}

/**
 * Sleep utility function
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Default retry interceptor instance
 */
export const retryInterceptor = createRetryInterceptor();

/**
 * Retry interceptor optimized for file uploads (fewer retries, longer delays)
 */
export const fileUploadRetryInterceptor = createRetryInterceptor({
  maxAttempts: 2,
  baseDelay: 2000,
  maxDelay: 10000,
  retryCondition: (error, attempt) => {
    // Only retry on network errors and 5xx server errors for uploads
    return (
      attempt < 2 &&
      (!error.status || error.status >= 500) &&
      !(error instanceof TimeoutError) // Don't retry timeouts for large uploads
    );
  }
});

/**
 * Retry interceptor for critical operations (more aggressive retries)
 */
export const criticalRetryInterceptor = createRetryInterceptor({
  maxAttempts: 5,
  baseDelay: 500,
  maxDelay: 15000,
  onRetry: (error, attempt, delay) => {
    console.warn(`Critical operation retry (${attempt}/5) in ${delay}ms:`, error.message);
  }
});

/**
 * Check if error is retryable based on common patterns
 */
export function isRetryableError(error: any): boolean {
  // Network errors
  if (error instanceof NetworkError) {
    return true;
  }

  // Timeout errors (usually retryable)
  if (error instanceof TimeoutError) {
    return true;
  }

  // HTTP status codes that are typically retryable
  if (error.status) {
    return (
      error.status >= 500 || // Server errors
      error.status === 408 || // Request timeout
      error.status === 429    // Too many requests (rate limiting)
    );
  }

  // Fetch network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return true;
  }

  // AbortController timeouts
  if (error.name === 'AbortError') {
    return true;
  }

  return false;
}

/**
 * Create a retry wrapper for any async function
 */
export function withRetry<T>(
  fn: () => Promise<T>,
  config: RetryConfig = {}
): Promise<T> {
  const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...config };

  return new Promise(async (resolve, reject) => {
    let lastError: any;
    let attempt = 0;

    while (attempt < retryConfig.maxAttempts) {
      attempt++;

      try {
        const result = await fn();
        resolve(result);
        return;
      } catch (error) {
        lastError = error;

        if (!retryConfig.retryCondition(error, attempt, retryConfig.maxAttempts)) {
          break;
        }

        if (attempt >= retryConfig.maxAttempts) {
          break;
        }

        const delay = calculateRetryDelay(attempt, retryConfig.baseDelay, retryConfig);
        retryConfig.onRetry(error, attempt, delay);
        await sleep(delay);
      }
    }

    retryConfig.onMaxRetriesReached(lastError, attempt);
    reject(lastError);
  });
}

/**
 * Exponential backoff calculator for external use
 */
export function exponentialBackoff(
  attempt: number,
  baseDelay: number = 1000,
  maxDelay: number = 30000,
  jitter: boolean = true
): number {
  return calculateRetryDelay(attempt, baseDelay, {
    ...DEFAULT_RETRY_CONFIG,
    maxDelay,
    enableJitter: jitter
  });
}