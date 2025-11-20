/**
 * Data Cell Renderer - Displays preview data values from imported CSV/JSON
 *
 * Handles different data types (string, number, boolean, JSON) with proper
 * truncation and tooltips for long values.
 *
 * @component DataCellRenderer
 */

import React from "react";
import type { ICellRendererParams } from "ag-grid-community";

export interface DataCellRendererProps extends ICellRendererParams {
  value: unknown;
}

export const DataCellRenderer: React.FC<DataCellRendererProps> = ({
  value,
}) => {
  // Handle null/undefined values
  if (value === null || value === undefined) {
    return <div className="px-3 py-2 text-sm text-gray-400 italic">-</div>;
  }

  // Convert value to string for display
  let displayValue: string;

  if (typeof value === "boolean") {
    displayValue = value ? "true" : "false";
  } else if (typeof value === "object" && value !== null) {
    // Handle JSON objects/arrays (but not null, which is also typeof 'object')
    try {
      displayValue = JSON.stringify(value);
    } catch {
      displayValue = "[Object]";
    }
  } else {
    displayValue = String(value);
  }

  // Truncate very long values (> 50 chars)
  const isTruncated = displayValue.length > 50;
  const truncatedValue = isTruncated
    ? displayValue.substring(0, 50) + "..."
    : displayValue;

  return (
    <div
      className="px-3 py-2 text-sm text-gray-900 truncate"
      title={isTruncated ? displayValue : undefined}
    >
      {truncatedValue}
    </div>
  );
};
