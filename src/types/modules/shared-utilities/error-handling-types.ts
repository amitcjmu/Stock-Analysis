/**
 * Error Handling Types
 *
 * Types for error handling, error boundaries, and error recovery.
 */

import type { ReactNode } from 'react';
import type { ErrorContext } from './base-types';

// Error handling service interfaces
export interface ErrorService {
  handleError: (error: Error, context?: ErrorContext) => void;
  reportError: (error: Error, context?: ErrorContext) => Promise<void>;
  logError: (error: Error, context?: ErrorContext) => void;
  createError: (message: string, code?: string, details?: Record<string, unknown>) => AppError;
  isRetryableError: (error: Error) => boolean;
  getErrorSeverity: (error: Error) => ErrorSeverity;
}

export interface ErrorBoundaryService {
  captureError: (error: Error, errorInfo: ErrorInfo) => void;
  reportErrorBoundary: (error: Error, errorInfo: ErrorInfo) => Promise<void>;
  getErrorFallback: (error: Error, errorInfo: ErrorInfo) => ReactNode;
  resetErrorBoundary: () => void;
}

export interface ErrorRecoveryService {
  attemptRecovery: (error: Error, strategy: RecoveryStrategy) => Promise<boolean>;
  getRecoveryStrategies: (error: Error) => RecoveryStrategy[];
  executeRecovery: (strategy: RecoveryStrategy) => Promise<void>;
  canRecover: (error: Error) => boolean;
}

// Error model types
export interface AppError extends Error {
  code: string;
  severity: ErrorSeverity;
  context?: ErrorContext;
  details?: Record<string, unknown>;
  timestamp: string;
  userId?: string;
  sessionId?: string;
  requestId?: string;
  stack?: string;
  cause?: Error;
}

export interface ErrorInfo {
  componentStack: string;
  errorBoundary?: string;
  errorBoundaryStack?: string;
}

export interface RecoveryStrategy {
  name: string;
  description: string;
  priority: number;
  execute: () => Promise<void>;
  canExecute: (error: Error) => boolean;
  maxAttempts: number;
  currentAttempts: number;
}

export interface ErrorReport {
  id: string;
  error: AppError;
  context: ErrorContext;
  timestamp: string;
  userAgent: string;
  url: string;
  userId?: string;
  sessionId?: string;
  stackTrace: string;
  breadcrumbs: ErrorBreadcrumb[];
  metadata: Record<string, unknown>;
}

export interface ErrorBreadcrumb {
  timestamp: string;
  message: string;
  category: string;
  level: 'info' | 'warning' | 'error';
  data?: Record<string, unknown>;
}

export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';
