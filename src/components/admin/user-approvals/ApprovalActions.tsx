/**
 * ApprovalActions Component
 * Action buttons for user approval operations
 */

import React from 'react';
import { Eye, XCircle, UserCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { ApprovalActionsProps } from './types';

export const ApprovalActions: React.FC<ApprovalActionsProps> = ({
  user,
  actionLoading,
  onApprove,
  onReject,
  onViewDetails
}) => {
  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={onViewDetails}
      >
        <Eye className="w-4 h-4 mr-1" />
        Details
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={onReject}
        disabled={actionLoading === user.user_id}
      >
        <XCircle className="w-4 h-4 mr-1" />
        Reject
      </Button>

      <Button
        size="sm"
        onClick={onApprove}
        disabled={actionLoading === user.user_id}
      >
        {actionLoading === user.user_id ? (
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
        ) : (
          <>
            <UserCheck className="w-4 h-4 mr-1" />
            Approve
          </>
        )}
      </Button>
    </div>
  );
};
