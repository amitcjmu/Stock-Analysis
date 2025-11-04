/**
 * Enhanced Asset Table Component (Issues #911 and #912)
 * Features:
 * - AI Grid inline editing with validation
 * - Soft delete with trash view
 * - Restore functionality
 * - Bulk operations
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Trash2, RotateCcw } from 'lucide-react';
import type { Asset } from '@/types/asset';
import { AssetTableFilters } from './AssetTableFilters';
import { AssetTablePagination } from './AssetTablePagination';
import { ColumnSelector } from './ColumnSelector';
import { EditableCell } from './EditableCell';
import { getReadinessColor, getTypeIcon } from '../../utils/iconHelpers';
import { useAssetInventoryGrid } from '@/hooks/discovery/useAssetInventoryGrid';
import { useAssetSoftDelete } from '@/hooks/discovery/useAssetSoftDelete';

interface EnhancedAssetTableProps {
  assets: Asset[];
  filteredAssets: Asset[];
  selectedAssets: number[];
  onSelectAsset: (assetId: number) => void;
  onSelectAll: (assetIds: number[]) => void;
  searchTerm: string;
  onSearchChange: (value: string) => void;
  selectedEnvironment: string;
  onEnvironmentChange: (value: string) => void;
  uniqueEnvironments: string[];
  showAdvancedFilters: boolean;
  onToggleAdvancedFilters: () => void;
  onExport: () => void;
  currentPage: number;
  recordsPerPage: number;
  onPageChange: (page: number) => void;
  selectedColumns: string[];
  allColumns: string[];
  onToggleColumn: (column: string) => void;
  onReclassifySelected?: () => void;
  isReclassifying?: boolean;
  onProcessForAssessment?: () => void;
  isApplicationsSelected?: boolean;
  isTrashView?: boolean;
}

export const EnhancedAssetTable: React.FC<EnhancedAssetTableProps> = ({
  assets,
  filteredAssets,
  selectedAssets,
  onSelectAsset,
  onSelectAll,
  searchTerm,
  onSearchChange,
  selectedEnvironment,
  onEnvironmentChange,
  uniqueEnvironments,
  showAdvancedFilters,
  onToggleAdvancedFilters,
  onExport,
  currentPage,
  recordsPerPage,
  onPageChange,
  selectedColumns,
  allColumns,
  onToggleColumn,
  onReclassifySelected,
  isReclassifying,
  onProcessForAssessment,
  isApplicationsSelected,
  isTrashView = false
}) => {
  const { editableColumns, updateField, isUpdating } = useAssetInventoryGrid();
  const { softDelete, restore, isDeleting, isRestoring } = useAssetSoftDelete();

  const totalPages = Math.ceil(filteredAssets.length / recordsPerPage);
  const startIndex = (currentPage - 1) * recordsPerPage;
  const endIndex = startIndex + recordsPerPage;
  const currentAssets = filteredAssets.slice(startIndex, endIndex);
  const currentAssetIds = currentAssets.map(a => a.id);

  const handleCellEdit = async (asset_id: number, field_name: string, field_value: any) => {
    updateField({ asset_id, field_name, field_value });
  };

  const handleDelete = (asset: Asset) => {
    softDelete(asset.id, asset.name);
  };

  const handleRestore = (asset: Asset) => {
    restore(asset.id, asset.name);
  };

  const formatValue = (asset: Asset, column: string): JSX.Element => {
    const value = asset[column as keyof Asset];

    if (value === null || value === undefined) return <span>-</span>;

    // Find editable column configuration
    const editableColumn = editableColumns.find(col => col.field_name === column);

    // If column is editable and not in trash view, render EditableCell
    if (editableColumn && !isTrashView) {
      return (
        <EditableCell
          value={value}
          column={editableColumn}
          onSave={(newValue) => handleCellEdit(asset.id, column, newValue)}
          isUpdating={isUpdating}
        />
      );
    }

    // Special formatting for non-editable or trash view columns
    if (column === 'risk_score' || column === 'migration_readiness') {
      const numValue = typeof value === 'number' ? value : parseInt(value as string);
      const color = getReadinessColor(numValue);
      return (
        <div className="flex items-center gap-2">
          <Progress value={numValue} className={`w-20 h-2`} />
          <span className={`text-sm font-medium text-${color}-600`}>
            {numValue}%
          </span>
        </div>
      );
    }

    if (column === 'business_criticality' || column === 'criticality') {
      const variant = value === 'High' ? 'destructive' :
                     value === 'Medium' ? 'secondary' : 'default';
      return <Badge variant={variant}>{String(value)}</Badge>;
    }

    if (column === 'status') {
      const variant = value === 'Active' ? 'default' : 'secondary';
      return <Badge variant={variant}>{String(value)}</Badge>;
    }

    if (column === 'asset_type') {
      const Icon = getTypeIcon(value as string);
      return (
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4" />
          <span>{String(value)}</span>
        </div>
      );
    }

    if ((column === 'last_updated' || column === 'deleted_at') && value) {
      return <span>{new Date(value as string).toLocaleDateString()}</span>;
    }

    return <span>{String(value)}</span>;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>
            {isTrashView ? 'Deleted Assets (Trash)' : 'Asset Inventory'}
          </CardTitle>
          <ColumnSelector
            allColumns={allColumns}
            selectedColumns={selectedColumns}
            onToggleColumn={onToggleColumn}
          />
        </div>
      </CardHeader>
      <CardContent>
        <AssetTableFilters
          searchTerm={searchTerm}
          onSearchChange={onSearchChange}
          selectedEnvironment={selectedEnvironment}
          onEnvironmentChange={onEnvironmentChange}
          uniqueEnvironments={uniqueEnvironments}
          showAdvancedFilters={showAdvancedFilters}
          onToggleAdvancedFilters={onToggleAdvancedFilters}
          onExport={onExport}
          selectedCount={selectedAssets.length}
          onReclassifySelected={onReclassifySelected}
          isReclassifying={isReclassifying}
          onProcessForAssessment={onProcessForAssessment}
          isApplicationsSelected={isApplicationsSelected}
        />

        <div className="mt-4 border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className={`${isTrashView ? 'bg-red-50' : 'bg-gray-50'} border-b`}>
                <tr>
                  <th className="p-3 text-left">
                    <Checkbox
                      checked={currentAssetIds.length > 0 &&
                        currentAssetIds.every(id => selectedAssets.includes(id))}
                      onCheckedChange={() => onSelectAll(currentAssetIds)}
                    />
                  </th>
                  {selectedColumns.map(column => (
                    <th key={column} className="p-3 text-left text-sm font-medium text-gray-700">
                      {column.split('_').map(word =>
                        word.charAt(0).toUpperCase() + word.slice(1)
                      ).join(' ')}
                    </th>
                  ))}
                  <th className="p-3 text-left text-sm font-medium text-gray-700">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {currentAssets.map((asset) => (
                  <tr
                    key={asset.id}
                    className={`hover:bg-gray-50 ${isTrashView ? 'opacity-60' : ''}`}
                  >
                    <td className="p-3">
                      <Checkbox
                        checked={selectedAssets.includes(asset.id)}
                        onCheckedChange={() => onSelectAsset(asset.id)}
                      />
                    </td>
                    {selectedColumns.map(column => (
                      <td key={column} className="p-3 text-sm">
                        {formatValue(asset, column)}
                      </td>
                    ))}
                    <td className="p-3">
                      {isTrashView ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRestore(asset)}
                          disabled={isRestoring}
                          title="Restore asset"
                        >
                          <RotateCcw className="h-4 w-4 text-green-600" />
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(asset)}
                          disabled={isDeleting}
                          title="Move to trash"
                        >
                          <Trash2 className="h-4 w-4 text-red-600" />
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {totalPages > 1 && (
          <AssetTablePagination
            currentPage={currentPage}
            totalPages={totalPages}
            startRecord={startIndex + 1}
            endRecord={Math.min(endIndex, filteredAssets.length)}
            totalRecords={filteredAssets.length}
            onPageChange={onPageChange}
          />
        )}
      </CardContent>
    </Card>
  );
};
