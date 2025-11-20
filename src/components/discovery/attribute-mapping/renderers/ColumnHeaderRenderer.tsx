/**
 * Column Header Renderer - Displays source CSV/JSON field names
 *
 * Shows the original column header from imported data with:
 * - FileText icon indicator
 * - Italicized styling
 * - Gray background for visual separation
 * - Truncation with tooltip for long names
 *
 * @component ColumnHeaderRenderer
 */

import React from 'react';
import type { ICellRendererParams } from 'ag-grid-community';
import { FileText } from 'lucide-react';

export interface ColumnHeaderRendererProps extends ICellRendererParams {
  value: string;
}

export const ColumnHeaderRenderer: React.FC<ColumnHeaderRendererProps> = ({ value }) => {
  // Handle empty/null values
  if (!value) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded">
        <FileText className="w-4 h-4 text-gray-400" />
        <span className="text-sm text-gray-400 italic">
          (empty)
        </span>
      </div>
    );
  }

  // Truncate long header names (> 40 chars)
  const isTruncated = value.length > 40;
  const displayValue = isTruncated
    ? value.substring(0, 40) + '...'
    : value;

  return (
    <div
      className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded"
      title={isTruncated ? value : undefined}
    >
      <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
      <span className="text-sm font-medium text-gray-700 italic truncate">
        {displayValue}
      </span>
    </div>
  );
};
