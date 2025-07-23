/**
 * PurgeActionDialog Component
 * Dialog for approving or rejecting purge requests
 */

import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Trash2, RotateCcw } from 'lucide-react';
import { getItemTypeColor } from '@/components/admin/shared/utils/adminFormatters'
import { formatDate, getItemTypeLabel } from '@/components/admin/shared/utils/adminFormatters'
import { SoftDeletedItem } from './PlatformStats';

export interface PurgeAction {
  action: 'approve' | 'reject';
  item: SoftDeletedItem;
  notes: string;
}

export interface PurgeActionDialogProps {
  isOpen: boolean;
  purgeAction: PurgeAction | null;
  onClose: () => void;
  onExecute: () => void;
  onNotesChange: (notes: string) => void;
}

export const PurgeActionDialog: React.FC<PurgeActionDialogProps> = ({
  isOpen,
  purgeAction,
  onClose,
  onExecute,
  onNotesChange
}) => {
  if (!purgeAction) return null;

  const isApprove = purgeAction.action === 'approve';
  const isReject = purgeAction.action === 'reject';

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isApprove ? 'Approve Permanent Deletion' : 'Reject Deletion and Restore'}
          </DialogTitle>
          <DialogDescription>
            {isApprove 
              ? `You are about to permanently delete "${purgeAction.item.item_name}". This action cannot be undone.`
              : `You are about to restore "${purgeAction.item.item_name}" and reject the deletion request.`
            }
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Item Summary */}
          <div className="bg-gray-50 rounded p-3 space-y-2">
            <div className="flex items-center gap-2">
              <Badge className={getItemTypeColor(purgeAction.item.item_type)}>
                {getItemTypeLabel(purgeAction.item.item_type)}
              </Badge>
              <span className="font-medium">{purgeAction.item.item_name}</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Deleted by {purgeAction.item.deleted_by_name} on {formatDate(purgeAction.item.deleted_at)}
            </p>
            {purgeAction.item.delete_reason && (
              <p className="text-sm">
                <strong>Original reason:</strong> {purgeAction.item.delete_reason}
              </p>
            )}
          </div>
          
          {/* Admin Notes */}
          <div>
            <label htmlFor="admin-notes" className="block text-sm font-medium mb-2">
              Admin Notes {isApprove ? '(Optional)' : '(Required)'}
            </label>
            <Textarea
              id="admin-notes"
              placeholder={isApprove 
                ? "Add any notes about this approval..."
                : "Explain why this deletion is being rejected..."
              }
              value={purgeAction.notes}
              onChange={(e) => onNotesChange(e.target.value)}
              required={isReject}
            />
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            variant={isApprove ? "destructive" : "default"}
            onClick={onExecute}
            disabled={isReject && !purgeAction.notes?.trim()}
          >
            {isApprove ? (
              <>
                <Trash2 className="w-4 h-4 mr-2" />
                Permanently Delete
              </>
            ) : (
              <>
                <RotateCcw className="w-4 h-4 mr-2" />
                Restore Item
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};