/**
 * ItemDetailsDialog Component  
 * Dialog for viewing detailed information about deletion requests
 */

import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { formatDate, getItemTypeLabel } from '@/components/admin/shared/utils/adminFormatters';
import type { SoftDeletedItem } from './PlatformStats';

export interface ItemDetailsDialogProps {
  item: SoftDeletedItem | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ItemDetailsDialog: React.FC<ItemDetailsDialogProps> = ({
  item,
  isOpen,
  onClose
}) => {
  if (!item) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Deletion Request Details</DialogTitle>
          <DialogDescription>
            Complete information about this deletion request
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Item Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Item Type</label>
              <p className="text-sm text-muted-foreground">
                {getItemTypeLabel(item.item_type)}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Item Name</label>
              <p className="text-sm text-muted-foreground">{item.item_name}</p>
            </div>
            <div>
              <label className="text-sm font-medium">Deleted By</label>
              <p className="text-sm text-muted-foreground">
                {item.deleted_by_name}<br />
                <span className="text-xs">{item.deleted_by_email}</span>
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Deletion Date</label>
              <p className="text-sm text-muted-foreground">
                {formatDate(item.deleted_at)}
              </p>
            </div>
          </div>
          
          {/* Context */}
          {(item.client_account_name || item.engagement_name) && (
            <div>
              <label className="text-sm font-medium">Context</label>
              <div className="space-y-1 text-sm text-muted-foreground">
                {item.client_account_name && (
                  <p>Client: {item.client_account_name}</p>
                )}
                {item.engagement_name && (
                  <p>Engagement: {item.engagement_name}</p>
                )}
              </div>
            </div>
          )}
          
          {/* Deletion Reason */}
          {item.delete_reason && (
            <div>
              <label className="text-sm font-medium">Deletion Reason</label>
              <div className="bg-gray-50 rounded p-3 mt-1">
                <p className="text-sm">{item.delete_reason}</p>
              </div>
            </div>
          )}
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};