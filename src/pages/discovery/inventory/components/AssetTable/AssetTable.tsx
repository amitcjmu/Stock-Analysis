import React from 'react';
import { Loader2, AlertCircle, ArrowUpDown, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Asset } from '@/types/discovery';
import { AssetRow } from './AssetRow';
import { AssetTableProps } from '../../types';

export const AssetTable: React.FC<AssetTableProps> = ({
  assets,
  selectedAssets,
  onSelectAsset,
  onSelectAll,
  onSort,
  sortConfig,
  isLoading,
  error,
  columnVisibility
}) => {
  const allSelected = assets.length > 0 && selectedAssets.length === assets.length;
  const someSelected = selectedAssets.length > 0 && !allSelected;

  const handleSort = (key: string) => {
    onSort(key);
  };

  const renderSortIcon = (key: string) => {
    if (!sortConfig) return null;
    if (sortConfig.key !== key) return null;
    return (
      <span className="ml-1">
        {sortConfig.direction === 'asc' ? '↑' : '↓'}
      </span>
    );
  };

  const renderHeaderCell = (key: string, label: string, sortable = true) => {
    if (!columnVisibility[key]) return null;
    
    return (
      <th 
        className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${sortable ? 'cursor-pointer hover:bg-gray-50' : ''}`}
        onClick={sortable ? () => handleSort(key) : undefined}
      >
        <div className="flex items-center">
          {label}
          {sortable && renderSortIcon(key)}
        </div>
      </th>
    );
  };

  if (isLoading) {
    return (
      <div className="mt-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center space-x-4 p-4 border-b">
            <Skeleton className="h-4 w-4 rounded" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-20" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 mt-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <AlertCircle className="h-5 w-5 text-red-400" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">
              Failed to load assets: {error.message}
            </p>
            <div className="mt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.reload()}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (assets.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg shadow">
        <Database className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No assets found</h3>
        <p className="mt-1 text-sm text-gray-500">
          Try adjusting your search or filter criteria.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-4 overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    checked={allSelected}
                    ref={input => {
                      if (input) {
                        input.indeterminate = someSelected;
                      }
                    }}
                    onChange={e => onSelectAll(e.target.checked)}
                  />
                </div>
              </th>
              {renderHeaderCell('name', 'Name')}
              {renderHeaderCell('type', 'Type')}
              {renderHeaderCell('environment', 'Environment')}
              {renderHeaderCell('department', 'Department')}
              {renderHeaderCell('criticality', 'Criticality')}
              {renderHeaderCell('last_seen', 'Last Seen')}
              <th className="px-4 py-3 text-right">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {assets.map((asset) => (
              <AssetRow
                key={asset.id}
                asset={asset}
                isSelected={selectedAssets.includes(asset.id)}
                onSelect={onSelectAsset}
                columnVisibility={columnVisibility}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
