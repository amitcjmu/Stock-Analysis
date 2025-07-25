import React from 'react';
import { TableCell, TableRow } from '../../../ui/table';
import { Checkbox } from '../../../ui/checkbox';
import { Button } from '../../../ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../../ui/dropdown-menu';
import { Eye, Archive, Trash2, MoreHorizontal, Star } from 'lucide-react';
import type { AnalysisHistoryItem } from '../types';
import { StrategyBadge } from './StrategyBadge';
import { StatusBadge } from './StatusBadge';
import { effortColors } from '../constants';
import { formatDate } from '../utils/dateUtils';

interface AnalysisTableRowProps {
  analysis: AnalysisHistoryItem;
  isSelected: boolean;
  onSelect: (id: number) => void;
  onViewDetails?: (id: number) => void;
  onArchive?: (id: number) => void;
  onDelete?: (id: number) => void;
}

export const AnalysisTableRow: React.FC<AnalysisTableRowProps> = ({
  analysis,
  isSelected,
  onSelect,
  onViewDetails,
  onArchive,
  onDelete
}) => {
  const effortColor = effortColors[analysis.estimated_effort.toLowerCase().replace(' ', '_') as keyof typeof effortColors] || 'bg-gray-100 text-gray-800';

  return (
    <TableRow key={analysis.id}>
      <TableCell className="w-12">
        <Checkbox
          checked={isSelected}
          onCheckedChange={() => onSelect(analysis.id)}
        />
      </TableCell>
      <TableCell>
        <div>
          <div className="font-medium">{analysis.application_name}</div>
          <div className="text-sm text-gray-500">{analysis.department}</div>
        </div>
      </TableCell>
      <TableCell>
        {formatDate(analysis.analysis_date)}
      </TableCell>
      <TableCell>
        <StatusBadge status={analysis.status} />
      </TableCell>
      <TableCell>
        <StrategyBadge strategy={analysis.recommended_strategy} />
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <span className="font-medium">{analysis.confidence_score}%</span>
          {analysis.confidence_score >= 80 && (
            <Star className="h-4 w-4 text-yellow-500 fill-current" />
          )}
        </div>
      </TableCell>
      <TableCell>
        <span className={`inline-flex px-2 py-1 text-xs rounded-full ${effortColor}`}>
          {analysis.estimated_effort}
        </span>
      </TableCell>
      <TableCell>{analysis.estimated_timeline}</TableCell>
      <TableCell>{analysis.analyst}</TableCell>
      <TableCell>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {onViewDetails && (
              <DropdownMenuItem onClick={() => onViewDetails(analysis.id)}>
                <Eye className="h-4 w-4 mr-2" />
                View Details
              </DropdownMenuItem>
            )}
            {onArchive && analysis.status !== 'archived' && (
              <DropdownMenuItem onClick={() => onArchive(analysis.id)}>
                <Archive className="h-4 w-4 mr-2" />
                Archive
              </DropdownMenuItem>
            )}
            {onDelete && (
              <DropdownMenuItem
                onClick={() => onDelete(analysis.id)}
                className="text-red-600"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
};
