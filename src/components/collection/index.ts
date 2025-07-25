/**
 * Collection Components Index
 *
 * Frontend components for the Manual Collection Framework
 * Agent Team B3 Implementation
 */

// Core collection components
export { AdaptiveForm } from './AdaptiveForm';
export { BulkDataGrid } from './BulkDataGrid';
export { ProgressTracker } from './ProgressTracker';
export { ValidationDisplay } from './ValidationDisplay';
export { TemplateSelector } from './TemplateSelector';
export { DataIntegrationView } from './DataIntegrationView';

// Sub-components and utilities
export { FormField } from './components/FormField';
export { SectionCard } from './components/SectionCard';
export { BulkUpload } from './components/BulkUpload';
export { ProgressMilestone } from './components/ProgressMilestone';
export { ConflictResolver } from './components/ConflictResolver';

// Types
export type {
  AdaptiveFormProps,
  BulkDataGridProps,
  ProgressTrackerProps,
  ValidationDisplayProps,
  FormFieldProps,
  CollectionFormData
} from './types';
