/**
 * Approved Card Component
 *
 * Card component for displaying approved field mappings.
 * Includes remove button to allow users to un-approve mappings.
 */

import React from 'react';
import { ArrowRight, X } from 'lucide-react';
import type { CardProps } from './types';
import { formatFieldValue, formatTargetAttribute } from './mappingUtils';

const ApprovedCard: React.FC<CardProps> = ({ mapping, onRemove }) => {
  const handleRemoveClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click event
    if (onRemove) {
      onRemove(mapping.id);
    }
  };

  return (
    <div className="p-4 border rounded-lg transition-all duration-200 bg-green-50 border-green-200 hover:shadow-md">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-1">
          <span className="font-medium text-gray-900">
            {formatFieldValue(mapping?.source_field ?? 'Unmapped')}
          </span>
          <ArrowRight className="h-4 w-4 text-gray-400" />
          <span className="text-green-600 font-medium">
            {formatTargetAttribute(mapping?.target_field ?? 'Unassigned')}
          </span>
        </div>

        {onRemove && (
          <button
            onClick={handleRemoveClick}
            className="p-1.5 rounded-md hover:bg-red-100 text-red-600 hover:text-red-700 transition-colors group"
            title="Remove this mapping"
            aria-label="Remove mapping"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default ApprovedCard;
