/**
 * FlowBlockerDisplay component
 * Displays blocker UI when there are incomplete flows
 * Extracted from AdaptiveForms.tsx for better maintainability
 */

import React from "react";
import CollectionPageLayout from "@/components/collection/layout/CollectionPageLayout";
import { CollectionUploadBlocker } from "@/components/collection/CollectionUploadBlocker";
import { IncompleteCollectionFlowManager } from "@/components/collection/IncompleteCollectionFlowManager";
import { FlowDeletionModal } from "@/components/flows/FlowDeletionModal";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import type { CollectionFlow } from "../types";

interface FlowBlockerDisplayProps {
  blockingFlows: CollectionFlow[];
  incompleteFlows: CollectionFlow[];
  deletionState: {
    isModalOpen: boolean;
    candidates: Array<{ flowId?: string }>;
    deletionSource: string;
    isDeleting: boolean;
  };
  showManageFlowsModal: boolean;
  isDeleting: boolean;
  onContinueFlow: (flowId: string) => void;
  onDeleteFlow: (flowId: string) => Promise<void>;
  onBatchDelete: (flowIds: string[]) => void;
  onViewDetails: (flowId: string, phase: string) => void;
  onManageFlows: () => void;
  onRefresh: () => void;
  onManageFlowsModalChange: (open: boolean) => void;
  onDeletionConfirm: () => Promise<void>;
  onDeletionCancel: () => void;
}

export const FlowBlockerDisplay: React.FC<FlowBlockerDisplayProps> = ({
  blockingFlows,
  incompleteFlows,
  deletionState,
  showManageFlowsModal,
  isDeleting,
  onContinueFlow,
  onDeleteFlow,
  onBatchDelete,
  onViewDetails,
  onManageFlows,
  onRefresh,
  onManageFlowsModalChange,
  onDeletionConfirm,
  onDeletionCancel,
}) => {
  return (
    <>
      <CollectionPageLayout
        title="Adaptive Data Collection"
        description="Collection workflow blocked - manage existing flows"
      >
        <CollectionUploadBlocker
          incompleteFlows={blockingFlows}
          onContinueFlow={onContinueFlow}
          onDeleteFlow={onDeleteFlow}
          onViewDetails={onViewDetails}
          onManageFlows={onManageFlows}
          onRefresh={onRefresh}
          isLoading={isDeleting}
        />
      </CollectionPageLayout>

      {/* Flow Deletion Modal - must be available even when blocking */}
      <FlowDeletionModal
        open={deletionState.isModalOpen}
        candidates={deletionState.candidates}
        deletionSource={deletionState.deletionSource}
        isDeleting={deletionState.isDeleting}
        onConfirm={onDeletionConfirm}
        onCancel={onDeletionCancel}
      />

      {/* Manage Flows Modal - must be available even when blocking */}
      <Dialog open={showManageFlowsModal} onOpenChange={onManageFlowsModalChange}>
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
