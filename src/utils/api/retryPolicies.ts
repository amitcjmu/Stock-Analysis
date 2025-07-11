/**
 * Retry policy utilities for API requests.
 * Provides configurable retry strategies with exponential backoff.
 */

import { ApiErrorType } from './apiTypes';
import { isRetryableError } from './errorHandling';

export interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  backoffFactor?: number;
  retryCondition?: (error: ApiErrorType, attempt: number) => boolean;
}

const DEFAULT_RETRY_OPTIONS: Required<RetryOptions> = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffFactor: 2,
  retryCondition: (error: ApiErrorType, attempt: number) => {
    return attempt < 3 && isRetryableError(error);
  }
};

export async function applyRetryPolicy<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const config = { ...DEFAULT_RETRY_OPTIONS, ...options };
  let lastError: any;
  
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt === config.maxRetries || !config.retryCondition(error as ApiErrorType, attempt)) {
        throw error;
      }
      
      const delay = calculateDelay(attempt, config.baseDelay, config.maxDelay, config.backoffFactor);
      await sleep(delay);
    }
  }
  
  throw lastError;
}

function calculateDelay(
  attempt: number,
  baseDelay: number,
  maxDelay: number,
  backoffFactor: number
): number {
  const delay = baseDelay * Math.pow(backoffFactor, attempt);
  return Math.min(delay, maxDelay);
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export const retryPolicies = {
  network: {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 8000,
    backoffFactor: 2
  },
  server: {
    maxRetries: 2,
    baseDelay: 2000,
    maxDelay: 10000,
    backoffFactor: 2
  },
  rateLimit: {
    maxRetries: 5,
    baseDelay: 5000,
    maxDelay: 30000,
    backoffFactor: 2
  }
};