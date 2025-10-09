/**
 * FlowControlPanel component
 * Handles modals, buttons, and controls for the adaptive forms workflow
 * Extracted from AdaptiveForms.tsx for better maintainability
 */

import React from "react";
import { FlowDeletionModal } from "@/components/flows/FlowDeletionModal";
import { QuestionnaireGenerationModal } from "@/components/collection/QuestionnaireGenerationModal";
import { IncompleteCollectionFlowManager } from "@/components/collection/IncompleteCollectionFlowManager";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import type { CollectionFlow, QuestionnaireData } from "../types";

interface FlowControlPanelProps {
  // Generation modal state
  showGenerationModal: boolean;
  activeFlowId: string | null;
  onQuestionnaireReady: (questionnaire: QuestionnaireData) => void;
  onQuestionnaireFallback: () => void;
  onGenerationRetry: () => void;

  // Deletion modal state
  deletionState: {
    isModalOpen: boolean;
    candidates: Array<{ flowId: string }>;
    deletionSource: string;
    isDeleting: boolean;
  };
  onDeletionConfirm: () => Promise<void>;
  onDeletionCancel: () => void;

  // Manage flows modal state
  showManageFlowsModal: boolean;
  incompleteFlows: CollectionFlow[];
  isDeleting: boolean;
  onManageFlowsChange: (open: boolean) => void;
  onContinueFlow: (flowId: string) => void;
  onDeleteFlow: (flowId: string) => void;
  onBatchDelete: (flowIds: string[]) => void;
  onViewDetails: (flowId: string, phase: string) => void;
}

export const FlowControlPanel: React.FC<FlowControlPanelProps> = ({
  showGenerationModal,
  activeFlowId,
  onQuestionnaireReady,
  onQuestionnaireFallback,
  onGenerationRetry,
  deletionState,
  onDeletionConfirm,
  onDeletionCancel,
  showManageFlowsModal,
  incompleteFlows,
  isDeleting,
  onManageFlowsChange,
  onContinueFlow,
  onDeleteFlow,
  onBatchDelete,
  onViewDetails,
}) => {
  return (
    <>
      {/* Flow Deletion Modal */}
      <FlowDeletionModal
        open={deletionState.isModalOpen}
        candidates={deletionState.candidates}
        deletionSource={deletionState.deletionSource}
        isDeleting={deletionState.isDeleting}
        onConfirm={onDeletionConfirm}
        onCancel={onDeletionCancel}
      />

      {/* Questionnaire Generation Modal */}
      <QuestionnaireGenerationModal
        isOpen={showGenerationModal}
        flowId={activeFlowId}
        onComplete={onQuestionnaireReady}
        onFallback={onQuestionnaireFallback}
        onRetry={onGenerationRetry}
      />

      {/* Manage Flows Modal */}
      <Dialog open={showManageFlowsModal} onOpenChange={onManageFlowsChange}>
        <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Manage Collection Flows</DialogTitle>
            <DialogDescription>
              Manage and resume incomplete collection flows. Complete existing flows before starting new ones.
            </DialogDescription>
          </DialogHeader>
          <IncompleteCollectionFlowManager
            flows={incompleteFlows}
            onContinueFlow={onContinueFlow}
            onDeleteFlow={onDeleteFlow}
            onBatchDelete={onBatchDelete}
            onViewDetails={onViewDetails}
            isLoading={isDeleting}
          />
        </DialogContent>
      </Dialog>
    </>
  );
};
