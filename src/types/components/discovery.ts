/**
 * Discovery Component Types
 * 
 * Re-exports all discovery component types from modular files for backward compatibility.
 * 
 * This file has been modularized into focused type definition files:
 * - base-types.ts: Core base interfaces and shared types
 * - field-mapping-types.ts: Field mapping components and related functionality 
 * - attribute-types.ts: Critical attribute management and editing
 * - data-import-types.ts: Data import selectors, file uploads, and raw data tables
 * - analysis-types.ts: Crew analysis panels, training progress, and analysis-related functionality
 */

// Re-export all types from modular files
export type * from './discovery/index';