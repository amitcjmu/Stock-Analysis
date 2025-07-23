import React from 'react';
import { Table, TableBody, TableHead, TableHeader, TableRow } from '../../../ui/table';
import { Checkbox } from '../../../ui/checkbox';
import { AnalysisHistoryItem } from '../types';
import { AnalysisTableRow } from './AnalysisTableRow';

interface AnalysisTableProps {
  analyses: AnalysisHistoryItem[];
  selectedAnalyses: number[];
  onSelectAnalysis: (id: number) => void;
  onSelectAll: (ids: number[]) => void;
  onViewDetails?: (id: number) => void;
  onArchive?: (id: number) => void;
  onDelete?: (id: number) => void;
}

export const AnalysisTable: React.FC<AnalysisTableProps> = ({
  analyses,
  selectedAnalyses,
  onSelectAnalysis,
  onSelectAll,
  onViewDetails,
  onArchive,
  onDelete
}) => {
  const allAnalysisIds = analyses.map(a => a.id);
  const allSelected = allAnalysisIds.length > 0 && 
    allAnalysisIds.every(id => selectedAnalyses.includes(id));

  return (
    <div className="border rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox
                checked={allSelected}
                onCheckedChange={() => onSelectAll(allAnalysisIds)}
              />
            </TableHead>
            <TableHead>Application</TableHead>
            <TableHead>Analysis Date</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Strategy</TableHead>
            <TableHead>Confidence</TableHead>
            <TableHead>Effort</TableHead>
            <TableHead>Timeline</TableHead>
            <TableHead>Analyst</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {analyses.length === 0 ? (
            <TableRow>
              <TableCell colSpan={10} className="text-center py-8 text-gray-500">
                No analyses found matching your criteria
              </TableCell>
            </TableRow>
          ) : (
            analyses.map(analysis => (
              <AnalysisTableRow
                key={analysis.id}
                analysis={analysis}
                isSelected={selectedAnalyses.includes(analysis.id)}
                onSelect={onSelectAnalysis}
                onViewDetails={onViewDetails}
                onArchive={onArchive}
                onDelete={onDelete}
              />
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
};