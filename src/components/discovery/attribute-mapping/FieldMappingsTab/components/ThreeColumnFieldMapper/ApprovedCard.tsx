/**
 * Approved Card Component
 *
 * Card component for displaying approved field mappings.
 */

import React from 'react';
import { ArrowRight } from 'lucide-react';
import type { CardProps } from './types';
import { formatFieldValue, formatTargetAttribute } from './mappingUtils';

const ApprovedCard: React.FC<CardProps> = ({ mapping }) => (
  <div className="p-4 border rounded-lg transition-all duration-200 bg-green-50 border-green-200">
    <div className="flex items-center gap-2">
      <span className="font-medium text-gray-900">
        {formatFieldValue(mapping.sourceField)}
      </span>
      <ArrowRight className="h-4 w-4 text-gray-400" />
      <span className="text-green-600 font-medium">
        {formatTargetAttribute(mapping.targetAttribute)}
      </span>
    </div>
  </div>
);

export default ApprovedCard;
