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
export * from './shared-utilities/index';

// Export grouped modules for organized access
export * as Auth from './shared-utilities/auth-types';
export * as API from './shared-utilities/api-types';
export * as Validation from './shared-utilities/validation-types';
export * as ErrorHandling from './shared-utilities/error-handling-types';
export * as Utils from './shared-utilities/utility-types';