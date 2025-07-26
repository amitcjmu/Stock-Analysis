/**
 * Bulk Actions Component
 *
 * Component for bulk approve and bulk reject operations.
 */

import React from 'react';
import { CheckCircle, XCircle } from 'lucide-react';
import type { BulkActionsProps } from './types';

const BulkActions: React.FC<BulkActionsProps> = ({
  buckets,
  onBulkApprove,
  onBulkReject,
  processingMappings,
  lastBulkOperationTime,
  client,
  engagement
}) => {
  if (buckets.autoMapped.length === 0) {
    return null;
  }

  const handleBulkApprove = (): void => {
    const mappingIds = buckets.autoMapped.map(m => m.id);
    onBulkApprove(mappingIds);
  };

  const handleBulkReject = (): void => {
    const mappingIds = buckets.autoMapped.map(m => m.id);
    onBulkReject(mappingIds);
  };

  const isDisabled = !client?.id || !engagement?.id ||
                    buckets.autoMapped.some(m => processingMappings.has(m.id)) ||
                    (Date.now() - lastBulkOperationTime < 5000);

  const getButtonText = (action: 'approve' | 'reject'): JSX.Element => {
    if (!client?.id || !engagement?.id) return 'Login Required';
    if (buckets.autoMapped.some(m => processingMappings.has(m.id))) return 'Processing...';
    if (Date.now() - lastBulkOperationTime < 5000) return 'Cooldown...';
    return action === 'approve' ? 'Approve All' : 'Reject All';
  };

  return (
    <div className="bg-white p-4 rounded-lg border">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">
          Bulk Actions for {buckets.autoMapped.length} auto-mapped fields
        </span>
        <div className="flex gap-2">
          <button
            onClick={handleBulkApprove}
            disabled={isDisabled}
            className="flex items-center gap-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckCircle className="h-4 w-4" />
            {getButtonText('approve')}
          </button>
          <button
            onClick={handleBulkReject}
            disabled={isDisabled}
            className="flex items-center gap-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <XCircle className="h-4 w-4" />
            {getButtonText('reject')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BulkActions;
