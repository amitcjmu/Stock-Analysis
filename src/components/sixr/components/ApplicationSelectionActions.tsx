/**
 * ApplicationSelectionActions Component
 * Extracted from ApplicationSelector.tsx for modularization
 */

import React from 'react';
import { Plus, Minus, Download, Upload } from 'lucide-react';
import { Button } from '../../ui/button';

interface ApplicationSelectionActionsProps {
  selectedCount: number;
  filteredCount: number;
  allSelected: boolean;
  onSelectAll: () => void;
}

export const ApplicationSelectionActions: React.FC<ApplicationSelectionActionsProps> = ({
  selectedCount,
  filteredCount,
  allSelected,
  onSelectAll
}) => {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onSelectAll}
        >
          {allSelected ? (
            <>
              <Minus className="h-4 w-4 mr-1" />
              Deselect All
            </>
          ) : (
            <>
              <Plus className="h-4 w-4 mr-1" />
              Select All
            </>
          )}
        </Button>
        {selectedCount > 0 && (
          <span className="text-sm text-gray-600">
            {selectedCount} applications selected
          </span>
        )}
      </div>
      <div className="flex items-center space-x-2">
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-1" />
          Export
        </Button>
        <Button variant="outline" size="sm">
          <Upload className="h-4 w-4 mr-1" />
          Import
        </Button>
      </div>
    </div>
  );
};