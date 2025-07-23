/**
 * Shared type definitions for test mocks to avoid any-types
 * Created by CC to improve type safety in test files
 */

import type { MockedFunction } from 'vitest';
import type { ComponentProps, ReactNode } from 'react';

// Common mock component props interface
export interface MockComponentProps {
  children?: ReactNode;
  className?: string;
  [key: string]: unknown;
}

// Mock button component props
export interface MockButtonProps extends MockComponentProps {
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

// Mock form component props
export interface MockFormProps extends MockComponentProps {
  onSubmit?: (event: React.FormEvent) => void;
}

// Mock input component props
export interface MockInputProps extends MockComponentProps {
  value?: string | number;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  type?: string;
  disabled?: boolean;
}

// Utility type for properly typed mock functions
export type TypedMockFunction<T extends (...args: never[]) => unknown> = MockedFunction<T>;

// Common test data interfaces
export interface MockApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface MockWebSocketMessage {
  type: string;
  data: unknown;
  timestamp: string;
  id?: string | number;
}

// Mock hook return types
export interface MockUseStateReturn<T> {
  state: T;
  setState: (value: T | ((prev: T) => T)) => void;
}

export interface MockUseEffectReturn {
  cleanup?: () => void;
}

// API mock utilities
export interface MockApiCallOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
}

export interface MockApiError {
  message: string;
  status: number;
  type: 'network' | 'server' | 'client' | 'unknown';
  details?: Record<string, unknown>;
}

// Mock navigation utilities
export interface MockNavigateFunction {
  (to: string, options?: { replace?: boolean; state?: unknown }): void;
}

export interface MockLocation {
  pathname: string;
  search?: string;
  hash?: string;
  state?: unknown;
}

// Test fixture types
export interface TestUser {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface TestFlow {
  flow_id: string;
  data_import_id: string;
  status: string;
  next_phase: string;
  progress_percentage: number;
}

export interface TestFieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string;
  confidence: number;
  mapping_type: string;
  sample_values: string[];
  status: string;
  ai_reasoning: string;
  is_user_defined: boolean;
  user_feedback: string | null;
  validation_method: string;
  is_validated: boolean;
}

// Helper function type definitions
export interface MockAssertionMatcher<T = unknown> {
  toBe(expected: T): void;
  toEqual(expected: T): void;
  toBeNull(): void;
  toBeUndefined(): void;
  toBeTruthy(): void;
  toBeFalsy(): void;
  toHaveLength(length: number): void;
  toHaveBeenCalled(): void;
  toHaveBeenCalledWith(...args: unknown[]): void;
  toHaveBeenCalledTimes(times: number): void;
}