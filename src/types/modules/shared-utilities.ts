/**
 * Shared Utilities Module
 * 
 * Re-exports all shared utility types from modular files for backward compatibility.
 * 
 * This file has been modularized into focused type definition files:
 * - base-types.ts: Common base types and configuration options
 * - auth-types.ts: Authentication, authorization, multi-tenancy, and session management
 * - api-types.ts: API clients, request handling, caching, and retry mechanisms
 * - validation-types.ts: Data validation, sanitization, and form validation
 * - error-handling-types.ts: Error handling, error boundaries, and error recovery
 * - utility-types.ts: Common utility services (date, string, number, array, object, color)
 */

// Re-export all types from modular files
export type * from './shared-utilities/index';

// Export grouped modules for organized access
export type * as Auth from './shared-utilities/auth-types';
export type * as API from './shared-utilities/api-types';
export type * as Validation from './shared-utilities/validation-types';
export type * as ErrorHandling from './shared-utilities/error-handling-types';
export type * as Utils from './shared-utilities/utility-types';