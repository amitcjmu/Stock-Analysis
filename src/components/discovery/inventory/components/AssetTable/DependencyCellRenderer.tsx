/**
 * Custom AG Grid Cell Renderer for Dependencies
 *
 * Displays count of selected dependencies as a badge with Edit button.
 * Click the Edit button to open the dependency editor popup.
 */

import React, { useCallback } from 'react';
import type { ICellRendererParams } from 'ag-grid-community';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Link, Edit2 } from 'lucide-react';

interface DependencyCellRendererProps extends ICellRendererParams {
  value: string | null | undefined;
}

export const DependencyCellRenderer: React.FC<DependencyCellRendererProps> = (props) => {
  const { value, data, api, node, colDef } = props;

  // CC FIX: Programmatically start editing when Edit button is clicked
  const handleEditClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent row selection
    console.log('[DependencyCellRenderer] Edit button clicked');
    console.log('[DependencyCellRenderer] node:', node);
    console.log('[DependencyCellRenderer] colDef:', colDef);

    if (api && node && colDef?.field) {
      // Use AG Grid API to start editing this cell
      api.startEditingCell({
        rowIndex: node.rowIndex!,
        colKey: colDef.field,
      });
      console.log('[DependencyCellRenderer] Started editing cell');
    } else {
      console.error('[DependencyCellRenderer] Missing api, node, or colDef.field');
    }
  }, [api, node, colDef]);

  // Early return for empty or whitespace-only values (avoids unnecessary string operations)
  const trimmedValue = value?.toString().trim();

  if (!trimmedValue) {
    return (
      <div className="flex items-center gap-2 py-1">
        <span className="text-xs text-gray-400">No dependencies</span>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2"
          onClick={handleEditClick}
        >
          <Edit2 className="h-3 w-3 mr-1" />
          Add
        </Button>
      </div>
    );
  }

  // Parse comma-separated IDs (can be numbers or UUIDs)
  const parts = trimmedValue.split(',').map(p => p.trim()).filter(p => p.length > 0);
  const count = parts.length;

  if (count === 0) {
    return (
      <div className="flex items-center gap-2 py-1">
        <span className="text-xs text-gray-400">No dependencies</span>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2"
          onClick={handleEditClick}
        >
          <Edit2 className="h-3 w-3 mr-1" />
          Add
        </Button>
      </div>
    );
  }

  // Get dependency names from data if available (preferred for readability)
  const dependencyNames = data?.dependency_names;
  const displayText = dependencyNames || `${count} ${count === 1 ? 'dependency' : 'dependencies'}`;

  return (
    <div className="flex items-center gap-2 py-1">
      <Badge variant="secondary" className="flex items-center gap-1">
        <Link className="h-3 w-3" />
        <span className="truncate max-w-[200px]" title={dependencyNames || undefined}>
          {displayText}
        </span>
      </Badge>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 px-2"
        onClick={handleEditClick}
      >
        <Edit2 className="h-3 w-3 mr-1" />
        Edit
      </Button>
    </div>
  );
};
