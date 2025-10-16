/**
 * Assessment Flow Hook
 *
 * Main React hook for managing assessment flow state and operations.
 *
 * This file has been modularized for better maintainability.
 * Individual modules are located in ./useAssessmentFlow/ directory.
 */

// Import from the modularized structure
import { useAssessmentFlow as useAssessmentFlowImpl } from './useAssessmentFlow/useAssessmentFlow';
import { assessmentFlowAPI } from './useAssessmentFlow/api';
// NOTE: eventSourceService removed per SSE elimination (HTTP/2 polling only)

// Re-export the main hook
export const useAssessmentFlow = useAssessmentFlowImpl;

// Re-export API client
export { assessmentFlowAPI };

// Re-export all types
export type {
  AssessmentFlowStatus,
  AssessmentPhase,
  ArchitectureStandard,
  ApplicationComponent,
  TechDebtItem,
  ComponentTreatment,
  SixRDecision,
  AssessmentFlowState,
  UseAssessmentFlowReturn
} from './useAssessmentFlow/types';
