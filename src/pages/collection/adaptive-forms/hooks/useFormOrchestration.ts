/**
 * useFormOrchestration Hook
 * Coordinates the main form flow, state management, and initialization logic
 * Refactored from 410-line "God Hook" into focused, composable hooks
 *
 * Architecture:
 * - useFlowParams: URL params and auth context
 * - useBlockingFlowCheck: Incomplete flow checking
 * - useAdaptiveFormFlow: Core form state management
 * - useFlowInitialization: Protected initialization with ref guards
 * - usePollingStateManager: HTTP polling for workflow updates
 * - useCollectionFlowQuery: Collection flow details
 * - useProgressMilestones: Dynamic progress tracking
 */

import { groupQuestionsByAsset } from '@/utils/questionnaireUtils';
import type { ProgressMilestone } from '@/components/collection/types';
import type { CollectionFormData } from '@/components/collection/types';
import { useAdaptiveFormFlow } from '@/hooks/collection/useAdaptiveFormFlow';

// Focused sub-hooks
import { useFlowParams } from './useFlowParams';
import { useBlockingFlowCheck } from './useBlockingFlowCheck';
import { useFlowInitialization } from './useFlowInitialization';
import { usePollingStateManager } from './usePollingStateManager';
import { useCollectionFlowQuery } from './useCollectionFlowQuery';
import { useProgressMilestones } from './useProgressMilestones';

// Define types for collection flow
interface CollectionFlowConfig {
  selected_application_ids?: string[];
  applications?: string[];
  application_ids?: string[];
  has_applications?: boolean;
}

interface CollectionFlow {
  flow_id?: string;
  id?: string;
  progress?: number;
  current_phase?: string;
  collection_config?: CollectionFlowConfig;
}

interface UseFormOrchestrationReturn {
  // URL params and auth
  applicationId: string | null;
  flowId: string | null;
  client: ReturnType<typeof useFlowParams>['client'];
  engagement: ReturnType<typeof useFlowParams>['engagement'];
  user: ReturnType<typeof useFlowParams>['user'];

  // Initialization state
  initializationAttempts: React.MutableRefObject<Set<string>>;
  isInitializingRef: React.MutableRefObject<boolean>;
  protectedInitializeFlow: () => Promise<void>;

  // Flow blocking state
  skipIncompleteCheck: boolean;
  checkingFlows: boolean;
  hasBlockingFlows: boolean;
  blockingFlows: CollectionFlow[];
  shouldAutoInitialize: boolean;

  // Adaptive form flow state
  formData: CollectionFormData | null;
  formValues: Record<string, unknown> | null;
  validation: ReturnType<typeof useAdaptiveFormFlow>['validation'];
  isLoading: boolean;
  isSaving: boolean;
  isCompleted: boolean;
  error: ReturnType<typeof useAdaptiveFormFlow>['error'];
  activeFlowId: string | null;
  isPolling: boolean;
  completionStatus: ReturnType<typeof useAdaptiveFormFlow>['completionStatus'];
  statusLine: ReturnType<typeof useAdaptiveFormFlow>['statusLine'];

  // Form handlers
  handleFieldChange: ReturnType<typeof useAdaptiveFormFlow>['handleFieldChange'];
  handleValidationChange: ReturnType<typeof useAdaptiveFormFlow>['handleValidationChange'];
  handleSave: ReturnType<typeof useAdaptiveFormFlow>['handleSave'];
  handleSubmit: ReturnType<typeof useAdaptiveFormFlow>['handleSubmit'];
  initializeFlow: ReturnType<typeof useAdaptiveFormFlow>['initializeFlow'];

  // Flow management
  deleteFlow: ReturnType<typeof useBlockingFlowCheck>['deleteFlow'];
  isDeleting: ReturnType<typeof useBlockingFlowCheck>['isDeleting'];
  incompleteFlows: CollectionFlow[];
  refetchFlows: () => void;

  // Polling state
  isPollingActive: boolean;
  requestStatusUpdate: () => Promise<unknown>;
  flowState: ReturnType<typeof usePollingStateManager>['flowState'];

  // Collection flow query
  currentCollectionFlow: CollectionFlow | null;
  isLoadingFlow: boolean;
  refetchCollectionFlow: () => void;
  hasApplicationsSelected: (flow: CollectionFlow | null) => boolean;

  // Asset grouping and navigation
  assetGroups: ReturnType<typeof groupQuestionsByAsset>;
  filteredFormData: CollectionFormData | null;

  // Progress milestones
  progressMilestones: ProgressMilestone[];
}

/**
 * Main orchestration hook for the adaptive forms page
 * Now dramatically simplified by delegating to focused sub-hooks
 */
export const useFormOrchestration = (): UseFormOrchestrationReturn => {
  // 1. Extract URL parameters and auth context
  const { applicationId, flowId, client, engagement, user } = useFlowParams();

  // 2. Check for blocking flows and calculate auto-initialization
  const {
    skipIncompleteCheck,
    checkingFlows,
    hasBlockingFlows,
    shouldAutoInitialize,
    incompleteFlows,
    blockingFlows,
    refetchFlows,
    deleteFlow,
    isDeleting,
  } = useBlockingFlowCheck({ flowId });

  // 3. Initialize adaptive form flow with auto-initialization
  const {
    formData,
    formValues,
    validation,
    isLoading,
    isSaving,
    isCompleted,
    error,
    flowId: activeFlowId,
    isPolling,
    completionStatus,
    statusLine,
    handleFieldChange,
    handleValidationChange,
    handleSave,
    handleSubmit,
    initializeFlow,
  } = useAdaptiveFormFlow({
    applicationId,
    flowId,
    autoInitialize: shouldAutoInitialize,
  });

  // 4. Set up protected initialization with ref guards
  const {
    initializationAttempts,
    isInitializingRef,
    protectedInitializeFlow,
  } = useFlowInitialization({
    initializeFlow,
    activeFlowId,
    flowId,
  });

  // 5. Set up HTTP polling for workflow updates
  const {
    isPollingActive,
    requestStatusUpdate,
    flowState,
  } = usePollingStateManager({
    activeFlowId,
    isLoading,
    formData,
  });

  // 6. Query collection flow details
  const {
    currentCollectionFlow,
    isLoadingFlow,
    refetchCollectionFlow,
    hasApplicationsSelected,
  } = useCollectionFlowQuery({ activeFlowId });

  // 7. Generate progress milestones
  const progressMilestones = useProgressMilestones({
    formData,
    formValues,
  });

  // 8. Group questions by asset
  const assetGroups = groupQuestionsByAsset(
    formData?.sections?.flatMap(section =>
      section.fields.map(field => ({
        field_id: field.id,
        question_text: field.label,
        field_type: field.fieldType,
        required: field.validation?.required,
        options: field.options,
        metadata: field.metadata,
        ...field
      }))
    ) || [],
    undefined,
    formValues
  );

  // Filter form data to show only selected asset's questions (will be handled in component)
  const filteredFormData = formData;

  // Return orchestrated state and handlers
  return {
    // URL params and auth
    applicationId,
    flowId,
    client,
    engagement,
    user,

    // Initialization state
    initializationAttempts,
    isInitializingRef,
    protectedInitializeFlow,

    // Flow blocking state
    skipIncompleteCheck,
    checkingFlows,
    hasBlockingFlows,
    blockingFlows,
    shouldAutoInitialize,

    // Adaptive form flow state
    formData,
    formValues,
    validation,
    isLoading,
    isSaving,
    isCompleted,
    error,
    activeFlowId,
    isPolling,
    completionStatus,
    statusLine,

    // Form handlers
    handleFieldChange,
    handleValidationChange,
    handleSave,
    handleSubmit,
    initializeFlow,

    // Flow management
    deleteFlow,
    isDeleting,
    incompleteFlows,
    refetchFlows,

    // Polling state
    isPollingActive,
    requestStatusUpdate,
    flowState,

    // Collection flow query
    currentCollectionFlow,
    isLoadingFlow,
    refetchCollectionFlow,
    hasApplicationsSelected,

    // Asset grouping
    assetGroups,
    filteredFormData,

    // Progress milestones
    progressMilestones,
  };
};
