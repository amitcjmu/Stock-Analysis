import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import type { AssetInventory } from '../../types/inventory.types';
import { AssetTableFilters } from './AssetTableFilters';
import { AssetTablePagination } from './AssetTablePagination';
import { ColumnSelector } from './ColumnSelector';
import { getReadinessColor } from '../../utils/iconHelpers'
import { getTypeIcon } from '../../utils/iconHelpers'

interface AssetTableProps {
  assets: AssetInventory[];
  filteredAssets: AssetInventory[];
  selectedAssets: string[];
  onSelectAsset: (assetId: string) => void;
  onSelectAll: (assetIds: string[]) => void;
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
}

export const AssetTable: React.FC<AssetTableProps> = ({
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
  isReclassifying
}) => {
  const totalPages = Math.ceil(filteredAssets.length / recordsPerPage);
  const startIndex = (currentPage - 1) * recordsPerPage;
  const endIndex = startIndex + recordsPerPage;
  const currentAssets = filteredAssets.slice(startIndex, endIndex);
  const currentAssetIds = currentAssets.map(a => a.id);

  const formatValue = (value: unknown, column: string): JSX.Element => {
    if (value === null || value === undefined) return '-';

    if (column === 'risk_score' || column === 'migration_readiness') {
      const numValue = typeof value === 'number' ? value : parseInt(value);
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
      return <Badge variant={variant}>{value}</Badge>;
    }

    if (column === 'status') {
      const variant = value === 'Active' ? 'default' : 'secondary';
      return <Badge variant={variant}>{value}</Badge>;
    }

    if (column === 'asset_type') {
      const Icon = getTypeIcon(value);
      return (
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4" />
          <span>{value}</span>
        </div>
      );
    }

    if (column === 'last_updated' && value) {
      return new Date(value).toLocaleDateString();
    }

    return String(value);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Asset Inventory</CardTitle>
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
        />

        <div className="mt-4 border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
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
                </tr>
              </thead>
              <tbody className="divide-y">
                {currentAssets.map((asset) => (
                  <tr key={asset.id} className="hover:bg-gray-50">
                    <td className="p-3">
                      <Checkbox
                        checked={selectedAssets.includes(asset.id)}
                        onCheckedChange={() => onSelectAsset(asset.id)}
                      />
                    </td>
                    {selectedColumns.map(column => (
                      <td key={column} className="p-3 text-sm">
                        {formatValue(asset[column], column)}
                      </td>
                    ))}
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
