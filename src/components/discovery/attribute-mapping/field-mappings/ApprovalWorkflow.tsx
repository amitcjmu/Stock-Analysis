import React from 'react';
import { CheckCircle, X, RefreshCw } from 'lucide-react';
import type { ApprovalWorkflowProps } from './types';

const ApprovalWorkflow: React.FC<ApprovalWorkflowProps> = ({
  mapping,
  isApproving,
  isRejecting,
  onApprove,
  onReject
}) => {
  // Only show approval workflow for pending mappings
  if (mapping.status !== 'pending' && mapping.status !== 'suggested' && mapping.status) {
    // Status indicator for completed mappings
    return (
      <div className={`px-2 py-1 text-xs rounded-full ${
        mapping.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
      }`}>
        {mapping.status}
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 ml-4">
      <button
        onClick={onApprove}
        disabled={isApproving || isRejecting}
        className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        title="Approve mapping"
      >
        {isApproving ? (
          <RefreshCw className="h-3 w-3 animate-spin" />
        ) : (
          <CheckCircle className="h-3 w-3" />
        )}
        <span>{isApproving ? 'Approving...' : 'Approve'}</span>
      </button>
      <button
        onClick={onReject}
        disabled={isApproving || isRejecting}
        className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
        title="Reject mapping"
      >
        {isRejecting ? (
          <RefreshCw className="h-3 w-3 animate-spin" />
        ) : (
          <X className="h-3 w-3" />
        )}
        <span>{isRejecting ? 'Rejecting...' : 'Reject'}</span>
      </button>
    </div>
  );
};

export default ApprovalWorkflow;