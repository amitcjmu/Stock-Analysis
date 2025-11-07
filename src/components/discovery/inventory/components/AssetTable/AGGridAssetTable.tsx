/**
 * AG Grid-based Asset Table Component (Issue #920 Enhancement)
 *
 * Migrated from custom HTML table to AG Grid for professional appearance
 * matching the gap-analysis page implementation.
 *
 * Features:
 * - Professional AG Grid UI with ag-theme-quartz
 * - Inline editing with validation
 * - Custom cell renderers for badges, progress bars, icons
 * - Row selection and bulk operations
 * - Soft delete with trash view
 * - Column visibility control
 * - Filtering and sorting
 */

import React, { useMemo, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import type {
  ColDef,
  GridReadyEvent,
  CellEditingStoppedEvent,
  SelectionChangedEvent,
} from 'ag-grid-community';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Trash2, RotateCcw } from 'lucide-react';
import type { Asset } from '@/types/asset';
import { AssetTableFilters } from './AssetTableFilters';
import { AssetTablePagination } from './AssetTablePagination';
import { ColumnSelector } from './ColumnSelector';
import { DependencyCellEditor } from './DependencyCellEditor';
import { DependencyCellRenderer } from './DependencyCellRenderer';
import { getReadinessColor, getTypeIcon } from '../../utils/iconHelpers';
import { useAssetInventoryGrid } from '@/hooks/discovery/useAssetInventoryGrid';
import { useAssetSoftDelete } from '@/hooks/discovery/useAssetSoftDelete';

interface AGGridAssetTableProps {
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

export const AGGridAssetTable: React.FC<AGGridAssetTableProps> = ({
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
  enableInlineEditing = true,
}) => {
  // Add custom tooltip styling (from gap-analysis DataGapDiscovery.tsx:56-76)
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .ag-tooltip {
        background-color: #1f2937 !important;
        color: white !important;
        border: 1px solid #374151 !important;
        border-radius: 4px !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        max-width: 400px !important;
        word-wrap: break-word !important;
        z-index: 9999 !important;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  const { editableColumns, updateField, isUpdating } = useAssetInventoryGrid();
  const { softDelete, restore, isDeleting, isRestoring } = useAssetSoftDelete();

  // Pagination
  const totalPages = Math.ceil(filteredAssets.length / recordsPerPage);
  const startIndex = (currentPage - 1) * recordsPerPage;
  const endIndex = startIndex + recordsPerPage;
  const currentAssets = filteredAssets.slice(startIndex, endIndex);

  // Handle inline cell editing
  const handleCellEditingStopped = useCallback(
    (event: CellEditingStoppedEvent<Asset>) => {
      if (event.oldValue !== event.newValue && event.data) {
        const fieldName = event.colDef.field;
        if (fieldName) {
          updateField({
            asset_id: event.data.id,
            field_name: fieldName,
            field_value: event.newValue,
          });
        }
      }
    },
    [updateField]
  );

  // Handle row selection
  const handleSelectionChanged = useCallback(
    (event: SelectionChangedEvent<Asset>) => {
      const selectedRows = event.api.getSelectedRows();
      const selectedIds = selectedRows.map((row) => row.id);

      // CC FIX (Qodo): Check if selection actually changed by comparing IDs, not just length
      // This prevents false negatives when deselecting one asset and selecting another (same length)
      const hasChanged = selectedIds.length !== selectedAssets.length ||
        selectedIds.some(id => !selectedAssets.includes(id)) ||
        selectedAssets.some(id => !selectedIds.includes(id));

      if (hasChanged) {
        onSelectAll(selectedIds);
      }
    },
    [selectedAssets, onSelectAll]
  );

  // Custom cell renderers
  const progressRenderer = useCallback((params: { value: number }) => {
    if (params.value === null || params.value === undefined) {
      return <span className="text-gray-400">-</span>;
    }
    const color = getReadinessColor(params.value);
    return (
      <div className="flex items-center gap-2">
        <Progress value={params.value} className="w-20 h-2" />
        <span className={`text-sm font-medium text-${color}-600`}>
          {params.value}%
        </span>
      </div>
    );
  }, []);

  const criticalityRenderer = useCallback((params: { value: string }) => {
    if (!params.value) return <span className="text-gray-400">-</span>;
    const variant =
      params.value === 'High' ? 'destructive' :
      params.value === 'Medium' ? 'secondary' : 'default';
    return <Badge variant={variant}>{params.value}</Badge>;
  }, []);

  const statusRenderer = useCallback((params: { value: string }) => {
    if (!params.value) return <span className="text-gray-400">-</span>;
    const variant = params.value === 'Active' ? 'default' : 'secondary';
    return <Badge variant={variant}>{params.value}</Badge>;
  }, []);

  const assetTypeRenderer = useCallback((params: { value: string }) => {
    if (!params.value) return <span className="text-gray-400">-</span>;
    const Icon = getTypeIcon(params.value);
    return (
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4" />
        <span>{params.value}</span>
      </div>
    );
  }, []);

  const dateRenderer = useCallback((params: { value: string | null }) => {
    if (!params.value) return <span className="text-gray-400">-</span>;
    return <span>{new Date(params.value).toLocaleDateString()}</span>;
  }, []);

  const actionRenderer = useCallback(
    (params: { data: Asset }) => {
      const asset = params.data;
      if (isTrashView) {
        return (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => restore(asset.id, asset.name)}
            disabled={isRestoring}
            title="Restore asset"
          >
            <RotateCcw className="h-4 w-4 text-green-600" />
          </Button>
        );
      }
      return (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => softDelete(asset.id, asset.name)}
          disabled={isDeleting}
          title="Move to trash"
        >
          <Trash2 className="h-4 w-4 text-red-600" />
        </Button>
      );
    },
    [isTrashView, isDeleting, isRestoring, softDelete, restore]
  );

  // Column definitions
  const columnDefs = useMemo<Array<ColDef<Asset>>>(() => {
    const cols: Array<ColDef<Asset>> = [];

    // Map selected columns to AG Grid column definitions
    selectedColumns.forEach((column) => {
      const colDef: ColDef<Asset> = {
        field: column as keyof Asset,
        headerName: column
          .split('_')
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' '),
        sortable: true,
        filter: true,
        resizable: true,
      };

      // Find if column is editable
      const editableColumn = editableColumns.find((col) => col.field_name === column);
      if (editableColumn && !isTrashView && enableInlineEditing) {
        colDef.editable = true;

        // Set editor based on column type (from useAssetInventoryGrid hook)
        if (editableColumn.column_type === 'dropdown') {
          colDef.cellEditor = 'agSelectCellEditor';
          colDef.cellEditorParams = {
            values: editableColumn.dropdown_options?.map(opt => opt.value) || [],
          };
        } else if (editableColumn.column_type === 'number') {
          colDef.cellEditor = 'agNumberCellEditor';
        } else if (editableColumn.column_type === 'boolean') {
          colDef.cellEditor = 'agCheckboxCellEditor';
        } else if (editableColumn.column_type === 'text') {
          // CC FIX: Explicitly set text editor and enable single-click editing
          colDef.cellEditor = 'agTextCellEditor';
          colDef.cellEditorParams = {
            maxLength: 255,
          };
          // Enable single-click editing for better UX (double-click was reported as not working)
          colDef.singleClickEdit = false; // Keep double-click for consistency
        }

        console.log(`✅ Column "${column}" marked as editable with ${editableColumn.column_type} editor`);
      }

      // Apply custom renderers for special columns
      if (column === 'risk_score' || column === 'migration_readiness') {
        colDef.cellRenderer = progressRenderer;
        colDef.width = 200;
      } else if (column === 'business_criticality' || column === 'criticality') {
        colDef.cellRenderer = criticalityRenderer;
        colDef.width = 150;
      } else if (column === 'status') {
        colDef.cellRenderer = statusRenderer;
        colDef.width = 120;
      } else if (column === 'asset_type') {
        colDef.cellRenderer = assetTypeRenderer;
        colDef.width = 180;
      } else if (column === 'last_updated' || column === 'deleted_at') {
        colDef.cellRenderer = dateRenderer;
        colDef.width = 150;
      } else if (column === 'dependencies' || column === 'dependents') {
        // CC FIX: Custom multi-select editor for dependencies
        colDef.cellRenderer = DependencyCellRenderer;
        colDef.cellEditor = DependencyCellEditor;
        colDef.cellEditorPopup = true; // Show as popup for better UX
        colDef.width = 250;
      }

      cols.push(colDef);
    });

    // Add actions column at the end
    cols.push({
      headerName: 'Actions',
      cellRenderer: actionRenderer,
      width: 100,
      pinned: 'right',
      sortable: false,
      filter: false,
      resizable: false,
    });

    return cols;
  }, [
    selectedColumns,
    editableColumns,
    isTrashView,
    enableInlineEditing,
    progressRenderer,
    criticalityRenderer,
    statusRenderer,
    assetTypeRenderer,
    dateRenderer,
    actionRenderer,
  ]);

  const defaultColDef = useMemo<ColDef<Asset>>(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
      tooltipValueGetter: (params) => params.value,
    }),
    []
  );

  // CC FIX: Store AG Grid API reference for column state management
  const gridApiRef = React.useRef<GridReadyEvent<Asset>['api'] | null>(null);

  const onGridReady = useCallback((params: GridReadyEvent<Asset>) => {
    gridApiRef.current = params.api;

    // Set initial selection based on selectedAssets prop
    params.api.forEachNode((node) => {
      if (node.data && selectedAssets.includes(node.data.id)) {
        node.setSelected(true);
      }
    });

    // CC FIX: Restore column state from localStorage if available
    try {
      const savedState = localStorage.getItem('ag-grid-column-state');
      if (savedState) {
        const columnState = JSON.parse(savedState);
        params.api.applyColumnState({ state: columnState, applyOrder: true });
      }
    } catch (error) {
      console.error('Failed to restore column state:', error);
    }
  }, [selectedAssets]);

  // CC FIX: Save column state whenever columns are moved or resized
  const handleColumnEvent = useCallback(() => {
    if (gridApiRef.current) {
      const columnState = gridApiRef.current.getColumnState();
      try {
        localStorage.setItem('ag-grid-column-state', JSON.stringify(columnState));
      } catch (error) {
        console.error('Failed to save column state:', error);
      }
    }
  }, []);

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
        {/* Inline editing hint - similar to gap-analysis description */}
        {enableInlineEditing && !isTrashView && (
          <div className="text-sm text-muted-foreground mt-2">
            Click cells to edit directly. Changes are saved automatically.
            <Badge className="ml-2 bg-green-100 text-green-800">Editable</Badge>
          </div>
        )}
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

        <div className="mt-4">
          <div
            className={`ag-theme-quartz ${isTrashView ? 'opacity-60' : ''}`}
            style={{ height: 600, width: '100%' }}
          >
            <AgGridReact<Asset>
              theme="legacy"
              rowData={currentAssets}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              rowSelection={{
                mode: 'multiRow',
                checkboxes: true,
                headerCheckbox: true,
                enableClickSelection: false, // Fix: Use this instead of suppressRowClickSelection (AG Grid v32.2+)
              }}
              onGridReady={onGridReady}
              onCellEditingStopped={handleCellEditingStopped}
              onSelectionChanged={handleSelectionChanged}
              onColumnMoved={handleColumnEvent}
              onColumnResized={handleColumnEvent}
              onColumnVisible={handleColumnEvent}
              getRowId={(params) => String(params.data.id)}
              enableCellTextSelection={true}
              ensureDomOrder={true}
            />
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
