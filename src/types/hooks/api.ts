/**
 * API Hook Types
 * 
 * Type definitions for API-related hooks including data fetching,
 * mutation hooks, and API client configuration patterns.
 * 
 * This file maintains backward compatibility by re-exporting all types
 * from the modularized structure. New imports should use the specific
 * module imports from the api/ subdirectory for better tree-shaking.
 * 
 * @deprecated Import from specific modules in api/ subdirectory instead
 * Example: import { UseQueryParams } from './api/query';
 */

// Re-export everything from the modularized structure for backward compatibility
export * from './api';
