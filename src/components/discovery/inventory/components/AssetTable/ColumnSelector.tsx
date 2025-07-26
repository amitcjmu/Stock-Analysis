import React from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { SlidersHorizontal } from 'lucide-react';

interface ColumnSelectorProps {
  allColumns: string[];
  selectedColumns: string[];
  onToggleColumn: (column: string) => void;
}

export const ColumnSelector: React.FC<ColumnSelectorProps> = ({
  allColumns,
  selectedColumns,
  onToggleColumn
}) => {
  const formatColumnName = (column: string): unknown => {
    return column
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <SlidersHorizontal className="h-4 w-4 mr-2" />
          Columns
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64 p-4 max-h-96 overflow-y-auto">
        <div className="space-y-2">
          <h4 className="font-medium text-sm mb-3">Visible Columns</h4>
          {allColumns.map(column => (
            <div key={column} className="flex items-center justify-between">
              <Label
                htmlFor={`column-${column}`}
                className="text-sm font-normal cursor-pointer"
              >
                {formatColumnName(column)}
              </Label>
              <Switch
                id={`column-${column}`}
                checked={selectedColumns.includes(column)}
                onCheckedChange={() => onToggleColumn(column)}
              />
            </div>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
