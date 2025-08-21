/**
 * Retry utility for handling failed operations with exponential backoff
 */

import { isRetryableError, getRetryDelay } from './errorHandling';

export interface RetryOptions {
  maxAttempts?: number;
  initialDelay?: number;
  maxDelay?: number;
  exponentialBackoff?: boolean;
  shouldRetry?: (error: any, attempt: number) => boolean;
}

const defaultRetryOptions: Required<RetryOptions> = {
  maxAttempts: 3,
  initialDelay: 500,
  maxDelay: 5000,
  exponentialBackoff: true,
  shouldRetry: isRetryableError
};

/**
 * Retry an async operation with exponential backoff
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts = { ...defaultRetryOptions, ...options };
  let lastError: any;

  for (let attempt = 1; attempt <= opts.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;

      // Don't retry on last attempt
      if (attempt === opts.maxAttempts) {
        break;
      }

      // Check if error is retryable
      if (!opts.shouldRetry(error, attempt)) {
        break;
      }

      // Calculate delay
      let delay = opts.initialDelay;

      // Use error-specific delay if available
      const errorDelay = getRetryDelay(error);
      if (errorDelay > 0) {
        delay = errorDelay;
      } else if (opts.exponentialBackoff) {
        delay = Math.min(opts.initialDelay * Math.pow(2, attempt - 1), opts.maxDelay);
      }

      // Add jitter to prevent thundering herd
      delay += Math.random() * 200;

      console.log(`Retry attempt ${attempt}/${opts.maxAttempts} after ${delay}ms delay`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

/**
 * Create a retry wrapper for a function
 */
export function createRetryWrapper<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  options: RetryOptions = {}
): T {
  return ((...args: Parameters<T>) => {
    return withRetry(() => fn(...args), options);
  }) as T;
}

/**
 * Exponential backoff delay calculation
 */
export function calculateBackoffDelay(
  attempt: number,
  baseDelay: number = 500,
  maxDelay: number = 5000
): number {
  const delay = Math.min(baseDelay * Math.pow(2, attempt - 1), maxDelay);
  // Add jitter (±25%)
  const jitter = delay * 0.25 * (Math.random() * 2 - 1);
  return Math.max(delay + jitter, 0);
}
