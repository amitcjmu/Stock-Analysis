/**
 * Custom AG Grid Cell Renderer for Dependencies
 *
 * Displays count of selected dependencies as a badge.
 * Double-click to open modal showing full asset names.
 */

import React from 'react';
import type { ICellRendererParams } from 'ag-grid-community';
import { Badge } from '@/components/ui/badge';
import { Link } from 'lucide-react';

interface DependencyCellRendererProps extends ICellRendererParams {
  value: string | null | undefined;
}

export const DependencyCellRenderer: React.FC<DependencyCellRendererProps> = ({ value }) => {
  if (!value) {
    return <span className="text-xs text-gray-400">No dependencies</span>;
  }

  // Parse comma-separated IDs (can be numbers or UUIDs)
  const parts = value.toString().split(',').map(p => p.trim()).filter(p => p.length > 0);
  const count = parts.length;

  if (count === 0) {
    return <span className="text-xs text-gray-400">No dependencies</span>;
  }

  return (
    <div className="flex items-center gap-2 py-1">
      <Badge variant="secondary" className="flex items-center gap-1">
        <Link className="h-3 w-3" />
        <span>{count} {count === 1 ? 'dependency' : 'dependencies'}</span>
      </Badge>
      <span className="text-xs text-gray-500">Double-click to view/edit</span>
    </div>
  );
};
