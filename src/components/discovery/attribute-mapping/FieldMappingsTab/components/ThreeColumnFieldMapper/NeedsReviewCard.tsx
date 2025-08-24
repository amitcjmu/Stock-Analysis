/**
 * Needs Review Card Component
 *
 * Card component for mappings that need manual review and configuration.
 */

import React from 'react'
import { useState } from 'react'
import { useCallback } from 'react'
import { CheckCircle } from 'lucide-react';
import { EnhancedFieldDropdown } from '../EnhancedFieldDropdown';
import type { CardProps } from './types';
import type { TargetField } from '../../types';
import { formatFieldValue } from './mappingUtils';

interface NeedsReviewCardProps extends CardProps {
  availableFields: TargetField[];
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  onApprove: (mappingId: string) => void;
}

const NeedsReviewCard: React.FC<NeedsReviewCardProps> = ({
  mapping,
  availableFields,
  onMappingChange,
  onApprove
}) => {
  const [selectedTarget, setSelectedTarget] = useState(mapping.target_field || '');

  const handleConfirmMapping = (): void => {
    if (onMappingChange && selectedTarget !== mapping.target_field) {
      onMappingChange(mapping.id, selectedTarget);
    }
    onApprove(mapping.id);
  };

  const handleFieldChange = useCallback((newValue: string) => {
    setSelectedTarget(newValue);
  }, []);

  return (
    <div className="p-4 border rounded-lg transition-all duration-200 hover:shadow-md bg-white border-gray-200">
      <div className="grid grid-cols-1 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Source Field:</label>
          <div className="px-3 py-2 bg-gray-50 rounded border text-sm font-medium">
            {formatFieldValue(mapping.source_field)}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Map to Asset Table Field:</label>
          <div className="flex gap-2">
            <div className="flex-1">
              <EnhancedFieldDropdown
                value={selectedTarget}
                onChange={handleFieldChange}
                availableFields={availableFields}
                placeholder="Select target field"
              />
            </div>
            <button
              onClick={handleConfirmMapping}
              className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
              disabled={!selectedTarget}
            >
              <CheckCircle className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NeedsReviewCard;
