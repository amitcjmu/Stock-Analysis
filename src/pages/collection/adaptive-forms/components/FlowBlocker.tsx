/**
 * FlowBlocker Component
 * UI shown when there are incomplete flows blocking new collection
 * Extracted from AdaptiveForms.tsx
 */

import React from 'react';
import CollectionPageLayout from '@/components/collection/layout/CollectionPageLayout';
import { CollectionUploadBlocker } from '@/components/collection/CollectionUploadBlocker';
import { FlowDeletionModal } from '@/components/flows/FlowDeletionModal';
import { IncompleteCollectionFlowManager } from '@/components/collection/IncompleteCollectionFlowManager';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';

interface CollectionFlow {
  flow_id?: string;
  id?: string;
  status?: string;
  current_phase?: string;
}

interface FlowBlockerProps {
  blockingFlows: CollectionFlow[];
  incompleteFlows: CollectionFlow[];
  isDeleting: boolean;
  showManageFlowsModal: boolean;
  onSetShowManageFlowsModal: (show: boolean) => void;
  onContinueFlow: (flowId: string) => Promise<void>;
  onDeleteFlow: (flowId: string) => Promise<void>;
  onViewDetails: (flowId: string, phase: string) => void;
  onManageFlows: () => void;
  onRefresh: () => void;
  // Deletion modal props
  deletionState: {
    isModalOpen: boolean;
    candidates: Array<{ flowId?: string }>;
    deletionSource: string;
    isDeleting: boolean;
  };
  onConfirmDeletion: () => Promise<void>;
  onCancelDeletion: () => void;
}

export const FlowBlocker: React.FC<FlowBlockerProps> = ({
  blockingFlows,
  incompleteFlows,
  isDeleting,
  showManageFlowsModal,
  onSetShowManageFlowsModal,
  onContinueFlow,
  onDeleteFlow,
  onViewDetails,
  onManageFlows,
  onRefresh,
  deletionState,
  onConfirmDeletion,
  onCancelDeletion,
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
        onConfirm={onConfirmDeletion}
        onCancel={onCancelDeletion}
      />

      {/* Manage Flows Modal - must be available even when blocking */}
      <Dialog open={showManageFlowsModal} onOpenChange={onSetShowManageFlowsModal}>
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
            onBatchDelete={(flowIds: string[]) => {
              // Handle batch deletion
              flowIds.forEach(flowId => onDeleteFlow(flowId));
            }}
            onViewDetails={onViewDetails}
            isLoading={isDeleting}
          />
        </DialogContent>
      </Dialog>
    </>
  );
};
