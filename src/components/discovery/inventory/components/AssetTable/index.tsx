import React from 'react';
import type { Asset } from '@/types/asset';
import { EnhancedAssetTable } from './EnhancedAssetTable';

interface AssetTableProps {
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
  enableInlineEditing?: boolean;
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
  isReclassifying,
  onProcessForAssessment,
  isApplicationsSelected,
  isTrashView = false,
  enableInlineEditing = true  // CC FIX: Enable inline editing by default (AG Grid migration)
}) => {
  return (
    <EnhancedAssetTable
      assets={assets}
      filteredAssets={filteredAssets}
      selectedAssets={selectedAssets}
      onSelectAsset={onSelectAsset}
      onSelectAll={onSelectAll}
      searchTerm={searchTerm}
      onSearchChange={onSearchChange}
      selectedEnvironment={selectedEnvironment}
      onEnvironmentChange={onEnvironmentChange}
      uniqueEnvironments={uniqueEnvironments}
      showAdvancedFilters={showAdvancedFilters}
      onToggleAdvancedFilters={onToggleAdvancedFilters}
      onExport={onExport}
      currentPage={currentPage}
      recordsPerPage={recordsPerPage}
      onPageChange={onPageChange}
      selectedColumns={selectedColumns}
      allColumns={allColumns}
      onToggleColumn={onToggleColumn}
      onReclassifySelected={onReclassifySelected}
      isReclassifying={isReclassifying}
      onProcessForAssessment={onProcessForAssessment}
      isApplicationsSelected={isApplicationsSelected}
      isTrashView={isTrashView}
      enableInlineEditing={enableInlineEditing}
    />
  );
};
