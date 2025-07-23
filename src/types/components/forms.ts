/**
 * Form Component Types
 * 
 * Re-exports all form component types from modular files for backward compatibility.
 * 
 * This file has been modularized into focused type definition files:
 * - base-types.ts: Common base interfaces, validation, and form utilities
 * - form-container-types.ts: Form containers, form fields, and form-level configuration
 * - input-types.ts: Text inputs, number inputs, textareas, and related input components
 * - select-types.ts: Select components, dropdowns, and select-related functionality
 * - choice-types.ts: Checkbox, radio, switch, and other choice-based form components
 * - advanced-types.ts: Sliders, file uploads, and other advanced form components
 */

// Re-export all types from modular files
export type * from './forms/index';