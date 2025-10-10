/**
 * useModalState Hook
 * Manages all modal/dialog state for the adaptive forms page
 * Extracted from AdaptiveForms.tsx - Modal state management
 */

import { useState, useCallback } from 'react';

interface QuestionnaireData {
  questions: Array<{
    id: string;
    text: string;
    type: string;
    options?: string[];
  }>;
  metadata?: Record<string, unknown>;
}

interface UseModalStateReturn {
  // App selection state
  showAppSelectionPrompt: boolean;
  setShowAppSelectionPrompt: (show: boolean) => void;
  showInlineAppSelection: boolean;
  setShowInlineAppSelection: (show: boolean) => void;
  hasRedirectedForApps: boolean;
  setHasRedirectedForApps: (redirected: boolean) => void;

  // Questionnaire generation state
  showGenerationModal: boolean;
  setShowGenerationModal: (show: boolean) => void;
  isFallbackQuestionnaire: boolean;
  setIsFallbackQuestionnaire: (fallback: boolean) => void;

  // Manage flows modal state
  showManageFlowsModal: boolean;
  setShowManageFlowsModal: (show: boolean) => void;

  // Handlers
  handleQuestionnaireGeneration: () => void;
  handleQuestionnaireReady: (questionnaire: QuestionnaireData) => void;
  handleQuestionnaireFallback: () => void;
  handleAppSelectionComplete: () => void;
  handleAppSelectionCancel: () => void;
  handleManageFlows: () => void;
}

/**
 * Hook for managing modal state in the adaptive forms page
 */
export const useModalState = (
  protectedInitializeFlow: () => Promise<void>
): UseModalStateReturn => {
  // State to show app selection prompt when no applications are selected
  const [showAppSelectionPrompt, setShowAppSelectionPrompt] = useState(false);
  const [showInlineAppSelection, setShowInlineAppSelection] = useState(false);
  const [hasRedirectedForApps, setHasRedirectedForApps] = useState(false);

  // State for questionnaire generation modal
  const [showGenerationModal, setShowGenerationModal] = useState(false);
  const [isFallbackQuestionnaire, setIsFallbackQuestionnaire] = useState(false);

  // State for manage flows modal
  const [showManageFlowsModal, setShowManageFlowsModal] = useState(false);

  // Show questionnaire generation modal when flow starts
  const handleQuestionnaireGeneration = useCallback(() => {
    setShowGenerationModal(true);
  }, []);

  // Handle questionnaire ready from modal
  const handleQuestionnaireReady = useCallback((questionnaire: QuestionnaireData) => {
    setShowGenerationModal(false);
    setIsFallbackQuestionnaire(false);
    // Reload the form with the new questionnaire
    window.location.reload();
  }, []);

  // Handle fallback to template questionnaire
  const handleQuestionnaireFallback = useCallback(() => {
    setShowGenerationModal(false);
    setIsFallbackQuestionnaire(true);
  }, []);

  // Handle inline application selection for 422 errors
  const handleAppSelectionComplete = useCallback(() => {
    setShowInlineAppSelection(false);
    // Re-initialize the flow after app selection
    protectedInitializeFlow();
  }, [protectedInitializeFlow]);

  const handleAppSelectionCancel = useCallback(() => {
    setShowInlineAppSelection(false);
  }, []);

  const handleManageFlows = useCallback((): void => {
    setShowManageFlowsModal(true);
  }, []);

  return {
    // App selection state
    showAppSelectionPrompt,
    setShowAppSelectionPrompt,
    showInlineAppSelection,
    setShowInlineAppSelection,
    hasRedirectedForApps,
    setHasRedirectedForApps,

    // Questionnaire generation state
    showGenerationModal,
    setShowGenerationModal,
    isFallbackQuestionnaire,
    setIsFallbackQuestionnaire,

    // Manage flows modal state
    showManageFlowsModal,
    setShowManageFlowsModal,

    // Handlers
    handleQuestionnaireGeneration,
    handleQuestionnaireReady,
    handleQuestionnaireFallback,
    handleAppSelectionComplete,
    handleAppSelectionCancel,
    handleManageFlows,
  };
};
