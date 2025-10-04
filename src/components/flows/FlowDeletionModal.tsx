/**
 * Flow Deletion Modal Component
 * Provides a React-based confirmation dialog for flow deletion
 * Replaces native browser confirm() dialogs
 */

import React from 'react';
import { AlertTriangle } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogAction,
  AlertDialogCancel,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import type { FlowDeletionRequest } from '@/services/flowDeletionService'
import type { FlowDeletionCandidate } from '@/services/flowDeletionService'

interface FlowDeletionModalProps {
  open: boolean;
  candidates: FlowDeletionCandidate[];
  deletionSource: FlowDeletionRequest['deletion_source'];
  isDeleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const FlowDeletionModal: React.FC<FlowDeletionModalProps> = ({
  open,
  candidates,
  deletionSource,
  isDeleting,
  onConfirm,
  onCancel
}) => {
  if (candidates.length === 0) {
    return null;
  }

  const getSourceIcon = (): unknown => {
    switch (deletionSource) {
      case 'automatic_cleanup':
        return '🤖';
      case 'bulk_cleanup':
        return '🧹';
      case 'navigation':
        return '🚨';
      default:
        return '🗑️';
    }
  };

  const getSourceTitle = (): unknown => {
    switch (deletionSource) {
      case 'automatic_cleanup':
        return 'System Cleanup Recommendation';
      case 'bulk_cleanup':
        return 'Bulk Cleanup Request';
      case 'navigation':
        return 'Navigation Cleanup Required';
      default:
        return 'Flow Deletion Confirmation';
    }
  };

  const getReasonDescription = (reason: FlowDeletionCandidate['reason_for_deletion']): string => {
    switch (reason) {
      case 'failed':
        return 'Failed/Error flows';
      case 'completed':
        return 'Completed flows';
      case 'stale':
        return 'Inactive flows (>30 days)';
      case 'user_requested':
        return 'User requested deletion';
      case 'cleanup_recommended':
        return 'Recommended for cleanup';
      default:
        return 'Unknown reason';
    }
  };

  const formatTimeAgo = (timestamp: string): string => {
    try {
      const now = new Date();
      const time = new Date(timestamp);
      const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));

      if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
      if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
      return `${Math.floor(diffInMinutes / 1440)}d ago`;
    } catch {
      return 'Unknown';
    }
  };

  const single = candidates.length === 1;

  return (
    <AlertDialog open={open} onOpenChange={(isOpen) => !isOpen && onCancel()}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <span>{getSourceIcon()}</span>
            <span>{getSourceTitle()}</span>
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              {single ? (
                <div className="space-y-2">
                  <p>Delete this flow?</p>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Flow:</span>
                      <span className="font-medium">{candidates[0].flow_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Flow ID:</span>
                      <span className="font-mono text-xs">{candidates[0].flowId}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Status:</span>
                      <Badge variant="outline" className="text-xs">
                        {candidates[0].status.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Phase:</span>
                      <span>{candidates[0].current_phase}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Progress:</span>
                      <span>{candidates[0].progress_percentage}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Reason:</span>
                      <span>{getReasonDescription(candidates[0].reason_for_deletion)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Last Updated:</span>
                      <span>{formatTimeAgo(candidates[0].updated_at)}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <p>Delete {candidates.length} flows?</p>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-2 text-sm">
                    <p className="font-medium">Breakdown by reason:</p>
                    {Object.entries(
                      candidates.reduce((acc, flow) => {
                        acc[flow.reason_for_deletion] = (acc[flow.reason_for_deletion] || 0) + 1;
                        return acc;
                      }, {} as Record<string, number>)
                    ).map(([reason, count]) => (
                      <div key={reason} className="flex justify-between">
                        <span className="text-gray-600">
                          {getReasonDescription(reason as FlowDeletionCandidate['reason_for_deletion'])}:
                        </span>
                        <span>{count} flows</span>
                      </div>
                    ))}
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-1 text-sm">
                    <p className="font-medium">Oldest flows:</p>
                    {candidates
                      .sort((a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime())
                      .slice(0, 3)
                      .map((flow) => (
                        <div key={flow.flowId} className="text-gray-600">
                          • {flow.flow_name} ({formatTimeAgo(flow.updated_at)})
                        </div>
                      ))}
                  </div>
                </div>
              )}

              <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
                <div className="text-sm text-red-800">
                  <p className="font-medium">This action cannot be undone.</p>
                  <p className="text-red-600 mt-1">
                    💡 Alternative: You can resume/retry flows instead of deleting them.
                  </p>
                </div>
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={isDeleting}
            className="bg-red-600 hover:bg-red-700"
          >
            {isDeleting ? 'Deleting...' : 'Delete Permanently'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};
