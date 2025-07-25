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
import { eventSourceService } from './useAssessmentFlow/eventSource';

// Re-export the main hook
export const useAssessmentFlow = useAssessmentFlowImpl;

// Re-export API client and event source
export { assessmentFlowAPI, eventSourceService };

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
