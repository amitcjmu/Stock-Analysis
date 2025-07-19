/**
 * Discovery Hooks Types
 * 
 * Re-exports all discovery hook types from modular files for backward compatibility.
 * 
 * This file has been modularized into focused type definition files:
 * - base-hooks.ts: Common base types and interfaces
 * - attribute-mapping-hooks.ts: Attribute mapping and field configuration types
 * - flow-detection-hooks.ts: Flow detection and workflow orchestration types
 * - analysis-hooks.ts: Data analysis, training, and model comparison types
 * - data-import-hooks.ts: Data import, validation, and export types
 */

// Re-export all types from modular files
export * from './discovery/index';