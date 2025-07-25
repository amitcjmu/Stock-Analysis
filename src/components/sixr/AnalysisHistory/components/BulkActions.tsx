import React from 'react';
import { Button } from '../../../ui/button';
import { GitCompare, Archive, Trash2 } from 'lucide-react';

interface BulkActionsProps {
  selectedCount: number;
  onCompare: () => void;
  onArchive: () => void;
  onDelete: () => void;
}

export const BulkActions: React.FC<BulkActionsProps> = ({
  selectedCount,
  onCompare,
  onArchive,
  onDelete
}) => {
  if (selectedCount === 0) return null;

  return (
    <div className="flex items-center gap-3 py-3 px-4 bg-blue-50 border rounded-lg">
      <span className="text-sm font-medium">
        {selectedCount} analysis{selectedCount > 1 ? 'es' : ''} selected
      </span>

      <div className="flex gap-2 ml-auto">
        {selectedCount >= 2 && (
          <Button
            variant="outline"
            size="sm"
            onClick={onCompare}
          >
            <GitCompare className="h-4 w-4 mr-1" />
            Compare
          </Button>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={onArchive}
        >
          <Archive className="h-4 w-4 mr-1" />
          Archive
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={onDelete}
          className="text-red-600 hover:text-red-700"
        >
          <Trash2 className="h-4 w-4 mr-1" />
          Delete
        </Button>
      </div>
    </div>
  );
};
