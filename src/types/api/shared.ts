/**
 * Shared API Types
 * 
 * Re-exports all shared API types from modular files for backward compatibility.
 * 
 * This file has been modularized into focused type definition files:
 * - base-types.ts: Core API request/response interfaces and error handling
 * - tenant-types.ts: Multi-tenant context and header types
 * - crud-types.ts: Standard CRUD operation patterns (Create, Read, Update, Delete)
 * - query-types.ts: Filtering, sorting, and querying utilities
 * - search-types.ts: Search operations and advanced search capabilities
 * - file-types.ts: File upload, download, and metadata handling
 * - bulk-types.ts: Bulk operations and batch processing
 * - import-export-types.ts: Data import/export and transformation
 * - realtime-types.ts: WebSocket connections and real-time messaging
 * - monitoring-types.ts: Health checks, metrics, and system observability
 */

// Re-export all types from modular files
export type * from './shared/index';