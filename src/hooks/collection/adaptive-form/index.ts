/**
 * Modularized adaptive form flow hooks
 *
 * This module provides a modular alternative to the monolithic useAdaptiveFormFlow hook.
 *
 * MIGRATION STRATEGY:
 * - Phase 1 (CURRENT): Modular hooks available for NEW code
 * - Phase 2: Gradual migration of existing components
 * - Phase 3: Replace useAdaptiveFormFlow.ts with composition of these hooks
 *
 * PRESERVED CRITICAL SECTIONS:
 * - HTTP polling logic (lines 808-930 of original) - stays in main hook for now
 * - Auto-init effects (lines 1700-1869) - extracted to useAutoInit
 * - All ref-based guards maintained exactly
 *
 * For existing code, continue using:
 * `import { useAdaptiveFormFlow } from "@/hooks/collection/useAdaptiveFormFlow";`
 *
 * For new code, you can use modular hooks:
 * `import { useFormState, useQuestionnaireHandlers } from "@/hooks/collection/adaptive-form";`
 */

// Re-export all types
export type {
  FormQuestion,
  UseAdaptiveFormFlowOptions,
  CollectionQuestionnaire,
  AdaptiveFormFlowState,
  AdaptiveFormFlowActions,
} from "./types";

// Re-export utility functions
export { extractExistingResponses } from "./types";

// Re-export modular hooks
export { useFormState } from "./useFormState";
export type { UseFormStateReturn } from "./useFormState";

export { useQuestionnaireHandlers } from "./useQuestionnaireHandlers";
export type {
  UseQuestionnaireHandlersProps,
  UseQuestionnaireHandlersReturn,
} from "./useQuestionnaireHandlers";

export { useSubmitHandler } from "./useSubmitHandler";
export type {
  UseSubmitHandlerProps,
  UseSubmitHandlerReturn,
} from "./useSubmitHandler";

export { useAutoInit } from "./useAutoInit";
export type {
  UseAutoInitProps,
  UseAutoInitReturn,
} from "./useAutoInit";

/**
 * Example usage of modular hooks (for NEW components):
 *
 * ```typescript
 * import {
 *   useFormState,
 *   useQuestionnaireHandlers,
 *   useSubmitHandler,
 *   useAutoInit,
 * } from "@/hooks/collection/adaptive-form";
 *
 * function MyComponent() {
 *   const urlFlowId = searchParams.get("flowId");
 *
 *   // 1. Initialize state
 *   const { state, setState, currentFlowIdRef, updateFlowId } = useFormState(urlFlowId);
 *
 *   // 2. Define initializeFlow (or import from main hook)
 *   const initializeFlow = useCallback(async () => {
 *     // Your initialization logic here
 *   }, [dependencies]);
 *
 *   // 3. Setup handlers
 *   const handlers = useQuestionnaireHandlers({
 *     state,
 *     setState,
 *     applicationId,
 *     currentFlowIdRef,
 *     setCurrentFlow,
 *     initializeFlow,
 *   });
 *
 *   // 4. Setup submit handler
 *   const { handleSubmit } = useSubmitHandler({
 *     state,
 *     setState,
 *     applicationId,
 *     updateFlowId,
 *   });
 *
 *   // 5. Setup auto-initialization
 *   useAutoInit({
 *     urlFlowId,
 *     autoInitialize: true,
 *     skipIncompleteCheck,
 *     checkingFlows,
 *     hasBlockingFlows,
 *     formData: state.formData,
 *     isLoading: state.isLoading,
 *     error: state.error,
 *     initializeFlow,
 *     setState,
 *   });
 *
 *   return <AdaptiveForm {...state} {...handlers} onSubmit={handleSubmit} />;
 * }
 * ```
 *
 * NOTE: For the full integrated experience with HTTP polling and all features,
 * continue using the main useAdaptiveFormFlow hook from useAdaptiveFormFlow.ts
 */
