/**
 * Shared Utilities Base Types
 *
 * Common base types and interfaces used across shared utilities.
 */

import type { ReactNode } from 'react';

// Base shared types
export interface BaseUtilityProps {
  className?: string;
  children?: ReactNode;
}

export interface ConfigurationOptions {
  [key: string]: unknown;
}

export interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  flowId?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}
